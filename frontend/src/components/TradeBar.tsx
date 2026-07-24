"use client";

import { useState } from "react";
import type { PortfolioOut, TradeOut } from "@/lib/types";

export interface TradeBarProps {
  onTradeExecuted?: (portfolio: PortfolioOut) => void;
}

type Side = "buy" | "sell";

export function TradeBar({ onTradeExecuted }: TradeBarProps) {
  const [ticker, setTicker] = useState("");
  const [quantity, setQuantity] = useState("");
  const [submitting, setSubmitting] = useState<Side | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<string | null>(null);

  async function submitTrade(side: Side) {
    const trimmedTicker = ticker.trim().toUpperCase();
    const parsedQuantity = Number(quantity);

    setError(null);
    setConfirmation(null);

    if (!trimmedTicker) {
      setError("Enter a ticker symbol.");
      return;
    }
    if (!Number.isFinite(parsedQuantity) || parsedQuantity <= 0) {
      setError("Enter a quantity greater than 0.");
      return;
    }

    setSubmitting(side);
    try {
      const response = await fetch("/api/portfolio/trade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: trimmedTicker, side, quantity: parsedQuantity }),
      });

      const data = await response.json();

      if (!response.ok) {
        const detail = typeof data?.detail === "string" ? data.detail : "Trade failed.";
        setError(detail);
        return;
      }

      const trade = data as TradeOut;
      setConfirmation(
        `${side === "buy" ? "Bought" : "Sold"} ${trade.quantity} ${trade.ticker} @ $${trade.price.toFixed(2)}`,
      );
      setQuantity("");
      onTradeExecuted?.(trade.portfolio);
    } catch {
      setError("Network error — could not reach the server.");
    } finally {
      setSubmitting(null);
    }
  }

  const disabled = submitting !== null;

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-4">
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-[11px] uppercase tracking-wide text-foreground-muted">
          Ticker
          <input
            value={ticker}
            onChange={(event) => setTicker(event.target.value.toUpperCase())}
            placeholder="AAPL"
            maxLength={10}
            disabled={disabled}
            className="w-24 rounded border border-border bg-background px-2 py-1.5 font-mono text-sm text-foreground focus:border-primary-blue focus:outline-none disabled:opacity-50"
          />
        </label>

        <label className="flex flex-col gap-1 text-[11px] uppercase tracking-wide text-foreground-muted">
          Quantity
          <input
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
            placeholder="10"
            inputMode="decimal"
            disabled={disabled}
            className="w-24 rounded border border-border bg-background px-2 py-1.5 font-mono text-sm text-foreground focus:border-primary-blue focus:outline-none disabled:opacity-50"
          />
        </label>

        <button
          type="button"
          onClick={() => submitTrade("buy")}
          disabled={disabled}
          className="rounded bg-positive px-4 py-1.5 text-sm font-semibold text-background transition-opacity disabled:opacity-50"
        >
          {submitting === "buy" ? "Buying…" : "Buy"}
        </button>

        <button
          type="button"
          onClick={() => submitTrade("sell")}
          disabled={disabled}
          className="rounded bg-negative px-4 py-1.5 text-sm font-semibold text-background transition-opacity disabled:opacity-50"
        >
          {submitting === "sell" ? "Selling…" : "Sell"}
        </button>
      </div>

      {error && (
        <p role="alert" className="text-xs text-negative">
          {error}
        </p>
      )}
      {confirmation && !error && <p className="text-xs text-positive">{confirmation}</p>}
    </div>
  );
}
