# Market Simulator

Documents the approach and code structure of the built-in price simulator — the default
market data source used whenever `MASSIVE_API_KEY` is not set (PLAN.md §6, §5). Implemented
in `backend/app/market/simulator.py` and `backend/app/market/seed_prices.py`; wired into
the shared `MarketDataSource` interface documented in `MARKET_INTERFACE.md`.

## Goal

Produce live-looking price action with zero external dependencies: correlated moves across
related tickers, realistic volatility differences per stock, and occasional dramatic
one-off moves — enough visual life for a trading-terminal demo without needing a market
data subscription.

## Two-layer design

```
GBMSimulator          — pure math: tickers → next prices, no I/O, no asyncio
        │
        ▼
SimulatorDataSource    — MarketDataSource adapter: owns the asyncio loop, writes to PriceCache
```

`GBMSimulator` is deliberately decoupled from the cache/asyncio machinery — `step()` is a
plain synchronous function (`dict[str, float] -> dict[str, float]` conceptually), which is
what makes it unit-testable in isolation (`tests/market/test_simulator.py`, 17 tests, 98%
coverage) without spinning up an event loop.

## The math: Geometric Brownian Motion

Each ticker's price evolves under GBM, the standard model for a random walk with drift used
throughout quantitative finance:

```
S(t+dt) = S(t) * exp((mu - sigma^2/2) * dt + sigma * sqrt(dt) * Z)
```

- `S(t)` — current price
- `mu` — annualized drift (expected return)
- `sigma` — annualized volatility
- `dt` — time step, expressed as a fraction of a trading year
- `Z` — a (correlated) standard normal random draw

```python
drift = (mu - 0.5 * sigma**2) * dt
diffusion = sigma * math.sqrt(dt) * z_correlated[i]
new_price = price * math.exp(drift + diffusion)
```

### Choosing `dt` for 500ms ticks

The simulator ticks every 500ms (matching the SSE push interval, PLAN.md §6), so `dt` is
500ms expressed as a fraction of a trading year:

```python
TRADING_SECONDS_PER_YEAR = 252 * 6.5 * 3600  # 5,896,800 (252 trading days, 6.5h each)
DEFAULT_DT = 0.5 / TRADING_SECONDS_PER_YEAR  # ~8.48e-8
```

This tiny `dt` naturally produces sub-cent moves per tick, which accumulate into
realistic-looking intraday movement over minutes of real time — no artificial clamping or
smoothing needed to avoid unrealistic per-tick jumps.

## Correlated moves via Cholesky decomposition

Real markets don't move independently — tech stocks tend to move together, unrelated
sectors less so. The simulator reproduces this by drawing **correlated** standard normal
variables instead of independent ones per ticker, using a Cholesky decomposition of a
sector-based correlation matrix:

```python
z_independent = np.random.standard_normal(n)      # n independent draws
z_correlated = self._cholesky @ z_independent      # apply correlation structure
```

The correlation matrix is built per-pair from sector grouping (`seed_prices.py`):

```python
CORRELATION_GROUPS = {
    "tech": {"AAPL", "GOOGL", "MSFT", "AMZN", "META", "NVDA", "NFLX"},
    "finance": {"JPM", "V"},
}
INTRA_TECH_CORR = 0.6      # tech stocks move together
INTRA_FINANCE_CORR = 0.5   # finance stocks move together
CROSS_GROUP_CORR = 0.3     # different sectors, or either ticker unknown
TSLA_CORR = 0.3            # TSLA is in the tech set but treated as independent-ish
```

```python
def _pairwise_correlation(t1: str, t2: str) -> float:
    if t1 == "TSLA" or t2 == "TSLA":
        return TSLA_CORR
    if t1 in tech and t2 in tech:
        return INTRA_TECH_CORR
    if t1 in finance and t2 in finance:
        return INTRA_FINANCE_CORR
    return CROSS_GROUP_CORR
```

The full `n x n` correlation matrix (1s on the diagonal, pairwise `rho` off-diagonal) is
decomposed once via `np.linalg.cholesky(corr)` and cached; `step()` reuses the cached
decomposition every tick, only paying the `O(n^2)`-ish decomposition cost when tickers are
added or removed (`_rebuild_cholesky()`), not on every 500ms step. With `n < 50` tickers
(30-ticker watchlist cap, PLAN.md §7) this is cheap even on every add/remove.

## Random shock events

To avoid prices looking too smooth/boring over a short demo session, each ticker has a
small independent chance per tick of a sudden 2-5% move:

```python
event_probability: float = 0.001  # 0.1% per tick per ticker

if random.random() < self._event_prob:
    shock_magnitude = random.uniform(0.02, 0.05)
    shock_sign = random.choice([-1, 1])
    self._prices[ticker] *= 1 + shock_magnitude * shock_sign
```

At 2 ticks/sec (500ms interval) across 10 default tickers, this works out to roughly one
shock event every ~50 seconds somewhere in the watchlist — frequent enough to be
noticeable during a live demo, rare enough not to dominate the GBM drift/diffusion.

## Seed data

`seed_prices.py` provides realistic starting points and per-ticker parameters for the
default watchlist:

```python
SEED_PRICES = {"AAPL": 190.00, "GOOGL": 175.00, "MSFT": 420.00, ...}

TICKER_PARAMS = {
    "AAPL":  {"sigma": 0.22, "mu": 0.05},
    "TSLA":  {"sigma": 0.50, "mu": 0.03},  # high volatility
    "NVDA":  {"sigma": 0.40, "mu": 0.08},  # high volatility, strong drift
    "JPM":   {"sigma": 0.18, "mu": 0.04},  # low volatility (bank)
    "V":     {"sigma": 0.17, "mu": 0.04},  # low volatility (payments)
    ...
}

DEFAULT_PARAMS = {"sigma": 0.25, "mu": 0.05}  # fallback for dynamically-added tickers
```

A ticker added at runtime that isn't in `SEED_PRICES`/`TICKER_PARAMS` (e.g., the user or
the LLM adds `"PYPL"` to the watchlist) falls back to `DEFAULT_PARAMS` for its GBM
parameters and a `random.uniform(50.0, 300.0)` starting price — plausible enough for demo
purposes without needing a real quote to seed from.

## `GBMSimulator` — the pure simulation core

`app/market/simulator.py`. Public surface:

```python
sim = GBMSimulator(tickers=["AAPL", "GOOGL", ...], event_probability=0.001)

prices = sim.step()          # dict[str, float] — advance one tick, hot path (500ms)
sim.add_ticker("TSLA")       # rebuilds Cholesky
sim.remove_ticker("GOOGL")   # rebuilds Cholesky
sim.get_price("AAPL")        # float | None
sim.get_tickers()            # list[str]
```

`step()` is the hot path — called on every tick for every active ticker — and is kept
allocation-light: one `np.random.standard_normal(n)` call, one matrix multiply, then a
per-ticker loop doing scalar float math. All internal state (`_prices`, `_params`,
`_tickers`, `_cholesky`) is private; consumers only see the four public methods above.

## `SimulatorDataSource` — the `MarketDataSource` adapter

`app/market/simulator.py`. Bridges the pure `GBMSimulator` into the async
`MarketDataSource` contract (`MARKET_INTERFACE.md`):

```python
class SimulatorDataSource(MarketDataSource):
    def __init__(self, price_cache: PriceCache, update_interval: float = 0.5,
                 event_probability: float = 0.001):
        ...

    async def start(self, tickers: list[str]) -> None:
        self._sim = GBMSimulator(tickers=tickers, event_probability=self._event_prob)
        for ticker in tickers:                       # seed the cache immediately —
            price = self._sim.get_price(ticker)       # don't make the first SSE client
            if price is not None:                      # wait up to 500ms for tick 1
                self._cache.update(ticker=ticker, price=price)
        self._task = asyncio.create_task(self._run_loop(), name="simulator-loop")

    async def _run_loop(self) -> None:
        while True:
            try:
                if self._sim:
                    for ticker, price in self._sim.step().items():
                        self._cache.update(ticker=ticker, price=price)
            except Exception:
                logger.exception("Simulator step failed")   # never let one bad
            await asyncio.sleep(self._interval)               # step kill the loop
```

`add_ticker`/`remove_ticker` on the data source delegate straight to the simulator, then
(for add) immediately seed the cache with the new ticker's starting price the same way
`start()` does — so a newly-watchlisted ticker has a price before the next tick, matching
the "ticker just added returns `price: null` until the cache has a value" behavior
documented for the real Massive path in PLAN.md §8 (the simulator just closes that window
faster since there's no network round-trip).

`stop()` cancels the `asyncio.Task` and awaits its `CancelledError`, matching the same
idempotent-stop contract as `MassiveDataSource` (`MARKET_INTERFACE.md`) — both
implementations can be stopped more than once safely.

## Why this design

| Choice | Rationale |
|---|---|
| GBM over a random walk on price directly | Standard, well-understood model; guarantees prices stay positive (log-normal), unlike additive noise |
| Cholesky-correlated draws over independent per-ticker noise | Sector correlation is the single biggest visual cue that makes the simulator feel like a real market rather than N unrelated coin flips |
| Sector-group correlation over a full historical correlation matrix | No external data needed to seed correlations; "tech stocks move together" is close enough for a demo and trivially explainable |
| Occasional random shocks | Pure GBM at realistic `sigma` looks visually flat over a short demo session; shocks create the "something's happening" moments the terminal aesthetic wants (PLAN.md §2) |
| Pure `GBMSimulator` decoupled from asyncio | Enables fast, deterministic-seed-free unit testing of the math without an event loop; `SimulatorDataSource` is the only piece that needs `pytest-asyncio` |
| Same `PriceCache`/`MarketDataSource` contract as `MassiveDataSource` | Swapping to real data by setting `MASSIVE_API_KEY` requires no changes anywhere else in the app (SSE, portfolio, trade execution) |
