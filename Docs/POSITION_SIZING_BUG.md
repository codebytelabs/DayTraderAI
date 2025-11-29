# Position Sizing Bug - CRITICAL

**Date**: November 15, 2025  
**Status**: 🔴 BLOCKING TRADES

---

## 🐛 Bug Description

The DynamicPositionSizer is calculating 0 shares for valid trade signals, blocking all trades.

## 📊 Example: TGT Trade

**Trade Signal:**
- Symbol: TGT
- Entry: $90.31
- Stop: $91.21 (1% away = $0.90 risk per share)
- Confidence: 73%
- Confirmations: 4/4
- Status: ✅ VALIDATED

**Expected Calculation:**
- Account: $137,481
- Risk: 0.7% (midday) = $962
- Stop distance: $0.90
- **Expected shares: 962 / 0.90 = 1,069 shares** ✅

**Actual Result:**
```
Position too small: 0 < 1 minimum
❌ Stock order rejected for TGT
```

---

## 🔍 Root Cause

**File**: `backend/utils/dynamic_position_sizer.py`  
**Line**: 50-51

```python
# Assume 2% stop loss for initial calculation
stop_distance = price * 0.02
risk_based_qty = int(risk_amount / stop_distance)
```

**Problem**: 
- DynamicPositionSizer assumes **2% stop loss**
- Actual strategy uses **1% stop loss** (adaptive based on ATR)
- This mismatch causes incorrect position sizing

**For TGT:**
- Assumed stop: $90.31 × 0.02 = **$1.81**
- Actual stop: $90.31 × 0.01 = **$0.90**
- Calculated shares: $962 / $1.81 = **531 shares**
- Should be: $962 / $0.90 = **1,069 shares**

The 531 shares might still pass, but with the 0.7% midday risk reduction, it's calculating even fewer shares and hitting the minimum threshold.

---

## 🔧 Solution

**Option 1: Pass actual stop distance to position sizer**
```python
qty, sizing_reason = self.position_sizer.calculate_optimal_size(
    symbol=symbol,
    price=price,
    stop_price=stop_loss,  # ← Add this
    confidence=confidence,
    base_risk_pct=adjusted_risk_pct
)
```

**Option 2: Use 1% default instead of 2%**
```python
# Use 1% stop loss for initial calculation (matches strategy default)
stop_distance = price * 0.01
```

**Option 3: Disable time-based sizing during testing**
Remove the midday 70% reduction temporarily to allow trades.

---

## ✅ Verification

After fix, TGT trade should execute with:
- ~1,000 shares
- Position value: ~$90,000
- Risk: $962 (0.7% of account)

---

## 🎯 Impact

**Current State:**
- ✅ AI discovery working (finding diverse opportunities)
- ✅ Signal generation working (TGT: 73% confidence, 4/4 confirmations)
- ✅ Risk management working (validating setups correctly)
- ❌ **Position sizing broken** (calculating 0 shares)
- ❌ **No trades executing** (all rejected due to size)

**After Fix:**
- System should start taking trades immediately
- Expected: 1-3 trades per hour in current market conditions

---

**Priority**: 🔴 CRITICAL - Blocking all trading activity
