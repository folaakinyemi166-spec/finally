import type { ConnectionStatus } from "@/lib/types";

const STYLES: Record<ConnectionStatus, { color: string; label: string; pulse: boolean }> = {
  connected: { color: "bg-gain", label: "Live", pulse: false },
  connecting: { color: "bg-yellow", label: "Connecting", pulse: true },
  reconnecting: { color: "bg-yellow", label: "Reconnecting", pulse: true },
  disconnected: { color: "bg-loss", label: "Disconnected", pulse: false },
};

export function ConnectionDot({ status }: { status: ConnectionStatus }) {
  const s = STYLES[status];
  return (
    <div className="flex items-center gap-2" data-testid="connection-dot" data-status={status}>
      <span className={`h-2 w-2 rounded-full ${s.color} ${s.pulse ? "pulse-dot" : ""}`} />
      <span className="text-xs uppercase tracking-wider text-text-dim">{s.label}</span>
    </div>
  );
}
