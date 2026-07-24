export interface Position {
  ticker: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
}

export interface Portfolio {
  cash_balance: number;
  positions: Position[];
  total_value: number;
  total_unrealized_pnl: number;
}

export interface HistoryPoint {
  total_value: number;
  recorded_at: string;
}

export interface History {
  history: HistoryPoint[];
}

async function errorDetail(res: Response): Promise<string | null> {
  try {
    const body = await res.json();
    return typeof body?.detail === "string" ? body.detail : null;
  } catch {
    return null;
  }
}

export async function fetchPortfolio(): Promise<Portfolio> {
  const res = await fetch("/api/portfolio");
  if (!res.ok) {
    throw new Error((await errorDetail(res)) ?? `Failed to load portfolio (${res.status})`);
  }
  return res.json();
}

export async function fetchPortfolioHistory(): Promise<History> {
  const res = await fetch("/api/portfolio/history");
  if (!res.ok) {
    throw new Error((await errorDetail(res)) ?? `Failed to load portfolio history (${res.status})`);
  }
  return res.json();
}
