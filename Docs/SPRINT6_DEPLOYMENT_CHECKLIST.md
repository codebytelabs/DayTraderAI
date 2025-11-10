# Sprint 6 Deployment Checklist ✅

## Pre-Deployment Validation

### 1. Tests Pass ✅
```bash
python backend/test_sprint6_day1.py
```
**Result**: 12/12 tests passed

### 2. Integration Complete ✅
```bash
python backend/test_integration.py
```
**Result**: 
- ✅ Position Manager initialized
- ✅ Trailing Stop Manager: Active
- ✅ Profit Taker: Active
- ✅ Shadow Mode: Active (safe)
- ✅ Configuration: Correct

### 3. No Diagnostics Errors ✅
- ✅ `backend/config.py` - Clean
- ✅ `backend/trading/profit_taker.py` - Clean
- ✅ `backend/trading/position_manager.py` - Clean
- ✅ `backend/.env` - Clean

### 4. Configuration Verified ✅
```bash
# backend/.env
PARTIAL_PROFITS_ENABLED=false          # Shadow mode (safe)
PARTIAL_PROFITS_FIRST_TARGET_R=1.0     # Take profits at +1R
PARTIAL_PROFITS_PERCENTAGE=0.5         # Sell 50%
PARTIAL_PROFITS_SECOND_TARGET_R=2.0    # Let rest run to +2R
PARTIAL_PROFITS_USE_TRAILING=true      # Use trailing stops
MAX_PARTIAL_PROFIT_POSITIONS=999       # Unlimited (shadow mode)
```

## Deployment Steps

### Step 1: Restart Backend ✅
```bash
pm2 restart backend
```

### Step 2: Verify Startup
Check logs for:
```
✓ Profit Taker auto-initialized in Position Manager
✓ Profit Taker initialized - Status: SHADOW MODE
```

### Step 3: Monitor During Trading Hours
Watch for shadow predictions:
```
[SHADOW] Would take partial profits for AAPL: +1.05R 
(target: +1.0R, would sell 50%)
```

## What Will Happen (Day 1)

### Shadow Mode Behavior:
1. **System monitors all positions**
2. **When position reaches +1R profit**:
   - Logs: `[SHADOW] Would take partial profits...`
   - Tracks prediction data
   - **NO actual order placed**
   - Position continues unchanged
3. **Accumulates predictions for analysis**

### What WON'T Happen:
- ❌ No actual partial profit orders
- ❌ No position changes
- ❌ No impact on trading
- ❌ No risk to existing positions

## Monitoring Checklist

### During Trading Hours:
- [ ] Check logs for `[SHADOW]` messages
- [ ] Verify positions unchanged
- [ ] Confirm no unexpected orders
- [ ] Watch for any errors

### End of Day:
- [ ] Review shadow predictions count
- [ ] Check average profit R
- [ ] Verify logic is correct
- [ ] Look for any issues

### Run Monitor (Optional):
```bash
python backend/monitor_sprint6_day1.py
```

## Success Criteria (Day 1)

- [ ] Backend restarts successfully
- [ ] Profit Taker initializes in shadow mode
- [ ] Shadow predictions logged for +1R positions
- [ ] NO actual orders placed
- [ ] No errors in logs
- [ ] Positions behave normally

## If All Good → Day 2

### Tomorrow's Changes:
```bash
# In backend/.env
PARTIAL_PROFITS_ENABLED=true           # Enable live mode
MAX_PARTIAL_PROFIT_POSITIONS=2         # Limit to 2 positions
```

### Day 2 Expectations:
- First 2 positions that reach +1R: Take partial profits
- Additional positions: Stay in shadow mode
- Monitor closely for issues

## Rollback Plan

### If ANY Issues:
```bash
# In backend/.env
PARTIAL_PROFITS_ENABLED=false

# Restart
pm2 restart backend
```

System returns to normal immediately.

## Current System Status

### Sprint 5 (Trailing Stops):
- ✅ Active in limited test mode (2 positions)
- ✅ Working correctly
- ✅ No issues

### Sprint 6 (Partial Profits):
- ✅ Implemented and tested
- ✅ Shadow mode active
- ✅ Ready for deployment
- ⏳ Awaiting Day 1 validation

## Files Modified

### Configuration:
- `backend/config.py` - Added Sprint 6 config
- `backend/.env` - Added Sprint 6 variables

### Core Logic:
- `backend/trading/profit_taker.py` - New file (Sprint 6)
- `backend/trading/position_manager.py` - Integrated profit taker

### Testing:
- `backend/test_sprint6_day1.py` - Test suite
- `backend/monitor_sprint6_day1.py` - Monitoring tool
- `backend/test_integration.py` - Integration test

### Documentation:
- `docs/sprints/SPRINT6_DAY1_COMPLETE.md` - Full details
- `docs/sprints/SPRINT6_OVERVIEW.md` - Overview
- `docs/SPRINT6_QUICK_START.md` - Quick reference
- `docs/SPRINT6_DEPLOYMENT_CHECKLIST.md` - This file

## Final Verification

### Run All Checks:
```bash
# Test suite
python backend/test_sprint6_day1.py

# Integration test
python backend/test_integration.py

# Sprint 5 validation (ensure still working)
python backend/test_sprint5_day2.py
```

### Expected Results:
- ✅ Sprint 6: 12/12 tests passed
- ✅ Integration: All components initialized
- ✅ Sprint 5: Still working correctly

## Ready to Deploy? ✅

**All checks passed!**

### To Deploy:
```bash
pm2 restart backend
```

### Then Monitor:
- Watch logs for shadow predictions
- Verify no errors
- Confirm positions unchanged
- Review at end of day

---

**Status**: ✅ READY FOR DEPLOYMENT  
**Risk Level**: LOW (Shadow mode only)  
**Impact**: NONE (No actual trades)  
**Next**: Day 2 limited test (after Day 1 success)
