import { useState, useEffect, useCallback, useRef } from "react";
import {
  Position,
  Order,
  LogEntry,
  AdvisoryMessage,
  PerformanceDataPoint,
  TradeAnalysis,
  OrderSide,
  OrderStatus,
  LogLevel,
} from "../types";
import { apiClient } from "../lib/apiClient";
import { PerformanceResponse } from "../types/api";

export type StreamingStatus = "disabled" | "connecting" | "connected" | "error";

const API_BASE = apiClient.getBaseUrl();

const toNumber = (value: unknown): number | undefined => {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : undefined;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  return undefined;
};

const numberOrZero = (value: unknown): number => toNumber(value) ?? 0;

const normaliseSide = (value: unknown): OrderSide => {
  if (typeof value === "string") {
    return value.toLowerCase() === OrderSide.SELL
      ? OrderSide.SELL
      : OrderSide.BUY;
  }
  return OrderSide.BUY;
};

const normaliseStatus = (value: unknown): OrderStatus => {
  if (typeof value === "string") {
    const lowered = value.toLowerCase();
    if (lowered === OrderStatus.FILLED) return OrderStatus.FILLED;
    if (lowered === OrderStatus.CANCELED) return OrderStatus.CANCELED;
  }
  return OrderStatus.OPEN;
};

const transformMetrics = (metrics: any) => ({
  equity: numberOrZero(metrics?.equity),
  cash: numberOrZero(metrics?.cash),
  buying_power: numberOrZero(metrics?.buying_power),
  daily_pl: numberOrZero(metrics?.daily_pl),
  daily_pl_pct: numberOrZero(metrics?.daily_pl_pct),
  total_pl: numberOrZero(metrics?.total_pl),
  win_rate: numberOrZero(metrics?.win_rate),
  profit_factor: numberOrZero(metrics?.profit_factor),
  wins: numberOrZero(metrics?.wins),
  losses: numberOrZero(metrics?.losses),
  total_trades: numberOrZero(metrics?.total_trades),
  open_positions: numberOrZero(metrics?.open_positions),
  circuit_breaker_triggered: Boolean(metrics?.circuit_breaker_triggered),
});

const transformPositions = (positions: any[]): Position[] =>
  positions.map((p) => ({
    id: p.symbol,
    symbol: p.symbol,
    qty: numberOrZero(p.qty),
    side: normaliseSide(p.side),
    avgEntryPrice: numberOrZero(p.avg_entry_price),
    currentPrice: numberOrZero(p.current_price),
    unrealizedPl: numberOrZero(p.unrealized_pl),
    unrealizedPlpc: numberOrZero(p.unrealized_pl_pct) / 100,
    marketValue: numberOrZero(p.market_value),
    takeProfit: toNumber(p.take_profit) ?? undefined,
    stopLoss: toNumber(p.stop_loss) ?? undefined,
  }));

const transformOrders = (orders: any[]): Order[] =>
  orders.map((o) => ({
    id: o.order_id,
    symbol: o.symbol,
    qty: numberOrZero(o.qty),
    side: normaliseSide(o.side),
    type: (typeof o.type === "string" ? o.type.toLowerCase() : "market") as
      | "market"
      | "limit"
      | "stop",
    status: normaliseStatus(o.status),
    filledQty: numberOrZero(o.filled_qty),
    filledAvgPrice: toNumber(o.filled_avg_price),
    submittedAt: o.submitted_at,
  }));

const transformLogs = (logs: any[]): LogEntry[] =>
  logs.map((l) => ({
    id: l.id,
    timestamp: l.timestamp,
    level: (l.level as LogLevel) ?? LogLevel.INFO,
    message: l.message,
    source: l.source || "system",
  }));

const transformAdvisories = (advisories: any[]): AdvisoryMessage[] =>
  advisories.map((a) => {
    const model = a.model as string | undefined;
    let source: string | undefined;
    if (typeof a.source === "string" && a.source.trim() !== "") {
      source = a.source;
    } else if (model) {
      source = model.toLowerCase().includes("perplexity")
        ? "Perplexity"
        : "OpenRouter";
    } else if (typeof a.type === "string") {
      source = a.type;
    }

    return {
      id: a.id,
      timestamp: a.timestamp,
      type: a.type,
      symbol: a.symbol,
      content: a.content,
      model,
      source,
      confidence: toNumber(a.confidence) ?? undefined,
    };
  });

const transformTradeAnalyses = (analyses: any[]): TradeAnalysis[] =>
  analyses.map((a) => ({
    id: a.id,
    timestamp: a.timestamp,
    symbol: a.symbol,
    side: normaliseSide(a.side),
    action: a.action,
    analysis: a.analysis,
    pnl: toNumber(a.pnl),
    pnlPct: toNumber(a.pnl_pct),
    source: a.source ?? a.model,
    entryPrice: toNumber(a.entry_price),
    takeProfit: toNumber(a.take_profit),
    stopLoss: toNumber(a.stop_loss),
  }));

const buildPerformanceData = (
  history: PerformanceResponse[],
  stats: ReturnType<typeof transformMetrics>
): PerformanceDataPoint[] => {
  if (history.length > 0) {
    return history.map((p) => ({
      timestamp: new Date(p.timestamp).getTime(),
      open: numberOrZero(p.equity),
      high: numberOrZero(p.equity) * 1.001,
      low: numberOrZero(p.equity) * 0.999,
      close: numberOrZero(p.equity),
      pnl: numberOrZero(p.daily_pl),
      winRate: numberOrZero(p.win_rate),
      profitFactor: numberOrZero(p.profit_factor),
      wins: numberOrZero(p.wins),
      losses: numberOrZero(p.losses),
    }));
  }

  return [
    {
      timestamp: Date.now(),
      open: stats.equity,
      high: stats.equity,
      low: stats.equity,
      close: stats.equity,
      pnl: stats.daily_pl,
      winRate: stats.win_rate,
      profitFactor: stats.profit_factor,
      wins: stats.wins,
      losses: stats.losses,
    },
  ];
};

const buildWebSocketUrl = (baseUrl: string): string => {
  const url = new URL(baseUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = url.pathname.replace(/\/$/, "") + "/ws/stream";
  return url.toString();
};

const computeMidpoint = (bid?: number, ask?: number): number | undefined => {
  if (bid && ask) {
    return (bid + ask) / 2;
  }
  return bid ?? ask;
};

const updatePositionWithPrice = (
  position: Position,
  price: number
): Position => {
  if (!price || position.qty <= 0) {
    return position;
  }

  const isLong = position.side === OrderSide.BUY;
  const unrealizedPl = isLong
    ? (price - position.avgEntryPrice) * position.qty
    : (position.avgEntryPrice - price) * position.qty;
  const marketValue = isLong ? price * position.qty : -price * position.qty;
  const costBasis = position.avgEntryPrice * position.qty || 1;

  return {
    ...position,
    currentPrice: price,
    marketValue,
    unrealizedPl,
    unrealizedPlpc: unrealizedPl / costBasis,
  };
};

export type BackendStats = ReturnType<typeof transformMetrics>;

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
  const [timeframe, setTimeframe] = useState<string>("1W");
  const [streamingStatusState, setStreamingStatusState] =
    useState<StreamingStatus>("connecting");
  const streamingStatusRef = useRef<StreamingStatus>("connecting");
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number>();

  const setStreamingStatus = useCallback((status: StreamingStatus) => {
    streamingStatusRef.current = status;
    setStreamingStatusState(status);
  }, []);

  const [data, setData] = useState<BackendTradingData>({
    stats: transformMetrics({}),
    positions: [],
    orders: [],
    logs: [],
    advisories: [],
    tradeAnalyses: [],
    performanceData: [],
    isConnected: false,
    error: null,
  });

  const applySnapshot = useCallback(
    (snapshot: any) => {
      const metrics = transformMetrics(snapshot?.metrics ?? {});
      const positions = transformPositions(snapshot?.positions ?? []);
      const orders = transformOrders(snapshot?.orders ?? []);
      const logs = transformLogs(snapshot?.logs ?? []);
      const advisories = transformAdvisories(snapshot?.advisories ?? []);
      const flags = snapshot?.feature_flags ?? {};

      if (flags.streaming === false) {
        setStreamingStatus("disabled");
      }

      setData((prev) => ({
        ...prev,
        stats: metrics,
        positions,
        orders,
        logs,
        advisories,
        isConnected: true,
        error: null,
      }));
    },
    [setStreamingStatus]
  );

  const updatePositionFromStream = useCallback(
    (symbol: string, price?: number) => {
      if (!price) {
        return;
      }
      setData((prev) => {
        const positions = prev.positions.map((pos) =>
          pos.symbol === symbol ? updatePositionWithPrice(pos, price) : pos
        );
        return { ...prev, positions };
      });
    },
    []
  );

  const handleStreamMessage = useCallback(
    (event: MessageEvent<string>) => {
      try {
        const message = JSON.parse(event.data);
        switch (message.type) {
          case "snapshot":
            applySnapshot(message.payload ?? {});
            break;
          case "metrics":
            setData((prev) => ({
              ...prev,
              stats: transformMetrics(message.payload ?? {}),
              isConnected: true,
              error: null,
            }));
            break;
          case "quote": {
            const price = computeMidpoint(
              toNumber(message.bid),
              toNumber(message.ask)
            );
            updatePositionFromStream(message.symbol, price);
            break;
          }
          case "trade":
            updatePositionFromStream(message.symbol, toNumber(message.price));
            break;
          case "bar":
            updatePositionFromStream(message.symbol, toNumber(message.close));
            break;
          case "error":
            if (message.message === "Streaming disabled") {
              setStreamingStatus("disabled");
            }
            break;
          default:
            break;
        }
      } catch (error) {
        console.error("Streaming message parse error", error);
      }
    },
    [applySnapshot, updatePositionFromStream, setStreamingStatus]
  );

  const fetchData = useCallback(async () => {
    try {
      const [
        metricsRes,
        positionsRes,
        ordersRes,
        logsRes,
        advisoriesRes,
        analysesRes,
        performanceRes,
      ] = await Promise.all([
        fetch(`${API_BASE}/metrics`),
        fetch(`${API_BASE}/positions`),
        fetch(`${API_BASE}/orders`),
        fetch(`${API_BASE}/logs?limit=100`),
        fetch(`${API_BASE}/advisories?limit=50`),
        fetch(`${API_BASE}/analyses?limit=50`),
        fetch(`${API_BASE}/performance?timeframe=${timeframe}&limit=100`),
      ]);

      if (!metricsRes.ok || !positionsRes.ok || !ordersRes.ok) {
        throw new Error("Failed to fetch data from backend");
      }

      const metricsJson = await metricsRes.json();
      const positionsJson = await positionsRes.json();
      const ordersJson = await ordersRes.json();
      const logsJson = logsRes.ok ? await logsRes.json() : [];
      const advisoriesJson = advisoriesRes.ok ? await advisoriesRes.json() : [];
      const analysesJson = analysesRes.ok ? await analysesRes.json() : [];
      const performanceHistory: PerformanceResponse[] = performanceRes.ok
        ? await performanceRes.json()
        : [];

      const metrics = transformMetrics(metricsJson);
      const transformedLogs = transformLogs(logsJson);
      const transformedAnalyses = transformTradeAnalyses(analysesJson);
      const performanceData = buildPerformanceData(
        performanceHistory,
        metrics
      ).slice(-100);

      setData({
        stats: metrics,
        positions: transformPositions(positionsJson),
        orders: transformOrders(ordersJson),
        logs: transformedLogs,
        advisories: transformAdvisories(advisoriesJson),
        tradeAnalyses: transformedAnalyses,
        performanceData,
        isConnected: true,
        error: null,
      });
    } catch (error) {
      console.error("Backend connection error:", error);
      setData((prev) => ({
        ...prev,
        isConnected: false,
        error: error instanceof Error ? error.message : "Connection failed",
      }));
    }
  }, [timeframe]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (streamingStatusRef.current === "connected") {
      return () => undefined;
    }

    const interval = window.setInterval(fetchData, 10000);
    return () => window.clearInterval(interval);
  }, [fetchData, streamingStatusState]);

  useEffect(() => {
    const url = buildWebSocketUrl(API_BASE);
    let cancelled = false;

    const cleanup = () => {
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      if (websocketRef.current) {
        websocketRef.current.close();
        websocketRef.current = null;
      }
    };

    const connect = () => {
      if (cancelled || streamingStatusRef.current === "disabled") {
        return;
      }

      setStreamingStatus("connecting");

      const ws = new WebSocket(url);
      websocketRef.current = ws;

      ws.onopen = () => {
        if (cancelled) {
          return;
        }
        setStreamingStatus("connected");
        setData((prev) => ({ ...prev, isConnected: true, error: null }));
      };

      ws.onmessage = handleStreamMessage;

      ws.onclose = () => {
        if (cancelled || streamingStatusRef.current === "disabled") {
          return;
        }
        setStreamingStatus("error");
        reconnectTimerRef.current = window.setTimeout(connect, 5000);
      };

      ws.onerror = () => {
        if (cancelled) {
          return;
        }
        setStreamingStatus("error");
        ws.close();
      };
    };

    connect();

    return () => {
      cancelled = true;
      cleanup();
    };
  }, [handleStreamMessage, setStreamingStatus]);

  const closePosition = useCallback(
    async (positionId: string, reason = "Manual Close") => {
      try {
        const response = await fetch(
          `${API_BASE}/positions/${positionId}/close`,
          {
            method: "POST",
          }
        );

        if (response.ok) {
          console.log(`Position closed: ${positionId}`);
          fetchData();
        }
      } catch (error) {
        console.error("Failed to close position:", error);
      }
    },
    [fetchData]
  );

  const cancelOrder = useCallback(
    async (orderId: string) => {
      try {
        const response = await fetch(`${API_BASE}/orders/${orderId}/cancel`, {
          method: "POST",
        });

        if (response.ok) {
          console.log(`Order canceled: ${orderId}`);
          fetchData();
        }
      } catch (error) {
        console.error("Failed to cancel order:", error);
      }
    },
    [fetchData]
  );

  const placeOrder = useCallback(
    async (symbol: string, side: OrderSide, qty: number, reason: string) => {
      try {
        const response = await fetch(
          `${API_BASE}/orders/submit?symbol=${symbol}&side=${side}&qty=${qty}&reason=${encodeURIComponent(
            reason
          )}`,
          { method: "POST" }
        );

        if (response.ok) {
          const result = await response.json();
          console.log("Order submitted:", result);
          fetchData();
        }
      } catch (error) {
        console.error("Failed to place order:", error);
      }
    },
    [fetchData]
  );

  const sendMessage = useCallback(async (message: string): Promise<string> => {
    try {
      const response = await fetch(
        `${API_BASE}/chat?message=${encodeURIComponent(message)}`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error(`Chat failed: ${response.status}`);
      }

      const data = await response.json();
      return data.response || "No response from AI";
    } catch (error) {
      console.error("Chat error:", error);
      return "Sorry, I encountered an error. Please try again.";
    }
  }, []);

  return {
    ...data,
    timeframe,
    setTimeframe,
    streamingStatus: streamingStatusState,
    closePosition,
    cancelOrder,
    placeOrder,
    sendMessage,
    refresh: fetchData,
  };
};
