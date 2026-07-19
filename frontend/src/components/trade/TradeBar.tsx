"use client";

import { useState } from "react";
import type { TradeRequest, TradeResult } from "@/lib/types";

interface TradeBarProps {
  defaultTicker: string | null;
  onTrade: (req: TradeRequest) => Promise<TradeResult>;
}

export function TradeBar({ defaultTicker, onTrade }: TradeBarProps) {
  const [ticker, setTicker] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [submitting, setSubmitting] = useState<"buy" | "sell" | null>(null);
  const [feedback, setFeedback] = useState<{ ok: boolean; text: string } | null>(null);

  const effectiveTicker = (ticker || defaultTicker || "").toUpperCase();

  async function handleTrade(side: "buy" | "sell") {
    const qty = parseFloat(quantity);
    if (!effectiveTicker || !Number.isFinite(qty) || qty <= 0) {
      setFeedback({ ok: false, text: "Enter a ticker and a valid quantity." });
      return;
    }
    setSubmitting(side);
    setFeedback(null);
    try {
      const result = await onTrade({ ticker: effectiveTicker, quantity: qty, side });
      if (result.success && result.trade) {
        setFeedback({
          ok: true,
          text: `${side === "buy" ? "Bought" : "Sold"} ${qty} ${effectiveTicker} @ $${result.trade.price.toFixed(2)}`,
        });
      } else {
        setFeedback({ ok: false, text: result.error ?? "Trade failed" });
      }
    } catch (err) {
      setFeedback({ ok: false, text: (err as Error).message });
    } finally {
      setSubmitting(null);
    }
  }

  return (
    <div className="border-t border-border bg-panel px-3 py-2.5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-text-faint">
          Trade
        </span>
        <input
          data-testid="trade-ticker-input"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder={defaultTicker ?? "Ticker"}
          maxLength={5}
          className="w-20 rounded border border-border bg-panel-alt px-2 py-1.5 font-data text-xs uppercase text-text placeholder:text-text-faint focus:border-blue focus:outline-none"
        />
        <input
          data-testid="trade-quantity-input"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          placeholder="Qty"
          inputMode="decimal"
          className="w-24 rounded border border-border bg-panel-alt px-2 py-1.5 font-data text-xs text-text placeholder:text-text-faint focus:border-blue focus:outline-none"
        />
        <button
          type="button"
          onClick={() => handleTrade("buy")}
          disabled={submitting !== null}
          className="rounded bg-gain px-4 py-1.5 text-xs font-bold uppercase tracking-wide text-[#04170a] transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          Buy
        </button>
        <button
          type="button"
          onClick={() => handleTrade("sell")}
          disabled={submitting !== null}
          className="rounded bg-loss px-4 py-1.5 text-xs font-bold uppercase tracking-wide text-[#1a0403] transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          Sell
        </button>
        <span className="text-[10px] text-text-faint">Market order · instant fill · no fees</span>
        {feedback && (
          <span
            data-testid="trade-feedback"
            className={`ml-auto font-data text-xs ${feedback.ok ? "text-gain" : "text-loss"}`}
          >
            {feedback.text}
          </span>
        )}
      </div>
    </div>
  );
}
