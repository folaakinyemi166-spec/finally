"use client";

import { useEffect, useState } from "react";
import { Sparkline } from "./Sparkline";
import { formatPercent, formatPrice } from "@/lib/format";
import type { TickerMarketState } from "@/hooks/useMarketData";

interface WatchlistRowProps {
  ticker: string;
  market: TickerMarketState | undefined;
  selected: boolean;
  onSelect: (ticker: string) => void;
  onRemove: (ticker: string) => void;
}

const SPARK_COLOR = { up: "#3fb950", down: "#f85149", flat: "#8b98a5" };

export function WatchlistRow({ ticker, market, selected, onSelect, onRemove }: WatchlistRowProps) {
  const [flashClass, setFlashClass] = useState("");
  // Track the last tick we've reacted to as plain render-time state (React's
  // "adjust state during render" pattern) instead of an effect, so the flash
  // class is derived synchronously with the new price rather than one tick
  // behind it.
  const [seenToken, setSeenToken] = useState<number | undefined>(market?.flashToken);

  if (market && market.flashToken !== seenToken) {
    const isFirstSighting = seenToken === undefined;
    setSeenToken(market.flashToken);
    if (!isFirstSighting) {
      if (market.direction === "up") setFlashClass("flash-up");
      else if (market.direction === "down") setFlashClass("flash-down");
    }
  }

  // The flash is a genuine effect: a timer that clears the class after the
  // CSS animation finishes.
  useEffect(() => {
    if (!flashClass) return;
    const t = setTimeout(() => setFlashClass(""), 550);
    return () => clearTimeout(t);
  }, [flashClass]);

  const direction = market?.direction ?? "flat";
  const color = direction === "up" ? "text-gain" : direction === "down" ? "text-loss" : "text-text-dim";
  const sparkValues = market?.history.slice(-40).map((p) => p.price) ?? [];

  return (
    <button
      type="button"
      onClick={() => onSelect(ticker)}
      data-testid={`watchlist-row-${ticker}`}
      className={`group flex w-full items-center justify-between border-b border-border-soft px-3 py-2 text-left transition-colors ${flashClass} ${
        selected ? "bg-panel-alt" : "hover:bg-panel-alt/60"
      }`}
    >
      <div className="flex min-w-0 flex-col">
        <span className={`font-data text-sm font-semibold ${selected ? "text-yellow" : "text-text"}`}>
          {ticker}
        </span>
        <span className={`font-data text-xs tabular-nums ${color}`}>
          {formatPercent(market?.changePercent ?? null)}
        </span>
      </div>

      <Sparkline values={sparkValues} color={SPARK_COLOR[direction]} />

      <div className="flex items-center gap-2">
        <span className="font-data text-sm tabular-nums text-text">{formatPrice(market?.price ?? null)}</span>
        <span
          role="button"
          tabIndex={0}
          aria-label={`Remove ${ticker} from watchlist`}
          onClick={(e) => {
            e.stopPropagation();
            onRemove(ticker);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.stopPropagation();
              onRemove(ticker);
            }
          }}
          className="rounded px-1.5 py-0.5 text-xs text-text-faint opacity-0 transition-opacity hover:bg-loss-dim hover:text-text group-hover:opacity-100"
        >
          ✕
        </span>
      </div>
    </button>
  );
}
