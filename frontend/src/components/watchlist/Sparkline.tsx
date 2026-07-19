interface SparklineProps {
  values: number[];
  width?: number;
  height?: number;
  color: string;
}

/**
 * Minimal inline SVG sparkline. Deliberately not a canvas/chart-library
 * instance per row — with up to 30 watchlist rows re-rendering on every
 * tick, a lightweight SVG polyline is cheaper than 30 chart instances.
 * The main chart (MainChart.tsx) uses lightweight-charts for the one
 * detailed view that needs it.
 */
export function Sparkline({ values, width = 72, height = 26, color }: SparklineProps) {
  if (values.length < 2) {
    return <svg width={width} height={height} aria-hidden="true" />;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = width / (values.length - 1);

  const points = values
    .map((v, i) => {
      const x = i * step;
      const y = height - ((v - min) / range) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <polyline points={points} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
