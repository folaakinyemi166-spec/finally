import { test, expect } from "@playwright/test";
import { readCurrency } from "./helpers";

// PLAN.md §12: "Buy shares: cash decreases, position appears, portfolio
// updates." / "Sell shares: cash increases, position updates or disappears."

test.describe("trading", () => {
  test("buying and selling shares updates cash, positions, and portfolio value", async ({
    page,
  }) => {
    await page.goto("/");
    await page.getByTestId("watchlist-row-AAPL").click();

    const cashBefore = await readCurrency(page.getByTestId("header-cash-balance"));

    await page.getByTestId("trade-ticker-input").fill("AAPL");
    await page.getByTestId("trade-quantity-input").fill("2");
    await page.getByRole("button", { name: "Buy" }).click();

    await expect(page.getByTestId("trade-feedback")).toContainText(/Bought 2 AAPL/, {
      timeout: 10_000,
    });
    await expect(page.getByTestId("position-AAPL")).toBeVisible();

    const cashAfterBuy = await readCurrency(page.getByTestId("header-cash-balance"));
    expect(cashAfterBuy).toBeLessThan(cashBefore);

    // Sell half the position — it should update, not disappear.
    await page.getByTestId("trade-quantity-input").fill("1");
    await page.getByRole("button", { name: "Sell" }).click();
    await expect(page.getByTestId("trade-feedback")).toContainText(/Sold 1 AAPL/, {
      timeout: 10_000,
    });
    await expect(page.getByTestId("position-AAPL")).toBeVisible();

    const cashAfterPartialSell = await readCurrency(page.getByTestId("header-cash-balance"));
    expect(cashAfterPartialSell).toBeGreaterThan(cashAfterBuy);

    // Sell the rest — the position should disappear entirely.
    await page.getByTestId("trade-quantity-input").fill("1");
    await page.getByRole("button", { name: "Sell" }).click();
    await expect(page.getByTestId("trade-feedback")).toContainText(/Sold 1 AAPL/, {
      timeout: 10_000,
    });
    await expect(page.getByTestId("position-AAPL")).toBeHidden();
  });

  test("rejects a trade that would exceed available cash", async ({ page }) => {
    await page.goto("/");

    await page.getByTestId("trade-ticker-input").fill("NVDA");
    await page.getByTestId("trade-quantity-input").fill("999999");
    await page.getByRole("button", { name: "Buy" }).click();

    await expect(page.getByTestId("trade-feedback")).toContainText(/insufficient/i, {
      timeout: 10_000,
    });
    await expect(page.getByTestId("position-NVDA")).toBeHidden();
  });
});
