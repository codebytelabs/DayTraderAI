-- Phase 1: Add Enhanced Indicator Columns
-- Migration to support multi-indicator confirmation system

-- Add VWAP indicator
ALTER TABLE market_data 
ADD COLUMN IF NOT EXISTS vwap DOUBLE PRECISION;

-- Add RSI indicator
ALTER TABLE market_data 
ADD COLUMN IF NOT EXISTS rsi DOUBLE PRECISION;

-- Add MACD indicators
ALTER TABLE market_data 
ADD COLUMN IF NOT EXISTS macd DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS macd_signal DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS macd_histogram DOUBLE PRECISION;

-- Add ADX and directional indicators
ALTER TABLE market_data 
ADD COLUMN IF NOT EXISTS adx DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS plus_di DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS minus_di DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS market_regime VARCHAR(20);

-- Add enhanced volume indicators
ALTER TABLE market_data 
ADD COLUMN IF NOT EXISTS volume_ratio DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS volume_spike BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS obv DOUBLE PRECISION;

-- Add signal indicators
ALTER TABLE market_data 
ADD COLUMN IF NOT EXISTS vwap_signal INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS rsi_momentum INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS macd_momentum INTEGER DEFAULT 0;

-- Add confidence score
ALTER TABLE market_data 
ADD COLUMN IF NOT EXISTS confidence_score DOUBLE PRECISION DEFAULT 50.0;

-- Create index on confidence score for faster queries
CREATE INDEX IF NOT EXISTS idx_market_data_confidence 
ON market_data(confidence_score DESC);

-- Create index on market regime
CREATE INDEX IF NOT EXISTS idx_market_data_regime 
ON market_data(market_regime);

-- Create index on RSI for overbought/oversold queries
CREATE INDEX IF NOT EXISTS idx_market_data_rsi 
ON market_data(rsi);

-- Add comments for documentation
COMMENT ON COLUMN market_data.vwap IS 'Volume-Weighted Average Price';
COMMENT ON COLUMN market_data.rsi IS 'Relative Strength Index (0-100)';
COMMENT ON COLUMN market_data.macd IS 'MACD Line';
COMMENT ON COLUMN market_data.macd_signal IS 'MACD Signal Line';
COMMENT ON COLUMN market_data.macd_histogram IS 'MACD Histogram';
COMMENT ON COLUMN market_data.adx IS 'Average Directional Index (0-100)';
COMMENT ON COLUMN market_data.plus_di IS 'Plus Directional Indicator';
COMMENT ON COLUMN market_data.minus_di IS 'Minus Directional Indicator';
COMMENT ON COLUMN market_data.market_regime IS 'Market regime: trending, ranging, or transitional';
COMMENT ON COLUMN market_data.volume_ratio IS 'Current volume / Average volume';
COMMENT ON COLUMN market_data.volume_spike IS 'True if volume spike detected';
COMMENT ON COLUMN market_data.obv IS 'On-Balance Volume';
COMMENT ON COLUMN market_data.confidence_score IS 'Multi-indicator confidence score (0-100)';

-- Update existing rows with default values
UPDATE market_data 
SET 
    rsi = 50.0,
    confidence_score = 50.0,
    volume_ratio = 1.0,
    volume_spike = FALSE,
    vwap_signal = 0,
    rsi_momentum = 0,
    macd_momentum = 0,
    market_regime = 'transitional'
WHERE rsi IS NULL;

COMMIT;
