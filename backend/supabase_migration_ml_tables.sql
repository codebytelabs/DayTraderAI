-- Sprint 1: ML Foundation Database Tables
-- Created: November 6, 2025
-- Purpose: Create all database tables needed for ML system
-- Note: Uses BIGINT/BIGSERIAL to match existing trades table schema

-- ============================================================================
-- ML Trade Features Table
-- Stores feature vectors for each trade for ML training
-- ============================================================================
CREATE TABLE IF NOT EXISTS ml_trade_features (
    id BIGSERIAL PRIMARY KEY,
    trade_id BIGINT REFERENCES trades(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Technical Indicator Features
    ema_20 DECIMAL,
    ema_50 DECIMAL,
    rsi DECIMAL,
    macd DECIMAL,
    macd_signal DECIMAL,
    adx DECIMAL,
    vwap DECIMAL,
    price_vs_vwap DECIMAL,  -- (price - vwap) / vwap * 100
    
    -- Market Regime Features
    regime VARCHAR(50),  -- 'broad_bullish', 'narrow_bullish', etc.
    market_breadth DECIMAL,  -- % of stocks above EMA
    vix DECIMAL,
    sector_strength DECIMAL,
    
    -- Timing Features
    hour_of_day INTEGER,  -- 0-23
    day_of_week INTEGER,  -- 0-6 (Monday=0)
    market_session VARCHAR(20),  -- 'pre_market', 'open', 'mid_day', 'close', 'after_hours'
    
    -- Historical Performance Features
    recent_win_rate DECIMAL,  -- Win rate of last 10 trades
    current_streak INTEGER,  -- Current win/loss streak
    symbol_performance DECIMAL,  -- Historical performance for this symbol
    
    -- Normalized Features (stored as JSON for flexibility)
    features_vector JSONB,  -- Complete normalized feature vector
    
    -- Trade Outcome (filled after trade completes)
    outcome VARCHAR(20),  -- 'WIN', 'LOSS', 'BREAKEVEN'
    pnl_percent DECIMAL,
    hold_time_minutes INTEGER,
    
    -- Metadata
    feature_version VARCHAR(20) DEFAULT '1.0',
    
    CONSTRAINT unique_trade_features UNIQUE(trade_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ml_features_trade_id ON ml_trade_features(trade_id);
CREATE INDEX IF NOT EXISTS idx_ml_features_created_at ON ml_trade_features(created_at);
CREATE INDEX IF NOT EXISTS idx_ml_features_outcome ON ml_trade_features(outcome);
CREATE INDEX IF NOT EXISTS idx_ml_features_regime ON ml_trade_features(regime);

-- ============================================================================
-- ML Models Table
-- Stores trained ML models and their metadata
-- ============================================================================
CREATE TABLE IF NOT EXISTS ml_models (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Model Information
    model_type VARCHAR(50) NOT NULL,  -- 'xgboost', 'lightgbm', 'ensemble'
    version VARCHAR(20) NOT NULL,
    description TEXT,
    
    -- Training Metadata
    training_samples INTEGER,
    training_date TIMESTAMP,
    feature_count INTEGER,
    training_duration_seconds INTEGER,
    
    -- Performance Metrics
    accuracy DECIMAL,
    precision_score DECIMAL,
    recall DECIMAL,
    f1_score DECIMAL,
    auc_roc DECIMAL,
    
    -- Model Binary Data (stored as base64 encoded string)
    model_data TEXT,  -- Pickled model
    scaler_data TEXT,  -- Pickled StandardScaler
    
    -- Feature Importance (stored as JSON)
    feature_importance JSONB,
    
    -- Validation Results
    validation_accuracy DECIMAL,
    test_accuracy DECIMAL,
    confusion_matrix JSONB,
    
    -- Status
    is_active BOOLEAN DEFAULT false,
    validation_status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'passed', 'failed'
    
    -- Hyperparameters (stored as JSON)
    hyperparameters JSONB,
    
    CONSTRAINT unique_model_version UNIQUE(model_type, version)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ml_models_created_at ON ml_models(created_at);
CREATE INDEX IF NOT EXISTS idx_ml_models_is_active ON ml_models(is_active);
CREATE INDEX IF NOT EXISTS idx_ml_models_type ON ml_models(model_type);

-- ============================================================================
-- ML Predictions Table
-- Logs all ML predictions for tracking and validation
-- ============================================================================
CREATE TABLE IF NOT EXISTS ml_predictions (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- References
    trade_id BIGINT REFERENCES trades(id) ON DELETE CASCADE,
    model_id BIGINT REFERENCES ml_models(id) ON DELETE SET NULL,
    
    -- Prediction Details
    probability DECIMAL NOT NULL,  -- 0.0 to 1.0 (probability of WIN)
    confidence DECIMAL,  -- 0.0 to 1.0 (model confidence)
    prediction VARCHAR(20) NOT NULL,  -- 'WIN' or 'LOSS'
    
    -- Feature Vector Used (for debugging)
    features_used JSONB,
    
    -- Performance Tracking
    latency_ms INTEGER,  -- Prediction latency in milliseconds
    
    -- Actual Outcome (filled after trade completes)
    actual_outcome VARCHAR(20),  -- 'WIN', 'LOSS', 'BREAKEVEN'
    was_correct BOOLEAN,
    
    -- Metadata
    prediction_weight DECIMAL DEFAULT 0.0,  -- Weight used in signal blending (0-1)
    
    CONSTRAINT unique_trade_prediction UNIQUE(trade_id, model_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ml_predictions_trade_id ON ml_predictions(trade_id);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_model_id ON ml_predictions(model_id);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_created_at ON ml_predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_was_correct ON ml_predictions(was_correct);

-- ============================================================================
-- ML Performance Table
-- Tracks daily ML system performance metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS ml_performance (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    model_id BIGINT REFERENCES ml_models(id) ON DELETE CASCADE,
    
    -- Daily Prediction Metrics
    predictions_made INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    accuracy DECIMAL,
    
    -- Performance Comparison
    baseline_win_rate DECIMAL,  -- Win rate without ML
    ml_win_rate DECIMAL,  -- Win rate with ML
    improvement_percent DECIMAL,  -- (ml_win_rate - baseline_win_rate) / baseline_win_rate * 100
    
    -- Latency Metrics
    avg_latency_ms DECIMAL,
    max_latency_ms INTEGER,
    min_latency_ms INTEGER,
    
    -- Financial Impact
    baseline_pnl DECIMAL,  -- P/L without ML
    ml_pnl DECIMAL,  -- P/L with ML
    pnl_improvement DECIMAL,
    
    -- Model Confidence Metrics
    avg_confidence DECIMAL,
    high_confidence_count INTEGER,  -- Predictions with confidence > 0.7
    high_confidence_accuracy DECIMAL,
    
    CONSTRAINT unique_daily_performance UNIQUE(date, model_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ml_performance_date ON ml_performance(date);
CREATE INDEX IF NOT EXISTS idx_ml_performance_model_id ON ml_performance(model_id);

-- ============================================================================
-- Position Exits Table
-- Tracks all position exits (early and normal) for analysis
-- ============================================================================
CREATE TABLE IF NOT EXISTS position_exits (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- References
    trade_id BIGINT REFERENCES trades(id) ON DELETE CASCADE,
    
    -- Exit Details
    exit_type VARCHAR(50) NOT NULL,  -- 'volume', 'time', 'momentum', 'breakeven', 'stop_loss', 'take_profit', 'normal'
    exit_reason TEXT,
    
    -- Position State at Exit
    symbol VARCHAR(10),
    side VARCHAR(10),  -- 'long' or 'short'
    entry_price DECIMAL,
    exit_price DECIMAL,
    quantity INTEGER,
    
    -- Metrics at Exit
    hold_time_minutes INTEGER,
    pnl_dollars DECIMAL,
    pnl_percent DECIMAL,
    
    -- Volume Analysis (for volume-based exits)
    volume_at_entry BIGINT,
    volume_at_exit BIGINT,
    volume_vs_entry DECIMAL,  -- volume_at_exit / volume_at_entry
    
    -- Technical Indicators at Exit
    rsi_at_exit DECIMAL,
    macd_at_exit DECIMAL,
    adx_at_exit DECIMAL,
    
    -- Performance Impact Analysis
    would_have_pnl DECIMAL,  -- What P/L would have been without early exit
    exit_benefit DECIMAL,  -- Positive if early exit helped, negative if hurt
    
    -- Metadata
    was_early_exit BOOLEAN DEFAULT false,
    
    CONSTRAINT unique_trade_exit UNIQUE(trade_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_position_exits_trade_id ON position_exits(trade_id);
CREATE INDEX IF NOT EXISTS idx_position_exits_created_at ON position_exits(created_at);
CREATE INDEX IF NOT EXISTS idx_position_exits_exit_type ON position_exits(exit_type);
CREATE INDEX IF NOT EXISTS idx_position_exits_symbol ON position_exits(symbol);

-- ============================================================================
-- Views for Easy Querying
-- ============================================================================

-- View: ML Model Performance Summary
CREATE OR REPLACE VIEW ml_model_performance_summary AS
SELECT 
    m.id,
    m.model_type,
    m.version,
    m.created_at,
    m.is_active,
    m.accuracy as training_accuracy,
    m.validation_accuracy,
    m.test_accuracy,
    m.auc_roc,
    COUNT(p.id) as total_predictions,
    SUM(CASE WHEN p.was_correct = true THEN 1 ELSE 0 END) as correct_predictions,
    ROUND(AVG(CASE WHEN p.was_correct = true THEN 1.0 ELSE 0.0 END) * 100, 2) as live_accuracy,
    ROUND(AVG(p.latency_ms), 2) as avg_latency_ms
FROM ml_models m
LEFT JOIN ml_predictions p ON m.id = p.model_id
GROUP BY m.id, m.model_type, m.version, m.created_at, m.is_active, m.accuracy, m.validation_accuracy, m.test_accuracy, m.auc_roc;

-- View: Daily Exit Performance
CREATE OR REPLACE VIEW daily_exit_performance AS
SELECT 
    DATE(created_at) as date,
    exit_type,
    COUNT(*) as exit_count,
    ROUND(AVG(pnl_percent), 2) as avg_pnl_percent,
    ROUND(AVG(hold_time_minutes), 2) as avg_hold_time_minutes,
    ROUND(AVG(exit_benefit), 2) as avg_exit_benefit,
    SUM(CASE WHEN pnl_percent > 0 THEN 1 ELSE 0 END) as winning_exits,
    SUM(CASE WHEN pnl_percent <= 0 THEN 1 ELSE 0 END) as losing_exits
FROM position_exits
GROUP BY DATE(created_at), exit_type
ORDER BY date DESC, exit_type;

-- View: Feature Statistics
CREATE OR REPLACE VIEW ml_feature_statistics AS
SELECT 
    COUNT(*) as total_features,
    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
    ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
    ROUND(AVG(pnl_percent), 2) as avg_pnl_percent,
    ROUND(AVG(hold_time_minutes), 2) as avg_hold_time_minutes,
    regime,
    market_session
FROM ml_trade_features
WHERE outcome IS NOT NULL
GROUP BY regime, market_session
ORDER BY win_rate DESC;

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE ml_trade_features IS 'Stores feature vectors for each trade for ML training and analysis';
COMMENT ON TABLE ml_models IS 'Stores trained ML models with metadata and performance metrics';
COMMENT ON TABLE ml_predictions IS 'Logs all ML predictions for tracking and validation';
COMMENT ON TABLE ml_performance IS 'Tracks daily ML system performance metrics';
COMMENT ON TABLE position_exits IS 'Tracks all position exits for analysis and optimization';

-- ============================================================================
-- Success Message
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ ML Database Tables Created Successfully!';
    RAISE NOTICE '📊 Tables: ml_trade_features, ml_models, ml_predictions, ml_performance, position_exits';
    RAISE NOTICE '📈 Views: ml_model_performance_summary, daily_exit_performance, ml_feature_statistics';
    RAISE NOTICE '🚀 Ready for ML system implementation!';
END $$;
