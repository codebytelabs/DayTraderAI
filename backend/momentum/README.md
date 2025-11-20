# Momentum-Based Bracket Adjustment System

## Overview

This system intelligently extends profit targets and moves stop losses when strong momentum is detected, helping capture larger wins while protecting profits.

## What We've Built

### ✅ Completed (Task 1)

1. **API Error Fix** - Enhanced `position_manager.py` with:
   - Better order cancellation before closing positions
   - Retry logic for "insufficient qty available" errors
   - Force cleanup for stuck positions
   - Prevents the AAPL/CRWD API errors you were seeing

2. **Momentum Infrastructure** - Complete foundation:
   - `config.py` - Configuration with validation
   - `signals.py` - Data models for signals and positions
   - `indicators.py` - ADX, volume, trend strength, ATR calculators
   - `validator.py` - Combines indicators to make decisions
   - `engine.py` - Handles Alpaca API calls to adjust brackets

## How It Works

### Detection Flow

```
Position at +0.75R
    ↓
Evaluate Momentum
    ↓
Check 3 Indicators:
  • ADX > 25 (trending market)
  • Volume > 1.5x average
  • Trend Strength > 0.7
    ↓
All Pass? → EXTEND TARGET
    ↓
Adjust Brackets:
  • Target: +2R → +3R
  • Stop: Entry → BE + 0.5R
```

### Key Features

- **Conservative by default** - Disabled until you enable it
- **Multiple indicators** - ADX, volume, trend strength all must agree
- **Progressive stops** - Moves stop to breakeven + 0.5R to protect profits
- **ATR trailing** - Optional ATR-based trailing stops
- **One-time adjustment** - Only adjusts once per position

## Quick Start

### 1. Basic Usage

```python
from momentum import MomentumConfig, BracketAdjustmentEngine

# Create config (disabled by default)
config = MomentumConfig.default_conservative()

# Initialize engine
engine = BracketAdjustmentEngine(
    alpaca_client=alpaca,
    config=config
)

# Evaluate a position
signal = engine.evaluate_and_adjust(
    symbol='AAPL',
    entry_price=150.00,
    current_price=151.50,  # +0.75R profit
    stop_loss=148.00,
    take_profit=154.00,
    quantity=100,
    side='long',
    market_data={
        'high': [...],  # Last 50+ bars
        'low': [...],
        'close': [...],
        'volume': [...]
    }
)

if signal and signal.extend:
    print(f"🎯 Extended target for {symbol}!")
```

### 2. Enable the System

```python
# Start conservative
config = MomentumConfig(
    enabled=True,  # Turn it on
    adx_threshold=30.0,  # Higher = fewer signals
    volume_threshold=1.8,
    trend_threshold=0.75
)
```

### 3. Integration Points

The system needs to be called from your trading engine when:
- Position reaches +0.75R profit (configurable)
- You have fresh market data (OHLCV)
- Position hasn't been adjusted yet

## Configuration Options

### Conservative (Recommended Start)
```python
config = MomentumConfig.default_conservative()
# ADX > 30, Volume > 1.8x, Trend > 0.75
# Fewer signals, higher quality
```

### Aggressive (After Validation)
```python
config = MomentumConfig.default_aggressive()
# ADX > 25, Volume > 1.5x, Trend > 0.7
# More signals, standard quality
```

### Custom
```python
config = MomentumConfig(
    enabled=True,
    adx_threshold=28.0,
    volume_threshold=1.6,
    trend_threshold=0.72,
    extended_target_r=3.5,  # How far to extend
    progressive_stop_r=0.75,  # Where to move stop
    use_atr_trailing=True,
    atr_trailing_multiplier=2.0
)
```

## Next Steps

### Task 2: Integrate with Trading Engine

You'll need to:
1. Add momentum engine to your trading engine initialization
2. Call `evaluate_and_adjust()` when positions reach +0.75R
3. Fetch market data (OHLCV) for evaluation
4. Handle the adjustment results

### Task 3: Testing

Before going live:
1. Backtest on historical trades
2. Run in shadow mode (log decisions without executing)
3. Validate the extension rate is 20-40%
4. Monitor for API errors

## API Error Fix

The position manager now handles:
- ✅ Cancels all orders before closing positions
- ✅ Retries on "insufficient qty available" errors
- ✅ Force cleanup for stuck positions
- ✅ Better error logging

This should fix the AAPL/CRWD issues you were seeing.

## Files Created

```
backend/momentum/
├── __init__.py          # Package exports
├── config.py            # Configuration with validation
├── signals.py           # Data models
├── indicators.py        # Technical calculations
├── validator.py         # Momentum decision logic
├── engine.py            # Bracket adjustment API calls
└── README.md            # This file
```

## Example Output

```
📊 Momentum Signal - AAPL | 🎯 EXTEND TARGET
   Profit: +0.85R
   ADX: 32.5 ✅
   Volume: 2.1x ✅
   Trend: 0.78 ✅
   Reason: Strong momentum detected

🎯 Adjusting brackets for AAPL
New levels for AAPL:
  Target: $154.00 → $156.00 (+3.0R)
  Stop: $148.00 → $151.00 (BE + 0.5R)

✅ Successfully adjusted brackets for AAPL
```

## Safety Features

- **Disabled by default** - Must explicitly enable
- **Data freshness check** - Rejects stale data
- **One adjustment per position** - Won't over-adjust
- **Validation on all indicators** - All must pass
- **API retry logic** - Handles transient errors
- **Force cleanup** - Prevents stuck positions

## Questions?

Check the design doc at `.kiro/specs/momentum-bracket-adjustment/design.md` for detailed architecture and decision rationale.
