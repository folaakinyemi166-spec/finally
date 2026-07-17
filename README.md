# FinAlly — AI Trading Workstation

A visually stunning AI-powered trading workstation: live market data, a simulated portfolio, and an LLM chat assistant that can analyze positions and execute trades via natural language. Bloomberg-terminal aesthetic, single Docker container.

Capstone project for an agentic AI coding course — built entirely by coding agents, with `planning/PLAN.md` as the shared spec they build against.

## Status

In progress. Completed so far:

- **Market data subsystem** (`backend/app/market/`) — GBM price simulator with correlated moves, Massive (Polygon.io) client, thread-safe price cache, SSE streaming endpoint. See `planning/MARKET_DATA_SUMMARY.md`.

Not yet built: frontend, portfolio/trade/watchlist/chat APIs, database layer, Docker packaging, start/stop scripts, E2E tests.

## Architecture

Single Docker container serving everything on port 8000 once complete:

- **Frontend**: Next.js (static export), TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python, managed with `uv`), SSE streaming
- **Database**: SQLite, lazily initialized, volume-mounted
- **AI**: LiteLLM → OpenRouter (Cerebras inference), structured outputs
- **Market data**: built-in GBM simulator by default, or Massive API if `MASSIVE_API_KEY` is set

Full spec: [`planning/PLAN.md`](planning/PLAN.md).

## Backend — Quick Start

```bash
cd backend
uv sync --dev
uv run pytest              # run test suite
uv run market_data_demo.py # live terminal dashboard of the simulator
```

See [`backend/README.md`](backend/README.md) for backend-specific details.

## Project Structure

```
finally/
├── backend/     # FastAPI uv project (market data subsystem complete)
├── planning/    # Project spec and agent-facing docs
└── ...          # frontend/, test/, scripts/, db/, Docker files — planned, not yet present
```

## License

See [LICENSE](LICENSE).
