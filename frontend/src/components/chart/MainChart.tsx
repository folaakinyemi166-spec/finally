"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  AreaSeries,
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import type { PricePoint } from "@/hooks/useMarketData";
import { formatPrice } from "@/lib/format";

interface MainChartProps {
  ticker: string | null;
  price: number | null;
  changePercent: number | null;
  history: PricePoint[];
}

/**
 * The detailed chart for the ticker currently selected in the watchlist.
 * Canvas-based via lightweight-charts (PLAN.md §10) — the one view in the
 * app that warrants a dedicated chart instance; sparklines use plain SVG.
 */
export function MainChart({ ticker, price, changePercent, history }: MainChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#8b98a5",
        fontFamily: "'IBM Plex Mono', ui-monospace, monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "#1c2531" },
        horzLines: { color: "#1c2531" },
      },
      rightPriceScale: { borderColor: "#2a3441" },
      timeScale: { borderColor: "#2a3441", timeVisible: true, secondsVisible: true },
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
    });

    const series = chart.addSeries(AreaSeries, {
      lineColor: "#209dd7",
      topColor: "rgba(32, 157, 215, 0.32)",
      bottomColor: "rgba(32, 157, 215, 0.02)",
      lineWidth: 2,
      priceLineVisible: false,
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const observer = new ResizeObserver(() => {
      if (!containerRef.current) return;
      chart.applyOptions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
      });
    });
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current) return;
    const data: { time: UTCTimestamp; value: number }[] = [];
    for (const point of history) {
      const time = Math.floor(new Date(point.timestamp).getTime() / 1000) as UTCTimestamp;
      const last = data[data.length - 1];
      if (last && last.time === time) {
        last.value = point.price;
      } else if (!last || time > last.time) {
        data.push({ time, value: point.price });
      }
    }
    seriesRef.current.setData(data);
    chartRef.current?.timeScale().fitContent();
  }, [history]);

  const direction = (changePercent ?? 0) >= 0 ? "text-gain" : "text-loss";

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-text-dim">Chart</h2>
        {ticker ? (
          <div className="flex items-baseline gap-2">
            <span className="font-display text-sm font-bold text-text">{ticker}</span>
            <span className="font-data text-sm tabular-nums text-text">{formatPrice(price)}</span>
            <span className={`font-data text-xs tabular-nums ${direction}`}>
              {changePercent !== null ? `${changePercent >= 0 ? "+" : ""}${changePercent.toFixed(2)}%` : ""}
            </span>
          </div>
        ) : (
          <span className="text-xs text-text-faint">Select a ticker from the watchlist</span>
        )}
      </div>
      <div ref={containerRef} className="min-h-0 flex-1 px-1 py-1" />
    </div>
  );
}
