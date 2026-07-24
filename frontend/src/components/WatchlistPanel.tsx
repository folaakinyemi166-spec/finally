"use client";

import { useEffect, useState, type FormEvent, type KeyboardEvent } from "react";
import { ConnectionStatusDot } from "@/components/ConnectionStatusDot";
import { Sparkline } from "@/components/Sparkline";
import { usePriceStream, type PriceTick } from "@/hooks/usePriceStream";
import { addWatchlistTicker, fetchWatchlist, removeWatchlistTicker } from "@/lib/watchlist";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const percentFormatter = new Intl.NumberFormat("en-US", {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  signDisplay: "exceptZero",
});

function changeColorClass(percent: number | null): string {
  if (percent === null || percent === 0) return "text-foreground-muted";
  return percent > 0 ? "text-positive" : "text-negative";
}

export interface WatchlistPanelProps {
  selectedTicker: string | null;
  onSelectTicker: (ticker: string) => void;
}

export function WatchlistPanel({ selectedTicker, onSelectTicker }: WatchlistPanelProps) {
  const [tickers, setTickers] = useState<string[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [newTicker, setNewTicker] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const { prices, history, status } = usePriceStream();

  useEffect(() => {
    let cancelled = false;
    fetchWatchlist()
      .then((entries) => {
        if (cancelled) return;
        setTickers(entries.map((entry) => entry.ticker));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setLoadError(err instanceof Error ? err.message : "Failed to load watchlist");
      })
      .finally(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleAdd(event: FormEvent) {
    event.preventDefault();
    const ticker = newTicker.trim().toUpperCase();
    if (!ticker || tickers.includes(ticker)) return;

    setPending(true);
    setFormError(null);
    try {
      await addWatchlistTicker(ticker);
      setTickers((current) => (current.includes(ticker) ? current : [...current, ticker]));
      setNewTicker("");
    } catch (err) {
      setFormError(err instanceof Error ? err.message : `Failed to add ${ticker}`);
    } finally {
      setPending(false);
    }
  }

  async function handleRemove(ticker: string) {
    setTickers((current) => current.filter((t) => t !== ticker));
    try {
      await removeWatchlistTicker(ticker);
    } catch (err) {
      // Roll back the optimistic removal if the backend call failed.
      setTickers((current) => (current.includes(ticker) ? current : [...current, ticker]));
      setFormError(err instanceof Error ? err.message : `Failed to remove ${ticker}`);
    }
  }

  return (
    <section className="flex w-full max-w-md flex-col gap-3 rounded-lg border border-border bg-surface p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-foreground-muted">
          Watchlist
        </h2>
        <ConnectionStatusDot status={status} />
      </div>

      <form onSubmit={handleAdd} className="flex gap-2">
        <input
          value={newTicker}
          onChange={(event) => setNewTicker(event.target.value)}
          placeholder="Add ticker..."
          maxLength={10}
          aria-label="Add ticker to watchlist"
          className="min-w-0 flex-1 rounded border border-border bg-background px-2 py-1 text-sm uppercase text-foreground placeholder:normal-case placeholder:text-foreground-muted focus:outline-none focus:ring-1 focus:ring-primary-blue"
        />
        <button
          type="submit"
          disabled={pending || !newTicker.trim()}
          className="shrink-0 rounded bg-secondary-purple px-3 py-1 text-sm font-medium text-foreground disabled:cursor-not-allowed disabled:opacity-50"
        >
          Add
        </button>
      </form>
      {formError && <p className="text-xs text-negative">{formError}</p>}
      {loadError && <p className="text-xs text-negative">{loadError}</p>}

      <div className="flex flex-col divide-y divide-border">
        {!loaded && <p className="py-4 text-center text-xs text-foreground-muted">Loading watchlist…</p>}
        {loaded && tickers.length === 0 && (
          <p className="py-4 text-center text-xs text-foreground-muted">
            No tickers yet. Add one above.
          </p>
        )}
        {tickers.map((ticker) => (
          <WatchlistRow
            key={ticker}
            ticker={ticker}
            tick={prices[ticker]}
            sparkline={history[ticker] ?? []}
            selected={ticker === selectedTicker}
            onSelect={() => onSelectTicker(ticker)}
            onRemove={() => handleRemove(ticker)}
          />
        ))}
      </div>
    </section>
  );
}

interface WatchlistRowProps {
  ticker: string;
  tick: PriceTick | undefined;
  sparkline: number[];
  selected: boolean;
  onSelect: () => void;
  onRemove: () => void;
}

function WatchlistRow({ ticker, tick, sparkline, selected, onSelect, onRemove }: WatchlistRowProps) {
  const price = tick?.price ?? null;
  const changePercent = tick?.change_percent ?? null;
  const flashClass =
    tick?.flashDirection === "up"
      ? "animate-flash-green"
      : tick?.flashDirection === "down"
        ? "animate-flash-red"
        : "";

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect();
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={handleKeyDown}
      className={`flex cursor-pointer items-center gap-3 px-1 py-2 text-sm transition-colors hover:bg-surface-raised ${
        selected ? "bg-surface-raised" : ""
      }`}
    >
      <div className="w-14 shrink-0 font-mono font-semibold text-foreground">{ticker}</div>

      <div
        key={tick?.flashSeq ?? 0}
        className={`w-20 shrink-0 rounded text-right font-mono tabular-nums text-foreground ${flashClass}`}
      >
        {price !== null ? currencyFormatter.format(price) : "—"}
      </div>

      <div className={`w-16 shrink-0 text-right font-mono text-xs ${changeColorClass(changePercent)}`}>
        {changePercent !== null ? percentFormatter.format(changePercent / 100) : "—"}
      </div>

      <Sparkline data={sparkline} direction={tick?.direction ?? null} />

      <button
        type="button"
        onClick={(event) => {
          event.stopPropagation();
          onRemove();
        }}
        aria-label={`Remove ${ticker} from watchlist`}
        className="ml-auto shrink-0 rounded px-1.5 py-0.5 text-xs text-foreground-muted hover:bg-negative/20 hover:text-negative"
      >
        ✕
      </button>
    </div>
  );
}
