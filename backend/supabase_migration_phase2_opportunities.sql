-- Phase 2: Opportunities Table
-- Store scanned opportunities with scores

CREATE TABLE IF NOT EXISTS opportunities (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    grade VARCHAR(5) NOT NULL,
    
    -- Component scores
    technical_score DOUBLE PRECISION,
    momentum_score DOUBLE PRECISION,
    volume_score DOUBLE PRECISION,
    volatility_score DOUBLE PRECISION,
    regime_score DOUBLE PRECISION,
    
    -- Market data
    price DOUBLE PRECISION,
    rsi DOUBLE PRECISION,
    adx DOUBLE PRECISION,
    volume_ratio DOUBLE PRECISION,
    market_regime VARCHAR(20),
    confidence DOUBLE PRECISION,
    
    -- Metadata
    scanned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique constraint: one record per symbol per scan time
    UNIQUE(symbol, scanned_at)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_opportunities_score 
ON opportunities(score DESC);

CREATE INDEX IF NOT EXISTS idx_opportunities_symbol 
ON opportunities(symbol);

CREATE INDEX IF NOT EXISTS idx_opportunities_scanned_at 
ON opportunities(scanned_at DESC);

CREATE INDEX IF NOT EXISTS idx_opportunities_grade 
ON opportunities(grade);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_opportunities_symbol_scanned 
ON opportunities(symbol, scanned_at DESC);

-- Comments
COMMENT ON TABLE opportunities IS 'Scanned trading opportunities with scores';
COMMENT ON COLUMN opportunities.score IS 'Total opportunity score (0-110)';
COMMENT ON COLUMN opportunities.grade IS 'Letter grade (A+ to F)';
COMMENT ON COLUMN opportunities.technical_score IS 'Technical setup score (0-40)';
COMMENT ON COLUMN opportunities.momentum_score IS 'Momentum score (0-25)';
COMMENT ON COLUMN opportunities.volume_score IS 'Volume score (0-20)';
COMMENT ON COLUMN opportunities.volatility_score IS 'Volatility score (0-15)';
COMMENT ON COLUMN opportunities.regime_score IS 'Market regime score (0-10)';

COMMIT;
