# Restart Guide - Long-Only Mode Enabled

## What Changed

1. **Long-only mode configured** in `config.py`
2. **SELL signal filter added** in `trading_engine.py` (line 269-272)
3. **Trailing stops already configured** (no changes needed)

## How to Restart

### Step 1: Stop Current Engine
In the terminal running the trading engine, press:
```
Ctrl+C
```

### Step 2: Restart Engine
```bash
cd backend
python main.py
```

## What to Look For

### ✅ SUCCESS - Long-Only Mode Active:
```
⚠️  AAPL SELL signal rejected: Long-only mode enabled
⚠️  AMD SELL signal rejected: Long-only mode enabled
⚠️  WFC SELL signal rejected: Long-only mode enabled
📈 Signal detected: BUY PLTR
✅ Order submitted: BUY 79 PLTR
```

### ❌ PROBLEM - Long-Only Mode NOT Active:
```
📈 Signal detected: SELL AAPL
❌ Stock order rejected for AAPL (account not allowed to short)
```

If you see the PROBLEM pattern, the configuration didn't load. Check:
1. `backend/config.py` has `long_only_mode: bool = True`
2. `backend/trading/trading_engine.py` has the filter at line 269-272

## Expected Results

- **No more short selling errors** ✅
- **Only BUY signals processed** ✅
- **Cleaner logs** ✅
- **Trailing stops for profitable positions** ✅
- **Stop loss protection for all positions** ✅

## Quick Verification

After restart, run:
```bash
# Check first 100 lines of logs for SELL signals
tail -100 backend/logs/trading_*.log | grep "SELL signal"
```

You should see:
```
⚠️  SYMBOL SELL signal rejected: Long-only mode enabled
```

NOT:
```
❌ Stock order rejected for SYMBOL (account not allowed to short)
```

Ready to restart! 🚀
