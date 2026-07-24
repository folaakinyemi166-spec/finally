# Backend — Developer Guide

## Project Setup

```bash
cd backend
uv sync --extra dev   # Install all dependencies including test/lint tools
```

## Market Data API

The market data subsystem lives in `app/market/`. Use these imports:

```python
from app.market import PriceCache, PriceUpdate, MarketDataSource, create_market_data_source
```

### Core Types

- **`PriceUpdate`** — Immutable dataclass: `ticker`, `price`, `previous_price`, `timestamp`, plus properties `change`, `change_percent`, `direction` ("up"/"down"/"flat"), and `to_dict()` for JSON serialization.

- **`PriceCache`** — Thread-safe in-memory store. Key methods:
  - `update(ticker, price, timestamp=None) -> PriceUpdate`
  - `get(ticker) -> PriceUpdate | None`
  - `get_price(ticker) -> float | None`
  - `get_all() -> dict[str, PriceUpdate]`
  - `remove(ticker)`
  - `version` property — monotonic counter, increments on every update (for SSE change detection)

- **`MarketDataSource`** — Abstract interface implemented by `SimulatorDataSource` and `MassiveDataSource`. Lifecycle: `start(tickers)` -> `add_ticker()` / `remove_ticker()` -> `stop()`.

- **`create_market_data_source(cache)`** — Factory. Returns `MassiveDataSource` if `MASSIVE_API_KEY` is set, otherwise `SimulatorDataSource`.

## Persistence (SQLite)

The DB layer lives in `app/db/`. Use these imports:

```python
from app.db import ensure_db, init_db, get_connection, get_db_path
```

- **`ensure_db(db_path=None) -> sqlite3.Connection`** — Lazy-init entry point for app startup: opens (creating parent dirs as needed) the SQLite file, creates the schema if missing, and seeds default data if the DB is empty. Idempotent — safe to call every startup.
- **`get_connection(db_path=None) -> sqlite3.Connection`** — Opens a connection with `row_factory = sqlite3.Row` (dict-like column access) and `PRAGMA foreign_keys = ON`. Does not create schema/seed data.
- **`get_db_path() -> Path`** — Resolves the DB file path: honors the `FINALLY_DB_PATH` env var, else defaults to `<repo root>/db/finally.db`.
- **`init_db(conn)`** / **`create_schema(conn)`** / **`seed_default_data(conn)`** — Lower-level pieces of `ensure_db`, each idempotent, for callers that already have a connection.

Tables: `users_profile`, `watchlist`, `positions`, `trades`, `portfolio_snapshots`, `chat_messages` — see `app/db/schema.py`. All are scoped by a `user_id` column defaulting to `"default"`. Default seed: cash balance 10000.0, watchlist tickers from `app.market.seed_prices.SEED_PRICES` (the same 10-ticker default watchlist as the market simulator).

### SSE Streaming

```python
from app.market import create_stream_router

router = create_stream_router(price_cache)  # Returns FastAPI APIRouter
# Endpoint: GET /api/stream/prices (text/event-stream)
```

## Portfolio API

The portfolio subsystem lives in `app/portfolio/`. Use these imports:

```python
from app.portfolio import create_portfolio_router, snapshot_loop
from app.portfolio import get_portfolio, execute_trade, record_snapshot, get_history
from app.portfolio import UnknownTickerError, InsufficientCashError, InsufficientSharesError
```

- **`create_portfolio_router(price_cache, db_path=None) -> APIRouter`** — Factory (same pattern as `create_stream_router`). Registers:
  - `GET /api/portfolio` — cash balance, positions with live P&L, total value
  - `POST /api/portfolio/trade` — body `{ticker, side: "buy"|"sell", quantity}`; instant fill at the current `PriceCache` price. Returns 400 on `UnknownTickerError`/`InsufficientCashError`/`InsufficientSharesError`, 422 on schema validation (e.g. non-positive quantity).
  - `GET /api/portfolio/history` — `{history: [{total_value, recorded_at}, ...]}` oldest first, for the P&L chart

- **`snapshot_loop(price_cache, db_path=None, user_id="default", interval=30.0)`** — Async background task; call `asyncio.create_task(snapshot_loop(price_cache))` from the app lifespan and `task.cancel()` on shutdown. Records a `portfolio_snapshots` row every `interval` seconds (opens a fresh DB connection per tick).

- Core logic in `app/portfolio/service.py` (`get_portfolio`, `execute_trade`, `record_snapshot`, `get_history`) operates on a plain `sqlite3.Connection` + `PriceCache` — useful for calling directly from the AI chat trade-execution flow without going through HTTP.

- Trades: buys average cost across fills; sells reduce quantity and delete the position row once it hits ~0. All validation (unknown ticker, insufficient cash, insufficient shares) happens before any write. Fractional share quantities are supported throughout.

### Seed Data

Default tickers: AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX. Seed prices and per-ticker volatility/drift params are in `app/market/seed_prices.py`.

## AI Chat API

The chat subsystem lives in `app/ai/`. Use these imports:

```python
from app.ai import create_chat_router, process_chat, call_llm, LLMResponseError
```

- **`create_chat_router(price_cache, db_path=None) -> APIRouter`** — Factory (same pattern as the portfolio/watchlist routers). Registers `POST /api/chat`: body `{message}`, response `{message, trades, watchlist_changes}` where `trades`/`watchlist_changes` are the LLM's proposed actions annotated with their execution result (`price` on success, `error` string on failure). A failed/malformed LLM call raises `LLMResponseError`, mapped to HTTP 502 (never a 500).

- **`process_chat(conn, price_cache, user_message, user_id="default") -> ChatResponseOut`** (`app/ai/service.py`) — Loads portfolio + watchlist context and the last 20 `chat_messages` rows, calls the LLM for a structured `{message, trades[], watchlist_changes[]}` response, auto-executes each trade via `app.portfolio.service.execute_trade` and each watchlist change via direct insert/delete — both through the same validation as the manual APIs — then persists the user + assistant turn to `chat_messages` (`actions` column holds the executed-action JSON). Trade/watchlist failures (e.g. insufficient cash) are captured as an `error` string on that action, not raised.

- **`call_llm(messages, user_message) -> LLMChatResponse`** (`app/ai/llm.py`) — LiteLLM → OpenRouter call using the Cerebras inference provider (model `openrouter/openai/gpt-oss-120b`, structured output via `response_format=LLMChatResponse`). Raises `LLMResponseError` on any provider failure or invalid JSON, so callers can degrade gracefully.

### LLM_MOCK

When the `LLM_MOCK` env var is `"true"`, `call_llm` never makes a network call — a small deterministic regex parser stands in for the LLM (for fast/free/reproducible E2E and CI tests). Recognized phrasing (case-insensitive):

```
buy <qty> <TICKER>            -> trade: buy
sell <qty> <TICKER>           -> trade: sell   (also accepts "sell <qty> shares of <TICKER>")
add <TICKER> to [my/the] watchlist     -> watchlist add
remove <TICKER> from [my/the] watchlist -> watchlist remove
```

Anything else returns a canned acknowledgement with no actions. Multiple trades/changes in one message are all parsed.

## Running Tests

```bash
uv run --extra dev pytest -v              # All tests
uv run --extra dev pytest --cov=app       # With coverage
uv run --extra dev ruff check app/ tests/ # Lint
```

## Demo

```bash
uv run market_data_demo.py   # Live terminal dashboard with simulated prices
```
