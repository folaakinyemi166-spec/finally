import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { HistoryPoint } from "@/lib/portfolio";

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const timeFormatter = new Intl.DateTimeFormat("en-US", {
  hour: "2-digit",
  minute: "2-digit",
});

export interface PnlChartProps {
  history: HistoryPoint[];
}

export function PnlChart({ history }: PnlChartProps) {
  if (history.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-border bg-surface text-sm text-foreground-muted">
        No portfolio history yet.
      </div>
    );
  }

  const data = history.map((point) => ({
    time: timeFormatter.format(new Date(point.recorded_at)),
    total_value: point.total_value,
  }));

  return (
    <div className="h-64 rounded-lg border border-border bg-surface p-2">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="time" stroke="var(--foreground-muted)" fontSize={11} />
          <YAxis
            width={64}
            stroke="var(--foreground-muted)"
            fontSize={11}
            tickFormatter={(value: number) => currency.format(value)}
            domain={["auto", "auto"]}
          />
          <Tooltip
            formatter={(value) => currency.format(Number(value))}
            contentStyle={{
              backgroundColor: "var(--surface-raised)",
              borderColor: "var(--border)",
              fontSize: 12,
            }}
          />
          <Line
            type="monotone"
            dataKey="total_value"
            stroke="var(--color-primary-blue)"
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
