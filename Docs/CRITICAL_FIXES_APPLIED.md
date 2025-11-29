# Critical Fixes Applied - Stop Loss & Dynamic Watchlist

## Issues Found

### 1. Dynamic Watchlist Disabled ❌
**Problem:** System was trading hardcoded base watchlist (SPY, QQQ, AAPL, etc.) instead of AI-discovered opportunities.

**Root Cause:** 
- `.env` had `USE_DYNAMIC_WATCHLIST=true`
- But `config.py` had hardcoded default `use_dynamic_watchlist: bool = False`
- The hardcoded default was overriding the environment variable

**Fix Applied:**
```python
# backend/config.py line 59
use_dynamic_watchlist: bool = True  # Changed from False
```

**Expected Behavior After Fix:**
- Scanner runs every 30 minutes during market hours
- Discovers 20-30 high-quality opportunities using AI
- Updates watchlist with top-scoring symbols
- Trades AI-discovered opportunities instead of hardcoded list

### 2. Stop Losses Not Being Set 🚨
**Problem:** All positions showing "NO ACTIVE STOP LOSS" despite bracket orders being created.

**Root Cause:**
- Bracket orders are created successfully
- But Alpaca paper trading sometimes doesn't properly activate the stop loss and take profit legs
- Legs remain in "held" status or never transition to "active"

**Current Protection:**
- `check_and_fix_held_orders()` runs every 60 seconds
- `verify_position_protection()` alerts on unprotected positions
- Auto-creates emergency stop losses for unprotected positions

**Diagnostic Tool Created:**
```bash
cd backend
python check_bracket_orders.py
```

This will show:
- All positions and their P/L
- All bracket orders and their leg status
- Which positions lack stop loss protection
- Specific recommendations

## What to Do Now

### 1. Restart the Trading Engine
```bash
# Stop current process (Ctrl+C)
# Then restart
cd backend
python main.py
```

### 2. Verify Dynamic Watchlist is Active
Look for these log messages:
```
✓ Opportunity scanner initialized (dynamic watchlist: True)
🔍 Dynamic watchlist enabled - scanner loop started
🔍 Running AI-powered opportunity scan...
✓ Watchlist updated: 20 AI-discovered symbols
```

### 3. Monitor Stop Loss Protection
The system will automatically:
- Check positions every 60 seconds
- Alert if any position lacks stop loss
- Auto-create emergency stops for unprotected positions

Watch for:
```
✅ All positions protected
🚨 NO ACTIVE STOP LOSS for SYMBOL!  # Will trigger auto-fix
✅ Created new stop loss for SYMBOL at $XXX.XX
```

### 4. Run Diagnostic if Issues Persist
```bash
python check_bracket_orders.py
```

## Expected Trading Behavior

### Before Fix:
- Trading: SPY, QQQ, AAPL, MSFT, NVDA, TSLA, AMD, GOOG, AMZN, META (hardcoded)
- Stop losses: Missing or not active
- Risk: Unprotected positions

### After Fix:
- Trading: AI-discovered opportunities (WMT, LLY, UNH, DE, MRK, GM, NEM, LOW, COST, etc.)
- Watchlist updates every 30 minutes with top-scoring symbols
- Stop losses: Auto-created and monitored
- Protection: Emergency stops if bracket orders fail

## Monitoring Checklist

✅ Dynamic watchlist enabled in logs
✅ Scanner running every 30 minutes
✅ Trading AI-discovered symbols (not hardcoded list)
✅ All positions have active stop losses
✅ Emergency stops created if bracket orders fail

## If Stop Losses Still Missing

1. **Check bracket order status:**
   ```bash
   python check_bracket_orders.py
   ```

2. **Manually create stop losses:**
   - Go to Alpaca dashboard
   - For each position, create a stop loss order
   - Set stop 1-2% below entry price

3. **Consider switching to standalone orders:**
   - Modify `order_manager.py` to create separate stop loss orders
   - Instead of relying on bracket orders

## Next Steps

1. Monitor for 1-2 hours to verify:
   - Dynamic watchlist is updating
   - AI-discovered symbols are being traded
   - Stop losses are being set and staying active

2. If issues persist:
   - Run diagnostic script
   - Check Alpaca dashboard for order status
   - Consider implementing standalone stop loss orders

## Files Modified

- `backend/config.py` - Fixed `use_dynamic_watchlist` default
- `backend/check_bracket_orders.py` - New diagnostic tool

## Files to Monitor

- `backend/trading/trading_engine.py` - Scanner loop and watchlist updates
- `backend/trading/position_manager.py` - Stop loss protection and auto-fix
- `backend/orders/bracket_orders.py` - Bracket order creation
