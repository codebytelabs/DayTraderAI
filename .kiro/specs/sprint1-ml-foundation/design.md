# Sprint 1: ML Foundation + Position Management - Design

## Overview

This design document outlines the architecture and implementation approach for Sprint 1, which establishes the ML infrastructure foundation and implements intelligent position management features. The design prioritizes simplicity, performance, and seamless integration with the existing trading system.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Trading System                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Scanner    │───▶│   Strategy   │───▶│Position Mgr  │  │
│  │  (existing)  │    │  (existing)  │    │   (NEW)      │  │
│  └──────────────┘    └──────┬───────┘    └──────┬───────┘  │
│                              │                    │          │
│                              ▼                    ▼          │
│                      ┌──────────────┐    ┌──────────────┐  │
│                      │  ML System   │    │ Exit Monitor │  │
│                      │    (NEW)     │    │    (NEW)     │  │
│                      └──────┬───────┘    └──────────────┘  │
│                              │                               │
└──────────────────────────────┼───────────────────────────────┘
                               │
                               ▼
                      ┌──────────────┐
                      │   Supabase   │
                      │   Database   │
                      └──────────────┘
```

### Component Breakdown

1. **ML System** (NEW)
   - Feature extractor
   - Model trainer
   - Prediction engine
   - Performance tracker

2. **Position Manager** (ENHANCED)
   - Exit monitor (volume, time, momentum)
   - Breakeven stop adjuster
   - Performance tracker

3. **Database** (ENHANCED)
   - New tables for ML data
   - Enhanced trades table

## Components and Interfaces

### 1. ML System Module

**Location**: `backend/ml/`

**Files**:
- `ml_system.py` - Main ML system coordinator
- `feature_extractor.py` - Feature engineering
- `model_trainer.py` - Model training and validation
- `predictor.py` - Real-time prediction engine
- `performance_tracker.py` - ML performance monitoring

**Key Classes**:

```python
class MLSystem:
    """Main ML system coordinator"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.feature_extractor = FeatureExtractor()
        self.model_trainer = ModelTrainer()
        self.predictor = Predictor()
        self.performance_tracker = PerformanceTracker()
    
    async def collect_trade_data(self, trade_data: dict) -> None:
        """Collect and store trade data with features"""
        pass
    
    async def train_model(self) -> dict:
        """Train ML model on historical data"""
        pass
    
    async def predict(self, features: dict) -> float:
        """Make prediction for new trade signal"""
        pass
    
    async def get_performance_metrics(self) -> dict:
        """Get ML system performance metrics"""
        pass
```

```python
class FeatureExtractor:
    """Extract features from trade data"""
    
    def extract_technical_features(self, market_data: dict) -> dict:
        """Extract technical indicator features"""
        # EMA, RSI, MACD, ADX, VWAP values
        pass
    
    def extract_market_features(self, market_data: dict) -> dict:
        """Extract market regime and breadth features"""
        # Regime type, breadth, volatility
        pass
    
    def extract_timing_features(self, timestamp: datetime) -> dict:
        """Extract timing-based features"""
        # Time of day, day of week, market session
        pass
    
    def extract_historical_features(self, symbol: str) -> dict:
        """Extract historical performance features"""
        # Recent win rate, current streak
        pass
    
    def normalize_features(self, features: dict) -> np.ndarray:
        """Normalize features to consistent scale"""
        pass
```

```python
class ModelTrainer:
    """Train and validate ML models"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
    
    async def load_training_data(self) -> tuple:
        """Load historical trades with features"""
        pass
    
    def train_xgboost_model(self, X_train, y_train) -> xgb.XGBClassifier:
        """Train XGBoost binary classifier"""
        params = {
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'objective': 'binary:logistic',
            'eval_metric': 'auc'
        }
        pass
    
    def walk_forward_validation(self, data: pd.DataFrame) -> dict:
        """Perform walk-forward validation"""
        # 70/15/15 split, no data leakage
        pass
    
    def evaluate_model(self, X_test, y_test) -> dict:
        """Evaluate model performance"""
        # Accuracy, precision, recall, F1, AUC-ROC
        pass
    
    async def save_model(self, model, metadata: dict) -> None:
        """Save trained model to database"""
        pass
```

```python
class Predictor:
    """Real-time prediction engine"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_extractor = FeatureExtractor()
    
    async def load_latest_model(self) -> None:
        """Load the latest trained model"""
        pass
    
    async def predict_trade_outcome(self, trade_signal: dict) -> dict:
        """Predict outcome for trade signal"""
        # Returns: {
        #   'probability': 0.65,
        #   'confidence': 0.85,
        #   'prediction': 'WIN',
        #   'latency_ms': 23
        # }
        pass
    
    def _ensure_low_latency(self, func):
        """Decorator to ensure <50ms latency"""
        pass
```

### 2. Enhanced Position Manager

**Location**: `backend/trading/position_manager.py` (ENHANCED)

**New Classes**:

```python
class ExitMonitor:
    """Monitor positions for early exit conditions"""
    
    def __init__(self, alpaca_client, supabase_client):
        self.alpaca = alpaca_client
        self.supabase = supabase_client
        self.market_data = MarketData(alpaca_client)
    
    async def monitor_positions(self) -> None:
        """Main monitoring loop - runs every 10 seconds"""
        pass
    
    async def check_volume_exit(self, position: dict) -> bool:
        """Check if volume has dried up"""
        # Exit if current volume < 50% of entry volume
        pass
    
    async def check_time_exit(self, position: dict) -> bool:
        """Check if position should exit due to time"""
        # Exit if 15 min elapsed and no profit
        pass
    
    async def check_momentum_exit(self, position: dict) -> bool:
        """Check if momentum has reversed"""
        # Exit if MACD crosses against position
        pass
    
    async def execute_early_exit(self, position: dict, reason: str) -> None:
        """Execute early exit and log reason"""
        pass
```

```python
class BreakevenStopManager:
    """Manage breakeven stop adjustments"""
    
    def __init__(self, alpaca_client, supabase_client):
        self.alpaca = alpaca_client
        self.supabase = supabase_client
    
    async def monitor_for_breakeven(self) -> None:
        """Check positions for breakeven stop adjustment"""
        pass
    
    async def move_stop_to_breakeven(self, position: dict) -> None:
        """Move stop loss to entry price"""
        # Triggered when position reaches +1R profit
        pass
    
    def calculate_breakeven_price(self, position: dict) -> float:
        """Calculate breakeven price including commissions"""
        pass
```

### 3. Database Schema

**New Tables**:

```sql
-- ML Features Table
CREATE TABLE ml_trade_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trade_id UUID REFERENCES trades(id),
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Technical Features
    ema_20 DECIMAL,
    ema_50 DECIMAL,
    rsi DECIMAL,
    macd DECIMAL,
    macd_signal DECIMAL,
    adx DECIMAL,
    vwap DECIMAL,
    price_vs_vwap DECIMAL,
    
    -- Market Features
    regime VARCHAR(50),
    market_breadth DECIMAL,
    vix DECIMAL,
    sector_strength DECIMAL,
    
    -- Timing Features
    hour_of_day INTEGER,
    day_of_week INTEGER,
    market_session VARCHAR(20),
    
    -- Historical Features
    recent_win_rate DECIMAL,
    current_streak INTEGER,
    symbol_performance DECIMAL,
    
    -- Normalized Features (JSON)
    features_vector JSONB,
    
    -- Outcome (for training)
    outcome VARCHAR(20), -- 'WIN', 'LOSS', 'BREAKEVEN'
    pnl_percent DECIMAL,
    hold_time_minutes INTEGER
);

-- ML Models Table
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP DEFAULT NOW(),
    model_type VARCHAR(50), -- 'xgboost', 'lightgbm', etc.
    version VARCHAR(20),
    
    -- Model Metadata
    training_samples INTEGER,
    training_date TIMESTAMP,
    feature_count INTEGER,
    
    -- Performance Metrics
    accuracy DECIMAL,
    precision_score DECIMAL,
    recall DECIMAL,
    f1_score DECIMAL,
    auc_roc DECIMAL,
    
    -- Model Binary (stored as base64)
    model_data TEXT,
    scaler_data TEXT,
    
    -- Feature Importance
    feature_importance JSONB,
    
    -- Status
    is_active BOOLEAN DEFAULT false,
    validation_status VARCHAR(20)
);

-- ML Predictions Table
CREATE TABLE ml_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP DEFAULT NOW(),
    trade_id UUID REFERENCES trades(id),
    model_id UUID REFERENCES ml_models(id),
    
    -- Prediction
    probability DECIMAL, -- 0.0 to 1.0
    confidence DECIMAL, -- 0.0 to 1.0
    prediction VARCHAR(20), -- 'WIN', 'LOSS'
    
    -- Performance
    latency_ms INTEGER,
    
    -- Actual Outcome (filled after trade completes)
    actual_outcome VARCHAR(20),
    was_correct BOOLEAN
);

-- ML Performance Tracking
CREATE TABLE ml_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE,
    model_id UUID REFERENCES ml_models(id),
    
    -- Daily Metrics
    predictions_made INTEGER,
    correct_predictions INTEGER,
    accuracy DECIMAL,
    
    -- Performance Impact
    baseline_win_rate DECIMAL,
    ml_win_rate DECIMAL,
    improvement_percent DECIMAL,
    
    -- Latency
    avg_latency_ms DECIMAL,
    max_latency_ms INTEGER
);

-- Position Exit Tracking
CREATE TABLE position_exits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP DEFAULT NOW(),
    trade_id UUID REFERENCES trades(id),
    
    -- Exit Details
    exit_type VARCHAR(50), -- 'volume', 'time', 'momentum', 'breakeven', 'normal'
    exit_reason TEXT,
    
    -- Metrics at Exit
    hold_time_minutes INTEGER,
    pnl_percent DECIMAL,
    volume_at_exit BIGINT,
    volume_vs_entry DECIMAL,
    
    -- Performance Impact
    would_have_pnl DECIMAL, -- What P/L would have been without early exit
    exit_benefit DECIMAL -- Positive if early exit helped
);
```

## Data Models

### Feature Vector Structure

```python
@dataclass
class TradeFeatures:
    """Complete feature vector for a trade"""
    
    # Technical Indicators
    ema_20: float
    ema_50: float
    rsi: float
    macd: float
    macd_signal: float
    adx: float
    vwap: float
    price_vs_vwap: float
    
    # Market Features
    regime: str
    market_breadth: float
    vix: float
    sector_strength: float
    
    # Timing Features
    hour_of_day: int
    day_of_week: int
    market_session: str
    
    # Historical Features
    recent_win_rate: float
    current_streak: int
    symbol_performance: float
    
    def to_vector(self) -> np.ndarray:
        """Convert to numpy array for ML"""
        pass
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        pass
```

### Prediction Result

```python
@dataclass
class PredictionResult:
    """ML prediction result"""
    
    probability: float  # 0.0 to 1.0
    confidence: float   # 0.0 to 1.0
    prediction: str     # 'WIN' or 'LOSS'
    latency_ms: int     # Prediction latency
    model_version: str  # Model used
    
    def is_confident(self, threshold: float = 0.7) -> bool:
        """Check if prediction is confident enough"""
        return self.confidence >= threshold
```

## Integration Points

### 1. Strategy Integration

The ML system integrates with the existing strategy at the signal generation point:

```python
# In backend/trading/strategy.py

async def evaluate_signal(self, symbol: str, signal_type: str) -> dict:
    """Evaluate trading signal (ENHANCED)"""
    
    # Existing signal evaluation
    signal_score = await self._calculate_signal_score(symbol, signal_type)
    
    # NEW: Collect features for ML
    features = await self.ml_system.feature_extractor.extract_all_features(
        symbol=symbol,
        signal_type=signal_type,
        market_data=self.market_data
    )
    
    # NEW: Store features for future training (Sprint 1: collection only)
    await self.ml_system.collect_trade_data({
        'symbol': symbol,
        'signal_type': signal_type,
        'features': features,
        'timestamp': datetime.now()
    })
    
    # Return signal (ML prediction not used yet in Sprint 1)
    return {
        'symbol': symbol,
        'signal_type': signal_type,
        'score': signal_score,
        'features_collected': True
    }
```

### 2. Position Manager Integration

The enhanced position manager runs as a background task:

```python
# In backend/main.py

async def start_position_monitoring():
    """Start position monitoring background task"""
    
    exit_monitor = ExitMonitor(alpaca_client, supabase_client)
    breakeven_manager = BreakevenStopManager(alpaca_client, supabase_client)
    
    while True:
        try:
            # Check for early exits every 10 seconds
            await exit_monitor.monitor_positions()
            
            # Check for breakeven stops every 30 seconds
            await breakeven_manager.monitor_for_breakeven()
            
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Position monitoring error: {e}")
            await asyncio.sleep(30)
```

## Error Handling

### ML System Error Handling

```python
class MLSystem:
    async def predict(self, features: dict) -> Optional[PredictionResult]:
        """Make prediction with error handling"""
        try:
            # Attempt prediction
            result = await self.predictor.predict_trade_outcome(features)
            return result
        except ModelNotLoadedError:
            logger.warning("ML model not loaded, skipping prediction")
            return None
        except PredictionTimeoutError:
            logger.error("ML prediction timeout (>50ms)")
            return None
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            return None
```

### Position Manager Error Handling

```python
class ExitMonitor:
    async def execute_early_exit(self, position: dict, reason: str) -> bool:
        """Execute early exit with error handling"""
        try:
            # Attempt to close position
            await self.alpaca.close_position(position['symbol'])
            
            # Log exit
            await self.supabase.table('position_exits').insert({
                'trade_id': position['trade_id'],
                'exit_type': reason,
                'exit_reason': f"Early exit: {reason}",
                'pnl_percent': position['unrealized_plpc']
            }).execute()
            
            return True
        except AlpacaAPIError as e:
            logger.error(f"Failed to close position: {e}")
            return False
        except Exception as e:
            logger.error(f"Exit execution error: {e}")
            return False
```

## Testing Strategy

### Unit Tests

```python
# tests/test_ml_system.py

def test_feature_extraction():
    """Test feature extraction produces correct format"""
    pass

def test_model_training():
    """Test model training with synthetic data"""
    pass

def test_prediction_latency():
    """Test prediction completes within 50ms"""
    pass

def test_walk_forward_validation():
    """Test walk-forward validation prevents data leakage"""
    pass
```

### Integration Tests

```python
# tests/test_position_manager.py

async def test_volume_exit():
    """Test volume-based exit triggers correctly"""
    pass

async def test_time_exit():
    """Test time-based exit triggers correctly"""
    pass

async def test_momentum_exit():
    """Test momentum reversal exit triggers correctly"""
    pass

async def test_breakeven_stop():
    """Test breakeven stop adjustment"""
    pass
```

### Performance Tests

```python
# tests/test_performance.py

async def test_ml_prediction_latency():
    """Ensure ML predictions complete within 50ms"""
    pass

async def test_database_write_latency():
    """Ensure database writes don't impact trading"""
    pass

async def test_position_monitoring_overhead():
    """Ensure position monitoring doesn't impact system"""
    pass
```

## Performance Considerations

### ML Prediction Optimization

1. **Model Loading**: Load model once at startup, keep in memory
2. **Feature Caching**: Cache frequently accessed features (market regime, VIX)
3. **Batch Predictions**: If multiple signals, batch predict for efficiency
4. **Async Operations**: All database operations are async to avoid blocking

### Database Optimization

1. **Indexes**: Create indexes on frequently queried columns
   ```sql
   CREATE INDEX idx_ml_features_trade_id ON ml_trade_features(trade_id);
   CREATE INDEX idx_ml_predictions_trade_id ON ml_predictions(trade_id);
   CREATE INDEX idx_position_exits_trade_id ON position_exits(trade_id);
   ```

2. **Connection Pooling**: Use connection pooling for database access
3. **Batch Inserts**: Batch insert features for multiple trades when possible

### Position Monitoring Optimization

1. **Polling Interval**: 10-second polling is sufficient, avoids excessive API calls
2. **Caching**: Cache position data between checks
3. **Selective Monitoring**: Only monitor positions that meet criteria (e.g., open > 5 min)

## Deployment Strategy

### Phase 1: Infrastructure Setup (Days 1-2)
1. Install ML packages
2. Create database tables
3. Set up ML module structure

### Phase 2: Feature Collection (Days 3-5)
1. Implement feature extractor
2. Integrate with strategy
3. Collect features for 2-3 days

### Phase 3: Model Training (Days 6-8)
1. Implement model trainer
2. Train initial model
3. Validate performance

### Phase 4: Position Management (Days 9-11)
1. Implement exit monitor
2. Implement breakeven manager
3. Test with paper trading

### Phase 5: Integration & Testing (Days 12-14)
1. Full system integration
2. Performance testing
3. Bug fixes and optimization

## Monitoring and Metrics

### ML System Metrics

- Model accuracy (daily)
- Prediction latency (per prediction)
- Feature collection rate (% of trades)
- Model training frequency

### Position Management Metrics

- Early exit frequency (by type)
- Early exit performance impact
- Breakeven stop frequency
- Average hold time reduction

### System Health Metrics

- Error rate
- API latency
- Database query time
- Memory usage

## Rollback Plan

If Sprint 1 features cause issues:

1. **ML System**: Disable feature collection, system continues normally
2. **Position Manager**: Disable early exits, revert to standard stops
3. **Database**: Tables can remain, no impact if not used
4. **Monitoring**: Keep monitoring active for debugging

All features are designed to be independently toggleable via feature flags.

## Success Criteria

Sprint 1 is successful when:

- ✅ ML model trained with >55% accuracy
- ✅ Feature collection working for 100% of trades
- ✅ Position management reducing average loss by 10-15%
- ✅ System stability maintained (zero critical errors)
- ✅ Performance improvement of +5-10% measurable
- ✅ All tests passing
- ✅ Documentation complete

## Next Steps (Sprint 2)

After Sprint 1 completion:
- Daily report system (automated analysis)
- ML shadow mode (predictions logged but not used)
- Enhanced early exit strategies
- Performance comparison dashboard
