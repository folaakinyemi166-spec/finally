import type { Position } from "@/lib/portfolio";

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const percent = new Intl.NumberFormat("en-US", {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function pnlClass(value: number): string {
  if (value > 0) return "text-positive";
  if (value < 0) return "text-negative";
  return "text-foreground-muted";
}

export interface PositionsTableProps {
  positions: Position[];
}

export function PositionsTable({ positions }: PositionsTableProps) {
  if (positions.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6 text-center text-sm text-foreground-muted">
        No open positions.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-surface">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-[11px] uppercase tracking-wide text-foreground-muted">
            <th className="px-4 py-2 font-medium">Ticker</th>
            <th className="px-4 py-2 font-medium text-right">Quantity</th>
            <th className="px-4 py-2 font-medium text-right">Avg Cost</th>
            <th className="px-4 py-2 font-medium text-right">Current Price</th>
            <th className="px-4 py-2 font-medium text-right">Unrealized P&amp;L</th>
            <th className="px-4 py-2 font-medium text-right">% Change</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((position) => (
            <tr key={position.ticker} className="border-b border-border last:border-0">
              <td className="px-4 py-2 font-mono font-semibold text-foreground">
                {position.ticker}
              </td>
              <td className="px-4 py-2 text-right font-mono text-foreground">
                {position.quantity}
              </td>
              <td className="px-4 py-2 text-right font-mono text-foreground">
                {currency.format(position.avg_cost)}
              </td>
              <td className="px-4 py-2 text-right font-mono text-foreground">
                {currency.format(position.current_price)}
              </td>
              <td className={`px-4 py-2 text-right font-mono ${pnlClass(position.unrealized_pnl)}`}>
                {currency.format(position.unrealized_pnl)}
              </td>
              <td
                className={`px-4 py-2 text-right font-mono ${pnlClass(position.unrealized_pnl_percent)}`}
              >
                {percent.format(position.unrealized_pnl_percent / 100)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
