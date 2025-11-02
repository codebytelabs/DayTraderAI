# Frontend-Backend Integration Check

## Current Status: ❌ NOT CONNECTED

### Issue Found
The frontend is currently using **SIMULATED DATA** instead of the real backend.

## Files Analysis

### ✅ Backend Hook Ready (`hooks/useBackendTrading.ts`)
- ✅ API calls to `http://localhost:8006`
- ✅ Fetches metrics, positions, orders
- ✅ Polls every 5 seconds
- ✅ Transforms backend data to frontend format
- ✅ Implements closePosition, cancelOrder, placeOrder

### ❌ TradingContext Using Simulator (`state/TradingContext.tsx`)
**Current:** Uses `useTradingSimulator` (fake data)
**Should Use:** `useBackendTrading` (real data)

### Components Status
- ✅ Dashboard.tsx - Ready (uses TradingContext)
- ✅ All components - Ready (use TradingContext)

## What Needs to Change

### 1. Replace Simulator with Backend in TradingContext

**File:** `state/TradingContext.tsx`

**Current (Line ~35):**
```typescript
const {
  stats,
  performanceData,
  positions,
  orders,
  logs,
  advisories,
  tradeAnalyses,
  closePosition,
  cancelOrder,
  placeOrder,
  config: simConfig,
} = useTradingSimulator({
  universe: watchlist,
  maxPositions: config.strategy.maxPositions,
  riskPerTradePct: config.strategy.riskPerTradePct,
});
```

**Should Be:**
```typescript
const {
  stats,
  positions,
  orders,
  logs,
  advisories,
  tradeAnalyses,
  performanceData,
  closePosition,
  cancelOrder,
  placeOrder,
  isConnected,
  error,
} = useBackendTrading();
```

### 2. Update Imports

**Remove:**
```typescript
import { useTradingSimulator } from '../simulation/useTradingSimulator';
```

**Add:**
```typescript
import { useBackendTrading } from '../hooks/useBackendTrading';
```

### 3. Update Interface

**Current:**
```typescript
stats: SimulatorStats;
```

**Should Be:**
```typescript
stats: BackendStats;
isConnected: boolean;
error: string | null;
```

## Missing Features in Backend Hook

### ❌ Logs Not Implemented
Backend hook doesn't fetch logs. Need to add:
```typescript
const logsRes = await fetch(`${API_BASE}/logs`);
```

### ❌ Advisories Not Implemented
Backend hook doesn't fetch advisories. Need to add:
```typescript
const advisoriesRes = await fetch(`${API_BASE}/advisories`);
```

### ❌ Trade Analyses Not Implemented
Backend hook doesn't fetch trade analyses. Need to add:
```typescript
const analysesRes = await fetch(`${API_BASE}/analyses`);
```

## Backend API Endpoints Needed

Check if these exist in `backend/main.py`:
- ✅ `/metrics` - EXISTS
- ✅ `/positions` - EXISTS
- ✅ `/orders` - EXISTS
- ❓ `/logs` - NEED TO CHECK
- ❓ `/advisories` - NEED TO CHECK
- ❓ `/analyses` - NEED TO CHECK

## Action Plan

### Step 1: Check Backend Endpoints
```bash
curl http://localhost:8006/logs
curl http://localhost:8006/advisories
curl http://localhost:8006/analyses
```

### Step 2: Add Missing Endpoints (if needed)
Add to `backend/main.py`:
- GET /logs - Return recent logs
- GET /advisories - Return recent advisories
- GET /analyses - Return recent trade analyses

### Step 3: Update useBackendTrading Hook
Add fetching for logs, advisories, and analyses

### Step 4: Update TradingContext
Replace simulator with backend hook

### Step 5: Test Frontend
- Start backend: `cd backend && source venv/bin/activate && python main.py`
- Start frontend: `npm run dev`
- Verify real data displays

## Expected Result

After integration:
- ✅ Dashboard shows REAL trading data
- ✅ Positions from Alpaca (10 positions, $133k equity)
- ✅ Real-time updates every 5 seconds
- ✅ Real orders, metrics, performance
- ✅ Connection status indicator
- ✅ Error handling

## Testing Checklist

- [ ] Backend running on port 8006
- [ ] Frontend connects successfully
- [ ] Real positions display (10 positions)
- [ ] Real equity displays ($133,166.07)
- [ ] Real daily P/L displays
- [ ] Orders display correctly
- [ ] Close position works
- [ ] Cancel order works
- [ ] Place order works
- [ ] Data updates every 5 seconds
- [ ] Connection status shows "Connected"
- [ ] No console errors

## Next Steps

1. Check backend endpoints
2. Add missing endpoints if needed
3. Update useBackendTrading hook
4. Update TradingContext
5. Test integration
6. Verify all features work
7. Ready for UAT
