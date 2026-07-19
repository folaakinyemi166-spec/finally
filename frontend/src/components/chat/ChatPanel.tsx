"use client";

import { useEffect, useRef, useState } from "react";
import { ChatMessageBubble } from "./ChatMessageBubble";
import type { ChatMessage } from "@/lib/types";

interface ChatPanelProps {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (text: string) => Promise<void>;
  collapsed: boolean;
  onToggleCollapsed: () => void;
}

export function ChatPanel({ messages, loading, onSend, collapsed, onToggleCollapsed }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    // Plain scrollTop assignment rather than scrollTo({ behavior: "smooth" })
    // — jsdom (used in tests) doesn't implement Element.scrollTo.
    el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const text = input;
    setInput("");
    await onSend(text);
  }

  if (collapsed) {
    return (
      <button
        type="button"
        onClick={onToggleCollapsed}
        aria-label="Expand AI chat panel"
        className="flex h-full w-10 flex-col items-center justify-center gap-3 border-l border-border bg-panel text-text-dim hover:text-yellow"
      >
        <span className="rotate-180 text-[10px] font-semibold uppercase tracking-widest [writing-mode:vertical-rl]">
          AI Chat
        </span>
      </button>
    );
  }

  return (
    <section className="flex h-full w-full flex-col border-l border-border bg-panel">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-text-dim">
          AI Assistant
        </h2>
        <button
          type="button"
          onClick={onToggleCollapsed}
          aria-label="Collapse AI chat panel"
          className="text-text-faint hover:text-text"
        >
          ›
        </button>
      </div>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-3 py-3">
        {messages.map((m) => (
          <ChatMessageBubble key={m.id} message={m} />
        ))}
        {loading && (
          <div className="flex items-center gap-1 rounded-lg bg-panel-alt px-3 py-2 text-text-dim" data-testid="chat-loading">
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-text-faint [animation-delay:-0.3s]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-text-faint [animation-delay:-0.15s]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-text-faint" />
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-border p-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask FinAlly anything…"
          className="min-w-0 flex-1 rounded border border-border bg-panel-alt px-2.5 py-2 text-sm text-text placeholder:text-text-faint focus:border-blue focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded bg-purple px-3.5 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </section>
  );
}
