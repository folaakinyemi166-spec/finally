import { test, expect } from "@playwright/test";

// PLAN.md §12: "AI chat (mocked): send a message, receive a response, trade
// execution appears inline."
//
// The app runs with LLM_MOCK=true (docker-compose.test.yml), which
// deterministically parses "buy/sell <qty> <ticker>" phrases without calling
// the real LLM (app/ai.py) — this exercises the full stack (frontend ->
// POST /api/chat -> app.chat orchestration -> app.trading -> db) with no
// network dependency.

test.describe("AI chat", () => {
  test("a mocked chat response executes a trade and shows it inline", async ({ page }) => {
    await page.goto("/");

    // Submitted via Enter rather than clicking "Send": under continuous
    // live-price re-renders the button's bounding box never satisfies
    // Playwright's click-stability check within the test timeout, even
    // though it's perfectly clickable by a real user.
    await page.getByPlaceholder("Ask FinAlly anything…").fill("buy 1 NFLX");
    await page.getByPlaceholder("Ask FinAlly anything…").press("Enter");

    await expect(page.getByTestId("chat-loading")).toBeVisible();
    await expect(page.getByTestId("chat-loading")).toBeHidden({ timeout: 10_000 });

    const actionPill = page.getByTestId("chat-action").last();
    await expect(actionPill).toBeVisible();
    await expect(actionPill).toContainText(/Bought 1 NFLX/);

    // The chat-driven trade actually executed against the real backend.
    await expect(page.getByTestId("position-NFLX")).toBeVisible({ timeout: 10_000 });
  });

  test("a plain question gets a conversational reply with no actions", async ({ page }) => {
    await page.goto("/");

    await page.getByPlaceholder("Ask FinAlly anything…").fill("how is my portfolio doing?");
    await page.getByPlaceholder("Ask FinAlly anything…").press("Enter");
    await expect(page.getByTestId("chat-loading")).toBeHidden({ timeout: 10_000 });

    await expect(page.getByTestId("chat-action")).toHaveCount(0);
  });
});
