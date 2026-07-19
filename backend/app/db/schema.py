"""Schema DDL and seed data for the FinAlly SQLite database.

Table definitions mirror PLAN.md §7 exactly (columns, types, constraints).
All statements are ``CREATE ... IF NOT EXISTS`` so running them against an
already-initialized database is a safe no-op.
"""

from __future__ import annotations

from app.market.seed_prices import SEED_PRICES

# Hardcoded single-user id for now; every table carries a user_id column so
# multi-user support later doesn't require a schema migration (PLAN.md §7).
DEFAULT_USER_ID = "default"
DEFAULT_CASH_BALANCE = 10000.0

# Matches the market simulator's seed tickers 1:1 (app/market/seed_prices.py)
# so the watchlist and the price cache agree on the default symbol set.
DEFAULT_WATCHLIST_TICKERS: list[str] = list(SEED_PRICES.keys())

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users_profile (
    id TEXT PRIMARY KEY,
    cash_balance REAL NOT NULL DEFAULT 10000.0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watchlist (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    ticker TEXT NOT NULL,
    added_at TEXT NOT NULL,
    UNIQUE (user_id, ticker)
);

CREATE TABLE IF NOT EXISTS positions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    ticker TEXT NOT NULL,
    quantity REAL NOT NULL,
    avg_cost REAL NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (user_id, ticker)
);

CREATE TABLE IF NOT EXISTS trades (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    ticker TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    executed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    total_value REAL NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    actions TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trades_user_time ON trades (user_id, executed_at);
CREATE INDEX IF NOT EXISTS idx_snapshots_user_time ON portfolio_snapshots (user_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_chat_user_time ON chat_messages (user_id, created_at);
"""
