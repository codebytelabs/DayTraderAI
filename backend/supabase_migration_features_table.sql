-- Add Phase 1 Indicator Columns to Features Table
-- This complements the market_data migration

-- Add VWAP indicator
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS vwap DOUBLE PRECISION;

-- Add RSI indicator
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS rsi DOUBLE PRECISION;

-- Add MACD indicators
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS macd DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS macd_signal DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS macd_histogram DOUBLE PRECISION;

-- Add ADX and directional indicators
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS adx DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS plus_di DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS minus_di DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS market_regime VARCHAR(20);

-- Add enhanced volume indicators
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS volume_ratio DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS volume_spike BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS obv DOUBLE PRECISION;

-- Add signal indicators
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS vwap_signal INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS rsi_momentum INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS macd_momentum INTEGER DEFAULT 0;

-- Add confidence score
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS confidence_score DOUBLE PRECISION DEFAULT 50.0;

-- Add prev_ema columns if not exists (for crossover detection)
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS prev_ema_short DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS prev_ema_long DOUBLE PRECISION;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_features_confidence 
ON features(confidence_score DESC);

CREATE INDEX IF NOT EXISTS idx_features_regime 
ON features(market_regime);

CREATE INDEX IF NOT EXISTS idx_features_rsi 
ON features(rsi);

-- Update existing rows with default values
UPDATE features 
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
