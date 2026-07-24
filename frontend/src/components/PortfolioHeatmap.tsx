import { ResponsiveContainer, Treemap, type TreemapNode } from "recharts";
import type { Position } from "@/lib/portfolio";

const POSITIVE_RGB = "46, 204, 113";
const NEGATIVE_RGB = "240, 71, 91";
const NEUTRAL_RGB = "139, 148, 158";

// Saturates color intensity at +/-10% P&L so a handful of big movers don't
// wash out the rest of the map.
const INTENSITY_SATURATION_PERCENT = 10;

function heatColor(pnlPercent: number): string {
  if (!Number.isFinite(pnlPercent) || pnlPercent === 0) {
    return `rgb(${NEUTRAL_RGB})`;
  }
  const magnitude = Math.min(Math.abs(pnlPercent) / INTENSITY_SATURATION_PERCENT, 1);
  const alpha = 0.35 + magnitude * 0.55;
  const rgb = pnlPercent > 0 ? POSITIVE_RGB : NEGATIVE_RGB;
  return `rgba(${rgb}, ${alpha.toFixed(2)})`;
}

interface HeatmapCellProps extends Partial<TreemapNode> {
  pnlPercent?: number;
}

// Recharts clones this element per rectangle, injecting layout props (x, y,
// width, height) plus every key from the original data entry (pnlPercent).
function HeatmapCell({ x = 0, y = 0, width = 0, height = 0, name = "", pnlPercent = 0 }: HeatmapCellProps) {
  if (width <= 0 || height <= 0) {
    return null;
  }

  const showLabel = width > 44 && height > 24;
  const showPnl = width > 44 && height > 40;

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{ fill: heatColor(pnlPercent), stroke: "var(--border)", strokeWidth: 1 }}
      />
      {showLabel ? (
        <text
          x={x + width / 2}
          y={y + height / 2 - (showPnl ? 6 : 0)}
          textAnchor="middle"
          fill="var(--foreground)"
          fontSize={13}
          fontWeight={600}
        >
          {name}
        </text>
      ) : null}
      {showPnl ? (
        <text
          x={x + width / 2}
          y={y + height / 2 + 12}
          textAnchor="middle"
          fill="var(--foreground)"
          fontSize={11}
          opacity={0.85}
        >
          {pnlPercent >= 0 ? "+" : ""}
          {pnlPercent.toFixed(2)}%
        </text>
      ) : null}
    </g>
  );
}

export interface PortfolioHeatmapProps {
  positions: Position[];
}

export function PortfolioHeatmap({ positions }: PortfolioHeatmapProps) {
  if (positions.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-border bg-surface text-sm text-foreground-muted">
        No open positions.
      </div>
    );
  }

  const data = positions.map((position) => ({
    name: position.ticker,
    size: Math.max(position.market_value, 0.01),
    pnlPercent: position.unrealized_pnl_percent,
  }));

  return (
    <div className="h-64 rounded-lg border border-border bg-surface p-2">
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={data}
          dataKey="size"
          nameKey="name"
          aspectRatio={4 / 3}
          isAnimationActive={false}
          content={<HeatmapCell />}
        />
      </ResponsiveContainer>
    </div>
  );
}
