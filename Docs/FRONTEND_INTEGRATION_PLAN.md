# Frontend-Backend Integration Plan

## Current Status

### ✅ Backend Endpoints Available
- `/metrics` - Trading metrics
- `/positions` - Open positions
- `/orders` - Orders
- `/account` - Account info
- `/health` - Health check
- `/engine/status` - Engine status

### ❌ Missing Backend Endpoints
- `/logs` - System logs (not implemented)
- `/advisories` - AI advisories (not implemented)
- `/analyses` - Trade analyses (not implemented)

### ❌ Frontend Status
- Using SIMULATOR instead of real backend
- `useBackendTrading` hook exists but not used
- `TradingContext` needs to be updated

## Integration Strategy

### Option 1: Quick Integration (RECOMMENDED)
**Connect what exists now, add missing features later**

1. Update `TradingContext` to use `useBackendTrading`
2. Use empty arrays for logs, advisories, analyses
3. Test with real trading data
4. Add missing endpoints later if needed

**Pros:**
- Fast (5 minutes)
- Shows real trading data immediately
- Can test UAT now

**Cons:**
- No logs/advisories/analyses initially
- Need to add later

### Option 2: Complete Integration
**Add all endpoints first, then connect**

1. Add `/logs`, `/advisories`, `/analyses` endpoints to backend
2. Update `useBackendTrading` to fetch all data
3. Update `TradingContext`
4. Test everything

**Pros:**
- Complete feature set
- All data available

**Cons:**
- Takes longer (30-60 minutes)
- More complex
- Delays UAT testing

## Recommendation: Option 1

**Reason:** The core trading functionality (positions, orders, metrics) is what matters for UAT. Logs and advisories are nice-to-have but not critical for validating the trading system works.

## Implementation Steps (Option 1)

### Step 1: Update TradingContext (5 minutes)

**File:** `state/TradingContext.tsx`

**Changes:**
1. Import `useBackendTrading` instead of `useTradingSimulator`
2. Use backend hook
3. Provide empty arrays for missing data
4. Add connection status

### Step 2: Test Integration (5 minutes)

1. Start backend: `cd backend && source venv/bin/activate && python main.py`
2. Start frontend: `npm run dev`
3. Verify:
   - Real positions display (10 positions)
   - Real equity ($133,166.07)
   - Real daily P/L
   - Data updates every 5 seconds

### Step 3: UAT Testing (Ready!)

Once connected:
- ✅ Real trading data
- ✅ Real positions
- ✅ Real orders
- ✅ Real metrics
- ✅ Close position works
- ✅ Cancel order works
- ✅ Place order works

## What to Expect After Integration

### Dashboard Will Show:
- **Real Equity:** $133,166.07 (from Alpaca)
- **Real Positions:** 10 open positions
- **Real Daily P/L:** Actual trading performance
- **Real Orders:** Live orders from Alpaca
- **Win Rate:** Calculated from real trades
- **Profit Factor:** Real performance metrics

### What Won't Work Initially:
- Logs panel (empty)
- Advisories panel (empty)
- Trade analyses (empty)
- Chat copilot (needs backend endpoint)

### Can Add Later:
- Logs endpoint
- Advisories endpoint
- Analyses endpoint
- Chat/copilot endpoint

## Decision Point

**Do you want to:**

**A) Quick Integration (5 min) → UAT Now**
- Connect what exists
- Test real trading immediately
- Add missing features later

**B) Complete Integration (30-60 min) → UAT Later**
- Add all endpoints first
- Complete feature set
- Test everything together

**Recommendation: Option A** - Get UAT started with real trading data, add nice-to-have features later.

What would you like to do?
