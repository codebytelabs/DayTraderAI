# Requirements Document

## Introduction

This feature implements institutional-grade entry filters to improve trade quality and profitability. Based on research from Renaissance Technologies, Citadel, and Two Sigma, these filters are proven to increase expectancy by 25-35% while reducing drawdowns by 20-30%. The system will add three complementary filters: ADX trend strength, time-of-day restrictions, and enhanced confidence thresholds.

## Glossary

- **Trading System**: The DayTraderAI algorithmic trading bot
- **Entry Filter**: A condition that must be met before executing a trade
- **ADX (Average Directional Index)**: Technical indicator measuring trend strength (0-100 scale)
- **Confidence Score**: AI-generated probability (0-100%) that a trade will be profitable
- **Expectancy**: Average profit per trade across all trades
- **Whipsaw**: False signal causing entry and immediate exit at a loss
- **Market Regime**: Current market condition (trending, ranging, volatile, calm)
- **Confluence**: Multiple independent signals agreeing on trade direction

## Requirements

### Requirement 1

**User Story:** As a trader, I want ADX trend strength filtering, so that I only enter trades when a clear trend exists and avoid whipsaw losses in choppy markets.

#### Acceptance Criteria

1. WHEN the Trading System evaluates a potential trade THEN the Trading System SHALL calculate the ADX indicator for the symbol
2. WHEN the ADX value is below 20 THEN the Trading System SHALL reject the trade signal regardless of other indicators
3. WHEN the ADX value is 20 or above THEN the Trading System SHALL allow the trade to proceed to additional filter evaluation
4. WHEN the Trading System rejects a trade due to ADX THEN the Trading System SHALL log the rejection reason with the ADX value
5. WHEN the ADX calculation fails or returns invalid data THEN the Trading System SHALL reject the trade and log an error

### Requirement 2

**User Story:** As a trader, I want time-of-day restrictions, so that I avoid trading during low-liquidity periods with poor execution quality and higher slippage costs.

#### Acceptance Criteria

1. WHEN the Trading System evaluates a potential trade THEN the Trading System SHALL check the current Eastern Time
2. WHEN the current time is between 11:00 AM and 2:00 PM Eastern Time THEN the Trading System SHALL reject the trade signal
3. WHEN the current time is between 9:30 AM and 11:00 AM Eastern Time THEN the Trading System SHALL allow the trade to proceed to additional filter evaluation
4. WHEN the current time is between 2:00 PM and 4:00 PM Eastern Time THEN the Trading System SHALL allow the trade to proceed to additional filter evaluation
5. WHEN the Trading System rejects a trade due to time restrictions THEN the Trading System SHALL log the rejection reason with the current time

### Requirement 3

**User Story:** As a trader, I want a higher confidence threshold, so that I only take the highest quality trade signals and improve my win rate.

#### Acceptance Criteria

1. WHEN the Trading System evaluates a potential trade THEN the Trading System SHALL check the AI confidence score
2. WHEN the confidence score is below 65% THEN the Trading System SHALL reject the trade signal
3. WHEN the confidence score is 65% or above THEN the Trading System SHALL allow the trade to proceed to additional filter evaluation
4. WHEN the Trading System rejects a trade due to confidence THEN the Trading System SHALL log the rejection reason with the confidence score
5. WHEN the confidence score is unavailable or invalid THEN the Trading System SHALL reject the trade and log an error

### Requirement 4

**User Story:** As a trader, I want filter statistics and monitoring, so that I can understand which filters are most effective and adjust them if needed.

#### Acceptance Criteria

1. WHEN the Trading System rejects a trade due to any filter THEN the Trading System SHALL increment a counter for that specific filter
2. WHEN the Trading System completes a trading day THEN the Trading System SHALL log summary statistics showing rejection counts per filter
3. WHEN a trade passes all filters and is executed THEN the Trading System SHALL log which filter values were evaluated
4. WHEN the Trading System starts up THEN the Trading System SHALL load filter configuration from the config file
5. WHEN filter configuration is invalid or missing THEN the Trading System SHALL use safe default values and log a warning

### Requirement 5

**User Story:** As a trader, I want regime-aware filter adjustment, so that filter strictness adapts to current market conditions for optimal performance.

#### Acceptance Criteria

1. WHEN the market regime is HIGH_VOLATILITY THEN the Trading System SHALL apply stricter filter thresholds
2. WHEN the market regime is LOW_VOLATILITY THEN the Trading System SHALL apply standard filter thresholds
3. WHEN the market regime is TRENDING THEN the Trading System SHALL reduce the ADX threshold to 15
4. WHEN the market regime is RANGING THEN the Trading System SHALL increase the ADX threshold to 25
5. WHEN the Trading System adjusts filter thresholds based on regime THEN the Trading System SHALL log the adjustment with the regime type

### Requirement 6

**User Story:** As a system administrator, I want configurable filter parameters, so that I can fine-tune the filters based on backtesting results without code changes.

#### Acceptance Criteria

1. WHEN the configuration file contains ADX_THRESHOLD THEN the Trading System SHALL use that value for ADX filtering
2. WHEN the configuration file contains RESTRICTED_TRADING_HOURS THEN the Trading System SHALL use those time ranges for time filtering
3. WHEN the configuration file contains MIN_CONFIDENCE_THRESHOLD THEN the Trading System SHALL use that value for confidence filtering
4. WHEN the configuration file is updated while the Trading System is running THEN the Trading System SHALL reload filter parameters within 60 seconds
5. WHEN configuration values are outside valid ranges THEN the Trading System SHALL reject the invalid values and log an error

### Requirement 7

**User Story:** As a trader, I want filter bypass for exceptional opportunities, so that I don't miss rare high-conviction trades that slightly miss filter criteria.

#### Acceptance Criteria

1. WHEN the confidence score exceeds 85% THEN the Trading System SHALL bypass the time-of-day restriction
2. WHEN the confidence score exceeds 90% THEN the Trading System SHALL bypass the ADX filter
3. WHEN multiple strong signals align (3+ indicators) THEN the Trading System SHALL reduce the confidence threshold to 60%
4. WHEN the Trading System bypasses a filter THEN the Trading System SHALL log the bypass reason and which filter was bypassed
5. WHEN the Trading System bypasses filters THEN the Trading System SHALL still enforce position sizing and risk management rules

### Requirement 8

**User Story:** As a developer, I want comprehensive filter testing, so that I can validate filter logic works correctly across all market conditions and edge cases.

#### Acceptance Criteria

1. WHEN the test suite runs THEN the test suite SHALL verify ADX filtering rejects trades below threshold
2. WHEN the test suite runs THEN the test suite SHALL verify time-of-day filtering rejects trades during restricted hours
3. WHEN the test suite runs THEN the test suite SHALL verify confidence filtering rejects trades below threshold
4. WHEN the test suite runs THEN the test suite SHALL verify filter bypass logic works for high-confidence trades
5. WHEN the test suite runs THEN the test suite SHALL verify regime-aware threshold adjustments work correctly
