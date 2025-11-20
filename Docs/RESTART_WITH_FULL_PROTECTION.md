# Restart Backend with Full Protection System

## 🚀 Quick Restart Guide

Your backend needs to restart to activate all the new protection features.

### What's New:
1. ✅ Trailing stops enabled
2. ✅ Partial profits enabled
3. ✅ Order monitoring active
4. ✅ HELD order auto-fix

---

## Restart Steps

### Option 1: Terminal Restart (Recommended)
```bash
# Stop current backend (Ctrl+C in terminal)
# Then restart:
cd backend
python main.py
```

### Option 2: Kill and Restart
```bash
# Find and kill the process
pkill -f "python.*main.py"

# Restart
cd backend
python main.py
```

---

## What to Watch For

### On Startup, You Should See:
```
✅ Trailing Stop Manager auto-initialized
✅ Profit Taker auto-initialized
✅ Symbol Cooldown Manager auto-initialized
✅ Smart Order Executor initialized
```

### During Operation:
```
# Every 60 seconds:
✅ Synced 3 positions from Alpaca
✅ Checking for HELD orders...
✅ Verifying position protection...

# When profits hit:
✅ Partial profits taken for AAPL: 25 shares sold
✅ Trailing stop activated for CRWD at $535.00
```

### If Issues Detected:
```
🚨 HELD stop loss detected for AAPL!
✅ Canceled HELD order: abc123
✅ Created new stop loss at $270.00
```

---

## Verify It's Working

### 1. Check Current Positions
```bash
python backend/check_all_position_protection.py
```

Should show:
```
✅ All positions have active stop loss protection
```

### 2. Check Logs
```bash
tail -f backend/backend.log | grep -E "Trailing|Partial|HELD"
```

### 3. Monitor First Trade
Watch for:
- Limit order execution (not market)
- Active stop loss (not HELD)
- Partial profit at +1R
- Trailing stop at +2R

---

## Current Protection Status

### AAPL
- Entry: $273.77
- Stop: $269.40 (active)
- Status: ✅ Protected

### CRWD
- Entry: $536.00
- Stop: $524.57 (active)
- Status: ✅ Protected

### ONDS
- Entry: $6.75
- Stop: $6.59 (active)
- Status: ✅ Protected

---

## If Something Goes Wrong

### Disable Features Individually:

```python
# In backend/config.py

# Disable trailing stops
trailing_stops_enabled: False

# Disable partial profits
partial_profits_enabled: False

# Disable smart executor
USE_SMART_EXECUTOR: False
```

Then restart backend.

---

## Success Indicators

### ✅ Good Signs:
- No HELD orders detected
- Trailing stops activating
- Partial profits being taken
- All positions have active stops

### ⚠️ Warning Signs:
- HELD orders appearing
- Positions without stops
- Order creation failures

### 🚨 Critical Issues:
- Multiple HELD orders
- Unprotected positions
- Stop loss failures

If you see critical issues, check:
1. Buying power (may be too low)
2. Position sizes (may be too large)
3. Number of positions (may be too many)

---

## Quick Reference

### Check Protection:
```bash
python backend/check_all_position_protection.py
```

### Fix HELD Orders:
```bash
python backend/fix_all_held_stops.py
```

### View Logs:
```bash
tail -f backend/backend.log
```

---

**Status**: ✅ Ready to restart  
**Protection**: 🟢 Maximum  
**Confidence**: HIGH

**Restart now to activate full protection!**
