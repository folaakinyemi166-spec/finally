"use client";

import { useEffect, useState } from "react";
import { TradeBar } from "@/components/TradeBar";
import type { PortfolioOut } from "@/lib/types";

export default function Home() {
  const [portfolio, setPortfolio] = useState<PortfolioOut | null>(null);

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
      <div className="rounded-lg border border-border bg-surface px-8 py-6 text-center">
        <p className="text-sm text-foreground-muted">
          Watchlist and chart panels land here.
        </p>
      </div>

      <TradeBar onTradeExecuted={setPortfolio} />

      {portfolio && (
        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="mb-3 flex items-center justify-between text-sm">
            <span className="text-foreground-muted">Cash Balance</span>
            <span className="font-mono text-foreground">
              ${portfolio.cash_balance.toFixed(2)}
            </span>
          </div>

          {portfolio.positions.length > 0 ? (
            <table className="w-full text-left text-xs">
              <thead className="uppercase tracking-wide text-foreground-muted">
                <tr>
                  <th className="pb-2 font-normal">Ticker</th>
                  <th className="pb-2 font-normal">Qty</th>
                  <th className="pb-2 font-normal">Avg Cost</th>
                  <th className="pb-2 font-normal">Price</th>
                  <th className="pb-2 font-normal">Unrealized P&amp;L</th>
                </tr>
              </thead>
              <tbody className="font-mono text-foreground">
                {portfolio.positions.map((position) => (
                  <tr key={position.ticker} className="border-t border-border">
                    <td className="py-1.5">{position.ticker}</td>
                    <td className="py-1.5">{position.quantity}</td>
                    <td className="py-1.5">${position.avg_cost.toFixed(2)}</td>
                    <td className="py-1.5">${position.current_price.toFixed(2)}</td>
                    <td
                      className={`py-1.5 ${
                        position.unrealized_pnl >= 0 ? "text-positive" : "text-negative"
                      }`}
                    >
                      {position.unrealized_pnl >= 0 ? "+" : ""}
                      ${position.unrealized_pnl.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-xs text-foreground-muted">No open positions.</p>
          )}
        </div>
      )}
    </main>
  );
}
