import React, { createContext, useContext, useMemo } from 'react';
import { AdvisoryMessage, LogEntry, Order, Position, TradeAnalysis } from '../types';
import { useBackendTrading, BackendStats, StreamingStatus } from '../hooks/useBackendTrading';
import { useConfig } from './ConfigContext';
import { OrderSide } from '../types';

export interface TradingContextValue {
  stats: BackendStats;
  performanceData: ReturnType<typeof useBackendTrading>['performanceData'];
  positions: Position[];
  orders: Order[];
  logs: LogEntry[];
  advisories: AdvisoryMessage[];
  tradeAnalyses: TradeAnalysis[];
  timeframe: string;
  setTimeframe: (timeframe: string) => void;
  closePosition: (positionId: string, reason?: string) => void;
  cancelOrder: (orderId: string) => void;
  placeOrder: (symbol: string, side: OrderSide, qty: number, reason: string) => void;
  getStateSummary: () => string;
  getStateSnapshot: () => Record<string, unknown>;
  riskSettings: {
    maxPositions: number;
    riskPerTradePct: number;
  };
  watchlist: string[];
  isConnected: boolean;
  error: string | null;
  streamingStatus: StreamingStatus;
}

const TradingContext = createContext<TradingContextValue | undefined>(undefined);

const normaliseWatchlist = (list: string): string[] =>
  list
    .split(',')
    .map((symbol) => symbol.trim().toUpperCase())
    .filter(Boolean);

export const TradingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { config } = useConfig();

  const watchlist = useMemo(() => normaliseWatchlist(config.strategy.watchlist), [config.strategy.watchlist]);
  
  // Use real backend instead of simulator
  const {
    stats,
    performanceData,
    positions,
    orders,
    logs,
    advisories,
    tradeAnalyses,
    timeframe,
    setTimeframe,
    closePosition,
    cancelOrder,
    placeOrder,
    isConnected,
    error,
    streamingStatus,
  } = useBackendTrading();

  const contextValue = useMemo<TradingContextValue>(() => {
    const getStateSummary = () => {
      const openPositionSummary =
        positions.length === 0
          ? 'No open positions.'
          : positions
              .map(
                (pos) =>
                  `${pos.symbol} ${pos.side.toUpperCase()} ${pos.qty} @ ${pos.avgEntryPrice.toFixed(2)} (P/L ${pos.unrealizedPl.toFixed(
                    2,
                  )})`,
              )
              .join('; ');
      const pendingOrders =
        orders.length === 0
          ? 'No pending orders.'
          : orders.map((order) => `${order.side.toUpperCase()} ${order.qty} ${order.symbol} (${order.status})`).join('; ');
      const latestLog = logs.at(-1)?.message ?? 'No logs yet.';
      return [
        `Equity ${stats.daily_pl >= 0 ? 'up' : 'down'} ${stats.daily_pl.toFixed(2)} (${stats.daily_pl_pct.toFixed(2)}%).`,
        `Win rate ${(stats.win_rate * 100).toFixed(1)}%, profit factor ${stats.profit_factor.toFixed(2)}.`,
        openPositionSummary,
        pendingOrders,
        `Latest log: ${latestLog}`,
      ].join(' ');
    };

    const getStateSnapshot = () => ({
      stats,
      positions,
      orders,
      advisories,
      logs,
      tradeAnalyses,
      watchlist,
    });

    return {
      stats,
      performanceData,
      positions,
      orders,
      logs,
      advisories,
      tradeAnalyses,
      timeframe,
      setTimeframe,
      closePosition,
      cancelOrder,
      placeOrder,
      getStateSummary,
      getStateSnapshot,
      riskSettings: {
        maxPositions: config.strategy.maxPositions,
        riskPerTradePct: config.strategy.riskPerTradePct,
      },
      watchlist,
      isConnected,
      error,
      streamingStatus,
    };
  }, [
    advisories,
    cancelOrder,
    closePosition,
    config.strategy.maxPositions,
    config.strategy.riskPerTradePct,
    error,
    isConnected,
    logs,
    orders,
    performanceData,
    placeOrder,
    positions,
    stats,
    timeframe,
    setTimeframe,
    tradeAnalyses,
    watchlist,
    streamingStatus,
  ]);

  return <TradingContext.Provider value={contextValue}>{children}</TradingContext.Provider>;
};

export const useTrading = (): TradingContextValue => {
  const context = useContext(TradingContext);
  if (!context) {
    throw new Error('useTrading must be used within TradingProvider');
  }
  return context;
};
