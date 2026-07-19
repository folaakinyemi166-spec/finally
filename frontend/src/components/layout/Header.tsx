import { ConnectionDot } from "./ConnectionDot";
import { formatCurrency } from "@/lib/format";
import type { ConnectionStatus } from "@/lib/types";

interface HeaderProps {
  totalValue: number | null;
  cashBalance: number | null;
  dayPnl: number | null;
  connectionStatus: ConnectionStatus;
}

export function Header({ totalValue, cashBalance, dayPnl, connectionStatus }: HeaderProps) {
  const pnlPositive = (dayPnl ?? 0) >= 0;
  return (
    <header className="flex items-center justify-between border-b border-border bg-panel px-5 py-3">
      <div className="flex items-center gap-3">
        <span className="font-display text-lg font-bold tracking-tight text-text">
          Fin<span className="text-yellow">Ally</span>
        </span>
        <span className="hidden text-xs text-text-faint sm:inline">AI Trading Workstation</span>
      </div>

      <div className="flex items-center gap-6">
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wider text-text-faint">Total Value</div>
          <div
            data-testid="header-total-value"
            className="font-data text-lg font-semibold text-text tabular-nums"
          >
            {totalValue !== null ? formatCurrency(totalValue) : "—"}
          </div>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wider text-text-faint">Unrealized P&amp;L</div>
          <div
            className={`font-data text-lg font-semibold tabular-nums ${
              pnlPositive ? "text-gain" : "text-loss"
            }`}
          >
            {dayPnl !== null ? formatCurrency(dayPnl) : "—"}
          </div>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wider text-text-faint">Cash</div>
          <div
            data-testid="header-cash-balance"
            className="font-data text-lg font-semibold text-text tabular-nums"
          >
            {cashBalance !== null ? formatCurrency(cashBalance) : "—"}
          </div>
        </div>
        <div className="border-l border-border pl-6">
          <ConnectionDot status={connectionStatus} />
        </div>
      </div>
    </header>
  );
}
