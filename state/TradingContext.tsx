import React, { createContext, useContext, useMemo } from 'react';
import { AdvisoryMessage, LogEntry, Order, Position, TradeAnalysis } from '../types';
import { SimulatorStats, useTradingSimulator } from '../simulation/useTradingSimulator';
import { useConfig } from './ConfigContext';
import { OrderSide } from '../types';

export interface TradingContextValue {
  stats: SimulatorStats;
  performanceData: ReturnType<typeof useTradingSimulator>['performanceData'];
  positions: Position[];
  orders: Order[];
  logs: LogEntry[];
  advisories: AdvisoryMessage[];
  tradeAnalyses: TradeAnalysis[];
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
  const {
    stats,
    performanceData,
    positions,
    orders,
    logs,
    advisories,
    tradeAnalyses,
    closePosition,
    cancelOrder,
    placeOrder,
    config: simConfig,
  } = useTradingSimulator({
    universe: watchlist,
    maxPositions: config.strategy.maxPositions,
    riskPerTradePct: config.strategy.riskPerTradePct,
  });

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
        `Equity ${stats.dailyPl >= 0 ? 'up' : 'down'} ${stats.dailyPl.toFixed(2)} (${stats.dailyPlPc.toFixed(2)}%).`,
        `Win rate ${(stats.winRate * 100).toFixed(1)}%, profit factor ${stats.profitFactor.toFixed(2)}.`,
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
      closePosition,
      cancelOrder,
      placeOrder,
      getStateSummary,
      getStateSnapshot,
      riskSettings: {
        maxPositions: simConfig.maxPositions,
        riskPerTradePct: simConfig.riskPerTradePct,
      },
        watchlist,
    };
  }, [
    advisories,
    cancelOrder,
    closePosition,
    logs,
    orders,
    performanceData,
    placeOrder,
    positions,
    simConfig.maxPositions,
    simConfig.riskPerTradePct,
    stats,
    tradeAnalyses,
    watchlist,
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
