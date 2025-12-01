# Requirements Document

## Introduction

This spec defines a **Data-Driven Momentum Wave Rider** strategy that replaces the slow AI-based opportunity discovery with fast, real-time market data analysis. The goal is to identify stocks that are actively trending with high volume (institutional interest) and ride the momentum wave with confidence-based position sizing.

**Key Insight**: Professional momentum traders achieve 55-65% win rates with 2:1 risk-reward ratios. The key is not a high win rate, but favorable risk-reward combined with proper position sizing.

## Glossary

- **Wave**: A sustained price movement in one direction with volume confirmation
- **Volume Surge**: Trading volume 150%+ above the 20-period average
- **Breakout**: Price moving above recent resistance with volume confirmation
- **Momentum Zone**: RSI between 40-70 (not overbought/oversold)
- **Fresh Crossover**: EMA9/EMA21 difference between 0.05% and 0.3%
- **ADX**: Average Directional Index - measures trend strength (>25 = strong)
- **R-Multiple**: Risk unit - 1R = initial risk amount
- **Confidence Score**: 0-100 score based on momentum indicators

## Requirements

### Requirement 1: Data-Driven Opportunity Discovery

**User Story:** As a trader, I want to discover trending stocks using real-time market data instead of slow AI APIs, so that I can catch momentum waves early.

#### Acceptance Criteria

1. WHEN the scanner runs THEN the system SHALL fetch top movers from Alpaca Market Data API within 2 seconds
2. WHEN fetching market data THEN the system SHALL retrieve volume, price, and technical indicators for each candidate
3. WHEN filtering candidates THEN the system SHALL only include stocks with volume 150%+ above 20-period average
4. WHEN the scanner completes THEN the system SHALL return up to 50 momentum candidates ranked by score
5. WHEN the AI opportunity finder is disabled THEN the system SHALL use the data-driven scanner as the primary discovery method

### Requirement 2: Momentum-Focused Scoring with Upside Analysis

**User Story:** As a trader, I want stocks scored based on momentum indicators AND upside potential, so that I can identify waves with both strength AND room to run.

#### Acceptance Criteria

1. WHEN scoring a candidate THEN the system SHALL calculate a momentum score from 0-100 based on technical indicators AND upside potential
2. WHEN calculating volume score (0-25 pts) THEN the system SHALL award 25 points for 200%+ volume ratio, 20 points for 150-200%, 10 points for 100-150%
3. WHEN calculating momentum score (0-20 pts) THEN the system SHALL award 12 points for ADX > 25, 8 points for RSI in momentum zone (40-70)
4. WHEN calculating breakout score (0-20 pts) THEN the system SHALL award 12 points for price above recent resistance, 8 points for fresh EMA crossover (0.05-0.3% diff)
5. WHEN calculating upside potential (0-25 pts) THEN the system SHALL award 25 points for >5% to resistance, 20 points for 3-5%, 15 points for 2-3%, 10 points for 1-2%, 0 points for <1%
6. WHEN calculating trend score (0-10 pts) THEN the system SHALL award 10 points for multi-timeframe alignment, 5 points for consistent price direction
7. WHEN a stock has RSI > 75 or RSI < 25 THEN the system SHALL reduce the score by 20 points (overbought/oversold penalty)
8. WHEN upside potential is less than 1% to resistance THEN the system SHALL reduce the score by 15 points (insufficient room penalty)

### Requirement 3: Resistance and Upside Analysis

**User Story:** As a trader, I want to know how much room a stock has to run before hitting resistance, so that I don't chase stocks at the top.

#### Acceptance Criteria

1. WHEN analyzing a candidate THEN the system SHALL identify the next major resistance level using recent highs and pivot points
2. WHEN calculating upside potential THEN the system SHALL measure distance from current price to resistance as a percentage
3. WHEN upside potential is >5% to resistance THEN the system SHALL classify as "excellent room" (25 pts)
4. WHEN upside potential is 3-5% to resistance THEN the system SHALL classify as "good room" (20 pts)
5. WHEN upside potential is 2-3% to resistance THEN the system SHALL classify as "some room" (15 pts)
6. WHEN upside potential is 1-2% to resistance THEN the system SHALL classify as "limited room" (10 pts)
7. WHEN upside potential is <1% to resistance THEN the system SHALL classify as "no room" (0 pts + 15 pt penalty)
8. WHEN risk/reward ratio is >3:1 THEN the system SHALL add 5 bonus points to upside score
9. WHEN risk/reward ratio is >2:1 THEN the system SHALL add 3 bonus points to upside score

### Requirement 4: Confidence-Based Position Sizing

**User Story:** As a trader, I want position sizes to scale with confidence level, so that I can maximize profits on high-conviction trades.

#### Acceptance Criteria

1. WHEN confidence score is 90+ THEN the system SHALL use 15% of equity as maximum position size
2. WHEN confidence score is 80-89 THEN the system SHALL use 12% of equity as maximum position size
3. WHEN confidence score is 70-79 THEN the system SHALL use 10% of equity as maximum position size
4. WHEN confidence score is 60-69 THEN the system SHALL use 8% of equity as maximum position size
5. WHEN confidence score is below 60 THEN the system SHALL skip the trade
6. WHEN volume is confirmed (150%+ average) THEN the system SHALL add 2% bonus to position size (up to max 15%)

### Requirement 5: Wave Entry Timing

**User Story:** As a trader, I want to enter trades at optimal momentum points, so that I can catch waves early rather than chasing extended moves.

#### Acceptance Criteria

1. WHEN EMA crossover difference is 0.05-0.3% THEN the system SHALL classify it as a "fresh crossover" (ideal entry)
2. WHEN EMA crossover difference is > 1% THEN the system SHALL classify it as "extended" and reduce confidence by 15 points
3. WHEN price is within 0.5% of VWAP THEN the system SHALL add 5 points to confidence (good entry point)
4. WHEN ADX is below 20 THEN the system SHALL skip the trade (choppy market)
5. WHEN multiple timeframes show aligned momentum THEN the system SHALL add 10 points to confidence

### Requirement 6: Profit Protection and Exit Strategy

**User Story:** As a trader, I want to lock in profits while letting winners run, so that I can maximize gains on successful trades.

#### Acceptance Criteria

1. WHEN a position reaches 2R profit THEN the system SHALL take 50% partial profit
2. WHEN partial profit is taken THEN the system SHALL move stop loss to breakeven on remaining position
3. WHEN a position reaches 3R profit THEN the system SHALL tighten trailing stop to 1R
4. WHEN RSI divergence is detected (price up, RSI down) THEN the system SHALL exit the position
5. WHEN momentum loss is detected (ADX drops below 20) THEN the system SHALL tighten stop to 0.5R

### Requirement 7: Risk Management

**User Story:** As a trader, I want strict risk controls to protect capital, so that losses are limited and recoverable.

#### Acceptance Criteria

1. WHEN entering a trade THEN the system SHALL set stop loss at minimum 1.5% from entry (or 1.5-2 ATR)
2. WHEN calculating risk THEN the system SHALL limit risk to 1% of equity per trade
3. WHEN daily loss reaches 2% of equity THEN the system SHALL pause trading for the day
4. WHEN 3 consecutive losses occur THEN the system SHALL reduce position sizes by 50% for next 3 trades
5. WHEN a position is opened THEN the system SHALL always have a stop loss order active

### Requirement 8: Scanner Refresh Rate

**User Story:** As a trader, I want frequent momentum scans, so that I can catch new waves as they develop.

#### Acceptance Criteria

1. WHEN market is open THEN the system SHALL run momentum scan every 5 minutes
2. WHEN a high-confidence opportunity (score 85+) is found THEN the system SHALL alert immediately
3. WHEN the first 60 minutes of market open THEN the system SHALL scan every 2 minutes (highest predictability period)
4. WHEN market is closed THEN the system SHALL not run scans

### Requirement 9: Performance Targets

**User Story:** As a trader, I want the system to achieve consistent profitability, so that I can grow my account over time.

#### Acceptance Criteria

1. WHEN measuring performance THEN the system SHALL target 55-65% win rate
2. WHEN measuring risk-reward THEN the system SHALL target minimum 2:1 average R/R ratio
3. WHEN measuring expectancy THEN the system SHALL target +0.5R per trade average
4. WHEN a trade is closed THEN the system SHALL log the R-multiple achieved for performance tracking
