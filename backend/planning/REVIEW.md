# Review

## Findings

- High: [`app/market/stream.py`](/Users/sfoa6558/pm/finally/backend/app/market/stream.py#L17) keeps a module-level `router` and `create_stream_router()` decorates the same object on every call. Because `create_app()` calls that factory each time, each new app instance accumulates another `/api/stream/prices` route, and those stale route objects retain the `PriceCache` closure from earlier apps. I verified this by instantiating the app twice and seeing the route count grow from 2 to 3, which means tests and multi-app processes are not isolated.

- High: [`app/trading.py`](/Users/sfoa6558/pm/finally/backend/app/trading.py#L20) says trade execution persists the trade, position, and portfolio snapshot as one logical unit, but the implementation calls `users.set_cash_balance()`, `trades.insert_trade()`, and `snapshots.insert_snapshot()` as separate database operations. Any failure after the cash update leaves the account state partially applied, with cash/positions changed but no matching trade log or snapshot, which is a consistency bug for a financial workflow.

## Notes

- Verification run: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q` passed (`181 passed`).
