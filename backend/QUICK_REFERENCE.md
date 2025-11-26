# 🚀 QUICK REFERENCE - Trading Bot Commands

## Start/Stop Commands

### Start Bot
```bash
./backend/RESTART_FIXED_BOT.sh
```

### Stop Bot
```bash
pkill -f "python.*main.py"
```

### Check if Running
```bash
pgrep -f "python.*main.py"
```

## Monitoring Commands

### Watch Live Logs
```bash
tail -f bot.log
```

### Check Last 50 Lines
```bash
tail -50 bot.log
```

### Search for Errors
```bash
grep "ERROR" bot.log | tail -20
```

### Search for Trades
```bash
grep "Order filled" bot.log | tail -10
```

### Check Brackets
```bash
grep "Brackets created" bot.log | tail -10
```

## Verification Commands

### Verify All Fixes
```bash
python backend/verify_all_fixes.py
```

### Check Account Status
```bash
python backend/check_account_and_trade.py
```

### Check Current Positions
```bash
python backend/check_live_brackets.py
```

## Key Settings

### Smart Order Executor
- **Timeout:** 60 seconds
- **Max Slippage:** 0.1%
- **Min R/R:** 1:2.0
- **Status:** ENABLED ✅

### Risk Management
- **Max Risk per Trade:** 1.0% of equity
- **Max Position Size:** 20% of equity
- **Stop Loss:** Always enabled
- **Take Profit:** Always enabled

### Trading Hours
- **Regular Hours:** 9:30 AM - 4:00 PM ET
- **Extended Hours:** DISABLED
- **Timezone:** US/Eastern

## What to Look For

### Good Signs ✅
```
✅ Signal detected: BUY AMD (72% confidence)
✅ Order filled: AMD @ $211.22 (slippage: 0.01%)
✅ Brackets created: SL $207.99, TP $217.50
✅ R/R validated: 1:2.5
```

### Warning Signs ⚠️
```
⚠️  Smart executor rejected trade: Fill timeout
⚠️  Excessive slippage: 0.15%
⚠️  R/R ratio too low: 1:1.5
```

### Error Signs ❌
```
❌ Order submission failed
❌ Bracket order submission failed
❌ Position too large
```

## Quick Troubleshooting

### Bot Won't Start
1. Check if already running: `pgrep -f "python.*main.py"`
2. Kill existing: `pkill -9 -f "python.*main.py"`
3. Check logs: `tail -50 bot.log`
4. Restart: `./backend/RESTART_FIXED_BOT.sh`

### No Trades Executing
1. Check market hours (9:30 AM - 4:00 PM ET)
2. Check AI discovery: `grep "opportunities found" bot.log | tail -5`
3. Check signals: `grep "Signal detected" bot.log | tail -5`
4. Check rejections: `grep "rejected" bot.log | tail -10`

### Brackets Not Creating
1. Check if Smart Executor enabled: `grep "Smart Executor" bot.log | head -1`
2. Check bracket creation: `grep "Brackets created" bot.log | tail -5`
3. Check for errors: `grep "Bracket" bot.log | grep -i error | tail -5`

## Performance Metrics

### Check Today's Performance
```bash
grep "$(date +%Y-%m-%d)" bot.log | grep "filled" | wc -l
```

### Check Win/Loss
```bash
grep "TAKE PROFIT" bot.log | tail -10
grep "STOP LOSS" bot.log | tail -10
```

### Check AI Opportunities
```bash
grep "opportunities found" bot.log | tail -5
```

## Emergency Commands

### Force Stop Everything
```bash
pkill -9 -f "python.*main.py"
```

### Close All Positions (Manual)
```python
python backend/close_all_positions.py
```

### Cancel All Orders (Manual)
```python
python backend/cancel_all_orders.py
```

## Files to Check

### Configuration
- `backend/config.py` - Main settings
- `.env.local` - API keys

### Logs
- `bot.log` - Main bot log
- `backend.log` - Backend log

### Status
- `backend/FINAL_STATUS_REPORT.md` - Full status
- `backend/BEST_BOT_READY.md` - Ready status

## Support

### Check System Status
```bash
python backend/verify_all_fixes.py
```

### Full Diagnostic
```bash
python backend/check_account_and_trade.py
python backend/check_live_brackets.py
python backend/verify_all_fixes.py
```

---

**Keep this handy for quick reference!** 📋
