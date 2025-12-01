# Momentum Wave Rider Strategy Guide

## Overview

The Momentum Wave Rider is a data-driven trading strategy that replaces slow AI discovery with fast market data analysis. It identifies momentum waves in real-time and provides confidence-based position sizing.

## Key Features

### 1. Momentum Scanner
- Scans for top movers using Alpaca Market Data API
- Filters by volume surge (150%+ of 20-period average)
- Scores candidates 0-100 based on multiple factors
- Refreshes every 5 minutes (2 minutes in first hour)

### 2. Scoring System (0-100 points)
- **Volume Score (0-25 pts)**: Institutional interest indicator
  - 200%+ volume: 25 pts
  - 150-200%: 20 pts
  - 100-150%: 10 pts
- **Momentum Score (0-20 pts)**: ADX + RSI analysis
- **Breakout Score (0-20 pts)**: Price vs resistance, EMA crossover freshness
- **Upside Potential (0-25 pts)**: Room to run to resistance
- **Trend Score (0-10 pts)**: Multi-timeframe alignment

### 3. Penalties Applied
- Overbought/Oversold (RSI > 75 or < 25): -20 pts
- Extended Move (EMA diff > 1%): -15 pts
- Insufficient Room (<1% to resistance): -15 pts

### 4. Confidence-Based Position Sizing
| Confidence | Max Position | Description |
|------------|--------------|-------------|
| 90-100     | 15%          | Ultra-high confidence |
| 80-89      | 12%          | High confidence |
| 70-79      | 10%          | Medium confidence |
| 60-69      | 8%           | Low confidence |
| <60        | Skip         | Do not trade |

### 5. Wave Entry Timing
- **Fresh Crossover (0.05-0.3%)**: Ideal entry, +5 bonus
- **Developing (0.3-1.0%)**: Good entry
- **Extended (>1%)**: Skip, -15 penalty
- **VWAP Proximity (<0.5%)**: +5 bonus
- **Multi-TF Alignment**: +10 bonus

## Risk Management

### Stop Loss Rules
- **Minimum Stop Distance**: 1.5% (enforced)
- **Max Risk Per Trade**: 1% of equity
- **Daily Loss Circuit Breaker**: 2% triggers halt

### Consecutive Loss Protection
- After 3 consecutive losses: Position sizes reduced by 50%
- Win resets the counter

## Configuration

Add to `backend/config.py` or `.env`:

```python
# Enable Momentum Scanner (instead of AI discovery)
USE_MOMENTUM_SCANNER=True

# Scan Intervals
MOMENTUM_SCAN_INTERVAL=300  # 5 minutes
FIRST_HOUR_SCAN_INTERVAL=120  # 2 minutes (9:30-10:30 AM)

# Thresholds
MOMENTUM_MIN_SCORE=60.0
MOMENTUM_HIGH_CONFIDENCE_THRESHOLD=85.0
```

## Expected Performance Metrics

Based on the strategy design:
- **Win Rate Target**: 55-65%
- **Average R-Multiple**: 1.5-2.0R
- **Risk/Reward Ratio**: 2:1 minimum
- **Max Drawdown**: <5% (with circuit breaker)

## Property-Based Tests

All correctness properties are validated with 100+ test iterations:

1. **Volume Filter Correctness** (Property 1)
2. **Score Range Invariant** (Property 2)
3. **Volume Score Calculation** (Property 3)
4. **Overbought/Oversold Penalty** (Property 5)
5. **Position Size Tiers** (Property 6)
6. **Low Confidence Skip** (Property 7)
7. **Volume Bonus Cap** (Property 8)
8. **Fresh Crossover Classification** (Property 9)
9. **Extended Crossover Penalty** (Property 10)
10. **ADX Filter** (Property 11)
11. **Minimum Stop Distance** (Property 14)
12. **Risk Per Trade Limit** (Property 15)
13. **Stop Loss Invariant** (Property 16)
14. **R-Multiple Logging** (Property 17)
15. **Upside Potential Scoring** (Property 18)
16. **Insufficient Room Penalty** (Property 19)

## Files Created

- `backend/scanner/momentum_scanner.py` - Main scanner
- `backend/scanner/momentum_scorer.py` - Scoring system
- `backend/scanner/momentum_models.py` - Data models
- `backend/scanner/resistance_analyzer.py` - Support/resistance analysis
- `backend/utils/confidence_sizer.py` - Position sizing
- `backend/trading/wave_entry.py` - Entry timing
- `backend/tests/test_*_properties.py` - Property tests

## Usage

1. Set `USE_MOMENTUM_SCANNER=True` in config
2. Restart trading engine
3. Monitor logs for "🌊 Momentum Wave Rider" messages
4. High-confidence alerts (85+) appear as "🔥 HIGH CONFIDENCE ALERT"

## Troubleshooting

- **No candidates found**: Market may be quiet, check volume thresholds
- **All candidates penalized**: Market may be overbought, wait for pullback
- **Position sizes too small**: Check consecutive loss counter, may need reset
