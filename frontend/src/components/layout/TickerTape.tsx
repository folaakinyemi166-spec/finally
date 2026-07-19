import type { TickerMarketState } from "@/hooks/useMarketData";
import { formatPercent, formatPrice } from "@/lib/format";

interface TickerTapeProps {
  tickers: TickerMarketState[];
}

const DIRECTION_COLOR: Record<string, string> = {
  up: "text-gain",
  down: "text-loss",
  flat: "text-text-dim",
};

const DIRECTION_ARROW: Record<string, string> = {
  up: "▲",
  down: "▼",
  flat: "•",
};

/**
 * Signature element: a continuously scrolling exchange-tape strip, the way
 * a real trading floor or terminal displays the whole market at a glance.
 * The list is duplicated so the CSS loop (-50%) reads as seamless.
 */
export function TickerTape({ tickers }: TickerTapeProps) {
  if (tickers.length === 0) {
    return <div className="h-9 border-b border-border bg-black/20" />;
  }

  const renderItem = (t: TickerMarketState, key: string) => (
    <span key={key} className="mx-4 inline-flex items-center gap-2 font-data text-xs">
      <span className="font-semibold text-text">{t.ticker}</span>
      <span className="tabular-nums text-text-dim">{formatPrice(t.price)}</span>
      <span className={`tabular-nums ${DIRECTION_COLOR[t.direction]}`}>
        {DIRECTION_ARROW[t.direction]} {formatPercent(t.changePercent)}
      </span>
    </span>
  );

  return (
    <div className="overflow-hidden border-b border-border bg-black/20">
      <div className="tape-track flex w-max whitespace-nowrap py-2">
        {tickers.map((t) => renderItem(t, `a-${t.ticker}`))}
        {tickers.map((t) => renderItem(t, `b-${t.ticker}`))}
      </div>
    </div>
  );
}
