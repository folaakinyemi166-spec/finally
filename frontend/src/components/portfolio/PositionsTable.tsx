import { formatCurrency, formatPercent, formatPrice, formatQuantity } from "@/lib/format";
import type { Position } from "@/lib/types";

export function PositionsTable({ positions }: { positions: Position[] }) {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-text-dim">Positions</h2>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {positions.length === 0 ? (
          <div className="flex h-full items-center justify-center p-4 text-center text-xs text-text-faint">
            No open positions. Use the trade bar below to buy your first shares.
          </div>
        ) : (
          <table className="w-full border-collapse font-data text-xs">
            <thead className="sticky top-0 bg-panel">
              <tr className="text-left text-text-faint">
                <th className="px-3 py-1.5 font-medium">Ticker</th>
                <th className="px-3 py-1.5 text-right font-medium">Qty</th>
                <th className="px-3 py-1.5 text-right font-medium">Avg Cost</th>
                <th className="px-3 py-1.5 text-right font-medium">Price</th>
                <th className="px-3 py-1.5 text-right font-medium">Unrealized P&amp;L</th>
                <th className="px-3 py-1.5 text-right font-medium">%</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => {
                const positive = p.unrealized_pnl >= 0;
                return (
                  <tr key={p.ticker} className="border-t border-border-soft" data-testid={`position-${p.ticker}`}>
                    <td className="px-3 py-1.5 font-semibold text-text">{p.ticker}</td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-text">
                      {formatQuantity(p.quantity)}
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-text-dim">
                      {formatPrice(p.avg_cost)}
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-text">
                      {formatPrice(p.current_price)}
                    </td>
                    <td
                      className={`px-3 py-1.5 text-right tabular-nums ${positive ? "text-gain" : "text-loss"}`}
                    >
                      {formatCurrency(p.unrealized_pnl)}
                    </td>
                    <td
                      className={`px-3 py-1.5 text-right tabular-nums ${positive ? "text-gain" : "text-loss"}`}
                    >
                      {formatPercent(p.unrealized_pnl_percent)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
