import { useState, useEffect, useCallback } from 'react';
import {
  Position, Order, LogEntry, AdvisoryMessage, PerformanceDataPoint, TradeAnalysis,
  OrderSide, OrderStatus,
} from '../types';

type LogLevel = 'info' | 'warning' | 'error' | 'debug';

const API_BASE = 'http://localhost:8006';

export interface BackendStats {
  equity: number;
  cash: number;
  buying_power: number;
  daily_pl: number;
  daily_pl_pct: number;
  total_pl: number;
  win_rate: number;
  profit_factor: number;
  wins: number;
  losses: number;
  total_trades: number;
  open_positions: number;
  circuit_breaker_triggered: boolean;
}

export interface BackendTradingData {
  stats: BackendStats;
  positions: Position[];
  orders: Order[];
  logs: LogEntry[];
  advisories: AdvisoryMessage[];
  tradeAnalyses: TradeAnalysis[];
  performanceData: PerformanceDataPoint[];
  isConnected: boolean;
  error: string | null;
}

export const useBackendTrading = () => {
  const [data, setData] = useState<BackendTradingData>({
    stats: {
      equity: 0,
      cash: 0,
      buying_power: 0,
      daily_pl: 0,
      daily_pl_pct: 0,
      total_pl: 0,
      win_rate: 0,
      profit_factor: 0,
      wins: 0,
      losses: 0,
      total_trades: 0,
      open_positions: 0,
      circuit_breaker_triggered: false,
    },
    positions: [],
    orders: [],
    logs: [],
    advisories: [],
    tradeAnalyses: [],
    performanceData: [],
    isConnected: false,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      // Fetch all data in parallel
      const [metricsRes, positionsRes, ordersRes, logsRes, advisoriesRes, analysesRes] = await Promise.all([
        fetch(`${API_BASE}/metrics`),
        fetch(`${API_BASE}/positions`),
        fetch(`${API_BASE}/orders`),
        fetch(`${API_BASE}/logs?limit=100`),
        fetch(`${API_BASE}/advisories?limit=50`),
        fetch(`${API_BASE}/analyses?limit=50`),
      ]);

      if (!metricsRes.ok || !positionsRes.ok || !ordersRes.ok) {
        throw new Error('Failed to fetch data from backend');
      }

      const metrics = await metricsRes.json();
      const positions = await positionsRes.json();
      const orders = await ordersRes.json();
      const logs = logsRes.ok ? await logsRes.json() : [];
      const advisories = advisoriesRes.ok ? await advisoriesRes.json() : [];
      const analyses = analysesRes.ok ? await analysesRes.json() : [];

      // Transform backend data to frontend format
      const transformedPositions: Position[] = positions.map((p: any) => ({
        id: p.symbol,
        symbol: p.symbol,
        qty: p.qty,
        side: p.side as OrderSide,
        avgEntryPrice: p.avg_entry_price,
        currentPrice: p.current_price,
        unrealizedPl: p.unrealized_pl,
        unrealizedPlpc: p.unrealized_pl_pct / 100,
        marketValue: p.market_value,
        takeProfit: p.take_profit,
        stopLoss: p.stop_loss,
      }));

      const transformedOrders: Order[] = orders.map((o: any) => ({
        id: o.order_id,
        symbol: o.symbol,
        qty: o.qty,
        side: o.side as OrderSide,
        type: o.type as 'market' | 'limit' | 'stop',
        status: o.status as OrderStatus,
        filledQty: o.filled_qty,
        filledAvgPrice: o.filled_avg_price,
        submittedAt: o.submitted_at,
      }));

      // Transform logs
      const transformedLogs: LogEntry[] = logs.map((l: any) => ({
        id: l.id,
        timestamp: new Date(l.timestamp).getTime(),
        level: l.level as LogLevel,
        message: l.message,
        source: l.source || 'system'
      }));

      // Transform advisories
      const transformedAdvisories: AdvisoryMessage[] = advisories.map((a: any) => ({
        id: a.id,
        timestamp: new Date(a.timestamp).getTime(),
        type: a.type,
        symbol: a.symbol,
        content: a.content,
        model: a.model,
        confidence: a.confidence
      }));

      // Transform analyses
      const transformedAnalyses: TradeAnalysis[] = analyses.map((a: any) => ({
        id: a.id,
        timestamp: new Date(a.timestamp).getTime(),
        symbol: a.symbol,
        side: a.side as OrderSide,
        action: a.action,
        analysis: a.analysis,
        pnl: a.pnl,
        pnlPct: a.pnl_pct
      }));

      // Create performance data point from current metrics
      const perfPoint: PerformanceDataPoint = {
        timestamp: Date.now(),
        open: metrics.equity,
        high: metrics.equity,
        low: metrics.equity,
        close: metrics.equity,
        pnl: metrics.daily_pl,
        winRate: metrics.win_rate,
        profitFactor: metrics.profit_factor,
        wins: metrics.wins,
        losses: metrics.losses,
      };

      setData((prev) => ({
        stats: {
          equity: metrics.equity,
          cash: metrics.cash,
          buying_power: metrics.buying_power,
          daily_pl: metrics.daily_pl,
          daily_pl_pct: metrics.daily_pl_pct,
          total_pl: metrics.total_pl,
          win_rate: metrics.win_rate,
          profit_factor: metrics.profit_factor,
          wins: metrics.wins,
          losses: metrics.losses,
          total_trades: metrics.total_trades,
          open_positions: metrics.open_positions,
          circuit_breaker_triggered: metrics.circuit_breaker_triggered,
        },
        positions: transformedPositions,
        orders: transformedOrders,
        logs: transformedLogs,
        advisories: transformedAdvisories,
        tradeAnalyses: transformedAnalyses,
        performanceData: [...prev.performanceData.slice(-99), perfPoint],
        isConnected: true,
        error: null,
      }));
    } catch (error) {
      console.error('Backend connection error:', error);
      setData((prev) => ({
        ...prev,
        isConnected: false,
        error: error instanceof Error ? error.message : 'Connection failed',
      }));
    }
  }, []);

  // Poll backend every 5 seconds
  useEffect(() => {
    fetchData(); // Initial fetch
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const closePosition = useCallback(async (positionId: string, reason = 'Manual Close') => {
    try {
      const response = await fetch(`${API_BASE}/positions/${positionId}/close`, {
        method: 'POST',
      });
      
      if (response.ok) {
        console.log(`Position closed: ${positionId}`);
        fetchData(); // Refresh data
      }
    } catch (error) {
      console.error('Failed to close position:', error);
    }
  }, [fetchData]);

  const cancelOrder = useCallback(async (orderId: string) => {
    try {
      const response = await fetch(`${API_BASE}/orders/${orderId}/cancel`, {
        method: 'POST',
      });
      
      if (response.ok) {
        console.log(`Order canceled: ${orderId}`);
        fetchData(); // Refresh data
      }
    } catch (error) {
      console.error('Failed to cancel order:', error);
    }
  }, [fetchData]);

  const placeOrder = useCallback(async (symbol: string, side: OrderSide, qty: number, reason: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/orders/submit?symbol=${symbol}&side=${side}&qty=${qty}&reason=${encodeURIComponent(reason)}`,
        { method: 'POST' }
      );
      
      if (response.ok) {
        const result = await response.json();
        console.log('Order submitted:', result);
        fetchData(); // Refresh data
      }
    } catch (error) {
      console.error('Failed to place order:', error);
    }
  }, [fetchData]);

  return {
    ...data,
    closePosition,
    cancelOrder,
    placeOrder,
    refresh: fetchData,
  };
};
