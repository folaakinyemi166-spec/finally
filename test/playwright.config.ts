import { defineConfig } from "@playwright/test";

/**
 * E2E tests run against the app container from docker-compose.test.yml
 * (PLAN.md §12) — a single shared backend/SQLite instance per test run, not
 * a fresh one per test. Specs are numbered (01-, 02-, ...) and run with a
 * single worker, serially, so each test can build on the state the
 * previous one left behind instead of racing against it.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:8000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
