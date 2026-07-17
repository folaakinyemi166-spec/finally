# Unified Market Data Interface

Documents the actual implementation in `backend/app/market/` — a source-agnostic Python
API for retrieving live stock prices, backed by either the Massive API (§`MASSIVE_API.md`)
or an in-process simulator (§`MARKET_SIMULATOR.md`), selected automatically by whether
`MASSIVE_API_KEY` is set.

## Goal

Every consumer of prices in FinAlly (the SSE stream, portfolio valuation, trade execution)
should be able to read "the current price of AAPL" without knowing or caring whether that
price came from a real Massive API poll or a simulated GBM walk. This is a textbook
Strategy pattern: one abstract producer interface, two interchangeable implementations,
one shared consumer-facing cache.

```
MarketDataSource (ABC)                          — the strategy interface
├── SimulatorDataSource   → GBMSimulator          — used when no MASSIVE_API_KEY
└── MassiveDataSource     → massive.RESTClient     — used when MASSIVE_API_KEY is set
        │
        ▼
   PriceCache (thread-safe, in-memory)            — the shared consumer-facing store
        │
        ├──→ SSE stream endpoint (/api/stream/prices)
        ├──→ Portfolio valuation (§8 PLAN.md)
        └──→ Trade execution      (§8 PLAN.md)
```

Module layout (`backend/app/market/`):

| File | Responsibility |
|------|-----------------|
| `models.py` | `PriceUpdate` — immutable, frozen price snapshot |
| `interface.py` | `MarketDataSource` ABC — the contract both sources implement |
| `cache.py` | `PriceCache` — thread-safe store, single point of truth for readers |
| `factory.py` | `create_market_data_source()` — picks a source based on env var |
| `simulator.py` | `SimulatorDataSource` (wraps `GBMSimulator`, see `MARKET_SIMULATOR.md`) |
| `massive_client.py` | `MassiveDataSource` (wraps `massive.RESTClient`) |
| `seed_prices.py` | Simulator-only seed data (not part of the public interface) |
| `stream.py` | `create_stream_router()` — FastAPI SSE endpoint reading from `PriceCache` |

## `PriceUpdate` — the shared price model

`app/market/models.py`. An immutable, frozen dataclass — every price observation, from
either source, is normalized into this one shape before anything downstream sees it.

```python
@dataclass(frozen=True, slots=True)
class PriceUpdate:
    ticker: str
    price: float
    previous_price: float
    timestamp: float = field(default_factory=time.time)  # Unix seconds

    @property
    def change(self) -> float: ...          # price - previous_price
    @property
    def change_percent(self) -> float: ...  # % change vs previous_price
    @property
    def direction(self) -> str: ...         # "up" | "down" | "flat"

    def to_dict(self) -> dict: ...  # JSON-ready, used directly for SSE payloads
```

`previous_price` is the price *one update ago* (i.e., previous tick/poll), not the prior
trading day's close — the two data sources compute "previous" differently upstream (see
below), but by the time a value reaches `PriceUpdate` it's always tick-over-tick.

## `PriceCache` — the single point of truth

`app/market/cache.py`. Thread-safe (`threading.Lock`, not asyncio-only) because
`MassiveDataSource` polls via `asyncio.to_thread`, so writes can arrive from a worker
thread while the event loop reads concurrently.

```python
cache = PriceCache()

cache.update(ticker="AAPL", price=190.50)     # → PriceUpdate; computes prev/direction
cache.get("AAPL")                              # → PriceUpdate | None
cache.get_price("AAPL")                        # → float | None (convenience)
cache.get_all()                                # → dict[str, PriceUpdate] (shallow copy)
cache.remove("AAPL")                            # drop a ticker (e.g., watchlist removal)
cache.version                                   # int, bumped on every update()
len(cache); "AAPL" in cache
```

The `version` counter is what makes SSE delta-only pushes possible (PLAN.md §6): the
stream endpoint polls `cache.version` every 500ms and only serializes+sends when it has
changed since the last tick, rather than diffing individual tickers.

Design choice: **producers write, consumers read — no direct coupling.** Neither the SSE
endpoint nor portfolio/trade code ever imports `SimulatorDataSource` or
`MassiveDataSource` directly; they only ever see a `PriceCache`.

## `MarketDataSource` — the producer contract

`app/market/interface.py`. Both implementations satisfy this ABC:

```python
class MarketDataSource(ABC):
    @abstractmethod
    async def start(self, tickers: list[str]) -> None:
        """Begin producing updates. Starts a background task. Call once."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the background task. Safe to call multiple times (idempotent)."""

    @abstractmethod
    async def add_ticker(self, ticker: str) -> None:
        """Add a ticker to the active set. No-op if already present."""

    @abstractmethod
    async def remove_ticker(self, ticker: str) -> None:
        """Remove a ticker. No-op if absent. Also evicts it from the PriceCache."""

    @abstractmethod
    def get_tickers(self) -> list[str]:
        """Current actively-tracked ticker list."""
```

Lifecycle used at app startup/shutdown:

```python
source = create_market_data_source(cache)
await source.start(["AAPL", "GOOGL", "MSFT", ...])   # from the watchlist table
# ... app runs; watchlist add/remove call through here too ...
await source.add_ticker("TSLA")
await source.remove_ticker("GOOGL")
# ... app shutting down ...
await source.stop()
```

`start()` is asymmetric with the rest of the contract by design: it's called exactly once
at process startup with the full initial ticker list (from the `watchlist` table), while
`add_ticker`/`remove_ticker` handle incremental changes from the running app (manual
watchlist edits or LLM-driven `watchlist_changes`, PLAN.md §9).

## The two implementations

### `SimulatorDataSource` (default — no API key)

Runs a `GBMSimulator` (see `MARKET_SIMULATOR.md`) in an `asyncio` background task, stepping
every 500ms and writing every ticker's new price straight to the cache:

```python
async def _run_loop(self) -> None:
    while True:
        try:
            if self._sim:
                prices = self._sim.step()
                for ticker, price in prices.items():
                    self._cache.update(ticker=ticker, price=price)
        except Exception:
            logger.exception("Simulator step failed")
        await asyncio.sleep(self._interval)
```

A caught-and-logged `except Exception` inside the loop, rather than around it, is
deliberate: one bad step must not kill the task — the loop must keep scheduling itself
every tick regardless of individual failures.

`start()` also seeds the cache synchronously with each ticker's initial price *before*
the background task's first tick, so the SSE stream has data on the very first poll
instead of waiting up to 500ms for the first `step()`.

### `MassiveDataSource` (real data — `MASSIVE_API_KEY` set)

Polls Massive's multi-ticker snapshot endpoint (`MASSIVE_API.md` §"Snapshot — All Tickers")
on a timer, using `asyncio.to_thread` because the `massive` package's `RESTClient` is
synchronous:

```python
async def _poll_once(self) -> None:
    if not self._tickers or not self._client:
        return
    try:
        snapshots = await asyncio.to_thread(self._fetch_snapshots)
        for snap in snapshots:
            try:
                price = snap.last_trade.price
                timestamp = snap.last_trade.timestamp / 1000.0  # ns → s, see below
                self._cache.update(ticker=snap.ticker, price=price, timestamp=timestamp)
            except (AttributeError, TypeError) as e:
                logger.warning("Skipping snapshot for %s: %s", ...)
    except Exception as e:
        logger.error("Massive poll failed: %s", e)
        # No re-raise — next scheduled poll retries.

def _fetch_snapshots(self) -> list:
    return self._client.get_snapshot_all(
        market_type=SnapshotMarketType.STOCKS,
        tickers=self._tickers,
    )
```

Two failure-isolation layers, matching two different failure modes:
- **Per-snapshot** `try/except (AttributeError, TypeError)` — one malformed ticker in the
  batch (e.g., no trades yet today) doesn't discard the other N-1 tickers' valid data.
- **Per-poll** `try/except Exception` around the whole cycle — an API-level failure
  (network error, 429, 401) logs and waits for the next scheduled interval rather than
  crashing the polling task.

**Verified bug in the current code**: `snap.last_trade.timestamp` does not exist on the
real `massive.rest.models.trades.LastTrade` object returned by `get_snapshot_all` — that
model exposes `sip_timestamp`, `participant_timestamp`, and `trf_timestamp`, but no field
named `timestamp` (confirmed against
`massive/rest/models/trades.py` in the installed package; see `MASSIVE_API.md`
§Timestamps). Against the real API this raises `AttributeError` inside `_poll_once`'s
per-snapshot loop for *every* ticker on *every* poll, which is silently caught by the
`except (AttributeError, TypeError)` above and logged as a per-ticker warning — meaning
`MassiveDataSource` currently never writes a price to the cache in production
(`processed` stays `0`). The unit tests in `tests/market/test_massive.py` don't catch
this because they stub `snap.last_trade` with a `MagicMock()` that has a `.timestamp`
attribute by construction, which the real SDK object never provides. Fix: use
`snap.last_trade.sip_timestamp` (nanoseconds) and divide by `1_000_000_000` for Unix
seconds, not `snap.last_trade.timestamp / 1000.0`.

`start()` does one `_poll_once()` immediately (synchronously awaited) before launching the
repeating loop, for the same reason as the simulator: don't make the first SSE client wait
a full poll interval for data.

`add_ticker`/`remove_ticker` only mutate `self._tickers` (and evict from the cache on
remove) — they do not trigger an out-of-band poll; the new ticker appears on the next
scheduled cycle. This is a deliberate rate-limit-friendly trade-off: an eagerly-triggered
extra call per watchlist edit would burn free-tier budget fast (5 req/min total).

## `create_market_data_source()` — the factory

`app/market/factory.py`. The only place that reads the environment variable:

```python
def create_market_data_source(price_cache: PriceCache) -> MarketDataSource:
    api_key = os.environ.get("MASSIVE_API_KEY", "").strip()
    if api_key:
        return MassiveDataSource(api_key=api_key, price_cache=price_cache)
    else:
        return SimulatorDataSource(price_cache=price_cache)
```

`.strip()` means a key set to whitespace-only is treated as absent — falls back to the
simulator rather than passing a blank string to `RESTClient` and failing at Massive's
`AuthError`. Returns an **unstarted** source; the caller is responsible for `await
source.start(tickers)` at app startup (FastAPI lifespan) and `await source.stop()` at
shutdown.

## SSE integration

`app/market/stream.py`. `create_stream_router(price_cache)` returns a FastAPI router
whose `GET /api/stream/prices` handler reads *only* from `PriceCache` — it has no
knowledge of which `MarketDataSource` is feeding it. The version-counter check
(`cache.version`) is what implements PLAN.md §6's delta-only requirement: a snapshot is
only serialized and sent when at least one ticker changed since the last 500ms tick.

## Usage summary for downstream code

```python
from app.market import PriceCache, create_market_data_source

# Startup (FastAPI lifespan)
cache = PriceCache()
source = create_market_data_source(cache)   # reads MASSIVE_API_KEY
await source.start(initial_tickers)          # from watchlist table

# Anywhere else in the app: read-only, source-agnostic
price = cache.get_price("AAPL")              # float | None
update = cache.get("AAPL")                   # PriceUpdate | None — for change/direction

# Watchlist add/remove (manual or LLM-driven, PLAN.md §9)
await source.add_ticker("PYPL")
await source.remove_ticker("NFLX")

# Shutdown
await source.stop()
```

Trade execution and portfolio valuation (PLAN.md §8) both call `cache.get_price(ticker)`
and reject with a validation error if it returns `None` (ticker not yet on the watchlist,
or the cache hasn't ticked since startup) — they never call into `MarketDataSource`
directly, keeping the read path fully decoupled from which source is active.
