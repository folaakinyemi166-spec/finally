export interface SparklineProps {
  data: number[];
  direction?: "up" | "down" | "flat" | null;
  width?: number;
  height?: number;
}

export function Sparkline({ data, direction, width = 72, height = 24 }: SparklineProps) {
  if (data.length < 2) {
    return (
      <div
        style={{ width, height }}
        className="flex shrink-0 items-center justify-center text-[10px] text-foreground-muted"
      >
        &ndash;
      </div>
    );
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const stepX = width / (data.length - 1);

  const points = data
    .map((value, index) => {
      const x = index * stepX;
      const y = height - ((value - min) / range) * height;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");

  const strokeColor =
    direction === "down"
      ? "var(--color-negative)"
      : direction === "up"
        ? "var(--color-positive)"
        : "var(--color-primary-blue)";

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="shrink-0 overflow-visible"
      aria-hidden="true"
    >
      <polyline
        points={points}
        fill="none"
        stroke={strokeColor}
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
