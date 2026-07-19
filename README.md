# FinAlly — AI Trading Workstation

A visually stunning AI-powered trading workstation: live market data, a simulated portfolio, and an LLM chat assistant that can analyze positions and execute trades via natural language. Bloomberg-terminal aesthetic, single Docker container.

Capstone project for an agentic AI coding course — built entirely by coding agents, with `planning/PLAN.md` as the shared spec they build against.

## Status

In progress. Completed so far:

- **Market data subsystem** (`backend/app/market/`) — GBM price simulator with correlated moves, Massive (Polygon.io) client, thread-safe price cache, SSE streaming endpoint. See `planning/MARKET_DATA_SUMMARY.md`.
- **Database layer** (`backend/app/db/`) — SQLite schema, lazy init/seed, per-table repositories.
- **Frontend** (`frontend/`) — Next.js static export: watchlist, chart, portfolio heatmap, P&L chart, positions table, trade bar, AI chat panel, dark terminal theme.
- **Backend REST API** (`backend/app/api/`) — portfolio/trade/watchlist/chat endpoints, business validation, trade execution.
- **LLM chat integration** (`backend/app/ai.py`, `backend/app/chat.py`) — LiteLLM → OpenRouter (Cerebras), structured outputs, auto-executed trades/watchlist changes, `LLM_MOCK` mode.
- **Docker packaging** — multi-stage `Dockerfile`, `docker-compose.yml`, OS-native start/stop scripts (`scripts/`).

Not yet built: E2E Playwright tests against the Docker build (`test/`).

## Architecture

Single Docker container serving everything on port 8000 once complete:

- **Frontend**: Next.js (static export), TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python, managed with `uv`), SSE streaming
- **Database**: SQLite, lazily initialized, volume-mounted
- **AI**: LiteLLM → OpenRouter (Cerebras inference), structured outputs
- **Market data**: built-in GBM simulator by default, or Massive API if `MASSIVE_API_KEY` is set

Full spec: [`planning/PLAN.md`](planning/PLAN.md).

## Running with Docker (recommended)

```bash
cp .env.example .env   # then set OPENROUTER_API_KEY
scripts/start_mac.sh   # builds the image on first run, then starts the container
scripts/stop_mac.sh    # stops the container; db/finally.db is preserved
```

Windows: `scripts\start_windows.ps1` / `scripts\stop_windows.ps1`. Or, if you prefer Compose: `docker compose up --build`.

The app is served at `http://localhost:8000` — one container, one port, both frontend and API.

## Backend — Quick Start (without Docker)

```bash
cd backend
uv sync --extra dev
uv run pytest              # run test suite
uv run market_data_demo.py # live terminal dashboard of the simulator
```

See [`backend/README.md`](backend/README.md) for backend-specific details.

## Frontend — Quick Start (without Docker)

```bash
cd frontend
npm install
npm run dev   # localhost:3000, talking to a separately-running backend on :8000
```

## Project Structure

```
finally/
├── backend/            # FastAPI uv project — market data, db, API, LLM chat
├── frontend/            # Next.js static export — terminal UI
├── planning/            # Project spec and agent-facing docs
├── scripts/             # OS-native Docker start/stop scripts
├── db/                   # Volume mount target for finally.db (gitignored)
├── Dockerfile            # Multi-stage build: Next.js export -> FastAPI + uv
├── docker-compose.yml    # Optional one-line alternative to the scripts
└── test/                 # E2E tests — not yet built
```

## License

See [LICENSE](LICENSE).
