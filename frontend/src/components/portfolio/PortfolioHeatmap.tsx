"use client";

import { Treemap, ResponsiveContainer } from "recharts";
import { heatmapColor } from "@/lib/colorScale";
import { formatPercent } from "@/lib/format";
import type { Position } from "@/lib/types";

interface HeatmapDatum {
  name: string;
  size: number;
  pnlPercent: number;
  // Recharts' TreemapDataType requires an index signature.
  [key: string]: unknown;
}

interface CellProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  name?: string;
  pnlPercent?: number;
  depth?: number;
}

function HeatmapCell(props: CellProps) {
  const { x = 0, y = 0, width = 0, height = 0, name, pnlPercent = 0, depth } = props;
  if (depth !== 1) return null;

  const showLabel = width > 46 && height > 28;
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill: heatmapColor(pnlPercent),
          stroke: "#0d1117",
          strokeWidth: 2,
        }}
      />
      {showLabel && (
        <>
          <text x={x + 8} y={y + 18} fill="#e6edf3" fontSize={12} fontWeight={600}>
            {name}
          </text>
          <text x={x + 8} y={y + 34} fill="#e6edf3" fillOpacity={0.85} fontSize={11}>
            {formatPercent(pnlPercent)}
          </text>
        </>
      )}
    </g>
  );
}

export function PortfolioHeatmap({ positions }: { positions: Position[] }) {
  const data: HeatmapDatum[] = positions
    .filter((p) => p.market_value > 0)
    .map((p) => ({
      name: p.ticker,
      size: p.market_value,
      pnlPercent: p.unrealized_pnl_percent,
    }));

  return (
    <div className="flex h-full flex-col" data-testid="portfolio-heatmap">
      <div className="border-b border-border px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-text-dim">
          Portfolio Heatmap
        </h2>
      </div>
      <div className="min-h-0 flex-1 p-2">
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-center text-xs text-text-faint">
            No open positions yet. Buy shares to see them sized and colored here.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <Treemap
              data={data}
              dataKey="size"
              stroke="#0d1117"
              fill="#1f2937"
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              content={HeatmapCell as any}
              isAnimationActive={false}
            />
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
