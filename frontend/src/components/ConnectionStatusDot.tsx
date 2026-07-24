export type ConnectionStatus = "connected" | "reconnecting" | "disconnected";

const STATUS_CONFIG: Record<ConnectionStatus, { color: string; label: string }> = {
  connected: { color: "bg-positive", label: "Connected" },
  reconnecting: { color: "bg-warning", label: "Reconnecting" },
  disconnected: { color: "bg-negative", label: "Disconnected" },
};

export function ConnectionStatusDot({ status }: { status: ConnectionStatus }) {
  const { color, label } = STATUS_CONFIG[status];

  return (
    <div className="flex items-center gap-2" title={label}>
      <span className={`h-2.5 w-2.5 rounded-full ${color}`} aria-hidden="true" />
      <span className="text-xs text-foreground-muted">{label}</span>
    </div>
  );
}
