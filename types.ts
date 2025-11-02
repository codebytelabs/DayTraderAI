export enum OrderSide {
  BUY = 'buy',
  SELL = 'sell',
}

export enum OrderStatus {
  OPEN = 'open',
  FILLED = 'filled',
  CANCELED = 'canceled',
}

export interface Position {
  id: string;
  symbol: string;
  qty: number;
  side: OrderSide;
  avgEntryPrice: number;
  currentPrice: number;
  unrealizedPl: number;
  unrealizedPlpc: number;
  marketValue: number;
  takeProfit?: number;
  stopLoss?: number;
}

export interface Order {
  id: string;
  symbol: string;
  qty: number;
  side: OrderSide;
  type: 'market' | 'limit' | 'stop';
  status: OrderStatus;
  filledQty: number;
  filledAvgPrice?: number;
  submittedAt: string;
}

export interface PerformanceDataPoint {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  pnl: number;
  winRate: number;
  profitFactor: number;
  wins: number;
  losses: number;
}

export enum ChecklistStatus {
  PASS = 'pass',
  FAIL = 'fail',
  PENDING = 'pending',
}

export interface ChecklistItem {
  category: string;
  items: {
    name: string;
    status: ChecklistStatus;
    details: string;
  }[];
}

export enum LogLevel {
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
}

export interface LogEntry {
  id: number;
  timestamp: string;
  level: LogLevel;
  message: string;
  source?: string;
}

export enum ServiceStatus {
  CONNECTED = 'connected',
  DEGRADED = 'degraded',
  DISCONNECTED = 'disconnected',
}

export interface ConnectionStatuses {
  alpaca: ServiceStatus;
  supabase: ServiceStatus;
  perplexity: ServiceStatus;
  openRouter: ServiceStatus;
}

export interface AdvisoryMessage {
  id: number;
  timestamp: string;
  content: string;
  symbol?: string;
  source?: string;
  type?: string;
  model?: string;
  confidence?: number;
}

export interface TradeAnalysis {
  id: string;
  timestamp: string;
  symbol: string;
  side: OrderSide;
  action: string;
  analysis: string;
  pnl?: number;
  pnlPct?: number;
  source?: string;
  entryPrice?: number;
  takeProfit?: number;
  stopLoss?: number;
}
