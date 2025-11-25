# 📋 DayTraderAI - Sprint TODO List
**Last Updated:** November 26, 2025  
**Source:** Comprehensive Code Audit

---

## ✅ SPRINT 1: CRITICAL FIXES (COMPLETED)
*Estimated Impact: +$1,300/month*

### 1.1 ✅ Fix Duplicate Confidence Scaling [EASY]
- **File:** `trading/strategy.py` lines 450-470, `utils/dynamic_position_sizer.py`
- **Issue:** Confidence may be applied twice (strategy + position_sizer)
- **Fix:** Audited flow - scaling happens ONLY in strategy.py, position_sizer has explicit comment preventing double-scaling
- **Impact:** Correct position sizing, prevent over-exposure
- **Status:** [x] VERIFIED - Already correctly implemented

### 1.2 ✅ Fix Smart Order Executor NoneType Error [MEDIUM]
- **File:** `trading/order_manager.py`, `config.py`
- **Issue:** Hardcoded to disabled, ignoring config setting
- **Fix:** Updated order_manager.py to read USE_SMART_EXECUTOR from config, removed duplicate config entries
- **Impact:** +$800/month in slippage savings
- **Status:** [x] COMPLETED - Now respects config setting

### 1.3 ✅ Fix AI Validation for Day Trading Context [MEDIUM]
- **File:** `trading/ai_trade_validator.py`, `config.py`
- **Issue:** AI rejects trades due to "large" position sizes (>8%)
- **Fix:** Updated prompt to explain 4x day trading leverage context, raised threshold to 25%, re-enabled AI validation
- **Impact:** +$500/month (avoid bad trades)
- **Status:** [x] COMPLETED - Prompt now understands day trading

---

## ⚠️ SPRINT 2: HIGH PRIORITY (Next Week)
*Estimated Impact: +$700/month*

### 2.1 🔧 Implement Sector Concentration Tracking [MEDIUM]
- **File:** `trading/risk_manager.py` line 280
- **Issue:** `_get_sector_concentration_multiplier()` returns 1.0 always
- **Fix:** 
  - Add symbol → sector mapping
  - Track current sector exposure
  - Reduce size if sector > 30%
  - Block if sector > 40%
- **Impact:** Prevents portfolio crash from sector concentration
- **Status:** [ ] Not Started

### 2.2 🔧 Fix Sentiment Async Handling [MEDIUM]
- **File:** `trading/strategy.py` lines 55-75
- **Issue:** Returns cached/default when event loop running
- **Fix:** Use `asyncio.run_coroutine_threadsafe()` or proper TTL cache
- **Impact:** Reliable sentiment data for trade decisions
- **Status:** [ ] Not Started

### 2.3 🔧 Add Trailing Stop Retry & Verification [MEDIUM]
- **File:** `trading/position_manager.py` lines 280-310
- **Issue:** No retry if Alpaca replace fails, no verification
- **Fix:**
  - Add 3-attempt retry logic
  - Verify new stop price after replace
  - Create stop if none found
- **Impact:** +$400/month (actual profit protection)
- **Status:** [ ] Not Started

### 2.4 ✅ Increase Order Cooldown [EASY]
- **File:** `trading/strategy.py` line 35
- **Issue:** 180 seconds too short, causes whipsaws
- **Fix:** Increase to 300-600 seconds
- **Impact:** +$200/month (fewer whipsaw trades)
- **Status:** [ ] Not Started

### 2.5 ✅ Add EOD Close Strategy Config [EASY]
- **File:** `config.py` + `trading/trading_engine.py`
- **Issue:** Only closes losers, no user choice
- **Fix:** Add `eod_close_strategy` config option
- **Impact:** User control over overnight risk
- **Status:** [ ] Not Started

---

## 📊 SPRINT 3: MEDIUM PRIORITY (Week 3)
*Estimated Impact: +$200/month + Risk Reduction*

### 3.1 🔧 Add Position Rebalancing [MEDIUM]
- **File:** `trading/position_manager.py`
- **Issue:** Winning positions can grow to 30%+ of portfolio
- **Fix:** Trim positions at 2x target size
- **Impact:** Maintains risk balance
- **Status:** [ ] Not Started

### 3.2 ✅ Add Midday Daily Cache Refresh [EASY]
- **File:** `config.py` + `data/daily_cache.py`
- **Issue:** 200-EMA data only refreshed at open
- **Fix:** Add optional midday refresh (12:00 PM ET)
- **Impact:** Fresh trend data for afternoon trades
- **Status:** [ ] Not Started

### 3.3 🔧 Add Correlation Check [HARD]
- **File:** `trading/risk_manager.py`
- **Issue:** Can hold 5 correlated tech stocks
- **Fix:** Add correlation matrix, block highly correlated entries
- **Impact:** True diversification
- **Status:** [ ] Not Started

---

## 💡 SPRINT 4: LOW PRIORITY (Week 4)
*Nice to Have - Quality of Life*

### 4.1 ✅ Add Trade Journal Export [EASY]
- **File:** `api/routes.py` (new endpoint)
- **Issue:** Hard to analyze performance externally
- **Fix:** Add `/api/export/trades` endpoint (CSV/JSON)
- **Impact:** Better performance analysis
- **Status:** [ ] Not Started

### 4.2 🔧 Add Drawdown Recovery Mode [MEDIUM]
- **File:** `trading/risk_manager.py`
- **Issue:** Same sizing after losses
- **Fix:** Reduce position size by 50% after 3% drawdown
- **Impact:** Faster recovery from losing streaks
- **Status:** [ ] Not Started

### 4.3 ✅ Add Weekend Position Review [EASY]
- **File:** `trading/trading_engine.py`
- **Issue:** Positions held over weekend without review
- **Fix:** Friday 3:30 PM alert/close option
- **Impact:** Avoid weekend gap risk
- **Status:** [ ] Not Started

---

## ✅ COMPLETED FIXES

### Session: November 26, 2025 (Sprint 1)
- [x] **Smart Order Executor Re-enabled** - Fixed order_manager.py to respect config, removed duplicate config entries
- [x] **AI Validation Fixed** - Updated prompt to understand 4x day trading leverage, raised position threshold from 8% to 25%
- [x] **Confidence Scaling Verified** - Confirmed scaling happens only in strategy.py (position_sizer has explicit guard)

### Previous Sessions
- [x] **Partial Profit Tiny Position Bug** - Now checks min position value
- [x] **ALGN Order De