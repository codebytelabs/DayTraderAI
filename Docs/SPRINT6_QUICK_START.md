# Sprint 6: Partial Profit Taking - Quick Start Guide

## 🎯 What Is This?

A system that:
- **Takes 50% profit at +1R** - Locks in guaranteed gains
- **Lets 50% run to +2R** - Captures bigger moves  
- **Uses trailing stops** - Protects remaining position

## 📊 Current Status

**Day 1**: ✅ COMPLETE - Shadow Mode Active  
**Tests**: 12/12 passed  
**Ready**: For live trading monitoring

## 🚀 Quick Commands

### Run Tests
```bash
cd backend
source venv/bin/activate
python test_sprint6_day1.py
```

### Monitor Shadow Mode
```bash
cd backend
source venv/bin/activate
python monitor_sprint6_day1.py
```

### Check Health
```python
from trading.profit_taker import ProfitTaker
from core.supabase_client import SupabaseClient

supabase = SupabaseClient()
profit_taker = ProfitTaker(supabase)

# Health check
health = profit_taker.check_health()
print(health)

# Shadow report
report = profit_taker.get_shadow_mode_report()
print(report)
```

## 📋 What to Watch For (Day 1)

### In Logs:
Look for messages like:
```
[SHADOW] Would take partial profits for AAPL: +1.05R 
(target: +1.0R, would sell 50%)
```

### What This Means:
- System detected +1R profit
- Would sell 50% if enabled
- NO actual order placed (shadow mode)
- Position continues unchanged

### Good Signs:
- ✅ Shadow predictions logged
- ✅ No errors
- ✅ Positions unchanged
- ✅ Logic working correctly

### Bad Signs:
- ❌ Errors in logs
- ❌ Unexpected position changes
- ❌ System crashes
- ❌ No predictions when positions reach +1R

## 🔧 Configuration

### Current Settings (Day 1):
```bash
# backend/.env
PARTIAL_PROFITS_ENABLED=false          # Shadow mode
PARTIAL_PROFITS_FIRST_TARGET_R=1.0     # Take profits at +1R
PARTIAL_PROFITS_PERCENTAGE=0.5         # Sell 50%
PARTIAL_PROFITS_SECOND_TARGET_R=2.0    # Let rest run to +2R
PARTIAL_PROFITS_USE_TRAILING=true      # Use trailing stops
MAX_PARTIAL_PROFIT_POSITIONS=999       # Unlimited (shadow mode)
```

### Day 2 Settings (After Day 1 Success):
```bash
PARTIAL_PROFITS_ENABLED=true           # Enable live mode
MAX_PARTIAL_PROFIT_POSITIONS=2         # Limit to 2 positions
```

## 📈 Example Scenario

### Without Partial Profits:
```
Entry: $100 (100 shares)
Reaches +2R: $104 (all 100 shares)
Reverses to +0.5R: $101 (all 100 shares)
Final profit: $100 (+0.5R)
```

### With Partial Profits:
```
Entry: $100 (100 shares)
Reaches +1R: $102 → Sell 50 shares (+1R locked = $100)
Reaches +2R: $104 (remaining 50 shares)
Reverses to +0.5R: $101 (remaining 50 shares)
Final profit: $100 (first 50%) + $50 (second 50%) = $150 (+0.75R)
```

**Result**: 50% more profit!

## 🎯 Next Steps

### End of Day 1:
1. Review shadow predictions
2. Check for any errors
3. Verify logic is correct
4. If all good → Proceed to Day 2

### Day 2 (Tomorrow):
1. Update `.env`:
   ```bash
   PARTIAL_PROFITS_ENABLED=true
   MAX_PARTIAL_PROFIT_POSITIONS=2
   ```
2. Restart backend
3. Monitor first 2 positions that reach +1R
4. Verify 50% sold correctly
5. Check remaining position continues

### Day 3 (If Day 2 Success):
1. Update `.env`:
   ```bash
   MAX_PARTIAL_PROFIT_POSITIONS=999
   ```
2. Enable for all positions
3. Monitor performance improvement

## ⚠️ Rollback Plan

If anything goes wrong:
```bash
# In backend/.env
PARTIAL_PROFITS_ENABLED=false

# Restart backend
pm2 restart backend
```

System returns to normal immediately.

## 📞 Support

### Documentation:
- `docs/sprints/SPRINT6_DAY1_COMPLETE.md` - Full Day 1 details
- `docs/sprints/SPRINT6_OVERVIEW.md` - Complete overview
- `TODO.md` - Sprint status and roadmap

### Test Files:
- `backend/test_sprint6_day1.py` - Test suite
- `backend/monitor_sprint6_day1.py` - Monitoring tool

### Code Files:
- `backend/trading/profit_taker.py` - Core logic
- `backend/trading/position_manager.py` - Integration
- `backend/config.py` - Configuration

## ✅ Day 1 Checklist

- [x] Configuration added
- [x] Code implemented
- [x] Tests pass (12/12)
- [x] Documentation complete
- [x] Shadow mode active
- [ ] Monitor during trading hours
- [ ] Review shadow predictions
- [ ] Verify no errors
- [ ] Decide on Day 2 deployment

---

**Status**: Day 1 Complete, Ready for Monitoring  
**Next**: Monitor shadow mode during trading hours  
**Goal**: Validate logic before Day 2 live test
