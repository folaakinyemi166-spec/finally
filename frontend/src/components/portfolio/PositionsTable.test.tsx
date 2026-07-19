import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { PositionsTable } from "./PositionsTable";
import type { Position } from "@/lib/types";

const winningPosition: Position = {
  ticker: "AAPL",
  quantity: 10,
  avg_cost: 100,
  current_price: 120,
  market_value: 1200,
  unrealized_pnl: 200,
  unrealized_pnl_percent: 20,
};

const losingPosition: Position = {
  ticker: "TSLA",
  quantity: 5,
  avg_cost: 300,
  current_price: 250,
  market_value: 1250,
  unrealized_pnl: -250,
  unrealized_pnl_percent: -16.67,
};

describe("PositionsTable", () => {
  it("shows an empty state when there are no positions", () => {
    render(<PositionsTable positions={[]} />);
    expect(screen.getByText(/no open positions/i)).toBeInTheDocument();
  });

  it("renders each position's ticker, quantity, and P&L", () => {
    render(<PositionsTable positions={[winningPosition, losingPosition]} />);

    expect(screen.getByTestId("position-AAPL")).toBeInTheDocument();
    expect(screen.getByTestId("position-TSLA")).toBeInTheDocument();
    expect(screen.getByText("+20.00%")).toBeInTheDocument();
    expect(screen.getByText("-16.67%")).toBeInTheDocument();
    expect(screen.getByText("$200.00")).toBeInTheDocument();
    expect(screen.getByText("-$250.00")).toBeInTheDocument();
  });

  it("colors gains green and losses red", () => {
    render(<PositionsTable positions={[winningPosition, losingPosition]} />);
    const gainCell = screen.getByText("$200.00");
    const lossCell = screen.getByText("-$250.00");
    expect(gainCell.className).toContain("text-gain");
    expect(lossCell.className).toContain("text-loss");
  });
});
