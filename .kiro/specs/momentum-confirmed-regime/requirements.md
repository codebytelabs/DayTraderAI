# Requirements Document

## Introduction

This feature upgrades the existing regime-adaptive trading strategy to use momentum confirmation before adjusting position sizing - matching how professional intraday trading firms operate. Instead of simply reducing position size during extreme greed (which misses profitable momentum runs), the system will combine Fear & Greed sentiment with real-time momentum indicators to make smarter sizing decisions.

Key insight from professional trading research: Extreme greed with strong momentum = INCREASE size (ride the wave). Extreme greed with weak momentum = DECREASE size (reversal risk). This conditional approach significantly outperforms simple regime-based sizing.

## Glossary

- **Trading Bot**: The automated day trading system that executes trades on Alpaca
- **Fear & Greed Index**: A market sentiment indicator ranging from 0-100
- **Market Regime**: The current state of market sentiment (extreme_fear, fear, neutral, greed, extreme_greed)
- **Momentum Confirmation**: Real-time validation that price momentum supports the current regime's expected behavior
- **Momentum Strength**: A composite score (0-1) combining ADX, volume ratio, and trend strength indicators
- **ADX (Average Directional Index)**: Measures trend strength regardless of direction (>25 = strong trend)
- **Volume Ratio**: Current volume divided by average volume (>1.5 = elevated volume)
- **Trend Strength**: Composite score based on EMA alignment, rate of change, and higher highs pattern
- **Position Size Multiplier**: Factor applied to base position size (e.g., 1.2x = 20% larger position)
- **R-Multiple**: Risk multiple where 1R equals the initial risk amount
- **VIX**: CBOE Volatility Index measuring market volatility expectations
- **Regime Manager**: Component that detects market regime and provides trading parameters
- **Momentum Validator**: Component that calculates real-time momentum strength

## Requirements

### Requirement 1

**User Story:** As a trader, I want the bot to calculate real-time momentum strength before making position sizing decisions, so that I can distinguish between strong trending conditions and weak/reversal-prone conditions.

#### Acceptance Criteria

1. WHEN evaluating a trade signal, THE Trading Bot SHALL calculate a composite momentum strength score from 0.0 to 1.0
2. WHEN calculating momentum strength, THE Trading Bot SHALL combine ADX value, volume ratio, and trend strength with equal weighting
3. WHEN ADX exceeds 25, THE Trading Bot SHALL classify momentum as "confirmed" for that component
4. WHEN volume ratio exceeds 1.5x average, THE Trading Bot SHALL classify volume as "confirmed"
5. WHEN trend strength score exceeds 0.7, THE Trading Bot SHALL classify trend as "confirmed"

### Requirement 2

**User Story:** As a trader, I want the bot to use momentum-confirmed position sizing during extreme greed, so that I can ride strong momentum waves while protecting against reversals.

#### Acceptance Criteria

1. WHEN the market is in extreme greed AND momentum strength exceeds 0.8, THE Trading Bot SHALL apply a 1.2x position size multiplier
2. WHEN the market is in extreme greed AND momentum strength is between 0.5-0.8, THE Trading Bot SHALL apply a 0.9x position size multiplier
3. WHEN the market is in extreme greed AND momentum strength is below 0.5, THE Trading Bot SHALL apply a 0.7x position size multiplier
4. WHEN applying momentum-confirmed sizing in extreme greed, THE Trading Bot SHALL use tighter stop losses (0.5R trailing)
5. WHEN momentum is strong in extreme greed, THE Trading Bot SHALL set profit targets to 2.0-2.5R instead of the default 1.5R

### Requirement 3

**User Story:** As a trader, I want the bot to use momentum-confirmed position sizing during extreme fear, so that I can capture volatility opportunities while managing heightened risk.

#### Acceptance Criteria

1. WHEN the market is in extreme fear AND momentum strength exceeds 0.7, THE Trading Bot SHALL apply a 1.0x position size multiplier (standard)
2. WHEN the market is in extreme fear AND momentum strength is below 0.7, THE Trading Bot SHALL apply a 0.8x position size multiplier
3. WHEN in extreme fear, THE Trading Bot SHALL always use wider stop losses (1.0R trailing) regardless of momentum
4. WHEN in extreme fear with strong momentum, THE Trading Bot SHALL set profit targets to 2.0R
5. WHEN in extreme fear with weak momentum, THE Trading Bot SHALL set profit targets to 1.5R (take profits faster)

### Requirement 4

**User Story:** As a trader, I want the bot to use VIX-based position sizing adjustments, so that I can adapt to actual market volatility levels.

#### Acceptance Criteria

1. WHEN VIX is below 15 (low volatility), THE Trading Bot SHALL allow position size multipliers up to 1.2x
2. WHEN VIX is between 15-25 (normal volatility), THE Trading Bot SHALL use standard position sizing (1.0x base)
3. WHEN VIX is between 25-35 (high volatility), THE Trading Bot SHALL cap position size multipliers at 0.9x
4. WHEN VIX exceeds 35 (extreme volatility), THE Trading Bot SHALL cap position size multipliers at 0.7x
5. WHEN VIX data is unavailable, THE Trading Bot SHALL default to normal volatility parameters

### Requirement 5

**User Story:** As a trader, I want the bot to combine regime, momentum, and VIX into a single effective position multiplier, so that all factors are considered together.

#### Acceptance Criteria

1. WHEN calculating final position size, THE Trading Bot SHALL multiply regime multiplier by momentum multiplier by VIX cap
2. WHEN the combined multiplier exceeds 1.5x, THE Trading Bot SHALL cap it at 1.5x maximum
3. WHEN the combined multiplier falls below 0.5x, THE Trading Bot SHALL floor it at 0.5x minimum
4. WHEN applying the combined multiplier, THE Trading Bot SHALL log all component values for audit
5. WHEN any component data is stale (older than 1 hour), THE Trading Bot SHALL use conservative defaults

### Requirement 6

**User Story:** As a trader, I want the bot to adjust R-targets based on the momentum-confirmed regime, so that profit targets match expected price movement.

#### Acceptance Criteria

1. WHEN momentum is strong (>0.8) in any regime, THE Trading Bot SHALL increase R-targets by 0.5R
2. WHEN momentum is weak (<0.5) in any regime, THE Trading Bot SHALL decrease R-targets by 0.5R
3. WHEN in extreme greed with strong momentum, THE Trading Bot SHALL set R-target to 2.5R
4. WHEN in extreme greed with weak momentum, THE Trading Bot SHALL set R-target to 1.5R
5. WHEN in extreme fear, THE Trading Bot SHALL cap R-targets at 2.0R regardless of momentum (take profits in volatility)

### Requirement 7

**User Story:** As a trader, I want the bot to provide a momentum-confirmed regime summary, so that I can understand why specific sizing decisions were made.

#### Acceptance Criteria

1. WHEN a trade is entered, THE Trading Bot SHALL log the momentum-confirmed regime decision with all component values
2. WHEN queried via API, THE Trading Bot SHALL return current regime, momentum strength, VIX level, and effective multiplier
3. WHEN momentum confirmation changes the default regime behavior, THE Trading Bot SHALL highlight this in logs
4. WHEN generating reports, THE Trading Bot SHALL include momentum-confirmed vs simple regime performance comparison
5. WHEN momentum data is unavailable, THE Trading Bot SHALL log a warning and fall back to simple regime sizing

### Requirement 8

**User Story:** As a trader, I want the bot to validate momentum-confirmed parameters before applying them, so that the system never uses invalid settings.

#### Acceptance Criteria

1. WHEN calculating momentum strength, THE Trading Bot SHALL validate all indicator values are within expected ranges
2. WHEN ADX value is negative or exceeds 100, THE Trading Bot SHALL reject it and use default (25)
3. WHEN volume ratio is negative or exceeds 10x, THE Trading Bot SHALL reject it and use default (1.0)
4. WHEN trend strength is outside 0-1 range, THE Trading Bot SHALL clamp it to valid bounds
5. WHEN validation fails, THE Trading Bot SHALL log the error and use conservative fallback values

