# Momentum-Confirmed Regime System - Quick Start

## Overview

This system upgrades your trading bot to use **professional intraday position sizing** by combining:
1. **Fear & Greed Index** (market sentiment)
2. **Momentum Strength** (ADX, volume, trend)
3. **VIX Caps** (volatility-based limits)

## Key Insight from Research

**Extreme greed doesn't always mean reduce size!**

| Regime | Momentum | Position Size | Why |
|--------|----------|---------------|-----|
| Extreme Greed | Strong (>0.8) | **1.2x** | Ride the wave |
| Extreme Greed | Medium (0.5-0.8) | 0.9x | Cautious |
| Extreme Greed | Weak (<0.5) | **0.7x** | Reversal risk |
| Extreme Fear | Strong (>0.7) | 1.0x | Standard |
| Extreme Fear | Weak (<=0.7) | 0.8x | Conservative |

## Files Created

```
backend/trading/
├── momentum_strength.py          # Calculates momentum score (0-1)
├── vix_provider.py               # VIX data with caching
├── momentum_confirmed_regime.py  # Main manager combining all factors
└── regime_manager.py             # Updated with momentum integration

backend/tests/
└── test_momentum_confirmed_regime_properties.py  # 15 property-based tests

backend/
└── verify_momentum_confirmed_regime.py  # Verification script
```

## Usage

### 1. Get Momentum-Confirmed Multiplier

```python
from trading.regime_manager import RegimeManager

regime_manager = RegimeManager(enable_momentum_confirmation=True)

# Get multiplier with momentum confirmation
multiplier = regime_manager.get_momentum_confirmed_multiplier(
    momentum_strength=0.8,  # From your momentum indicators
    confidence=80           # Signal confidence
)
# Returns: 1.15x (combines regime, momentum, VIX, and confidence)
```

### 2. Get Adjusted Trading Parameters

```python
params = regime_manager.get_momentum_adjusted_params(momentum_strength=0.8)
# Returns:
# {
#     "profit_target_r": 2.5,    # Boosted for strong momentum
#     "trailing_stop_r": 0.5,    # Tight for extreme greed
#     "position_size_mult": 1.2,
#     ...
# }
```

### 3. API Endpoint

```bash
curl http://localhost:8000/regime/status
```

Returns current regime, momentum strength, VIX level, and effective multiplier.

## Verification

```bash
cd backend
python verify_momentum_confirmed_regime.py
```

## Tests

```bash
cd backend
python -m pytest tests/test_momentum_confirmed_regime_properties.py -v
```

All 15 property-based tests verify the correctness properties from the design document.

## Position Sizing Logic Summary

```
Final Multiplier = Regime_Mult × Momentum_Mult × VIX_Cap × Confidence_Mult
                   (bounded to 0.5x - 1.5x)
```

### VIX Caps
- VIX < 15: Allow up to 1.2x
- VIX 15-25: Standard 1.0x
- VIX 25-35: Cap at 0.9x
- VIX > 35: Cap at 0.7x

### R-Target Adjustments
- Strong momentum: +0.5R
- Weak momentum: -0.5R
- Extreme fear: capped at 2.0R

### Trailing Stops
- Extreme greed + strong momentum: 0.5R (tight)
- Extreme fear: 1.0R (wide)
