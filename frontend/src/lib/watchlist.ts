export interface WatchlistEntry {
  ticker: string;
  price: number | null;
  previous_price: number | null;
  timestamp: number | null;
  change: number | null;
  change_percent: number | null;
  direction: "up" | "down" | "flat" | null;
}

async function errorDetail(res: Response): Promise<string | null> {
  try {
    const body = await res.json();
    return typeof body?.detail === "string" ? body.detail : null;
  } catch {
    return null;
  }
}

export async function fetchWatchlist(): Promise<WatchlistEntry[]> {
  const res = await fetch("/api/watchlist");
  if (!res.ok) {
    throw new Error((await errorDetail(res)) ?? `Failed to load watchlist (${res.status})`);
  }
  return res.json();
}

export async function addWatchlistTicker(ticker: string): Promise<WatchlistEntry> {
  const res = await fetch("/api/watchlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker }),
  });
  if (!res.ok) {
    throw new Error((await errorDetail(res)) ?? `Failed to add ${ticker} (${res.status})`);
  }
  return res.json();
}

export async function removeWatchlistTicker(ticker: string): Promise<void> {
  const res = await fetch(`/api/watchlist/${encodeURIComponent(ticker)}`, {
    method: "DELETE",
  });
  if (!res.ok && res.status !== 204) {
    throw new Error((await errorDetail(res)) ?? `Failed to remove ${ticker} (${res.status})`);
  }
}
