# Requirements Document

## Introduction

This feature implements a regime-adaptive trading strategy that dynamically adjusts position sizing, profit targets, partial profit levels, and risk management based on real-time market conditions. The system will optimize performance across all market regimes (extreme fear, fear, neutral, greed, extreme greed) by adapting trading parameters to match the expected volatility and directional strength of each regime.

## Glossary

- **Trading Bot**: The automated day trading system that executes trades on Alpaca
- **Fear & Greed Index**: A market sentiment indicator ranging from 0-100, where 0-20 is extreme fear, 21-40 is fear, 41-60 is neutral, 61-80 is greed, and 81-100 is extreme greed
- **Market Regime**: The current state of market sentiment and volatility as determined by the Fear & Greed Index
- **R-Multiple**: Risk multiple, where 1R equals the initial risk amount (e.g., 2R means 2x the initial risk as profit)
- **Position Size**: The dollar amount or percentage of capital allocated to a single trade
- **Profit Target**: The price level at which the system will automatically close a position to lock in gains
- **Partial Profit**: Taking profits on a portion of the position while leaving the remainder open
- **Trailing Stop**: A dynamic stop loss that moves with the price to protect profits
- **Confidence Score**: A numerical assessment (0-100) of trade signal quality based on technical indicators and AI analysis
- **Risk Manager**: The component responsible for calculating position sizes and managing trade risk
- **Position Manager**: The component responsible for managing open positions, including profit targets and stop losses
- **Strategy Module**: The component that generates trading signals and determines entry/exit logic

## Requirements

### Requirement 1

**User Story:** As a trader, I want the bot to dynamically adjust profit targets based on market regime, so that I can capture larger moves in trending markets and protect profits in choppy markets.

#### Acceptance Criteria

1. WHEN the Fear & Greed Index is below 20 (extreme fear), THE Trading Bot SHALL set profit targets to 4R minimum
2. WHEN the Fear & Greed Index is between 21-40 (fear), THE Trading Bot SHALL set profit targets to 3R minimum
3. WHEN the Fear & Greed Index is between 41-60 (neutral), THE Trading Bot SHALL set profit targets to 2R
4. WHEN the Fear & Greed Index is between 61-80 (greed), THE Trading Bot SHALL set profit targets to 2.5R
5. WHEN the Fear & Greed Index is above 80 (extreme greed), THE Trading Bot SHALL set profit targets to 3R minimum

### Requirement 2

**User Story:** As a trader, I want the bot to adjust position sizing based on signal confidence and market regime, so that I can maximize returns on high-probability setups while managing risk appropriately.

#### Acceptance Criteria

1. WHEN a trade signal has confidence above 70% AND the market is in extreme fear or extreme greed, THE Trading Bot SHALL increase position size to 1.5% of capital
2. WHEN a trade signal has confidence between 50-70%, THE Trading Bot SHALL use standard position size of 1.0% of capital
3. WHEN a trade signal has confidence below 50%, THE Trading Bot SHALL reduce position size to 0.5% of capital OR skip the trade
4. WHEN calculating position size, THE Trading Bot SHALL ensure the total does not exceed maximum portfolio risk limits
5. WHEN market volatility (VIX) exceeds 30, THE Trading Bot SHALL reduce all position sizes by 25% regardless of confidence

### Requirement 3

**User Story:** As a trader, I want the bot to adjust partial profit levels based on market regime, so that I can let winners run in strong trending markets while securing profits incrementally in normal conditions.

#### Acceptance Criteria

1. WHEN the market is in extreme fear (0-20), THE Trading Bot SHALL take first partial profit at 3R and second partial at 5R
2. WHEN the market is in fear (21-40), THE Trading Bot SHALL take first partial profit at 2.5R and second partial at 4R
3. WHEN the market is neutral (41-60), THE Trading Bot SHALL take first partial profit at 2R and second partial at 3R
4. WHEN the market is in greed (61-80), THE Trading Bot SHALL take first partial profit at 2R and second partial at 3.5R
5. WHEN the market is in extreme greed (81-100), THE Trading Bot SHALL take first partial profit at 2.5R and second partial at 4.5R

### Requirement 4

**User Story:** As a trader, I want the bot to implement trailing stops that adapt to market regime, so that I can protect profits while allowing room for normal price fluctuations in each regime.

#### Acceptance Criteria

1. WHEN a position reaches 2R profit in any regime, THE Trading Bot SHALL activate a trailing stop
2. WHEN the market is in extreme fear or extreme greed, THE Trading Bot SHALL set trailing stop distance to 1.5R from peak
3. WHEN the market is in fear or greed, THE Trading Bot SHALL set trailing stop distance to 1R from peak
4. WHEN the market is neutral, THE Trading Bot SHALL set trailing stop distance to 0.75R from peak
5. WHEN a trailing stop is triggered, THE Trading Bot SHALL close the entire remaining position

### Requirement 5

**User Story:** As a trader, I want the bot to tighten initial stop losses to improve risk/reward ratios, so that I can reduce average loss size while maintaining win rate.

#### Acceptance Criteria

1. WHEN entering a new position, THE Trading Bot SHALL calculate stop loss based on recent volatility (ATR)
2. WHEN the calculated stop loss exceeds 1% of entry price, THE Trading Bot SHALL cap it at 1% maximum
3. WHEN the calculated stop loss is below 0.3% of entry price, THE Trading Bot SHALL set it to 0.3% minimum
4. WHEN market volatility (VIX) is above 25, THE Trading Bot SHALL increase stop loss distance by 25%
5. WHEN a stop loss is hit, THE Trading Bot SHALL record the loss amount and update risk metrics

### Requirement 6

**User Story:** As a trader, I want the bot to skip low-confidence trades entirely, so that I can focus capital on the highest probability setups and improve overall win rate.

#### Acceptance Criteria

1. WHEN a trade signal has confidence below 40%, THE Trading Bot SHALL reject the trade and log the reason
2. WHEN a trade signal has confidence between 40-50%, THE Trading Bot SHALL require at least 2 confirming indicators before entry
3. WHEN rejecting a low-confidence trade, THE Trading Bot SHALL store the signal for performance tracking
4. WHEN market conditions improve, THE Trading Bot SHALL re-evaluate previously rejected signals
5. WHEN tracking rejected signals, THE Trading Bot SHALL calculate what the outcome would have been for learning purposes

### Requirement 7

**User Story:** As a trader, I want the bot to scale into winning positions in strong trending markets, so that I can maximize profits on the best setups.

#### Acceptance Criteria

1. WHEN a position reaches 1.5R profit AND confidence was above 70% AND market is in extreme fear or extreme greed, THE Trading Bot SHALL add 50% to the position size
2. WHEN adding to a position, THE Trading Bot SHALL move the stop loss to breakeven on the original entry
3. WHEN adding to a position, THE Trading Bot SHALL ensure total position size does not exceed 2.5% of capital
4. WHEN the added position reaches 1R profit, THE Trading Bot SHALL move stop to breakeven on the add
5. WHEN scaling into positions, THE Trading Bot SHALL track average entry price and adjust profit targets accordingly

### Requirement 8

**User Story:** As a trader, I want the bot to persist regime-adaptive settings across restarts, so that the system maintains consistent behavior and can be audited.

#### Acceptance Criteria

1. WHEN regime parameters are calculated, THE Trading Bot SHALL store them in the configuration system
2. WHEN the bot restarts, THE Trading Bot SHALL load the most recent regime parameters
3. WHEN regime parameters change, THE Trading Bot SHALL log the old and new values with timestamp
4. WHEN queried, THE Trading Bot SHALL provide current regime settings via API endpoint
5. WHEN regime settings are updated, THE Trading Bot SHALL apply them to new trades immediately without affecting existing positions

### Requirement 9

**User Story:** As a trader, I want comprehensive logging of regime-adaptive decisions, so that I can analyze performance and understand why the bot made specific choices.

#### Acceptance Criteria

1. WHEN a trade is entered, THE Trading Bot SHALL log the current regime, confidence score, position size, and all target levels
2. WHEN profit targets are adjusted, THE Trading Bot SHALL log the reason, old values, and new values
3. WHEN a trade is rejected due to low confidence, THE Trading Bot SHALL log the signal details and rejection reason
4. WHEN partial profits are taken, THE Trading Bot SHALL log the regime, R-multiple achieved, and remaining position size
5. WHEN generating daily reports, THE Trading Bot SHALL include regime-specific performance metrics for each market condition

### Requirement 10

**User Story:** As a trader, I want the bot to validate regime-adaptive parameters before applying them, so that the system never uses invalid or dangerous settings.

#### Acceptance Criteria

1. WHEN calculating position size, THE Trading Bot SHALL validate it does not exceed 2.5% of capital for any single trade
2. WHEN setting profit targets, THE Trading Bot SHALL validate they are at least 1.5R and not more than 10R
3. WHEN setting stop losses, THE Trading Bot SHALL validate they are between 0.3% and 2% of entry price
4. WHEN parameters fail validation, THE Trading Bot SHALL use safe default values and log an error
5. WHEN applying regime changes, THE Trading Bot SHALL verify the Fear & Greed Index is current (less than 1 hour old)
