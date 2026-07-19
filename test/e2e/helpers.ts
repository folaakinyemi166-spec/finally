import type { Locator } from "@playwright/test";

/** Parses a formatCurrency()-rendered string ("$10,000.00") back to a number. */
export async function readCurrency(locator: Locator): Promise<number> {
  const text = await locator.textContent();
  return Number(text?.replace(/[^0-9.-]/g, "") ?? NaN);
}

export const DEFAULT_TICKERS = [
  "AAPL",
  "GOOGL",
  "MSFT",
  "AMZN",
  "TSLA",
  "NVDA",
  "META",
  "JPM",
  "V",
  "NFLX",
];
