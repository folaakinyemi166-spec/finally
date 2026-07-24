"use client";

import { useEffect, useRef, useState } from "react";
import type { ConnectionStatus } from "@/components/ConnectionStatusDot";

export interface PriceUpdate {
  ticker: string;
  price: number;
  previous_price: number;
  timestamp: number;
  change: number;
  change_percent: number;
  direction: "up" | "down" | "flat";
}

export interface PriceTick extends PriceUpdate {
  /** Direction of the most recent change vs. the last value this client rendered. */
  flashDirection: "up" | "down" | null;
  /** Increments every time this ticker's price actually changes; used to restart the flash animation. */
  flashSeq: number;
}

const SPARKLINE_MAX_POINTS = 120;

/**
 * Connects to the live price SSE stream and accumulates per-ticker sparkline
 * history since the hook mounted. EventSource handles reconnection natively
 * (server sends a `retry:` directive); we only track status for display.
 */
export function usePriceStream() {
  const [prices, setPrices] = useState<Record<string, PriceTick>>({});
  const [history, setHistory] = useState<Record<string, number[]>>({});
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const lastPriceRef = useRef<Record<string, number>>({});
  const flashSeqRef = useRef<Record<string, number>>({});

  useEffect(() => {
    const source = new EventSource("/api/stream/prices");

    source.onopen = () => setStatus("connected");

    source.onerror = () => {
      setStatus(source.readyState === EventSource.CLOSED ? "disconnected" : "reconnecting");
    };

    source.onmessage = (event: MessageEvent<string>) => {
      const data = JSON.parse(event.data) as Record<string, PriceUpdate>;
      setStatus("connected");

      setPrices((current) => {
        const next = { ...current };
        for (const [ticker, update] of Object.entries(data)) {
          const lastPrice = lastPriceRef.current[ticker];
          let flashDirection: "up" | "down" | null = null;
          if (lastPrice !== undefined && update.price !== lastPrice) {
            flashDirection = update.price > lastPrice ? "up" : "down";
            flashSeqRef.current[ticker] = (flashSeqRef.current[ticker] ?? 0) + 1;
          }
          lastPriceRef.current[ticker] = update.price;
          next[ticker] = {
            ...update,
            flashDirection,
            flashSeq: flashSeqRef.current[ticker] ?? 0,
          };
        }
        return next;
      });

      setHistory((current) => {
        const next = { ...current };
        for (const [ticker, update] of Object.entries(data)) {
          const existing = next[ticker] ?? [];
          if (existing[existing.length - 1] === update.price) continue;
          const appended = [...existing, update.price];
          next[ticker] =
            appended.length > SPARKLINE_MAX_POINTS
              ? appended.slice(appended.length - SPARKLINE_MAX_POINTS)
              : appended;
        }
        return next;
      });
    };

    return () => {
      source.close();
    };
  }, []);

  return { prices, history, status };
}
