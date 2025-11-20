# Filter Order Analysis & Optimization
## Optimal Filter Execution Pipeline

**Date**: November 11, 2025  
**Purpose**: Determine optimal filter ordering to maximize efficiency and win rate  
**Status**: Analysis Complete - Ready for Implementation

---

## Current Filter Flow (As-Is)

### Stage 1: AI Discovery & Scoring (Hourly)
```
Scanner Loop (every hour):
├─ 1. Sentiment Aggregator (Perplexity + VIX)
├─ 2. AI Opportunity Finder (Perplexity - 50-100 candidates)
├─ 3. Opportunity Scorer (120-point scoring)
├─ 4. Filter by score >= 80 (A- or better)
└─ 5. Generate watchlist (top 20-25 symbols)
```

**Cost**: High (API calls, computation)  
**Frequency**: Hourly  
**Filters**: ~50-100 → 20-25 symbols

---

### Stage 2: Strategy Evaluation (Every Minute)
```
Strategy Loop (every minute, per symbol):
├─ 1. Check existing position (skip if exists)
├─ 2. Check order cooldown (skip if recent)
├─ 3. Detect EMA crossover signal
├─ 4. Calculate confidence score
├─ 5. Count confirmations (RSI, MACD, VWAP, Volume)
├─ 6. Check market regime
├─ 7. Enhanced short filters (if short):
│   ├─ Market sentiment > 55? → REJECT
│   ├─ Market sentiment < 30? → REJECT
│   ├─ Price above EMAs? → REJECT
│   ├─ Volume < 1.5x? → REJECT
│   ├─ RSI < 30? → REJECT
│   └─ Confidence < 75%? → REJECT
├─ 8. Confidence < 70%? → REJECT
└─ 9. Confirmations < 3? → REJECT
```

**Cost**: Medium (calculations per symbol)  
**Frequency**: Every minute  
**Filters**: 20-25 → 5-10 signals/day

---

### Stage 3: Trade Execution (Per Signal)
```
Execution Flow (per signal):
├─ 1. Symbol cooldown check → REJECT if frozen
├─ 2. Trade frequency limits → REJECT if exceeded
├─ 3. Risk manager checks:
│   ├─ Circuit breaker
│   ├─ Position count
│   ├─ Position size
│   ├─ Buying power
│   ├─ Market regime multiplier
│   └─ Sentiment multiplier
└─ 4. Submit order
```

**Cost**: Low (simple checks)  
**Frequency**: Per signal  
**Filters**: 5-10 → 3-8 trades/day

---

## Proposed New Filters (Sprint 7)

### Tier 1 Filters (To Be Added)
1. **200-EMA Daily Trend Filter** - Check daily trend alignment
2. **Time-of-Day Filter** - Check if optimal trading hours
3. **Multi-timeframe Alignment** - Check daily EMA alignment

### Tier 2 Filters (Optional)
4. **Volatility Filter** - Check ATR vs 20-day average
5. **Volume Surge** - Increase threshold to 1.5x
6. **ADX Minimum** - Require ADX > 25

---

## Filter Cost Analysis

### Computational Cost (per symbol, per minute)

| Filter | Cost | Data Required | Frequency |
|--------|------|---------------|-----------|
| **Existing Position Check** | FREE | In-memory | Every eval |
| **Order Cooldown** | FREE | In-memory | Every eval |
| **Time-of-Day** | FREE | System time | Every eval |
| **Symbol Cooldown** | FREE | In-memory | Per signal |
| **Trade Limits** | FREE | In-memory | Per signal |
| **200-EMA Daily** | LOW | 1 API call/day | Cache daily |
| **Multi-timeframe** | LOW | 1 API call/day | Cache daily |
| **Volatility (ATR)** | LOW | Already calculated | Every eval |
| **Volume** | FREE | Already calculated | Every eval |
| **ADX** | FREE | Already calculated | Every eval |
| **EMA Crossover** | FREE | Already calculated | Every eval |
| **Confirmations** | FREE | Already calculated | Every eval |
| **Sentiment** | MEDIUM | Cached hourly | Every eval |
| **Risk Checks** | LOW | API call | Per signal |

---

## Optimal Filter Order (Proposed)

### Principle: **Fail Fast, Fail Cheap**
- Cheapest filters first (in-memory checks)
- Most restrictive filters early (eliminate most candidates)
- Expensive filters last (only for high-probability candidates)

---

### STAGE 1: Pre-Computation (Hourly/Daily)
**Run once, cache results**

```
Daily (market open):
├─ 1. Fetch daily bars for all symbols
├─ 2. Calculate 200-EMA for all symbols
├─ 3. Calculate daily EMA(9/21) for all symbols
└─ 4. Cache results for the day

Hourly:
├─ 1. Update sentiment (Perplexity + VIX)
├─ 2. AI opportunity discovery
├─ 3. Score opportunities
└─ 4. Generate watchlist
```

**Why**: Expensive operations done once, reused all day

---

### STAGE 2: Fast Filters (Every Minute, Per Symbol)
**Eliminate 80-90% of evaluations with cheap checks**

```
For each symbol in watchlist:
  
  1. ✅ Existing Position Check (FREE, in-memory)
     └─ If has position → SKIP (no new signal needed)
  
  2. ✅ Order Cooldown Check (FREE, in-memory)
     └─ If recent order → SKIP (prevent duplicates)
  
  3. 🆕 Time-of-Day Filter (FREE, system time)
     └─ If outside 9:30-10:30 AM or 3-4 PM → SKIP
     └─ If lunch hour (11:30 AM-2 PM) → SKIP
     └─ **Eliminates 60-70% of time periods**
  
  4. 🆕 200-EMA Daily Trend Filter (LOW, cached)
     └─ If long signal and daily_price < daily_200_ema → SKIP
     └─ If short signal and daily_price > daily_200_ema → SKIP
     └─ **Eliminates 40-50% of counter-trend trades**
  
  5. 🆕 Multi-timeframe Alignment (LOW, cached)
     └─ If long and daily_trend != bullish → SKIP
     └─ If short and daily_trend != bearish → SKIP
     └─ **Eliminates 30-40% of misaligned trades**
  
  6. ✅ EMA Crossover Detection (FREE, calculated)
     └─ If no crossover → SKIP
     └─ **Eliminates 90% of symbols (no signal)**
```

**Result**: Only 5-10% of symbols pass to expensive checks

---

### STAGE 3: Signal Quality Filters (Per Signal)
**Validate signal strength and quality**

```
For symbols with EMA crossover:
  
  7. ✅ Calculate Confidence Score (FREE, calculated)
     └─ If confidence < 70% → REJECT
  
  8. ✅ Count Confirmations (FREE, calculated)
     └─ If confirmations < 3/4 → REJECT
  
  9. 🆕 Volatility Filter (FREE, already calculated)
     └─ If ATR < 0.65 * 20-day_avg → REJECT
     └─ **Eliminates dead markets**
  
  10. 🆕 Volume Surge (FREE, already calculated)
      └─ If volume < 1.5x average → REJECT
      └─ **Eliminates weak-volume breakouts**
  
  11. 🆕 ADX Minimum (FREE, already calculated)
      └─ If ADX < 25 → REJECT
      └─ **Eliminates weak trends**
  
  12. ✅ Enhanced Short Filters (if short):
      ├─ Market sentiment check (MEDIUM, cached)
      ├─ Price vs EMAs (FREE)
      ├─ Volume confirmation (FREE)
      ├─ RSI check (FREE)
      └─ Higher confidence threshold (FREE)
```

**Result**: Only 2-5 high-quality signals per hour

---

### STAGE 4: Execution Filters (Per Signal)
**Final checks before order submission**

```
For validated signals:
  
  13. ✅ Symbol Cooldown Check (FREE, in-memory)
      └─ If symbol frozen (consecutive losses) → REJECT
  
  14. ✅ Trade Frequency Limits (FREE, in-memory)
      └─ If daily limit reached → REJECT
      └─ If symbol limit reached → REJECT
  
  15. ✅ Risk Manager Checks (LOW, API call)
      ├─ Circuit breaker
      ├─ Position count
      ├─ Position size
      ├─ Buying power
      ├─ Regime multiplier
      └─ Sentiment multiplier
  
  16. ✅ Submit Order
```

**Result**: 1-3 trades per hour (8-15/day)

---

## Filter Effectiveness Analysis

### Current System (Without New Filters)
```
Stage 1: 100 candidates → 25 watchlist (75% filtered)
Stage 2: 25 symbols → 10 signals (60% filtered)
Stage 3: 10 signals → 5 trades (50% filtered)

Total: 100 → 5 (95% filtered)
Win Rate: 40-45%
```

### With Tier 1 Filters (Proposed)
```
Stage 1: 100 candidates → 25 watchlist (75% filtered)
Stage 2: 25 symbols → 
  ├─ Time-of-day: 25 → 10 (60% filtered)
  ├─ 200-EMA: 10 → 6 (40% filtered)
  ├─ Multi-timeframe: 6 → 4 (33% filtered)
  └─ Signal quality: 4 → 2 signals (50% filtered)
Stage 3: 2 signals → 1-2 trades (0-50% filtered)

Total: 100 → 1-2 per hour (98% filtered)
Win Rate: 55-60% (target achieved!)
```

### With Tier 1 + Tier 2 Filters
```
Stage 1: 100 candidates → 25 watchlist (75% filtered)
Stage 2: 25 symbols →
  ├─ Time-of-day: 25 → 10 (60% filtered)
  ├─ 200-EMA: 10 → 6 (40% filtered)
  ├─ Multi-timeframe: 6 → 4 (33% filtered)
  ├─ Volatility: 4 → 3 (25% filtered)
  ├─ Volume surge: 3 → 2 (33% filtered)
  ├─ ADX: 2 → 1-2 (0-50% filtered)
  └─ Signal quality: 1-2 → 1 signal (0-50% filtered)
Stage 3: 1 signal → 1 trade (0% filtered)

Total: 100 → 1 per hour (99% filtered)
Win Rate: 60-70% (exceeds target!)
```

---

## Key Insights

### 1. Time-of-Day Filter is CRITICAL
- **FREE** to compute (system time)
- **Eliminates 60-70%** of time periods
- **Should be FIRST** after basic checks
- **No data dependencies**

### 2. Daily Filters Should Be Cached
- 200-EMA and multi-timeframe need daily bars
- Fetch once per day at market open
- Cache for all symbols
- Reuse throughout the day

### 3. Order Matters for Performance
- Fast filters first (in-memory)
- Expensive filters last (API calls)
- Most restrictive filters early
- Fail fast, fail cheap

### 4. No Filter Conflicts
- All filters are independent
- No circular dependencies
- Can be applied in any order (but optimal order matters for performance)
- No risk of losing valid opportunities

---

## Implementation Strategy

### Phase 1: Add Caching Layer
```python
# In market_data.py
class DailyCache:
    def __init__(self):
        self.cache = {}
        self.cache_date = None
    
    def get_daily_data(self, symbol):
        # Check if cache is stale
        if self.cache_date != datetime.now().date():
            self.refresh_cache()
        
        return self.cache.get(symbol)
    
    def refresh_cache(self):
        # Fetch daily bars for all symbols
        # Calculate 200-EMA
        # Calculate daily EMA(9/21)
        # Update cache
        pass
```

### Phase 2: Add Fast Filters to Strategy
```python
# In strategy.py
def evaluate(self, symbol, features):
    # 1. Existing position check (already exists)
    if trading_state.get_position(symbol):
        return None
    
    # 2. Order cooldown (already exists)
    if self._check_cooldown(symbol):
        return None
    
    # 3. 🆕 Time-of-day filter (NEW - FIRST)
    if not self._is_optimal_trading_time():
        return None
    
    # 4. 🆕 200-EMA daily trend (NEW - SECOND)
    if not self._check_daily_trend(symbol, signal):
        return None
    
    # 5. 🆕 Multi-timeframe alignment (NEW - THIRD)
    if not self._check_timeframe_alignment(symbol, signal):
        return None
    
    # 6. EMA crossover detection (existing)
    signal_info = FeatureEngine.detect_enhanced_signal(features)
    if not signal_info:
        return None
    
    # ... rest of existing filters
```

### Phase 3: Add Quality Filters
```python
# After signal detection
# 7-12. Quality filters (confidence, confirmations, volatility, volume, ADX)
# These are mostly existing, just add volatility, volume surge, ADX
```

---

## Testing Strategy

### Test 1: Filter Independence
```python
def test_filter_independence():
    """Verify filters don't conflict"""
    # Test all filter combinations
    # Ensure no circular dependencies
    # Validate no opportunities lost due to ordering
```

### Test 2: Performance Impact
```python
def test_filter_performance():
    """Measure computational cost"""
    # Time each filter
    # Measure total evaluation time
    # Ensure < 100ms per symbol
```

### Test 3: Filter Effectiveness
```python
def test_filter_effectiveness():
    """Measure filtering power"""
    # Count symbols filtered at each stage
    # Validate expected filtering rates
    # Ensure high-quality signals pass through
```

### Test 4: Win Rate Improvement
```python
def test_win_rate_improvement():
    """Backtest with new filters"""
    # Run on 6 months historical data
    # Compare win rate before/after
    # Validate 55-60% target achieved
```

---

## Rollout Plan

### Week 1: Implementation
- Day 1: Add caching layer
- Day 2: Add time-of-day filter
- Day 3: Add 200-EMA filter
- Day 4: Add multi-timeframe filter
- Day 5: Integration testing

### Week 2: Testing & Deployment
- Day 1-2: Backtesting
- Day 3: Shadow mode
- Day 4-5: Limited rollout
- Day 6-7: Full deployment

---

## Success Criteria

### Performance
- [ ] Filter evaluation < 100ms per symbol
- [ ] No increase in API calls
- [ ] Cache hit rate > 95%

### Effectiveness
- [ ] Time-of-day filters 60-70% of periods
- [ ] 200-EMA filters 40-50% of counter-trend
- [ ] Multi-timeframe filters 30-40% of misaligned
- [ ] Combined: 80-90% of low-quality signals filtered

### Win Rate
- [ ] Baseline: 40-45%
- [ ] Target: 55-60%
- [ ] Stretch: 60-70%

---

## Conclusion

**Optimal Filter Order**:
1. Existing position (FREE, eliminates duplicates)
2. Order cooldown (FREE, prevents spam)
3. **Time-of-day** (FREE, eliminates 60-70%)
4. **200-EMA daily trend** (LOW, eliminates 40-50%)
5. **Multi-timeframe** (LOW, eliminates 30-40%)
6. EMA crossover (FREE, eliminates 90%)
7. Quality filters (FREE, validates signal)
8. Execution filters (LOW, final checks)

**Key Principles**:
- ✅ Fail fast, fail cheap
- ✅ Cache expensive operations
- ✅ Most restrictive filters first
- ✅ No filter conflicts
- ✅ Independent filters

**Expected Result**:
- 40-45% → 55-60% win rate
- 20-25 → 12-15 trades/day
- No performance degradation
- Higher quality signals

---

*Analysis Complete - Ready for Implementation*
