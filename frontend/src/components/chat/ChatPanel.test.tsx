import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatPanel } from "./ChatPanel";
import type { ChatMessage } from "@/lib/types";

const messages: ChatMessage[] = [
  {
    id: "1",
    role: "assistant",
    content: "Hi, I'm FinAlly.",
    actions: null,
    created_at: new Date().toISOString(),
  },
  {
    id: "2",
    role: "user",
    content: "Buy 5 AAPL",
    actions: null,
    created_at: new Date().toISOString(),
  },
  {
    id: "3",
    role: "assistant",
    content: "Done.",
    actions: [
      { type: "trade", ticker: "AAPL", side: "buy", quantity: 5, success: true, price: 190.12 },
    ],
    created_at: new Date().toISOString(),
  },
];

describe("ChatPanel", () => {
  it("renders message history and inline action confirmations", () => {
    render(
      <ChatPanel messages={messages} loading={false} onSend={vi.fn()} collapsed={false} onToggleCollapsed={vi.fn()} />,
    );
    expect(screen.getByText("Hi, I'm FinAlly.")).toBeInTheDocument();
    expect(screen.getByText("Buy 5 AAPL")).toBeInTheDocument();
    expect(screen.getByTestId("chat-action")).toHaveTextContent(/Bought 5 AAPL/);
  });

  it("shows a loading indicator while awaiting a response", () => {
    render(<ChatPanel messages={messages} loading onSend={vi.fn()} collapsed={false} onToggleCollapsed={vi.fn()} />);
    expect(screen.getByTestId("chat-loading")).toBeInTheDocument();
  });

  it("calls onSend with the input text and clears the field", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn().mockResolvedValue(undefined);
    render(
      <ChatPanel messages={messages} loading={false} onSend={onSend} collapsed={false} onToggleCollapsed={vi.fn()} />,
    );

    const input = screen.getByPlaceholderText(/ask finally anything/i);
    await user.type(input, "Analyze my portfolio");
    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(onSend).toHaveBeenCalledWith("Analyze my portfolio");
  });

  it("renders a collapsed rail instead of the full panel when collapsed", () => {
    render(<ChatPanel messages={messages} loading={false} onSend={vi.fn()} collapsed onToggleCollapsed={vi.fn()} />);
    expect(screen.queryByPlaceholderText(/ask finally anything/i)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/expand ai chat panel/i)).toBeInTheDocument();
  });
});
