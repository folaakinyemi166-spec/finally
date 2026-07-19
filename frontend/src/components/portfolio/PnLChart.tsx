"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCurrency } from "@/lib/format";
import type { PortfolioSnapshot } from "@/lib/types";

interface PnLChartProps {
  history: PortfolioSnapshot[];
}

interface TooltipPayloadItem {
  value: number;
}

function ValueTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayloadItem[] }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded border border-border bg-panel-raised px-2 py-1 font-data text-xs text-text shadow-lg">
      {formatCurrency(payload[0].value)}
    </div>
  );
}

export function PnLChart({ history }: PnLChartProps) {
  const data = history.map((s) => ({
    time: new Date(s.recorded_at).getTime(),
    value: s.total_value,
  }));
  const first = data[0]?.value ?? 0;
  const last = data[data.length - 1]?.value ?? 0;
  const up = last >= first;

  return (
    <div className="flex h-full flex-col" data-testid="pnl-chart">
      <div className="border-b border-border px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-text-dim">
          Portfolio Value
        </h2>
      </div>
      <div className="min-h-0 flex-1 p-2">
        {data.length < 2 ? (
          <div className="flex h-full items-center justify-center text-xs text-text-faint">
            Accumulating history…
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
              <XAxis
                dataKey="time"
                type="number"
                domain={["dataMin", "dataMax"]}
                tickFormatter={(t: number) =>
                  new Date(t).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
                }
                stroke="#5b6674"
                tick={{ fontSize: 10, fontFamily: "var(--font-data)" }}
                axisLine={{ stroke: "#2a3441" }}
                tickLine={false}
              />
              <YAxis
                domain={["auto", "auto"]}
                stroke="#5b6674"
                tick={{ fontSize: 10, fontFamily: "var(--font-data)" }}
                axisLine={{ stroke: "#2a3441" }}
                tickLine={false}
                width={56}
                tickFormatter={(v: number) => formatCurrency(v, { compact: true })}
              />
              <Tooltip content={<ValueTooltip />} />
              <Line
                type="monotone"
                dataKey="value"
                stroke={up ? "#3fb950" : "#f85149"}
                strokeWidth={1.75}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
