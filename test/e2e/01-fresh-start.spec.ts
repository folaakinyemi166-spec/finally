import { test, expect } from "@playwright/test";
import { DEFAULT_TICKERS } from "./helpers";

// PLAN.md §12: "Fresh start: default watchlist appears, $10k balance shown,
// prices are streaming." Runs first (numbered spec files, single worker) so
// it sees the app's genuinely fresh, unmodified state.

test.describe("fresh start", () => {
  test("shows the default watchlist, $10k cash, and live streaming prices", async ({ page }) => {
    await page.goto("/");

    for (const ticker of DEFAULT_TICKERS) {
      await expect(page.getByTestId(`watchlist-row-${ticker}`)).toBeVisible();
    }

    await expect(page.getByTestId("header-cash-balance")).toHaveText("$10,000.00");
    await expect(page.getByTestId("header-total-value")).toHaveText("$10,000.00");

    await expect(page.getByTestId("connection-dot")).toHaveAttribute("data-status", "connected", {
      timeout: 15_000,
    });

    // The simulator seeds the price cache synchronously at container startup
    // (app/market/simulator.py SimulatorDataSource.start()), so the first SSE
    // event should already carry real prices, not the "—" no-data placeholder.
    const firstRow = page.getByTestId(`watchlist-row-${DEFAULT_TICKERS[0]}`);
    await expect(firstRow).not.toContainText("—", { timeout: 5_000 });
  });
});
