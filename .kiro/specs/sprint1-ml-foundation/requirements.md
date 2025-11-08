# Sprint 1: ML Foundation + Position Management - Requirements

## Introduction

This specification defines the requirements for Sprint 1 of the DayTraderAI money printer transformation. The sprint focuses on building the machine learning infrastructure foundation and implementing basic intelligent position management features. This is the critical first step in our journey to 5-10x performance improvement.

## Glossary

- **ML System**: The machine learning system that learns from historical trades to predict future trade outcomes
- **Feature Vector**: A structured collection of numerical values representing trade characteristics (technical indicators, market conditions, timing)
- **Model**: A trained machine learning algorithm (XGBoost) that predicts trade success probability
- **Position Manager**: The system component responsible for managing open trading positions
- **Early Exit**: Closing a position before the normal stop loss or take profit is hit
- **Breakeven Stop**: Moving the stop loss to the entry price after the position becomes profitable
- **Walk-Forward Validation**: A backtesting method where the model is trained on past data and tested on future data sequentially

## Requirements

### Requirement 1: ML Infrastructure Setup

**User Story:** As a trading system, I want to have a complete ML infrastructure so that I can collect data, train models, and make predictions.

#### Acceptance Criteria

1. WHEN THE ML System initializes, THE ML System SHALL install all required Python packages (xgboost, lightgbm, river, shap, optuna, scikit-learn)
2. WHEN THE ML System starts, THE ML System SHALL create database tables for features, models, predictions, and performance metrics
3. WHEN a trade completes, THE ML System SHALL collect and store the feature vector and outcome in the database
4. THE ML System SHALL maintain a data collection pipeline that captures at least 20 features per trade
5. THE ML System SHALL ensure all database operations complete within 100 milliseconds

### Requirement 2: Feature Engineering

**User Story:** As a data scientist, I want comprehensive features extracted from each trade so that the ML model has rich information to learn from.

#### Acceptance Criteria

1. WHEN a trade signal is generated, THE ML System SHALL extract technical indicator features (EMA, RSI, MACD, ADX, VWAP values)
2. WHEN a trade signal is generated, THE ML System SHALL extract market regime features (regime type, breadth, volatility)
3. WHEN a trade signal is generated, THE ML System SHALL extract timing features (time of day, day of week, market session)
4. WHEN a trade signal is generated, THE ML System SHALL extract historical performance features (recent win rate, current streak)
5. THE ML System SHALL generate at least 20 distinct features for each trade
6. THE ML System SHALL normalize all features to a consistent scale (0-1 or z-score)

### Requirement 3: Model Training

**User Story:** As a trading system, I want a trained ML model that can predict trade outcomes so that I can make better trading decisions.

#### Acceptance Criteria

1. WHEN sufficient historical data exists (minimum 100 trades), THE ML System SHALL train an XGBoost binary classification model
2. WHEN training completes, THE ML System SHALL achieve a minimum accuracy of 55% on validation data
3. WHEN training completes, THE ML System SHALL store the trained model with version metadata in the database
4. THE ML System SHALL use walk-forward validation with 70% training, 15% validation, 15% test split
5. THE ML System SHALL prevent data leakage by ensuring future data never influences past predictions
6. WHEN making predictions, THE ML System SHALL complete inference within 50 milliseconds

### Requirement 4: Model Validation

**User Story:** As a system operator, I want to validate that the ML model performs well on unseen data so that I can trust its predictions.

#### Acceptance Criteria

1. WHEN validation runs, THE ML System SHALL test the model on data it has never seen during training
2. WHEN validation completes, THE ML System SHALL generate a performance report including accuracy, precision, recall, and F1 score
3. WHEN validation completes, THE ML System SHALL generate feature importance rankings
4. THE ML System SHALL achieve a minimum AUC-ROC score of 0.60 on test data
5. IF validation accuracy falls below 55%, THEN THE ML System SHALL log a warning and prevent model deployment

### Requirement 5: Volume Monitoring Exit

**User Story:** As a position manager, I want to exit positions when volume dries up so that I avoid being stuck in illiquid positions.

#### Acceptance Criteria

1. WHILE a position is open, THE Position Manager SHALL monitor current volume against entry volume
2. WHEN current volume falls below 50% of entry volume, THE Position Manager SHALL trigger an early exit
3. WHEN an early exit is triggered, THE Position Manager SHALL close the position at market price within 5 seconds
4. THE Position Manager SHALL log the exit reason as "low_volume" in the database
5. THE Position Manager SHALL track the performance impact of volume-based exits

### Requirement 6: Time-Based Exit

**User Story:** As a position manager, I want to exit positions that aren't profitable after a reasonable time so that I free up capital for better opportunities.

#### Acceptance Criteria

1. WHILE a position is open, THE Position Manager SHALL track the time elapsed since entry
2. WHEN 15 minutes have elapsed AND the position shows no profit (P/L <= 0%), THEN THE Position Manager SHALL trigger an early exit
3. WHEN a time-based exit is triggered, THE Position Manager SHALL close the position at market price within 5 seconds
4. THE Position Manager SHALL log the exit reason as "time_limit" in the database
5. THE Position Manager SHALL not apply time-based exits to positions showing any profit

### Requirement 7: Momentum Reversal Exit

**User Story:** As a position manager, I want to exit positions when momentum reverses so that I avoid giving back profits or accumulating losses.

#### Acceptance Criteria

1. WHILE a long position is open, THE Position Manager SHALL monitor for MACD bearish crossover (MACD line crosses below signal line)
2. WHILE a short position is open, THE Position Manager SHALL monitor for MACD bullish crossover (MACD line crosses above signal line)
3. WHEN a momentum reversal is detected, THE Position Manager SHALL trigger an early exit within 10 seconds
4. THE Position Manager SHALL log the exit reason as "momentum_reversal" in the database
5. THE Position Manager SHALL calculate MACD values using 12/26/9 period settings

### Requirement 8: Breakeven Stop Protection

**User Story:** As a position manager, I want to move stops to breakeven once profitable so that I protect against turning winners into losers.

#### Acceptance Criteria

1. WHILE a position is open, THE Position Manager SHALL monitor the unrealized profit/loss
2. WHEN a position reaches +1R profit (1x the initial risk), THE Position Manager SHALL move the stop loss to the entry price
3. WHEN the stop is moved to breakeven, THE Position Manager SHALL log the action in the database
4. THE Position Manager SHALL ensure the breakeven stop is only moved once per position
5. THE Position Manager SHALL account for commission costs when calculating the breakeven price

### Requirement 9: Performance Tracking

**User Story:** As a system operator, I want to track the performance impact of new features so that I can measure improvement.

#### Acceptance Criteria

1. WHEN Sprint 1 features are deployed, THE ML System SHALL track baseline performance metrics (win rate, Sharpe ratio, average P/L)
2. WHEN Sprint 1 features are active, THE ML System SHALL track performance metrics separately for ML-influenced decisions
3. WHEN Sprint 1 features are active, THE Position Manager SHALL track metrics for each exit type (volume, time, momentum, breakeven)
4. THE ML System SHALL generate a daily performance comparison report
5. THE ML System SHALL calculate the performance improvement percentage compared to baseline

### Requirement 10: System Stability

**User Story:** As a system operator, I want Sprint 1 features to integrate seamlessly so that trading operations are not disrupted.

#### Acceptance Criteria

1. WHEN Sprint 1 features are deployed, THE ML System SHALL not cause any trading interruptions
2. WHEN Sprint 1 features are active, THE ML System SHALL handle errors gracefully without crashing the trading system
3. IF an ML prediction fails, THEN THE ML System SHALL fall back to traditional signal generation
4. IF a position management feature fails, THEN THE Position Manager SHALL fall back to standard stop loss/take profit
5. THE ML System SHALL log all errors with sufficient detail for debugging

## Success Metrics

- ML model accuracy: >55% on validation data
- Position management: 10-15% reduction in average loss per trade
- System stability: Zero critical errors, 100% uptime
- Performance improvement: +5-10% overall system performance
- Feature collection: 100% of trades have complete feature vectors
- Prediction latency: <50ms per prediction

## Dependencies

- Existing trading system (Phase 1 + Phase 2 complete)
- Supabase database with trades table
- Python 3.9+ environment
- Sufficient historical trade data (minimum 100 trades)

## Constraints

- ML predictions must not add more than 50ms latency to signal generation
- Database operations must not impact real-time trading performance
- All new features must be backwards compatible with existing system
- Position management features must respect existing risk limits
- Sprint must be completed within 2 weeks (Nov 7-20, 2025)

## Out of Scope

- ML model deployment at non-zero weight (deferred to Sprint 3)
- Advanced position management features (trailing stops, scale-in) (deferred to Sprint 4+)
- Continuous learning and model retraining (deferred to Sprint 6)
- Ensemble methods and model optimization (deferred to Sprint 6)
- Daily report system (deferred to Sprint 2)
