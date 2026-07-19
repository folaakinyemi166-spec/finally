"use client";

import { useState } from "react";
import { WatchlistRow } from "./WatchlistRow";
import type { TickerMarketState } from "@/hooks/useMarketData";

interface WatchlistPanelProps {
  tickers: string[];
  marketByTicker: Record<string, TickerMarketState>;
  selectedTicker: string | null;
  onSelect: (ticker: string) => void;
  onAdd: (ticker: string) => Promise<void>;
  onRemove: (ticker: string) => void;
  error: string | null;
}

export function WatchlistPanel({
  tickers,
  marketByTicker,
  selectedTicker,
  onSelect,
  onAdd,
  onRemove,
  error,
}: WatchlistPanelProps) {
  const [input, setInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const ticker = input.trim().toUpperCase();
    if (!ticker) return;
    setSubmitting(true);
    setLocalError(null);
    try {
      await onAdd(ticker);
      setInput("");
    } catch (err) {
      setLocalError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="flex h-full flex-col border-r border-border bg-panel">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-text-dim">Watchlist</h2>
        <span className="font-data text-[10px] text-text-faint">{tickers.length}/30</span>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-1.5 border-b border-border p-2">
        <input
          data-testid="watchlist-add-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Add ticker…"
          maxLength={5}
          className="min-w-0 flex-1 rounded border border-border bg-panel-alt px-2 py-1 font-data text-xs uppercase text-text placeholder:text-text-faint focus:border-blue focus:outline-none"
        />
        <button
          type="submit"
          data-testid="watchlist-add-button"
          disabled={submitting || !input.trim()}
          className="rounded bg-purple px-2.5 py-1 text-xs font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          Add
        </button>
      </form>
      {(localError || error) && (
        <p className="border-b border-border bg-loss-dim/20 px-3 py-1.5 text-xs text-loss">
          {localError ?? error}
        </p>
      )}

      <div className="flex-1 overflow-y-auto">
        {tickers.length === 0 ? (
          <p className="p-4 text-center text-xs text-text-faint">
            Your watchlist is empty. Add a ticker above to start streaming prices.
          </p>
        ) : (
          tickers.map((ticker) => (
            <WatchlistRow
              key={ticker}
              ticker={ticker}
              market={marketByTicker[ticker]}
              selected={selectedTicker === ticker}
              onSelect={onSelect}
              onRemove={onRemove}
            />
          ))
        )}
      </div>
    </section>
  );
}
