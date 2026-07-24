import { ConnectionStatusDot, type ConnectionStatus } from "./ConnectionStatusDot";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export interface HeaderProps {
  portfolioValue: number;
  cashBalance: number;
  connectionStatus: ConnectionStatus;
}

export function Header({ portfolioValue, cashBalance, connectionStatus }: HeaderProps) {
  return (
    <header className="flex items-center justify-between border-b border-border bg-surface px-6 py-3">
      <div className="flex items-center gap-2">
        <span className="text-lg font-semibold tracking-tight text-accent-yellow">
          FinAlly
        </span>
        <span className="hidden text-xs text-foreground-muted sm:inline">
          AI Trading Workstation
        </span>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex flex-col items-end">
          <span className="text-[11px] uppercase tracking-wide text-foreground-muted">
            Portfolio Value
          </span>
          <span className="font-mono text-base font-semibold text-foreground">
            {currencyFormatter.format(portfolioValue)}
          </span>
        </div>

        <div className="flex flex-col items-end">
          <span className="text-[11px] uppercase tracking-wide text-foreground-muted">
            Cash
          </span>
          <span className="font-mono text-base text-foreground">
            {currencyFormatter.format(cashBalance)}
          </span>
        </div>

        <ConnectionStatusDot status={connectionStatus} />
      </div>
    </header>
  );
}
