"use client";

import { useCallback, useState } from "react";
import { Header } from "@/components/layout/Header";
import { TickerTape } from "@/components/layout/TickerTape";
import { WatchlistPanel } from "@/components/watchlist/WatchlistPanel";
import { MainChart } from "@/components/chart/MainChart";
import { PortfolioHeatmap } from "@/components/portfolio/PortfolioHeatmap";
import { PnLChart } from "@/components/portfolio/PnLChart";
import { PositionsTable } from "@/components/portfolio/PositionsTable";
import { TradeBar } from "@/components/trade/TradeBar";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { useMarketData } from "@/hooks/useMarketData";
import { useWatchlist } from "@/hooks/useWatchlist";
import { usePortfolio } from "@/hooks/usePortfolio";
import { useChat } from "@/hooks/useChat";

export default function Home() {
  const { status, tickers: marketByTicker } = useMarketData();
  const watchlist = useWatchlist();
  const portfolio = usePortfolio();
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [chatCollapsed, setChatCollapsed] = useState(false);

  const refreshPortfolio = useCallback(() => {
    // usePortfolio polls on its own interval; chat-triggered actions get
    // picked up on the next tick, so this is just a light nudge point for
    // future non-polling implementations.
  }, []);
  const chat = useChat(refreshPortfolio);

  const activeTicker = selectedTicker ?? watchlist.tickers[0] ?? null;
  const activeMarket = activeTicker ? marketByTicker[activeTicker] : undefined;
  const tapeTickers = watchlist.tickers.map((t) => marketByTicker[t]).filter(Boolean);

  return (
    <div className="flex h-full flex-col">
      <Header
        totalValue={portfolio.portfolio?.total_value ?? null}
        cashBalance={portfolio.portfolio?.cash_balance ?? null}
        dayPnl={portfolio.portfolio?.total_unrealized_pnl ?? null}
        connectionStatus={status}
      />
      <TickerTape tickers={tapeTickers} />

      <main className="grid min-h-0 flex-1 grid-cols-[300px_1fr_auto]">
        <WatchlistPanel
          tickers={watchlist.tickers}
          marketByTicker={marketByTicker}
          selectedTicker={activeTicker}
          onSelect={setSelectedTicker}
          onAdd={watchlist.add}
          onRemove={(t) => void watchlist.remove(t)}
          error={watchlist.error}
        />

        <div className="flex min-h-0 min-w-0 flex-col">
          <div className="h-[42%] min-h-[260px] border-b border-border">
            <MainChart
              ticker={activeTicker}
              price={activeMarket?.price ?? null}
              changePercent={activeMarket?.changePercent ?? null}
              history={activeMarket?.history ?? []}
            />
          </div>

          <div className="grid min-h-0 flex-1 grid-cols-2 border-b border-border">
            <div className="border-r border-border">
              <PortfolioHeatmap positions={portfolio.portfolio?.positions ?? []} />
            </div>
            <PnLChart history={portfolio.history} />
          </div>

          <div className="h-40 border-b border-border">
            <PositionsTable positions={portfolio.portfolio?.positions ?? []} />
          </div>

          <TradeBar defaultTicker={activeTicker} onTrade={portfolio.trade} />
        </div>

        <div className={chatCollapsed ? "w-10" : "w-[360px]"}>
          <ChatPanel
            messages={chat.messages}
            loading={chat.loading}
            onSend={chat.send}
            collapsed={chatCollapsed}
            onToggleCollapsed={() => setChatCollapsed((c) => !c)}
          />
        </div>
      </main>
    </div>
  );
}
