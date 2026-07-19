import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { WatchlistRow } from "./WatchlistRow";
import type { TickerMarketState } from "@/hooks/useMarketData";

function makeMarket(overrides: Partial<TickerMarketState>): TickerMarketState {
  return {
    ticker: "AAPL",
    price: 190,
    previousPrice: 189,
    change: 1,
    changePercent: 0.53,
    direction: "up",
    timestamp: new Date().toISOString(),
    history: [{ price: 189, timestamp: new Date().toISOString() }],
    flashToken: 1,
    ...overrides,
  };
}

describe("WatchlistRow", () => {
  it("renders ticker, price and change percent", () => {
    render(
      <WatchlistRow
        ticker="AAPL"
        market={makeMarket({})}
        selected={false}
        onSelect={vi.fn()}
        onRemove={vi.fn()}
      />,
    );
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("190.00")).toBeInTheDocument();
    expect(screen.getByText("+0.53%")).toBeInTheDocument();
  });

  it("applies a flash-up class when the price ticks upward", () => {
    const { rerender, getByTestId } = render(
      <WatchlistRow
        ticker="AAPL"
        market={makeMarket({ flashToken: 1 })}
        selected={false}
        onSelect={vi.fn()}
        onRemove={vi.fn()}
      />,
    );

    rerender(
      <WatchlistRow
        ticker="AAPL"
        market={makeMarket({ flashToken: 2, direction: "up", price: 191 })}
        selected={false}
        onSelect={vi.fn()}
        onRemove={vi.fn()}
      />,
    );

    expect(getByTestId("watchlist-row-AAPL").className).toContain("flash-up");
  });

  it("applies a flash-down class when the price ticks downward", () => {
    const { rerender, getByTestId } = render(
      <WatchlistRow
        ticker="AAPL"
        market={makeMarket({ flashToken: 1, direction: "down" })}
        selected={false}
        onSelect={vi.fn()}
        onRemove={vi.fn()}
      />,
    );

    rerender(
      <WatchlistRow
        ticker="AAPL"
        market={makeMarket({ flashToken: 2, direction: "down", price: 188 })}
        selected={false}
        onSelect={vi.fn()}
        onRemove={vi.fn()}
      />,
    );

    expect(getByTestId("watchlist-row-AAPL").className).toContain("flash-down");
  });

  it("calls onSelect when clicked and onRemove when the remove control is used", async () => {
    const onSelect = vi.fn();
    const onRemove = vi.fn();
    render(
      <WatchlistRow ticker="AAPL" market={makeMarket({})} selected={false} onSelect={onSelect} onRemove={onRemove} />,
    );

    screen.getByTestId("watchlist-row-AAPL").click();
    expect(onSelect).toHaveBeenCalledWith("AAPL");

    screen.getByLabelText("Remove AAPL from watchlist").click();
    expect(onRemove).toHaveBeenCalledWith("AAPL");
    // Selecting should not also fire from the nested remove control.
    expect(onSelect).toHaveBeenCalledTimes(1);
  });
});
