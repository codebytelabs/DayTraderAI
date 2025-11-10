# Dynamic VIX-Based Regime Multipliers

## Overview

Upgraded the market regime detection system to use **dynamic, volatility-adjusted position sizing** instead of static multipliers. This aligns with professional algorithmic trading best practices.

## What Changed

### Before (Static):
```python
choppy regime = 0.5x (always)
```

### After (Dynamic):
```python
Choppy + VIX < 20  = 0.75x  # Low volatility - less risky
Choppy + VIX 20-30 = 0.5x   # Medium volatility - moderate risk
Choppy + VIX > 30  = 0.25x  # High volatility - very risky
```

## Why This Matters

### Research Findings

Based on quantitative trading research:

1. **Static multipliers are suboptimal** - They treat all choppy conditions the same
2. **Volatility matters** - Choppy + low VIX is safer than choppy + high VIX
3. **Professional traders use dynamic sizing** - Position size should scale with actual market risk
4. **Opportunity cost** - Being too conservative in low-vol choppy markets leaves money on the table

### Expected Impact

**In Low Volatility Choppy Markets (VIX < 20):**
- Old: 0.5x multiplier (too conservative)
- New: 0.75x multiplier (50% more capital deployed)
- Result: Capture more opportunities in safer conditions

**In High Volatility Choppy Markets (VIX > 30):**
- Old: 0.5x multiplier (too aggressive)
- New: 0.25x multiplier (50% less capital at risk)
- Result: Better protection during extreme volatility

## Implementation Details

### Code Location
`backend/indicators/market_regime.py`

### Key Method
```python
def _calculate_position_multiplier(self, regime: str, volatility: Dict = None) -> float:
    """
    Calculate position size multiplier based on regime and volatility.
    
    For choppy regimes, multiplier varies with VIX:
    - VIX < 20 (low vol): 0.75x
    - VIX 20-30 (medium vol): 0.5x
    - VIX > 30 (high vol): 0.25x
    """
```

### VIX Thresholds

| VIX Range | Volatility Level | Choppy Multiplier | Rationale |
|-----------|------------------|-------------------|-----------|
| < 20      | Low              | 0.75x             | Safer to trade more |
| 20-30     | Medium           | 0.5x              | Standard caution |
| > 30      | High             | 0.25x             | Extreme caution |

## Testing

Run the test suite:
```bash
python backend/test_dynamic_regime.py
```

All 8 test cases pass:
- ✅ Choppy + Low VIX (15) → 0.75x
- ✅ Choppy + Medium VIX (20) → 0.5x
- ✅ Choppy + Medium VIX (25) → 0.5x
- ✅ Choppy + Medium VIX (30) → 0.5x
- ✅ Choppy + High VIX (35) → 0.25x
- ✅ Choppy + Very High VIX (50) → 0.25x
- ✅ Broad Bullish (any VIX) → 1.5x
- ✅ Narrow Bullish (any VIX) → 0.7x

## Monitoring

Watch for these log messages:
```
📊 Choppy + Low VIX (18.5) → 0.75x multiplier
📊 Choppy + Medium VIX (25.3) → 0.5x multiplier
📊 Choppy + High VIX (35.2) → 0.25x multiplier
```

## Expected Behavior Changes

### Current Market (VIX ~20-30, Choppy):
- **No change** - Still using 0.5x multiplier
- System behavior remains the same

### If VIX Drops Below 20 (Choppy):
- **More aggressive** - 0.75x instead of 0.5x
- Will take more trades in safer conditions
- Example: 3 trades/day → 4-5 trades/day

### If VIX Spikes Above 30 (Choppy):
- **More defensive** - 0.25x instead of 0.5x
- Will take fewer, smaller trades
- Example: 3 trades/day → 1-2 trades/day

## References

Based on research from:
- Professional algorithmic trading practices
- Volatility-based position sizing frameworks
- ATR and VIX-adjusted risk management systems

## Next Steps

1. ✅ Implementation complete
2. ✅ Tests passing
3. 🔄 Monitor live performance
4. 📊 Track trade frequency changes across VIX regimes
5. 📈 Measure impact on Sharpe ratio and total returns

## Rollback Plan

If this causes issues, revert to static multiplier:
```python
'choppy': 0.5  # Static multiplier (old behavior)
```

---

**Status:** ✅ Implemented and tested
**Date:** 2025-11-11
**Version:** Sprint 6+
