"""REST API routers, factory-created with their PriceCache/MarketDataSource dependencies.

See app/market/stream.py for the create_*_router(...) pattern this follows —
routers need the shared PriceCache (and, for watchlist, the MarketDataSource),
which are only constructed inside app.main.create_app(), so each module
exposes a factory instead of importing a global.
"""
