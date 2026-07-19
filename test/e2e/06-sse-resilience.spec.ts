import { test, expect } from "@playwright/test";

// PLAN.md §12: "SSE resilience: disconnect and verify reconnection."
//
// context.setOffline() blocks *new* requests but doesn't tear down an
// already-open streaming connection, so it never actually interrupts a
// live EventSource (confirmed empirically — the connection dot stayed
// "connected" through a real setOffline(true) run). Route-aborting the
// stream endpoint and reloading forces a fresh connection attempt that
// genuinely fails, then recovers via EventSource's built-in retry once
// the route is lifted.

test.describe("SSE resilience", () => {
  test("reconnects after a network interruption", async ({ page }) => {
    await page.goto("/");

    const dot = page.getByTestId("connection-dot");
    await expect(dot).toHaveAttribute("data-status", "connected", { timeout: 15_000 });

    await page.route("**/api/stream/prices", (route) => route.abort());
    await page.reload();

    await expect(dot).toHaveAttribute("data-status", /reconnecting|disconnected|connecting/, {
      timeout: 15_000,
    });

    await page.unroute("**/api/stream/prices");
    await expect(dot).toHaveAttribute("data-status", "connected", { timeout: 20_000 });
  });
});
