"use client";

import { useEffect, useState } from "react";
import { fetchPortfolio, fetchPortfolioHistory, type HistoryPoint, type Position } from "@/lib/portfolio";
import { PortfolioHeatmap } from "./PortfolioHeatmap";
import { PnlChart } from "./PnlChart";
import { PositionsTable } from "./PositionsTable";

const POLL_INTERVAL_MS = 5000;

export function PortfolioPanel() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [portfolio, historyResponse] = await Promise.all([
          fetchPortfolio(),
          fetchPortfolioHistory(),
        ]);
        if (cancelled) return;
        setPositions(portfolio.positions);
        setHistory(historyResponse.history);
        setError(null);
      } catch {
        if (!cancelled) {
          setError("Unable to load portfolio data.");
        }
      }
    }

    load();
    const interval = setInterval(load, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex flex-col gap-4">
      {error ? (
        <div className="rounded-lg border border-border bg-surface px-4 py-2 text-sm text-negative">
          {error}
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section>
          <h2 className="mb-2 text-xs font-medium uppercase tracking-wide text-foreground-muted">
            Portfolio Heatmap
          </h2>
          <PortfolioHeatmap positions={positions} />
        </section>

        <section>
          <h2 className="mb-2 text-xs font-medium uppercase tracking-wide text-foreground-muted">
            Portfolio Value
          </h2>
          <PnlChart history={history} />
        </section>
      </div>

      <section>
        <h2 className="mb-2 text-xs font-medium uppercase tracking-wide text-foreground-muted">
          Positions
        </h2>
        <PositionsTable positions={positions} />
      </section>
    </div>
  );
}
