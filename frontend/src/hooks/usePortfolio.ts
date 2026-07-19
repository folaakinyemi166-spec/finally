"use client";

import { useCallback, useEffect, useState } from "react";
import { executeTrade, fetchPortfolio, fetchPortfolioHistory } from "@/lib/api";
import type { PortfolioSnapshot, PortfolioSummary, TradeRequest, TradeResult } from "@/lib/types";

const POLL_MS = 2000;

export interface UsePortfolioResult {
  portfolio: PortfolioSummary | null;
  history: PortfolioSnapshot[];
  loading: boolean;
  trade: (req: TradeRequest) => Promise<TradeResult>;
}

/**
 * Owns portfolio state (GET /api/portfolio, GET /api/portfolio/history,
 * POST /api/portfolio/trade). Polls at a short interval so unrealized P&L
 * tracks the live price cache without wiring a second data path — a real
 * backend would recompute the same way on each GET.
 */
export function usePortfolio(): UsePortfolioResult {
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [history, setHistory] = useState<PortfolioSnapshot[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const [p, h] = await Promise.all([fetchPortfolio(), fetchPortfolioHistory()]);
    setPortfolio(p);
    setHistory(h);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadInitial() {
      await refresh();
      if (!cancelled) setLoading(false);
    }
    loadInitial();
    const id = setInterval(() => {
      refresh();
    }, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [refresh]);

  const trade = useCallback(
    async (req: TradeRequest) => {
      const result = await executeTrade(req);
      if (result.success) {
        setPortfolio(result.portfolio);
        const h = await fetchPortfolioHistory();
        setHistory(h);
      }
      return result;
    },
    [],
  );

  return { portfolio, history, loading, trade };
}
