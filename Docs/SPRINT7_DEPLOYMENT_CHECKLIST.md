# Sprint 7 Deployment Checklist

## Pre-Deployment Validation ✅

- [x] **Unit Tests**: 17/17 passed
- [x] **Integration Tests**: 6/6 passed  
- [x] **Validation Script**: 6/6 checks passed
- [x] **Code Review**: All filters implemented correctly
- [x] **Configuration**: All settings added to config.py
- [x] **Documentation**: Complete

## Implementation Verified ✅

### Files Modified
- [x] `backend/trading/strategy.py` - 3 filter methods added
- [x] `backend/config.py` - Sprint 7 settings added
- [x] `backend/trading/trading_engine.py` - Daily cache refresh added

### Tests Created
- [x] `backend/test_sprint7_filters.py` - Unit tests
- [x] `backend/test_sprint7_integration.py` - Integration tests
- [x] `backend/validate_sprint7.py` - Validation script

### Documentation Created
- [x] `docs/SPRINT7_DEPLOYED.md` - Full deployment guide
- [x] `backend/SPRINT7_SUMMARY.md` - Quick summary
- [x] `docs/SPRINT7_DEPLOYMENT_CHECKLIST.md` - This checklist

## Deployment Steps

### 1. Stop Backend (if running)
```bash
pm2 stop backend
```

### 2. Verify Implementation
```bash
cd backend
python3 validate_sprint7.py
```

Expected output: `🎉 ALL VALIDATIONS PASSED!`

### 3. Start Backend
```bash
pm2 start backend
# OR
pm2 restart backend
```

### 4. Monitor Startup
```bash
pm2 logs backend --lines 50
```

Look for:
- `✓ Daily cache ready for Sprint 7 filters`
- No errors during startup

### 5. Verify Filters Are Active

Watch logs for filter activity:
```bash
pm2 logs backend --lines 100
```

During trading hours, you should see:
- `⏰ {symbol} skipped:` - Time-of-day filter working
- `📊 {symbol} rejected:` - 200-EMA filter working
- `📈 {symbol} rejected:` - Multi-timeframe filter working

## Post-Deployment Monitoring

### Day 1: Immediate Validation
- [ ] Backend started successfully
- [ ] Daily cache refreshed at market open
- [ ] Filters are blocking signals (check logs)
- [ ] Trade frequency reduced (expect 12-15/day vs 20-25/day)
- [ ] No system errors or crashes

### Week 1: Performance Tracking
- [ ] Win rate trending upward
- [ ] Trade frequency stable at 12-15/day
- [ ] Filters working during optimal hours (9:30-10:30 AM, 3-4 PM)
- [ ] Filters blocking lunch hour (11:30 AM-2 PM)
- [ ] No unexpected behavior

### Week 2-4: Results Analysis
- [ ] Win rate improved to 55-60%
- [ ] Profit factor > 1.5
- [ ] Average win > $450
- [ ] Average loss < $275
- [ ] Sharpe ratio > 2.3

## Rollback Plan

If performance degrades or issues arise:

### Option 1: Disable All Filters
Edit `backend/config.py`:
```python
enable_time_of_day_filter: bool = False
enable_200_ema_filter: bool = False
enable_multitime_frame_filter: bool = False
```

Then: `pm2 restart backend`

### Option 2: Disable Individual Filters
Disable only problematic filter(s):
```python
enable_time_of_day_filter: bool = True   # Keep
enable_200_ema_filter: bool = False      # Disable
enable_multitime_frame_filter: bool = True  # Keep
```

Then: `pm2 restart backend`

### Option 3: Adjust Thresholds
Modify time windows or other settings in `backend/config.py`

## Success Metrics

### Primary Metrics (Target)
- Win Rate: 55-60% (from 40-45%)
- Profit Factor: 1.6+ (from 1.3)
- Daily P&L: +1.5-2.0% (from +1.0-1.5%)

### Secondary Metrics (Target)
- Trade Frequency: 12-15/day (from 20-25/day)
- Average Win: $500+ (from $400)
- Average Loss: $250 (from $300)
- Sharpe Ratio: 2.5+ (from 2.0)

## Troubleshooting

### Issue: Filters Not Working
**Symptoms**: No filter logs, trade frequency unchanged

**Solution**:
1. Check config: `cat backend/config.py | grep enable_`
2. Verify filters enabled: Should show `True`
3. Restart backend: `pm2 restart backend`

### Issue: Daily Cache Not Refreshing
**Symptoms**: Filters allowing all trades, no cache logs

**Solution**:
1. Check logs: `pm2 logs backend | grep "Daily cache"`
2. Verify cache module: `python3 -c "from data.daily_cache import get_daily_cache; print('OK')"`
3. Restart backend: `pm2 restart backend`

### Issue: Too Few Trades
**Symptoms**: <10 trades/day, filters too aggressive

**Solution**:
1. Review filter logs to see which filter is blocking most
2. Adjust thresholds in `backend/config.py`
3. Consider disabling one filter temporarily

### Issue: Win Rate Not Improving
**Symptoms**: Win rate still 40-45% after 2 weeks

**Solution**:
1. Verify filters are actually blocking signals (check logs)
2. Analyze which signals are getting through
3. Consider adjusting filter thresholds
4. Review backtest data for validation

## Support Resources

- **Full Documentation**: `docs/SPRINT7_DEPLOYED.md`
- **Quick Summary**: `backend/SPRINT7_SUMMARY.md`
- **Implementation Plan**: `docs/SPRINT7_IMPLEMENTATION_PLAN.md`
- **Research**: `docs/ALGO_TRADING_OPTIMIZATION_RESEARCH.md`

## Validation Commands

```bash
# Run all tests
cd backend
python3 test_sprint7_filters.py
python3 test_sprint7_integration.py
python3 validate_sprint7.py

# Check configuration
cat config.py | grep -A 20 "Sprint 7"

# Monitor logs
pm2 logs backend --lines 100

# Check backend status
pm2 status backend
```

## Sign-Off

- [x] **Implementation**: Complete
- [x] **Testing**: All tests passed
- [x] **Validation**: All checks passed
- [x] **Documentation**: Complete
- [ ] **Deployment**: Ready (restart backend)
- [ ] **Monitoring**: Ongoing (track for 2-4 weeks)

---

**Status**: ✅ READY TO DEPLOY  
**Action Required**: Restart backend with `pm2 restart backend`  
**Expected Impact**: Win rate 40-45% → 55-60%

---

*Sprint 7 deployment checklist - Last updated: November 11, 2025*
