import { test, expect } from "@playwright/test";

// PLAN.md §12: "Portfolio visualization: heatmap renders with correct
// colors, P&L chart has data points."
//
// By this point (spec 03 ran first), several trades have already executed,
// so portfolio_snapshots already has more than the 2 rows PnLChart needs to
// render a line instead of its "Accumulating history…" placeholder. This
// spec buys one more position so the heatmap has a cell to render.

test.describe("portfolio visualization", () => {
  test("heatmap and P&L chart render real data", async ({ page }) => {
    await page.goto("/");

    await page.getByTestId("watchlist-row-MSFT").click();
    await page.getByTestId("trade-ticker-input").fill("MSFT");
    await page.getByTestId("trade-quantity-input").fill("3");
    await page.getByRole("button", { name: "Buy" }).click();
    await expect(page.getByTestId("trade-feedback")).toContainText(/Bought 3 MSFT/, {
      timeout: 10_000,
    });

    // Heatmap: at least one colored treemap cell for the open position.
    const heatmap = page.getByTestId("portfolio-heatmap");
    await expect(heatmap.getByText("No open positions yet", { exact: false })).toHaveCount(0);
    const cells = heatmap.locator("rect");
    await expect(cells.first()).toBeVisible({ timeout: 10_000 });
    const fill = await cells.first().evaluate((el) => (el as SVGRectElement).style.fill);
    expect(fill).toBeTruthy();

    // P&L chart: enough snapshots exist that the placeholder is gone and an
    // actual line renders.
    const pnlChart = page.getByTestId("pnl-chart");
    await expect(pnlChart.getByText("Accumulating history…")).toHaveCount(0);
    await expect(pnlChart.locator("svg path").first()).toBeVisible({ timeout: 10_000 });
  });
});
