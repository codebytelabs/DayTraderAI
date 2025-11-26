-- Intelligent Profit Protection System Database Schema
-- Creates tables for position state tracking, partial profits, and stop loss history

-- Position States Table
CREATE TABLE IF NOT EXISTS position_states (
    symbol VARCHAR(10) PRIMARY KEY,
    entry_price DECIMAL(10, 2) NOT NULL,
    current_price DECIMAL(10, 2) NOT NULL,
    stop_loss DECIMAL(10, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    side VARCHAR(5) NOT NULL CHECK (side IN ('long', 'short')),
    r_multiple DECIMAL(10, 2) NOT NULL,
    unrealized_pl DECIMAL(10, 2) NOT NULL,
    protection_state VARCHAR(30) NOT NULL,
    trailing_active BOOLEAN DEFAULT FALSE,
    last_stop_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_position_states_protection_state ON position_states(protection_state);
CREATE INDEX IF NOT EXISTS idx_position_states_r_multiple ON position_states(r_multiple);

-- Partial Profits Table
CREATE TABLE IF NOT EXISTS partial_profits (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    r_multiple DECIMAL(10, 2) NOT NULL,
    shares_sold INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    profit_amount DECIMAL(10, 2) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_partial_profits_symbol ON partial_profits(symbol);
CREATE INDEX IF NOT EXISTS idx_partial_profits_timestamp ON partial_profits(timestamp);

-- Stop Loss History Table
CREATE TABLE IF NOT EXISTS stop_loss_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    old_stop DECIMAL(10, 2),
    new_stop DECIMAL(10, 2) NOT NULL,
    r_multiple DECIMAL(10, 2) NOT NULL,
    reason VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stop_loss_history_symbol ON stop_loss_history(symbol);
CREATE INDEX IF NOT EXISTS idx_stop_loss_history_timestamp ON stop_loss_history(timestamp);

-- Add comments for documentation
COMMENT ON TABLE position_states IS 'Real-time position state tracking for intelligent profit protection';
COMMENT ON TABLE partial_profits IS 'Record of all partial profit executions at R-multiple milestones';
COMMENT ON TABLE stop_loss_history IS 'Audit trail of all stop loss modifications';
