"use client";

import { useCallback, useEffect, useState } from "react";
import { addToWatchlist, fetchWatchlist, removeFromWatchlist } from "@/lib/api";
import type { WatchlistEntry } from "@/lib/types";

export interface UseWatchlistResult {
  tickers: string[];
  loading: boolean;
  error: string | null;
  add: (ticker: string) => Promise<void>;
  remove: (ticker: string) => Promise<void>;
}

/**
 * Owns the watchlist membership (GET/POST/DELETE /api/watchlist). Live
 * prices are NOT sourced here — they flow separately from the SSE stream
 * via useMarketData, matching the real architecture (§8: the watchlist
 * endpoint just joins the price cache at read time; the stream is what
 * keeps things live).
 */
export function useWatchlist(): UseWatchlistResult {
  const [entries, setEntries] = useState<WatchlistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchWatchlist()
      .then((data) => {
        if (!cancelled) setEntries(data);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const add = useCallback(async (ticker: string) => {
    setError(null);
    try {
      const entry = await addToWatchlist(ticker);
      setEntries((prev) => [...prev, entry]);
    } catch (err) {
      setError((err as Error).message);
      throw err;
    }
  }, []);

  const remove = useCallback(async (ticker: string) => {
    setError(null);
    try {
      await removeFromWatchlist(ticker);
      setEntries((prev) => prev.filter((e) => e.ticker !== ticker));
    } catch (err) {
      setError((err as Error).message);
      throw err;
    }
  }, []);

  return {
    tickers: entries.map((e) => e.ticker),
    loading,
    error,
    add,
    remove,
  };
}
