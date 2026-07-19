import { formatClock } from "@/lib/format";
import type { ChatMessage } from "@/lib/types";

function ActionPill({ action }: { action: ChatMessage["actions"] extends (infer U)[] | null ? U : never }) {
  const success = action.success;
  const label =
    action.type === "trade"
      ? `${action.side === "buy" ? "Bought" : "Sold"} ${action.quantity} ${action.ticker}${
          action.price ? ` @ $${action.price.toFixed(2)}` : ""
        }`
      : `${action.action === "add" ? "Added" : "Removed"} ${action.ticker} ${
          action.action === "add" ? "to" : "from"
        } watchlist`;

  return (
    <div
      data-testid="chat-action"
      className={`mt-1.5 flex items-center gap-1.5 rounded border px-2 py-1 text-[11px] font-data ${
        success
          ? "border-gain-dim bg-gain-dim/15 text-gain"
          : "border-loss-dim bg-loss-dim/15 text-loss"
      }`}
    >
      <span>{success ? "✓" : "✕"}</span>
      <span>{success ? label : action.error ?? "Action failed"}</span>
    </div>
  );
}

export function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}>
      <div
        className={`max-w-[90%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
          isUser ? "bg-blue/20 text-text" : "bg-panel-alt text-text"
        }`}
      >
        {message.content}
      </div>
      {message.actions?.map((action, i) => (
        <div key={i} className="w-full max-w-[90%]">
          <ActionPill action={action} />
        </div>
      ))}
      <span className="mt-0.5 px-1 text-[10px] text-text-faint">{formatClock(message.created_at)}</span>
    </div>
  );
}
