# 🚀 Restart Instructions - Autopilot Fixes

## Quick Start (3 Steps)

### Step 1: Run Database Migration (2 minutes)

1. Open Supabase Dashboard: https://supabase.com/dashboard
2. Go to your project → SQL Editor
3. Copy and paste this SQL:

```sql
-- Fix advisory table field lengths
ALTER TABLE advisories ALTER COLUMN source TYPE VARCHAR(200);

DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'advisories' AND column_name = 'model'
    ) THEN
        ALTER TABLE advisories ALTER COLUMN model TYPE VARCHAR(200);
    ELSE
        ALTER TABLE advisories ADD COLUMN model VARCHAR(200);
    END IF;
END $$;

-- Verify
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'advisories';
```

4. Click "Run"
5. You should see: `source: VARCHAR(200)` and `model: VARCHAR(200)`

---

### Step 2: Restart Backend (1 minute)

1. In your terminal where backend is running, press `Ctrl+C` to stop
2. Wait for it to fully stop
3. Restart:

```bash
cd backend
python main.py
```

4. Wait for this message:
```
✅ Backend initialized successfully
✅ Trading engine started
```

---

### Step 3: Run Diagnostic Test (2 minutes)

In a NEW terminal:

```bash
cd backend
python test_autopilot_full.py
```

**Expected Output:**
```
✅ PASS - Alpaca Connection
✅ PASS - Market Status  
✅ PASS - Data Fetching
✅ PASS - Feature Calculation
✅ PASS - Signal Detection
✅ PASS - Database Connection

🎉 ALL SYSTEMS GO! Autopilot ready for deployment!
```

---

## What to Watch For

### In Terminal Logs

**GOOD SIGNS ✅:**
```
📊 Market data loop started
🎯 Strategy loop started
👁️  Position monitor loop started
📈 Metrics loop started
🔍 Evaluating 10 symbols: SPY, QQQ, AAPL...
📊 AAPL: price=$175.50, EMA9=$174.20, EMA21=$173.80
```

**BAD SIGNS ❌:**
```
Failed to get bars: subscription does not permit querying recent SIP data
Failed to insert advisory: value too long for type character varying(50)
can't compare offset-naive and offset-aware datetimes
```

If you see bad signs, the fixes didn't apply. Make sure you:
1. Ran the database migration
2. Fully restarted the backend (not just refresh)

---

## When Will Trades Happen?

### Market Hours
- **US Market:** 9:30 AM - 4:00 PM EST (Monday-Friday)
- **Your Time (Singapore):** 10:30 PM - 5:00 AM SGT (Tuesday-Saturday)

### Signal Requirements
For a trade to execute automatically, ALL must be true:
1. ✅ Market is open
2. ✅ Trading is enabled (check with `curl http://localhost:8006/health`)
3. ✅ EMA(9) crosses EMA(21) for a symbol
4. ✅ No existing position in that symbol
5. ✅ Passes risk checks (buying power, position limits)
6. ✅ Circuit breaker not triggered

### Typical Behavior

**During Market Hours:**
- Every 60 seconds: System checks all 10 watchlist symbols
- If crossover detected: Order placed automatically within seconds
- Average: 2-5 trades per day (depends on volatility)

**When Market Closed:**
- System pauses strategy evaluation
- Continues monitoring existing positions
- Resumes automatically when market opens

---

## Monitoring

### Real-Time in Terminal

```bash
# Watch logs live
tail -f backend/logs/trading.log  # if logging to file

# Or just watch the terminal where backend is running
```

### In Your Dashboard

Open: http://localhost:5173

Watch for:
- New positions appearing
- Orders being filled
- Equity changing
- Daily P/L updating

### In Alpaca Dashboard

Open: https://app.alpaca.markets/paper/dashboard/overview

You should see:
- Orders appearing automatically
- Positions opening/closing
- Account value matching your UI

---

## Testing Without Waiting for Market Open

If you want to test NOW (market closed):

### Option 1: Manual Test Order

```bash
curl -X POST http://localhost:8006/orders/submit \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "side": "buy",
    "qty": 1,
    "reason": "manual_test"
  }'
```

### Option 2: Simulate Market Open

Temporarily comment out the market check in `trading_engine.py`:

```python
# if not self.alpaca.is_market_open():
#     logger.debug("Market closed, skipping strategy evaluation")
#     await asyncio.sleep(60)
#     continue
```

Then restart backend. **Remember to uncomment after testing!**

---

## Troubleshooting

### "No signals found"

This is NORMAL! EMA crossovers don't happen every minute. You might wait hours or days for a signal depending on market conditions.

To increase signal frequency:
1. Add more symbols to watchlist
2. Use shorter EMA periods (e.g., EMA(5/13) instead of EMA(9/21))
3. Add multiple strategies (not just EMA)

### "Order rejected"

Check:
```bash
curl http://localhost:8006/metrics
```

Look for:
- `circuit_breaker_triggered: true` → Reset with `/emergency/stop`
- `open_positions: 20` → At max, wait for a position to close
- Low buying power → Close some positions

### "Still seeing old errors"

1. Make sure you FULLY stopped the backend (Ctrl+C)
2. Make sure you ran the database migration
3. Make sure you're running the NEW code (check file timestamps)
4. Try: `git status` to see if files were modified

---

## Success Checklist

- [ ] Database migration ran successfully
- [ ] Backend restarted with no errors
- [ ] Diagnostic test shows all ✅ PASS
- [ ] Terminal shows "Evaluating X symbols" every 60 seconds
- [ ] No "Failed to get bars" errors
- [ ] No database errors
- [ ] No timezone errors
- [ ] Dashboard shows correct account balance
- [ ] Ready to let it run!

---

## 🎉 You're All Set!

Your autopilot is now:
- ✅ Fetching real-time market data
- ✅ Calculating technical indicators
- ✅ Detecting trading signals
- ✅ Ready to place orders automatically
- ✅ Working from Singapore timezone
- ✅ Logging everything for monitoring

**Just wait for market open and watch it trade! 💰🚀**

---

## Need Help?

If something isn't working:

1. Check `AUTOPILOT_FIX_COMPLETE.md` for detailed explanations
2. Run the diagnostic test: `python test_autopilot_full.py`
3. Check terminal logs for specific errors
4. Verify all fixes were applied (database migration, backend restart)

The system is designed to be fully autonomous. Once running, it will:
- Trade automatically during market hours
- Stop automatically when market closes
- Resume automatically when market opens
- Manage risk automatically
- Close positions automatically at stop/target

**Let the money printer do its thing! 🖨️💵**
