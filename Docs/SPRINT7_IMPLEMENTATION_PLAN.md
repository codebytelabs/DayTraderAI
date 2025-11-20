# Sprint 7: Win Rate Optimization - Implementation Plan
## 40-45% → 55-60% Win Rate

**Date**: November 11, 2025  
**Status**: ✅ READY TO IMPLEMENT  
**Timeline**: 1-2 weeks  
**Confidence**: HIGH (research-backed)

---

## Executive Summary

**Goal**: Improve win rate from 40-45% to 55-60% using 3 proven filters

**Approach**: Add research-backed filters in optimal order for maximum efficiency

**Expected Result**: +15-20% win rate improvement with acceptable trade frequency reduction

---

## Phase 1: Analysis & Testing ✅ COMPLETE

### Completed
- [x] Comprehensive research (`ALGO_TRADING_OPTIMIZATION_RESEARCH.md`)
- [x] Filter order analysis (`FILTER_ORDER_ANALYSIS.md`)
- [x] Test module created (`test_filter_pipeline.py`)
- [x] Optimal ordering validated

### Key Findings
1. **Time-of-day filter** should be FIRST (FREE, eliminates 60-70%)
2. **200-EMA filter** should be SECOND (LOW cost, eliminates 40-50%)
3. **Multi-timeframe** should be THIRD (LOW cost, eliminates 30-40%)
4. All filters are independent (no conflicts)
5. Optimal ordering: fail fast, fail cheap

---

## Phase 2: Implementation (Days 1-5)

### Day 1: Caching Layer
**Goal**: Add daily data caching for 200-EMA and multi-timeframe

**Files to Create/Modify**:
- `backend/data/daily_cache.py` (NEW)
- `backend/data/market_data.py` (MODIFY)

**Implementation**:
```python
# daily_cache.py
class DailyCache:
    """Cache daily bars and calculations"""
    
    def __init__(self):
        self.cache = {}
        self.cache_date = None
    
    def get_daily_data(self, symbol):
        """Get cached daily data"""
        if self.cache_date != datetime.now().date():
            self.refresh_cache()
        return self.cache.get(symbol)
    
    def refresh_cache(self):
        """Refresh cache at market open"""
        # Fetch daily bars for all symbols
        # Calculate 200-EMA
        # Calculate daily EMA(9/21)
        # Update cache
```

**Tests**:
- [ ] Unit test for cache initialization
- [ ] Unit test for cache refresh
- [ ] Unit test for cache hit/miss
- [ ] Integration test with market_data

---

### Day 2: Time-of-Day Filter
**Goal**: Add time-of-day filter (FREE, highest impact)

**Files to Modify**:
- `backend/trading/strategy.py`
- `backend/config.py` (add feature flag)

**Implementation**:
```python
# In strategy.py
def _is_optimal_trading_time(self) -> Tuple[bool, str]:
    """Check if current time is optimal for trading"""
    now = datetime.now(tz=pytz.timezone('US/Eastern'))
    hour = now.hour
    minute = now.minute
    
    # First hour (9:30-10:30 AM)
    if hour == 9 and minute >= 30:
        return True, ""
    if hour == 10 and minute <= 30:
        return True, ""
    
    # Last hour (3:00-4:00 PM)
    if 15 <= hour < 16:
        return True, ""
    
    # Lunch hour (11:30 AM-2:00 PM) - AVOID
    if hour == 11 and minute >= 30:
        return False, "Lunch hour - low volatility"
    if 12 <= hour < 14:
        return False, "Lunch hour - low volatility"
    
    return False, "Outside optimal trading hours"

# In evaluate()
def evaluate(self, symbol, features):
    # ... existing checks ...
    
    # NEW: Time-of-day filter (FIRST after basic checks)
    if settings.ENABLE_TIME_OF_DAY_FILTER:
        passed, reason = self._is_optimal_trading_time()
        if not passed:
            logger.debug(f"⏰ {symbol} skipped: {reason}")
            return None
    
    # ... rest of evaluation ...
```

**Tests**:
- [ ] Unit test for time check logic
- [ ] Test first hour (9:30-10:30 AM)
- [ ] Test last hour (3:00-4:00 PM)
- [ ] Test lunch hour blocking (11:30 AM-2:00 PM)
- [ ] Test timezone handling
- [ ] Integration test with strategy

---

### Day 3: 200-EMA Daily Trend Filter
**Goal**: Add 200-EMA daily trend filter (SECOND, high impact)

**Files to Modify**:
- `backend/trading/strategy.py`
- `backend/data/market_data.py`
- `backend/config.py` (add feature flag)

**Implementation**:
```python
# In market_data.py
def get_daily_trend_data(self, symbol):
    """Get daily trend data (cached)"""
    return self.daily_cache.get_daily_data(symbol)

# In strategy.py
def _check_daily_trend(self, symbol: str, signal: str) -> Tuple[bool, str]:
    """Check 200-EMA daily trend alignment"""
    try:
        daily_data = self.market_data.get_daily_trend_data(symbol)
        if not daily_data:
            return True, ""  # Allow if no data
        
        daily_price = daily_data['price']
        daily_200_ema = daily_data['ema_200']
        
        # Only long when price > 200-EMA
        if signal == 'buy' and daily_price < daily_200_ema:
            return False, f"Counter-trend long (daily price ${daily_price:.2f} < 200-EMA ${daily_200_ema:.2f})"
        
        # Only short when price < 200-EMA
        if signal == 'sell' and daily_price > daily_200_ema:
            return False, f"Counter-trend short (daily price ${daily_price:.2f} > 200-EMA ${daily_200_ema:.2f})"
        
        return True, ""
    except Exception as e:
        logger.warning(f"Could not check daily trend for {symbol}: {e}")
        return True, ""  # Allow if error

# In evaluate()
def evaluate(self, symbol, features):
    # ... time-of-day check ...
    
    # ... EMA crossover detection ...
    signal = signal_info['signal']
    
    # NEW: 200-EMA daily trend filter (AFTER signal detection)
    if settings.ENABLE_200_EMA_FILTER:
        passed, reason = self._check_daily_trend(symbol, signal)
        if not passed:
            logger.info(f"📊 {symbol} rejected: {reason}")
            return None
    
    # ... rest of evaluation ...
```

**Tests**:
- [ ] Unit test for 200-EMA calculation
- [ ] Unit test for trend check logic
- [ ] Test long blocking (price < 200-EMA)
- [ ] Test short blocking (price > 200-EMA)
- [ ] Test with missing data (graceful fallback)
- [ ] Integration test with strategy

---

### Day 4: Multi-timeframe Alignment
**Goal**: Add multi-timeframe alignment filter (THIRD, good impact)

**Files to Modify**:
- `backend/trading/strategy.py`
- `backend/data/market_data.py`
- `backend/config.py` (add feature flag)

**Implementation**:
```python
# In market_data.py
def get_daily_ema_trend(self, symbol):
    """Get daily EMA trend (cached)"""
    daily_data = self.daily_cache.get_daily_data(symbol)
    if not daily_data:
        return None
    
    return {
        'trend': daily_data['trend'],  # 'bullish' or 'bearish'
        'ema_9': daily_data['ema_9'],
        'ema_21': daily_data['ema_21']
    }

# In strategy.py
def _check_timeframe_alignment(self, symbol: str, signal: str) -> Tuple[bool, str]:
    """Check multi-timeframe alignment"""
    try:
        daily_trend = self.market_data.get_daily_ema_trend(symbol)
        if not daily_trend:
            return True, ""  # Allow if no data
        
        trend = daily_trend['trend']
        
        # Only long when daily trend is bullish
        if signal == 'buy' and trend != 'bullish':
            return False, f"Daily trend {trend}, not bullish"
        
        # Only short when daily trend is bearish
        if signal == 'sell' and trend != 'bearish':
            return False, f"Daily trend {trend}, not bearish"
        
        return True, ""
    except Exception as e:
        logger.warning(f"Could not check timeframe alignment for {symbol}: {e}")
        return True, ""  # Allow if error

# In evaluate()
def evaluate(self, symbol, features):
    # ... 200-EMA check ...
    
    # NEW: Multi-timeframe alignment (AFTER 200-EMA)
    if settings.ENABLE_MULTITIME_FRAME_FILTER:
        passed, reason = self._check_timeframe_alignment(symbol, signal)
        if not passed:
            logger.info(f"📈 {symbol} rejected: {reason}")
            return None
    
    # ... rest of evaluation ...
```

**Tests**:
- [ ] Unit test for daily EMA calculation
- [ ] Unit test for trend determination
- [ ] Test long blocking (daily bearish)
- [ ] Test short blocking (daily bullish)
- [ ] Test with missing data (graceful fallback)
- [ ] Integration test with strategy

---

### Day 5: Integration & Configuration
**Goal**: Integrate all filters and add configuration

**Files to Modify**:
- `backend/config.py`
- `backend/.env`

**Configuration**:
```python
# In config.py
# Sprint 7: Win Rate Optimization Filters
ENABLE_TIME_OF_DAY_FILTER: bool = True
ENABLE_200_EMA_FILTER: bool = True
ENABLE_MULTITIME_FRAME_FILTER: bool = True

# Time-of-day settings
OPTIMAL_HOURS_START_1: tuple = (9, 30)  # 9:30 AM
OPTIMAL_HOURS_END_1: tuple = (10, 30)   # 10:30 AM
OPTIMAL_HOURS_START_2: tuple = (15, 0)  # 3:00 PM
OPTIMAL_HOURS_END_2: tuple = (16, 0)    # 4:00 PM
AVOID_LUNCH_HOUR: bool = True

# Daily trend settings
DAILY_TREND_EMA_PERIOD: int = 200
CACHE_REFRESH_TIME: str = "09:30"  # Market open
```

**Tests**:
- [ ] Integration test: all filters together
- [ ] Test filter ordering
- [ ] Test feature flags
- [ ] Test configuration loading
- [ ] End-to-end test with mock data

---

## Phase 3: Testing & Validation (Days 6-7)

### Day 6: Backtesting
**Goal**: Validate win rate improvement on historical data

**Tasks**:
- [ ] Backtest on 6 months historical data
- [ ] Compare win rate before/after
- [ ] Measure trade frequency impact
- [ ] Test across market regimes:
  - [ ] Bull market
  - [ ] Bear market
  - [ ] Sideways market
  - [ ] High volatility
  - [ ] Low volatility

**Success Criteria**:
- [ ] Win rate improves to 55-60%
- [ ] Trade frequency 12-15/day (acceptable)
- [ ] No increase in max drawdown
- [ ] Profit factor > 1.6

---

### Day 7: Shadow Mode
**Goal**: Test on live data without affecting trades

**Tasks**:
- [ ] Deploy with all filters in shadow mode
- [ ] Log what WOULD be filtered
- [ ] Validate filter effectiveness
- [ ] Check for unexpected behavior
- [ ] Generate shadow mode report

**Monitoring**:
```
Track for 1 full trading day:
- Symbols evaluated: X
- Time-of-day filtered: X (expect 60-70%)
- 200-EMA filtered: X (expect 40-50% of remaining)
- Multi-timeframe filtered: X (expect 30-40% of remaining)
- Signals generated: X (expect 12-15/day)
- Signals that would trade: X
```

---

## Phase 4: Deployment (Days 8-10)

### Day 8-9: Limited Rollout
**Goal**: Test with 2-3 positions

**Tasks**:
- [ ] Enable filters for 2-3 positions
- [ ] Monitor closely for 2 days
- [ ] Compare to baseline performance
- [ ] Check for issues

**Monitoring**:
- [ ] Win rate on limited positions
- [ ] Trade execution quality
- [ ] Filter effectiveness
- [ ] System stability

---

### Day 10: Full Deployment
**Goal**: Enable for all positions

**Tasks**:
- [ ] Remove position limits
- [ ] Enable for all trades
- [ ] Monitor performance
- [ ] Track metrics daily

**Success Criteria**:
- [ ] Win rate 55-60%
- [ ] Trade frequency 12-15/day
- [ ] No system errors
- [ ] Profit factor > 1.6
- [ ] Sharpe ratio > 2.5

---

## Rollback Plan

**If performance degrades**:

1. **Immediate**: Disable filters via feature flags
   ```python
   # In config.py
   ENABLE_TIME_OF_DAY_FILTER = False
   ENABLE_200_EMA_FILTER = False
   ENABLE_MULTITIME_FRAME_FILTER = False
   ```

2. **Restart**: `pm2 restart backend`

3. **Analyze**: Review logs to identify issue

4. **Fix**: Adjust thresholds or logic

5. **Re-test**: Backtest and shadow mode again

6. **Re-deploy**: Limited rollout before full deployment

---

## Success Metrics

### Primary Metrics
- [ ] Win rate: 40-45% → 55-60%
- [ ] Profit factor: 1.3 → 1.6+
- [ ] Daily P&L: +1.0-1.5% → +1.5-2.0%

### Secondary Metrics
- [ ] Trade frequency: 20-25 → 12-15/day
- [ ] Average win: $400 → $500+
- [ ] Average loss: $300 → $250
- [ ] Max drawdown: <5%
- [ ] Sharpe ratio: 2.0 → 2.5+

### Filter Effectiveness
- [ ] Time-of-day filters 60-70% of periods
- [ ] 200-EMA filters 40-50% of counter-trend
- [ ] Multi-timeframe filters 30-40% of misaligned
- [ ] Combined: 80-90% of low-quality signals filtered

---

## Risk Assessment

### Low Risk ✅
- All filters are research-backed
- Feature flags allow easy rollback
- Shadow mode testing before deployment
- Gradual rollout (2-3 positions first)
- Existing system remains unchanged

### Mitigation
- Comprehensive unit tests
- Integration tests
- Backtesting on 6+ months data
- Shadow mode validation
- Limited rollout before full deployment

---

## Timeline Summary

| Day | Phase | Tasks | Deliverable |
|-----|-------|-------|-------------|
| 1 | Implementation | Caching layer | Daily cache working |
| 2 | Implementation | Time-of-day filter | Filter integrated |
| 3 | Implementation | 200-EMA filter | Filter integrated |
| 4 | Implementation | Multi-timeframe filter | Filter integrated |
| 5 | Implementation | Integration & config | All filters working |
| 6 | Testing | Backtesting | Performance report |
| 7 | Testing | Shadow mode | Shadow mode report |
| 8-9 | Deployment | Limited rollout | 2-3 positions live |
| 10 | Deployment | Full deployment | All positions live |

**Total**: 10 days (2 weeks)

---

## Next Steps

1. **TODAY**: Begin Day 1 implementation
   - Create daily cache module
   - Add to market_data.py
   - Write unit tests

2. **THIS WEEK**: Complete implementation (Days 1-5)
   - Add all 3 filters
   - Write comprehensive tests
   - Integrate and configure

3. **NEXT WEEK**: Test and deploy (Days 6-10)
   - Backtest and validate
   - Shadow mode
   - Limited rollout
   - Full deployment

---

## Documentation

### Created
- [x] `ALGO_TRADING_OPTIMIZATION_RESEARCH.md` - Full research
- [x] `OPTIMIZATION_IMPLEMENTATION_CHECKLIST.md` - Checklist
- [x] `OPTIMIZATION_EXECUTIVE_SUMMARY.md` - Executive summary
- [x] `FILTER_ORDER_ANALYSIS.md` - Filter ordering analysis
- [x] `SPRINT7_IMPLEMENTATION_PLAN.md` - This document
- [x] `test_filter_pipeline.py` - Test module

### To Create
- [ ] `SPRINT7_DAY1_COMPLETE.md` - Day 1 completion report
- [ ] `SPRINT7_BACKTEST_REPORT.md` - Backtesting results
- [ ] `SPRINT7_SHADOW_MODE_REPORT.md` - Shadow mode results
- [ ] `SPRINT7_DEPLOYMENT_REPORT.md` - Final deployment results

---

**Status**: ✅ READY TO IMPLEMENT  
**Confidence**: HIGH  
**Expected Result**: 40-45% → 55-60% win rate  
**Timeline**: 10 days (2 weeks)

---

*Implementation plan complete - Ready to begin Day 1*
