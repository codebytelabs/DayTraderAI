# Restart Trading Engine with Stop Loss Protection

## Quick Start

### 1. Stop Current Engine
```bash
# Press Ctrl+C in the terminal running the trading engine
```

### 2. Restart with New Protection
```bash
cd backend
python main.py
```

### 3. Verify Protection Manager Started

Look for these log messages:
```
✅ Stop Loss Protection Manager initialized (5-second checks)
🔍 Dynamic watchlist enabled - scanner loop started
```

### 4. Monitor for 5 Minutes

Watch for:
```
🛡️  Protection manager created X stop losses
✅ Created stop loss for SYMBOL: $XXX.XX
```

### 5. Check Alpaca Dashboard

Verify:
- Each position has a stop loss order
- Status is 'new' or 'accepted' (not 'held')
- Stop prices are reasonable (1-2% below entry)

## What to Expect

### Immediate (First 10 Seconds):
- Protection manager will scan all positions
- Create stop losses for any unprotected positions
- Cancel any 'held' bracket legs

### First Minute:
- All positions should have active stops
- Logs will show "Created stop loss for..." messages
- No more "NO ACTIVE STOP LOSS" errors

### Ongoing:
- Protection manager runs every 10 seconds
- Auto-creates stops for new positions
- Maintains 100% protection rate

## Troubleshooting

### If you see "NO ACTIVE STOP LOSS":
- Wait 10 seconds - protection manager will fix it
- Check next log cycle for "Created stop loss"
- If persists, check Alpaca API status

### If you see "Failed to create stop loss":
- Check Alpaca dashboard for errors
- Verify account has permission to place orders
- Check if position still exists

### If protection manager doesn't start:
- Check logs for initialization errors
- Verify trading_engine.py changes applied
- Restart the engine

## Success Criteria

✅ All positions have active stop loss orders
✅ No "NO ACTIVE STOP LOSS" errors in logs
✅ Alpaca dashboard shows stops with 'new' status
✅ Stop prices are 1-2% below entry prices
✅ Protection manager logs activity every 10 seconds

## Current Positions to Protect

Based on your Alpaca dashboard:
- AAPL: Needs stop at ~$267 (1% below entry)
- MRK: Needs stop at ~$92.50 (protect profit!)
- PEP: Needs stop at ~$145.75 (1% below entry)
- DE: Needs stop at ~$472.50 (1% below entry)

The protection manager will create these automatically within 10 seconds of startup.

## Status Check Command

```bash
./backend/check_protection_status.sh
```

This will show:
- If trading engine is running
- Recent protection manager activity
- Any warnings or errors
- Stop loss creation count

## Next Steps

1. Restart the engine (Ctrl+C, then `python main.py`)
2. Watch logs for 5 minutes
3. Verify all positions protected
4. Check Alpaca dashboard
5. Run status check script
6. Monitor for 1-2 hours to ensure stability

## Emergency: Manual Stop Loss Creation

If protection manager fails for any reason, manually create stops in Alpaca dashboard:

1. Go to Orders tab
2. Click "New Order"
3. Select symbol
4. Order Type: Stop
5. Side: Sell
6. Quantity: Match position size
7. Stop Price: 1% below entry
8. Time in Force: GTC
9. Submit

The protection manager will detect the manual stop and not create a duplicate.

## Support

If issues persist:
1. Check `backend/STOP_LOSS_PROTECTION_DEPLOYED.md` for full documentation
2. Review `backend/SOLUTION_SUMMARY.md` for architecture details
3. Check logs for specific error messages
4. Verify Alpaca API is responding

The protection manager is designed to be self-healing and should resolve most issues automatically within 10-20 seconds.
