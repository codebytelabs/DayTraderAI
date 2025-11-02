// Backend API Response Types

export interface MetricsResponse {
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

export interface PositionResponse {
  symbol: string;
  qty: number;
  side: string;
  avg_entry_price: number;
  current_price: number;
  unrealized_pl: number;
  unrealized_pl_pct: number;
  market_value: number;
  take_profit?: number;
  stop_loss?: number;
}

export interface OrderResponse {
  order_id: string;
  symbol: string;
  qty: number;
  side: string;
  type: string;
  status: string;
  filled_qty: number;
  filled_avg_price?: number;
  submitted_at: string;
}

export interface LogResponse {
  id: string;
  timestamp: string;
  level: string;
  message: string;
  source: string;
}

export interface AdvisoryResponse {
  id: string;
  timestamp: string;
  type: string;
  symbol: string;
  content: string;
  model?: string;
  source?: string;
  confidence?: number;
}

export interface AnalysisResponse {
  id: string;
  timestamp: string;
  symbol: string;
  side: string;
  action: string;
  analysis: string;
  pnl?: number;
  pnl_pct?: number;
  source?: string;
  model?: string;
  entry_price?: number;
  take_profit?: number;
  stop_loss?: number;
}

export interface PerformanceResponse {
  timestamp: string;
  equity: number;
  daily_pl: number;
  daily_pl_pct: number;
  win_rate: number;
  profit_factor: number;
  wins: number;
  losses: number;
}

export interface BackendConfig {
  alpaca_base_url: string;
  supabase_url: string;
  watchlist: string[];
  max_positions: number;
  risk_per_trade_pct: number;
  backend_url: string;
  streaming_enabled: boolean;
  stream_reconnect_delay: number;
  bracket_orders_enabled: boolean;
  default_take_profit_pct: number;
  default_stop_loss_pct: number;
}

export interface ServiceHealthStatus {
  alpaca: 'connected' | 'disconnected' | 'error';
  supabase: 'connected' | 'disconnected' | 'error';
  openrouter: 'connected' | 'disconnected' | 'error';
  perplexity: 'connected' | 'disconnected' | 'error';
  timestamp?: string;
  error?: string;
}
