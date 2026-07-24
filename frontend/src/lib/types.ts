export interface PositionOut {
  ticker: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
}

export interface PortfolioOut {
  cash_balance: number;
  positions: PositionOut[];
  total_value: number;
  total_unrealized_pnl: number;
}

export interface TradeOut {
  ticker: string;
  side: "buy" | "sell";
  quantity: number;
  price: number;
  executed_at: string;
  portfolio: PortfolioOut;
}
