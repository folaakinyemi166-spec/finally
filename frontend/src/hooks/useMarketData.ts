"use client";

import { useEffect, useRef, useState } from "react";
import { subscribeToPriceStream } from "@/lib/api";
import type { ConnectionStatus, Direction, PriceUpdate } from "@/lib/types";

const HISTORY_LIMIT = 180; // ~90s of ticks at 500ms — plenty for a sparkline and the main chart

export interface PricePoint {
  price: number;
  timestamp: string;
}

export interface TickerMarketState {
  ticker: string;
  price: number;
  previousPrice: number;
  change: number;
  changePercent: number;
  direction: Direction;
  timestamp: string;
  history: PricePoint[];
  /** Bumped on every update so consumers can key a CSS flash animation. */
  flashToken: number;
}

export interface MarketData {
  status: ConnectionStatus;
  /** Latest state per ticker, accumulated client-side since page load. */
  tickers: Record<string, TickerMarketState>;
}

/**
 * Subscribes to the live price feed (mocked today, EventSource later — see
 * lib/api.ts) and accumulates a per-ticker price history for sparklines and
 * the main chart, exactly as PLAN.md §10 describes ("accumulated on the
 * frontend from the SSE stream since page load").
 */
export function useMarketData(): MarketData {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [tickers, setTickers] = useState<Record<string, TickerMarketState>>({});
  const flashTokens = useRef<Record<string, number>>({});

  useEffect(() => {
    const unsubscribe = subscribeToPriceStream({
      onStatusChange: setStatus,
      onUpdate: (update: PriceUpdate) => {
        setTickers((prev) => {
          const existing = prev[update.ticker];
          const history = existing ? [...existing.history] : [];
          history.push({ price: update.price, timestamp: update.timestamp });
          if (history.length > HISTORY_LIMIT) history.shift();

          flashTokens.current[update.ticker] = (flashTokens.current[update.ticker] ?? 0) + 1;

          return {
            ...prev,
            [update.ticker]: {
              ticker: update.ticker,
              price: update.price,
              previousPrice: update.previous_price,
              change: update.change,
              changePercent: update.change_percent,
              direction: update.direction,
              timestamp: update.timestamp,
              history,
              flashToken: flashTokens.current[update.ticker],
            },
          };
        });
      },
    });

    return unsubscribe;
  }, []);

  return { status, tickers };
}
