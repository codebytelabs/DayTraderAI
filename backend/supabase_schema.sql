-- DayTraderAI Supabase Schema
-- Run this in your Supabase SQL editor to create all tables

-- Trades table: completed trades
CREATE TABLE IF NOT EXISTS trades (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL,
    qty INTEGER NOT NULL,
    entry_price DECIMAL(10, 4) NOT NULL,
    exit_price DECIMAL(10, 4) NOT NULL,
    pnl DECIMAL(12, 2) NOT NULL,
    pnl_pct DECIMAL(8, 4) NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    exit_time TIMESTAMPTZ NOT NULL,
    hold_duration_seconds INTEGER,
    strategy VARCHAR(50),
    reason VARCHAR(200),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_timestamp ON trades(timestamp DESC);

-- Positions table: current open positions
CREATE TABLE IF NOT EXISTS positions (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    qty INTEGER NOT NULL,
    side VARCHAR(4) NOT NULL,
    avg_entry_price DECIMAL(10, 4) NOT NULL,
    current_price DECIMAL(10, 4) NOT NULL,
    unrealized_pl DECIMAL(12, 2) NOT NULL,
    unrealized_pl_pct DECIMAL(8, 4) NOT NULL,
    market_value DECIMAL(12, 2) NOT NULL,
    stop_loss DECIMAL(10, 4),
    take_profit DECIMAL(10, 4),
    entry_time TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_positions_symbol ON positions(symbol);

-- Orders table: order history
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    client_order_id VARCHAR(50) UNIQUE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    qty INTEGER NOT NULL,
    side VARCHAR(4) NOT NULL,
    type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    filled_qty INTEGER DEFAULT 0,
    filled_avg_price DECIMAL(10, 4),
    submitted_at TIMESTAMPTZ NOT NULL,
    filled_at TIMESTAMPTZ,
    reason VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_client_order_id ON orders(client_order_id);

-- Order rejections table: track rejected orders for analysis
CREATE TABLE IF NOT EXISTS order_rejections (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL,
    qty INTEGER NOT NULL,
    reason VARCHAR(200) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rejections_timestamp ON order_rejections(timestamp DESC);

-- Market data table: OHLCV bars
CREATE TABLE IF NOT EXISTS market_data (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(10, 4) NOT NULL,
    high DECIMAL(10, 4) NOT NULL,
    low DECIMAL(10, 4) NOT NULL,
    close DECIMAL(10, 4) NOT NULL,
    volume BIGINT NOT NULL,
    timeframe VARCHAR(10) DEFAULT '1min',
    UNIQUE(symbol, timestamp, timeframe)
);

CREATE INDEX idx_market_data_symbol_timestamp ON market_data(symbol, timestamp DESC);

-- Features table: computed indicators
CREATE TABLE IF NOT EXISTS features (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    price DECIMAL(10, 4) NOT NULL,
    ema_short DECIMAL(10, 4),
    ema_long DECIMAL(10, 4),
    atr DECIMAL(10, 4),
    volume BIGINT,
    volume_zscore DECIMAL(8, 4),
    ema_diff DECIMAL(10, 4),
    ema_diff_pct DECIMAL(8, 4),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_features_symbol ON features(symbol);

-- Metrics table: performance metrics snapshots
CREATE TABLE IF NOT EXISTS metrics (
    id BIGSERIAL PRIMARY KEY,
    equity DECIMAL(12, 2) NOT NULL,
    cash DECIMAL(12, 2) NOT NULL,
    buying_power DECIMAL(12, 2) NOT NULL,
    daily_pl DECIMAL(12, 2) NOT NULL,
    daily_pl_pct DECIMAL(8, 4) NOT NULL,
    total_pl DECIMAL(12, 2) NOT NULL,
    win_rate DECIMAL(5, 4),
    profit_factor DECIMAL(8, 4),
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    open_positions INTEGER DEFAULT 0,
    circuit_breaker_triggered BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_metrics_timestamp ON metrics(timestamp DESC);

-- Advisories table: LLM insights
CREATE TABLE IF NOT EXISTS advisories (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    symbol VARCHAR(10),
    content TEXT NOT NULL,
    sentiment VARCHAR(20),
    confidence DECIMAL(5, 4),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_advisories_timestamp ON advisories(timestamp DESC);
CREATE INDEX idx_advisories_symbol ON advisories(symbol);

-- Logs table: system logs
CREATE TABLE IF NOT EXISTS logs (
    id BIGSERIAL PRIMARY KEY,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    component VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_logs_timestamp ON logs(timestamp DESC);
CREATE INDEX idx_logs_level ON logs(level);

-- Config table: strategy configuration
CREATE TABLE IF NOT EXISTS config (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(50) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default config
INSERT INTO config (key, value, description) VALUES
    ('watchlist', 'SPY,QQQ,AAPL,MSFT,NVDA', 'Trading universe symbols'),
    ('max_positions', '5', 'Maximum concurrent positions'),
    ('risk_per_trade_pct', '0.01', 'Risk per trade as decimal'),
    ('circuit_breaker_pct', '0.05', 'Daily loss limit as decimal'),
    ('ema_short', '9', 'Short EMA period'),
    ('ema_long', '21', 'Long EMA period'),
    ('stop_loss_atr_mult', '2.0', 'Stop loss ATR multiplier'),
    ('take_profit_atr_mult', '4.0', 'Take profit ATR multiplier')
ON CONFLICT (key) DO NOTHING;

-- Enable Row Level Security (optional, for production)
-- ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
-- etc.

-- Create views for common queries

-- Recent performance view
CREATE OR REPLACE VIEW recent_performance AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
    SUM(pnl) as total_pnl,
    AVG(pnl) as avg_pnl,
    MAX(pnl) as max_win,
    MIN(pnl) as max_loss
FROM trades
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Symbol performance view
CREATE OR REPLACE VIEW symbol_performance AS
SELECT 
    symbol,
    COUNT(*) as trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
    ROUND(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)::DECIMAL / COUNT(*), 4) as win_rate,
    SUM(pnl) as total_pnl,
    AVG(pnl) as avg_pnl
FROM trades
GROUP BY symbol
ORDER BY total_pnl DESC;

COMMENT ON TABLE trades IS 'Completed trades with P/L';
COMMENT ON TABLE positions IS 'Current open positions';
COMMENT ON TABLE orders IS 'Order history and status';
COMMENT ON TABLE market_data IS 'OHLCV bars for backtesting and analysis';
COMMENT ON TABLE features IS 'Computed technical indicators';
COMMENT ON TABLE metrics IS 'Performance metrics snapshots';
COMMENT ON TABLE advisories IS 'LLM-generated insights and recommendations';
