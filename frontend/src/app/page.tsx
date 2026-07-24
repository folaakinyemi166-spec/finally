"use client";

import { useEffect, useState } from "react";
import { PortfolioPanel } from "@/components/PortfolioPanel";
import { TradeBar } from "@/components/TradeBar";
import { WatchlistPanel } from "@/components/WatchlistPanel";
import type { PortfolioOut } from "@/lib/types";

export default function Home() {
  const [portfolio, setPortfolio] = useState<PortfolioOut | null>(null);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetch("/api/portfolio")
      .then((response) => (response.ok ? (response.json() as Promise<PortfolioOut>) : null))
      .then((data) => {
        if (!cancelled && data) setPortfolio(data);
      })
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="flex flex-1 flex-col gap-6 p-8">
      <div className="flex flex-1 gap-4">
        <WatchlistPanel selectedTicker={selectedTicker} onSelectTicker={setSelectedTicker} />
        <div className="flex flex-1 items-center justify-center rounded-lg border border-border bg-surface px-8 py-6 text-center">
          <p className="text-sm text-foreground-muted">
            {selectedTicker
              ? `Chart for ${selectedTicker} lands here.`
              : "Select a ticker to view its chart."}
          </p>
        </div>
      </div>

      <TradeBar onTradeExecuted={setPortfolio} />

      {portfolio && (
        <div className="flex items-center justify-between rounded-lg border border-border bg-surface px-4 py-2 text-sm">
          <span className="text-foreground-muted">Cash Balance</span>
          <span className="font-mono text-foreground">${portfolio.cash_balance.toFixed(2)}</span>
        </div>
      )}

      <PortfolioPanel />
    </main>
  );
}
