# 🚨 EMERGENCY FIXES NEEDED

## Critical Issues Identified (Nov 20, 2025 23:09)

### 1. NFLX Stop-Loss Wash Trade Error ❌
**Problem:** NFLX has take-profit order blocking stop-loss creation
```
🚨 NFLX has NO ACTIVE STOP LOSS
potential wash trade detected. use complex orders
opposite side limit order exists
```

**Impact:** NFLX position has NO protection - could lose all gains

**Fix:** Cancel conflicting orders and recreate proper bracket

---

### 2. Partial Profits Completely Blocked ❌
**Problem:** Stop-loss orders hold ALL shares, blocking partial profit taking
```
🎯 Taking partial profits for META: 11/23 shares at +5.46R
❌ insufficient qty available for order (held_for_orders: 23)

🎯 Taking partial profits for TSLA: 16/32 shares at +1.68R
❌ insufficient qty available for order (held_for_orders: 32)

🎯 Taking partial profits for AMD: 29/59 shares at +1.33R
❌ insufficient qty available for order (held_for_orders: 59)
```

**Impact:** Cannot lock in profits as positions move up

**Root Cause:** Stop-loss orders reserve ALL shares, preventing partial sells

**Fix:** Need to:
1. Cancel stop-loss before partial profit
2. Take partial profit
3. Recreate stop-loss for remaining shares

---

### 3. Momentum System Data Fetching Broken ❌
**Problem:** `_fetch_market_data_for_momentum()` fails to get bars
```
📊 Evaluating momentum for META at +1.29R
⚠️ No bars response for META

📊 Evaluating momentum for TSLA at +1.68R
⚠️ No bars response for TSLA
```

**Impact:** Trailing stops cannot adjust, profits given back

**Root Cause:** DataFrame check fails - `if barset is None or len(barset) == 0` doesn't work for empty DataFrames

**Fix:** Proper DataFrame empty check:
```python
if barset is None or barset.empty or len(barset) == 0:
    logger.warning(f"No bars response for {symbol}")
    return None
```

---

### 4. TSLA Profit Loss Example 💸
**Timeline:**
- Peak: $400+ profit (user saw this)
- Current: $250 profit
- **Loss: $150+ profit given back!**

**Why Protection Failed:**
1. ❌ Partial profits blocked by stop-loss
2. ❌ Trailing stops can't update (momentum broken)
3. ❌ Take-profit set too high, never triggered
4. ❌ No manual intervention

**What Should Have Happened:**
```
TSLA at +$400:
✅ Trailing stop moves to ~$350 profit level
✅ Partial profits lock in $200
✅ When price drops, stop triggers at $350, not $250
Result: $350 profit instead of $250 = $100 saved!
```

---

## Immediate Actions Required

### Priority 1: Fix NFLX (CRITICAL - No Protection)
```bash
python backend/emergency_fix_order_conflicts.py
```

### Priority 2: Fix Momentum Data Fetching
Edit `backend/trading/trading_engine.py` line 952:
```python
# BEFORE (BROKEN):
if barset is None or len(barset) == 0:

# AFTER (FIXED):
if barset is None or barset.empty or len(barset) == 0:
```

### Priority 3: Enable Partial Profit Taking
Need to modify `position_manager.py` to:
1. Temporarily cancel stop-loss
2. Execute partial profit
3. Recreate stop-loss for remaining shares

---

## Long-Term Solution

Replace current order management with proper bracket order modification:

**Current (Broken):**
```
Stop-loss holds ALL shares → Blocks everything
```

**Should Be:**
```
Bracket order (stop + take-profit) → Can modify → Can take partials
```

This requires using Alpaca's bracket order modification API instead of cancel/recreate.

---

## Files to Fix

1. `backend/trading/trading_engine.py` - Line 952 (momentum data fetch)
2. `backend/trading/position_manager.py` - Partial profit logic
3. `backend/emergency_fix_order_conflicts.py` - Run to fix NFLX

---

## Testing After Fixes

```bash
# 1. Fix NFLX
python backend/emergency_fix_order_conflicts.py

# 2. Restart bot
# 3. Monitor logs for:
#    - "No bars response" should disappear
#    - Partial profits should succeed
#    - NFLX should have both stop and take-profit
```
