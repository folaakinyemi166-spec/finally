# FinAlly Frontend

Next.js (App Router, TypeScript) trading-terminal UI for FinAlly. Built as a
static export (`output: "export"`) — in production this is served by the
FastAPI backend as static files from a single origin (see
`planning/PLAN.md` §11), so there is no separate dev server in Docker.

Right now the backend doesn't exist yet. All data comes from an in-browser
mock (`src/lib/mockBackend.ts`) reached through `src/lib/api.ts`, which
matches the real REST/SSE contracts exactly — swapping in real `fetch`/
`EventSource` calls later is a change confined to `api.ts`.

## Commands

```bash
npm install          # Install dependencies
npm run dev          # Start the dev server at localhost:3000
npm run build        # Production build; produces the static export in out/
npm run lint         # ESLint
npm run test:unit    # Run Vitest unit tests once
npm run test:unit:watch  # Run tests in watch mode
```

## Structure

- `src/app/` — App Router entry (`layout.tsx`, `page.tsx`, `globals.css`)
- `src/components/` — UI components, grouped by area (layout, watchlist,
  chart, portfolio, trade, chat)
- `src/hooks/` — data hooks (`useMarketData`, `useWatchlist`, `usePortfolio`,
  `useChat`) — the only things components talk to for data
- `src/lib/api.ts` — the API abstraction layer (mock today, real backend
  later)
- `src/lib/mockBackend.ts` — in-browser simulated backend (GBM price
  ticker, portfolio ledger, watchlist, canned chat responses)
- `src/lib/types.ts` — shared request/response types matching the backend
  contract in `planning/PLAN.md`

## Testing

Vitest + React Testing Library. Playwright/E2E tests live in the top-level
`test/` directory, owned separately, and are not part of this package.
