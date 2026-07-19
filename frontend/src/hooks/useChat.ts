"use client";

import { useCallback, useState } from "react";
import { sendChatMessage } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

function uid(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return `id-${Math.random().toString(36).slice(2)}-${Date.now()}`;
}

export interface UseChatResult {
  messages: ChatMessage[];
  loading: boolean;
  send: (text: string) => Promise<void>;
}

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "I'm FinAlly, your AI trading assistant. Ask me to analyze your portfolio, or tell me to buy, sell, or manage your watchlist.",
  actions: null,
  created_at: new Date().toISOString(),
};

/** Owns chat history and the request/response cycle for POST /api/chat. */
export function useChat(onPortfolioChange?: () => void): UseChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [loading, setLoading] = useState(false);

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;

      const userMessage: ChatMessage = {
        id: uid(),
        role: "user",
        content: trimmed,
        actions: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);

      try {
        const response = await sendChatMessage(trimmed);
        const assistantMessage: ChatMessage = {
          id: uid(),
          role: "assistant",
          content: response.message,
          actions: response.actions.length ? response.actions : null,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
        if (response.actions.some((a) => a.type === "trade" || a.type === "watchlist")) {
          onPortfolioChange?.();
        }
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          {
            id: uid(),
            role: "assistant",
            content: `Something went wrong reaching the assistant: ${(err as Error).message}`,
            actions: null,
            created_at: new Date().toISOString(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [onPortfolioChange],
  );

  return { messages, loading, send };
}
