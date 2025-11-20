-- Create ML Predictions Table for Shadow Mode
-- This table stores ML predictions and their outcomes for learning

-- Drop table if exists (for clean reinstall)
DROP TABLE IF EXISTS ml_predictions CASCADE;

-- Create table
CREATE TABLE ml_predictions (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    ml_confidence DOUBLE PRECISION,
    ml_prediction TEXT,
    existing_confidence DOUBLE PRECISION NOT NULL,
    blended_confidence DOUBLE PRECISION NOT NULL,
    ml_weight DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    signal_type TEXT,
    signal_price DOUBLE PRECISION,
    latency_ms DOUBLE PRECISION,
    actual_outcome TEXT,
    actual_pnl DOUBLE PRECISION,
    was_correct BOOLEAN,
    trade_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Create indexes
CREATE INDEX idx_ml_predictions_symbol ON ml_predictions(symbol);
CREATE INDEX idx_ml_predictions_created_at ON ml_predictions(created_at DESC);
CREATE INDEX idx_ml_predictions_outcome ON ml_predictions(actual_outcome) WHERE actual_outcome IS NOT NULL;
CREATE INDEX idx_ml_predictions_correct ON ml_predictions(was_correct) WHERE was_correct IS NOT NULL;

-- Enable Row Level Security
ALTER TABLE ml_predictions ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY "Enable all operations for ml_predictions" 
ON ml_predictions 
FOR ALL 
USING (true) 
WITH CHECK (true);

-- Add comment
COMMENT ON TABLE ml_predictions IS 'ML Shadow Mode predictions and outcomes for learning and accuracy tracking';
