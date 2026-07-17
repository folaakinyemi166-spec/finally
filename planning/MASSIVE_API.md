# Massive API Reference (formerly Polygon.io)

Research reference for the Massive REST API, covering realtime and end-of-day (EOD) price
retrieval for multiple tickers. This documents the API surface as actually used by
`backend/app/market/massive_client.py`, verified against the installed `massive` Python
package (`backend/.venv/lib/python3.14/site-packages/massive`, version 2.2.0) and
`massive.com/docs`.

## Overview

- **Company**: Polygon.io rebranded to Massive. `https://api.massive.com` is the current
  base URL; `https://api.polygon.io` still works during the transition.
- **Python package**: `massive` (`pip install -U massive` / `uv add massive`). Imports are
  still under the `massive` namespace (`from massive import RESTClient`).
- **Auth**: an API key, either passed to `RESTClient(api_key=...)` or read from the
  `MASSIVE_API_KEY` env var by the client automatically if omitted.
- **Auth transport**: the client sends `Authorization: Bearer <API_KEY>` on every request —
  nothing to do manually.
- **Transport**: synchronous HTTP via `urllib3` under the hood (`PoolManager`, with built-in
  retry on `413/429/499/500/502/503/504`). There is no native async client, which is why
  FinAlly wraps calls in `asyncio.to_thread(...)` (see `MARKET_INTERFACE.md`).

## Rate Limits & Data Recency

| Tier | Requests | Recency |
|------|----------|---------|
| Free | 5 requests/minute | End-of-day / delayed snapshot data |
| Starter / Developer | Higher caps (paid) | 15-minute delayed |
| Advanced / Business | Effectively unlimited | Real-time |

Paid plans start at $29/month and step up ($79, $199, ...) for lower delay and higher
throughput. For FinAlly's purposes (a course project, most users on the free tier), we
design for **5 requests/minute** and poll on a timer rather than per-request:

- Free tier: poll every 15s (well under 5/min)
- Paid tiers: poll every 2-5s

Snapshot data is cleared once per day (around 3:30am EST) and repopulates as exchanges
report new data (as early as 4am EST) — so very early risers may see stale/empty snapshots
until trading data starts flowing.

Sources: [Massive pricing](https://massive.com/pricing), [REST rate limit FAQ](https://massive.com/knowledge-base/article/what-is-the-request-limit-for-massives-restful-apis), [Stocks REST overview](https://massive.com/docs/rest/stocks/overview)

## Client Initialization

```python
from massive import RESTClient

# Reads MASSIVE_API_KEY from the environment automatically
client = RESTClient()

# Or pass the key explicitly
client = RESTClient(api_key="your_key_here")
```

`RESTClient` raises `massive.exceptions.AuthError` immediately at construction if no key is
found either way — there's no separate "connect" step to fail later.

## Realtime: Snapshot Endpoints

Snapshots are the realtime primitive — each returns the latest trade, latest NBBO quote,
today's minute/day bar, and the previous day's bar for one or more tickers in a single call.
This is the endpoint FinAlly polls.

### Snapshot — All Tickers (multi-ticker, one call)

The core endpoint for FinAlly: get current prices for an arbitrary list of tickers in a
**single API call**, so the whole watchlist costs one request per poll regardless of size
(up to the endpoint's ticker limit, well above FinAlly's 30-ticker cap).

**REST**: `GET /v2/snapshot/locale/us/markets/stocks/tickers?tickers=AAPL,GOOGL,MSFT`

```python
from massive import RESTClient
from massive.rest.models import SnapshotMarketType

client = RESTClient()

snapshots = client.get_snapshot_all(
    market_type=SnapshotMarketType.STOCKS,
    tickers=["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
)

for snap in snapshots:
    print(f"{snap.ticker}: last trade ${snap.last_trade.price}")
    print(f"  Today's change: {snap.todays_change} ({snap.todays_change_percent}%)")
    print(f"  Day OHLC: O={snap.day.open} H={snap.day.high} L={snap.day.low} C={snap.day.close}")
    print(f"  Prev close: {snap.prev_day.close}")
```

`market_type` accepts the `SnapshotMarketType` enum (`STOCKS`, `FOREX`, `CRYPTO`, `INDICES`)
or the equivalent string. `tickers` accepts either a list (joined into a comma-separated
string by the client) or a pre-joined string. Passing no `tickers` returns a snapshot for
every ticker in the market (10,000+ symbols) — always pass an explicit list for FinAlly's
watchlist-scoped polling.

**Deserialized shape** (`TickerSnapshot`, from `massive.rest.models.snapshot`):

```python
TickerSnapshot(
    ticker: str,
    day: Agg | None,             # today's bar so far: open/high/low/close/volume/vwap/timestamp
    prev_day: Agg | None,        # yesterday's full bar (same shape as `day`)
    min: MinuteSnapshot | None,  # most recent minute bar
    last_trade: LastTrade | None,
    last_quote: LastQuote | None,
    todays_change: float | None,         # absolute $ change vs prev close
    todays_change_percent: float | None, # % change vs prev close
    updated: int | None,          # Unix nanoseconds
    fair_market_value: float | None,  # Business plan only
)
```

Important: `todays_change` / `todays_change_percent` live on the top-level snapshot object,
**not** inside `day` — there is no `day.change_percent` or `day.previous_close` field. Use
`prev_day.close` for the previous close, and `snap.todays_change_percent` for day change.

Raw JSON (per ticker, field names before the client's snake_case mapping):

```json
{
  "ticker": "AAPL",
  "day": { "o": 129.61, "h": 130.15, "l": 125.07, "c": 125.07, "v": 111237700, "vw": 127.35 },
  "prevDay": { "o": 128.0, "h": 129.9, "l": 127.5, "c": 129.61, "v": 90000000, "vw": 128.5 },
  "lastTrade": { "p": 125.07, "s": 100, "x": 11, "t": 1675190399000000000 },
  "lastQuote": { "P": 125.08, "p": 125.06, "S": 1000, "s": 500, "t": 1675190399500000000 },
  "min": { "o": 125.0, "h": 125.1, "l": 124.9, "c": 125.07, "v": 12000 },
  "todaysChange": -4.54,
  "todaysChangePerc": -3.50,
  "updated": 1675190399500000000
}
```

Field mapping notes: `lastTrade.p` → `price`, `lastTrade.t` → `timestamp` (Unix
**nanoseconds** for trades/quotes — see Timestamps below), `lastQuote.P`/`p` → ask/bid price.

### Snapshot — Single Ticker

Used for a detail view of one ticker (same shape as one element of the all-tickers response).

**REST**: `GET /v2/snapshot/locale/us/markets/stocks/tickers/{ticker}`

```python
snapshot = client.get_snapshot_ticker(
    market_type=SnapshotMarketType.STOCKS,
    ticker="AAPL",
)

print(f"Price: ${snapshot.last_trade.price}")
print(f"Bid/Ask: ${snapshot.last_quote.bid_price} / ${snapshot.last_quote.ask_price}")
print(f"Day range: ${snapshot.day.low} - ${snapshot.day.high}")
```

### Snapshot — Gainers / Losers

Top 20 movers of the day; not currently used by FinAlly but relevant if a "market movers"
widget is added later.

```python
from massive.rest.models import Direction

movers = client.get_snapshot_direction(
    market_type=SnapshotMarketType.STOCKS,
    direction=Direction.GAINERS,  # or Direction.LOSERS
)
```

### Last Trade / Last Quote (single field, single ticker)

Lower-level than snapshots — useful only if you need *just* the trade or *just* the quote
without the rest of the snapshot payload.

```python
trade = client.get_last_trade(ticker="AAPL")
print(f"Last trade: ${trade.price} x {trade.size}")

quote = client.get_last_quote(ticker="AAPL")
print(f"Bid: ${quote.bid_price} x {quote.bid_size}")
print(f"Ask: ${quote.ask_price} x {quote.ask_size}")
```

FinAlly does not use these directly — `get_snapshot_all` already returns `last_trade` and
`last_quote` per ticker in the same call, which is more efficient for a multi-ticker
watchlist (one call instead of 2×N calls).

## End-of-Day (EOD) & Historical Prices

### Previous Close (single ticker)

The previous trading day's OHLCV for one ticker. Useful for seeding a ticker the moment
it's added to the watchlist, before the first live snapshot/poll has landed.

**REST**: `GET /v2/aggs/ticker/{ticker}/prev`

```python
prev = client.get_previous_close_agg(ticker="AAPL")

print(f"Previous close: ${prev.close}")
print(f"OHLC: O={prev.open} H={prev.high} L={prev.low} C={prev.close}")
print(f"Volume: {prev.volume}")
```

Returns a single `PreviousCloseAgg`, not a list, despite older docs/examples showing a
`results` array — the client already unwraps `result_key="results"` and hands back one
object.

### Daily Open/Close (single ticker, single date)

Open, close, and after-hours/pre-market prices for one ticker on one specific past date.

**REST**: `GET /v1/open-close/{ticker}/{date}`

```python
oc = client.get_daily_open_close_agg(ticker="AAPL", date="2026-06-30")

print(f"Open={oc.open} Close={oc.close}")
print(f"Pre-market={oc.pre_market} After-hours={oc.after_hours}")
```

### Grouped Daily (whole market, single date)

OHLC for every ticker in the market on one date — useful for backfilling many tickers'
EOD prices in one call rather than one call per ticker.

**REST**: `GET /v2/aggs/grouped/locale/us/market/stocks/{date}`

```python
day_bars = client.get_grouped_daily_aggs(date="2026-06-30", adjusted=True)

by_ticker = {bar.ticker: bar for bar in day_bars}
print(by_ticker["AAPL"].close)
```

### Aggregates / Bars (historical range, custom window)

Historical OHLCV bars over a date range at any granularity (`multiplier` + `timespan`, e.g.
`1 day`, `5 minute`). Not needed for live polling, but this is what a historical chart
endpoint would use if FinAlly adds one beyond the SSE-accumulated sparklines.

**REST**: `GET /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}`

```python
aggs = client.get_aggs(
    ticker="AAPL",
    multiplier=1,
    timespan="day",
    from_="2026-06-01",
    to="2026-06-30",
    limit=50000,
)

for bar in aggs:
    print(f"t={bar.timestamp} O={bar.open} H={bar.high} L={bar.low} C={bar.close} V={bar.volume}")
```

`list_aggs` (vs. `get_aggs`) returns an auto-paginating iterator instead of a single page —
prefer it for ranges that might exceed one page (`limit` default 5000, max 50000 per page).
`from_`/`to` accept `YYYY-MM-DD` strings, `date`/`datetime` objects, or Unix millisecond
timestamps.

## Timestamps

Timestamp units are **not consistent across endpoints** — check per-field:

| Source | Unit |
|--------|------|
| `LastTrade.sip_timestamp`, `LastQuote.sip_timestamp`, `TickerSnapshot.updated` | Unix **nanoseconds** |
| `Agg.timestamp` (day/prev_day/aggregates bars) | Unix **milliseconds** |
| `PreviousCloseAgg.timestamp` | Unix milliseconds |

`massive_client.py` divides `last_trade.timestamp` by `1_000_000` (not `1_000`) to get
seconds when reading from a snapshot's `last_trade` — see `MARKET_INTERFACE.md` for the
exact conversion FinAlly uses. Double-check the unit whenever pulling a new field.

## Market Status

Not used in polling itself, but useful to gate "is the market even open" UI messaging.

```python
status = client.get_market_status()
print(status.market)        # "open" | "closed" | "extended-hours"
print(status.exchanges.nasdaq, status.exchanges.nyse)
```

## Error Handling

- **`AuthError`** (raised locally, no network call): no API key supplied.
- **401**: invalid API key.
- **403**: plan doesn't include the requested endpoint/data (e.g., free tier hitting a
  Business-only field like `fair_market_value`).
- **429**: rate limit exceeded — the client's built-in retry (3 attempts, exponential
  backoff) will retry these automatically; sustained 429s mean the poll interval is too
  aggressive for the tier.
- **5xx**: server errors — also covered by the built-in retry.

`massive_client.py` wraps each poll cycle in a broad `try/except`, logs, and lets the next
scheduled poll retry rather than raising — a single failed poll should never crash the
background task (see `MARKET_INTERFACE.md`).

## How FinAlly Uses This API

Only one endpoint is used in production polling: **`get_snapshot_all`**, once per poll
interval, for the full current watchlist, in a single call. Everything else in this
document (previous close, aggregates, market status, gainers/losers) is documented for
completeness and potential future features (historical charts, watchlist seeding, market-
closed messaging) but is not wired into `backend/app/market/` today. See
`MARKET_INTERFACE.md` for exactly how the snapshot call is integrated into the shared
`MarketDataSource` abstraction.
