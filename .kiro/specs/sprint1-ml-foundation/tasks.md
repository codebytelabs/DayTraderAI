# Sprint 1: ML Foundation + Position Management - Implementation Tasks

## Overview

This task list breaks down Sprint 1 into discrete, actionable coding tasks. Each task builds incrementally on previous tasks and references specific requirements from the requirements document.

**Sprint Duration**: Nov 7-20, 2025 (14 days)  
**Total Story Points**: 29  
**Expected Velocity**: 2-3 story points per day

---

## Phase 1: ML Infrastructure Setup (Days 1-3)

### - [ ] 1. Install ML packages and verify imports

Install all required ML packages and verify they work correctly.

- Install packages: `xgboost`, `lightgbm`, `river`, `shap`, `optuna`, `scikit-learn`, `pandas`, `numpy`
- Add to `backend/requirements.txt`
- Test imports in a verification script
- Document versions used
- _Requirements: 1.1_
- _Story Points: 2_

### - [ ] 2. Create ML database schema

Create all database tables needed for ML system.

- Create `ml_trade_features` table with all feature columns
- Create `ml_models` table for model storage
- Create `ml_predictions` table for prediction logging
- Create `ml_performance` table for metrics tracking
- Create `position_exits` table for exit tracking
- Add indexes for performance
- Create migration script: `backend/supabase_migration_ml_tables.sql`
- _Requirements: 1.2_
- _Story Points: 3_

### - [ ] 3. Create ML module structure

Set up the basic ML module file structure.

- Create `backend/ml/` directory
- Create `backend/ml/__init__.py`
- Create `backend/ml/ml_system.py` with `MLSystem` class skeleton
- Create `backend/ml/feature_extractor.py` with `FeatureExtractor` class skeleton
- Create `backend/ml/model_trainer.py` with `ModelTrainer` class skeleton
- Create `backend/ml/predictor.py` with `Predictor` class skeleton
- Create `backend/ml/performance_tracker.py` with `PerformanceTracker` class skeleton
- _Requirements: 1.3_
- _Story Points: 2_

---

## Phase 2: Feature Engineering (Days 4-6)

### - [ ] 4. Implement technical feature extraction

Extract technical indicator features from market data.

- Implement `extract_technical_features()` method
- Extract: EMA 20, EMA 50, RSI, MACD, MACD Signal, ADX, VWAP
- Calculate price vs VWAP percentage
- Handle missing data gracefully
- _Requirements: 2.1_
- _Story Points: 3_

### - [ ] 5. Implement market feature extraction

Extract market regime and breadth features.

- Implement `extract_market_features()` method
- Get current market regime from `market_regime.py`
- Calculate market breadth (% of stocks above EMA)
- Get VIX value
- Calculate sector strength
- _Requirements: 2.2_
- _Story Points: 2_

### - [ ] 6. Implement timing feature extraction

Extract timing-based features.

- Implement `extract_timing_features()` method
- Extract hour of day (0-23)
- Extract day of week (0-6)
- Determine market session (pre-market, open, mid-day, close, after-hours)
- _Requirements: 2.3_
- _Story Points: 1_

### - [ ] 7. Implement historical feature extraction

Extract historical performance features.

- Implement `extract_historical_features()` method
- Calculate recent win rate (last 10 trades)
- Calculate current streak (wins/losses in a row)
- Calculate symbol-specific performance
- Query Supabase for historical trade data
- _Requirements: 2.4_
- _Story Points: 2_

### - [ ] 8. Implement feature normalization

Normalize all features to consistent scale.

- Implement `normalize_features()` method
- Use StandardScaler for continuous features
- Use one-hot encoding for categorical features (regime, session)
- Store scaler for later use
- Return numpy array ready for ML
- _Requirements: 2.6_
- _Story Points: 2_

### - [ ] 9. Integrate feature collection with strategy

Connect feature extraction to the trading strategy.

- Modify `backend/trading/strategy.py`
- Add ML system initialization
- Call feature extraction on every signal
- Store features in database
- Ensure no impact on signal generation latency
- _Requirements: 1.3, 1.5_
- _Story Points: 2_

---

## Phase 3: Model Training & Validation (Days 7-9)

### - [ ] 10. Implement training data loader

Load historical trade data with features for training.

- Implement `load_training_data()` method
- Query `ml_trade_features` table
- Join with `trades` table for outcomes
- Filter for complete records only
- Return X (features) and y (outcomes) arrays
- _Requirements: 3.1_
- _Story Points: 2_

### - [ ] 11. Implement XGBoost model training

Train the XGBoost binary classification model.

- Implement `train_xgboost_model()` method
- Configure XGBoost parameters (max_depth=6, learning_rate=0.1, n_estimators=100)
- Train binary classifier (WIN vs LOSS)
- Use early stopping with validation set
- Return trained model
- _Requirements: 3.1, 3.2_
- _Story Points: 3_

### - [ ] 12. Implement walk-forward validation

Validate model using walk-forward methodology.

- Implement `walk_forward_validation()` method
- Split data: 70% train, 15% validation, 15% test
- Ensure chronological order (no future data in training)
- Train on past, test on future
- Calculate metrics for each fold
- _Requirements: 3.4, 3.5_
- _Story Points: 3_

### - [ ] 13. Implement model evaluation

Evaluate model performance comprehensively.

- Implement `evaluate_model()` method
- Calculate accuracy, precision, recall, F1 score
- Calculate AUC-ROC score
- Generate confusion matrix
- Calculate feature importance
- Ensure accuracy >55% and AUC-ROC >0.60
- _Requirements: 3.2, 4.2, 4.3, 4.4_
- _Story Points: 2_

### - [ ] 14. Implement model persistence

Save and load trained models.

- Implement `save_model()` method
- Serialize model using pickle
- Store model binary in database (base64 encoded)
- Store model metadata (version, metrics, feature importance)
- Implement `load_latest_model()` method
- _Requirements: 3.3_
- _Story Points: 2_

---

## Phase 4: Position Management - Early Exits (Days 10-12)

### - [ ] 15. Create ExitMonitor class

Set up the exit monitoring infrastructure.

- Create `backend/trading/exit_monitor.py`
- Implement `ExitMonitor` class
- Set up monitoring loop (runs every 10 seconds)
- Get all open positions from Alpaca
- _Requirements: 5.1, 6.1, 7.1_
- _Story Points: 2_

### - [ ] 16. Implement volume-based exit

Exit positions when volume dries up.

- Implement `check_volume_exit()` method
- Get current volume from market data
- Compare to entry volume (stored in trade record)
- Trigger exit if current < 50% of entry
- Log exit reason as "low_volume"
- _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
- _Story Points: 2_

### - [ ] 17. Implement time-based exit

Exit positions that aren't profitable after 15 minutes.

- Implement `check_time_exit()` method
- Calculate time elapsed since entry
- Check if position is profitable (unrealized P/L > 0)
- Trigger exit if 15+ minutes AND no profit
- Log exit reason as "time_limit"
- _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
- _Story Points: 2_

### - [ ] 18. Implement momentum reversal exit

Exit positions when momentum reverses.

- Implement `check_momentum_exit()` method
- Calculate current MACD and signal line
- For long positions: detect bearish crossover (MACD < signal)
- For short positions: detect bullish crossover (MACD > signal)
- Trigger exit within 10 seconds of detection
- Log exit reason as "momentum_reversal"
- _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
- _Story Points: 2_

### - [ ] 19. Implement exit execution

Execute early exits and log to database.

- Implement `execute_early_exit()` method
- Close position via Alpaca API
- Insert record into `position_exits` table
- Log exit type, reason, P/L, hold time
- Handle errors gracefully (retry logic)
- _Requirements: 5.3, 5.4, 6.3, 6.4, 7.3, 7.4_
- _Story Points: 2_

---

## Phase 5: Position Management - Breakeven Stops (Day 13)

### - [ ] 20. Create BreakevenStopManager class

Set up breakeven stop management.

- Create `backend/trading/breakeven_manager.py`
- Implement `BreakevenStopManager` class
- Set up monitoring loop (runs every 30 seconds)
- Get all open positions from Alpaca
- _Requirements: 8.1_
- _Story Points: 1_

### - [ ] 21. Implement breakeven stop logic

Move stops to breakeven when profitable.

- Implement `monitor_for_breakeven()` method
- Calculate unrealized P/L for each position
- Determine if position has reached +1R profit
- Implement `move_stop_to_breakeven()` method
- Calculate breakeven price (entry + commissions)
- Update stop loss order via Alpaca API
- Mark position as "breakeven_set" to avoid duplicate moves
- Log action to database
- _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
- _Story Points: 2_

---

## Phase 6: Integration & Testing (Day 14)

### - [ ] 22. Integrate position monitoring with main system

Connect position monitoring to the main trading loop.

- Modify `backend/main.py`
- Start `ExitMonitor` as background task
- Start `BreakevenStopManager` as background task
- Add error handling and logging
- Ensure graceful shutdown
- _Requirements: 10.1, 10.2, 10.3, 10.4_
- _Story Points: 2_

### - [ ] 23. Implement performance tracking

Track performance metrics for Sprint 1 features.

- Create `backend/ml/performance_tracker.py`
- Track baseline metrics (win rate, Sharpe, avg P/L)
- Track ML feature collection rate
- Track position management metrics (exit frequency, impact)
- Generate daily performance report
- Store metrics in `ml_performance` table
- _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
- _Story Points: 2_

### - [ ] 24. Write unit tests

Create unit tests for ML system components.

- Test feature extraction (all types)
- Test feature normalization
- Test model training with synthetic data
- Test prediction latency (<50ms)
- Test walk-forward validation
- _Requirements: All_
- _Story Points: 3_

### - [ ] 25. Write integration tests

Create integration tests for position management.

- Test volume-based exit triggers correctly
- Test time-based exit triggers correctly
- Test momentum reversal exit triggers correctly
- Test breakeven stop adjustment
- Test error handling and fallback
- _Requirements: 5, 6, 7, 8, 10_
- _Story Points: 3_

### - [ ] 26. Performance testing and optimization

Ensure system meets performance requirements.

- Test ML prediction latency (<50ms)
- Test database write latency (<100ms)
- Test position monitoring overhead
- Optimize slow operations
- Add caching where beneficial
- _Requirements: 1.5, 3.6, 10.5_
- _Story Points: 2_

### - [ ] 27. Documentation and deployment

Complete documentation and deploy to production.

- Update README with Sprint 1 features
- Document ML system usage
- Document position management features
- Create deployment checklist
- Deploy to production
- Monitor for issues
- _Requirements: All_
- _Story Points: 1_

---

## Task Summary

**Total Tasks**: 27 (all required)  
**Total Story Points**: 29 (all required)  
**Estimated Duration**: 14 days  
**Daily Velocity**: ~2 story points/day

## Task Dependencies

```
Phase 1 (1-3) → Phase 2 (4-9) → Phase 3 (10-14)
                                      ↓
Phase 4 (15-19) ← ← ← ← ← ← ← ← ← ← ←
       ↓
Phase 5 (20-21)
       ↓
Phase 6 (22-27)
```

## Success Criteria

Sprint 1 is complete when:
- [ ] All non-optional tasks completed
- [ ] ML model trained with >55% accuracy
- [ ] Feature collection working for 100% of trades
- [ ] Position management reducing average loss by 10-15%
- [ ] System stability maintained (zero critical errors)
- [ ] Performance improvement of +5-10% measurable
- [ ] Documentation complete

## Notes

- All tasks are required for comprehensive implementation
- Focus on quality and testing from the start
- Test each phase before moving to the next
- Keep the existing system running while building new features
- Use feature flags to enable/disable new features easily

---

**Ready to start building the money printer! 🚀**
