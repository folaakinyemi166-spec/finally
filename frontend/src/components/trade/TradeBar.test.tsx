import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TradeBar } from "./TradeBar";
import type { TradeResult } from "@/lib/types";

const successResult: TradeResult = {
  success: true,
  trade: { ticker: "AAPL", side: "buy", quantity: 2, price: 190, executed_at: new Date().toISOString() },
  portfolio: {
    cash_balance: 9620,
    positions: [],
    total_value: 10000,
    total_unrealized_pnl: 0,
    total_unrealized_pnl_percent: 0,
  },
};

describe("TradeBar", () => {
  it("submits a buy order with the entered ticker and quantity", async () => {
    const user = userEvent.setup();
    const onTrade = vi.fn().mockResolvedValue(successResult);
    render(<TradeBar defaultTicker="AAPL" onTrade={onTrade} />);

    await user.clear(screen.getByPlaceholderText("Qty"));
    await user.type(screen.getByPlaceholderText("Qty"), "2");
    await user.click(screen.getByRole("button", { name: /buy/i }));

    expect(onTrade).toHaveBeenCalledWith({ ticker: "AAPL", quantity: 2, side: "buy" });
    expect(await screen.findByTestId("trade-feedback")).toHaveTextContent(/Bought 2 AAPL/);
  });

  it("shows the error message when a trade fails validation", async () => {
    const user = userEvent.setup();
    const onTrade = vi.fn().mockResolvedValue({
      success: false,
      error: "Insufficient cash",
      portfolio: successResult.portfolio,
    });
    render(<TradeBar defaultTicker="AAPL" onTrade={onTrade} />);

    await user.click(screen.getByRole("button", { name: /sell/i }));

    expect(await screen.findByTestId("trade-feedback")).toHaveTextContent("Insufficient cash");
  });

  it("blocks submission locally when no ticker is available", async () => {
    const user = userEvent.setup();
    const onTrade = vi.fn();
    render(<TradeBar defaultTicker={null} onTrade={onTrade} />);

    await user.click(screen.getByRole("button", { name: /buy/i }));

    expect(onTrade).not.toHaveBeenCalled();
    expect(await screen.findByTestId("trade-feedback")).toHaveTextContent(/enter a ticker/i);
  });
});
