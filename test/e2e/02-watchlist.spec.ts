import { test, expect } from "@playwright/test";

// PLAN.md §12: "Add and remove a ticker from the watchlist."

test.describe("watchlist management", () => {
  test("adds and removes a ticker", async ({ page }) => {
    await page.goto("/");

    await page.getByTestId("watchlist-add-input").fill("pypl");
    await page.getByTestId("watchlist-add-button").click();

    const row = page.getByTestId("watchlist-row-PYPL");
    await expect(row).toBeVisible();
    // Simulator.add_ticker() seeds the price synchronously, so no placeholder
    // dash is expected once the row appears.
    await expect(row).not.toContainText("—", { timeout: 5_000 });

    // Scoped to `row`: an unscoped page-level lookup is ambiguous, because
    // the row's own accessible name (ticker + price + sparkline text)
    // happens to contain this string too, once concatenated with the
    // nested remove button's aria-label.
    await row.getByRole("button", { name: "Remove PYPL from watchlist" }).click();
    await expect(row).toBeHidden();
  });

  test("rejects adding a ticker already on the watchlist", async ({ page }) => {
    await page.goto("/");

    await page.getByTestId("watchlist-add-input").fill("AAPL");
    await page.getByTestId("watchlist-add-button").click();

    await expect(page.locator("text=/already|duplicate/i")).toBeVisible({ timeout: 5_000 });
  });
});
