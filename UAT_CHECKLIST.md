# UAT Testing Checklist

## Pre-Launch Checklist

### Backend
- [ ] Backend running on port 8006
- [ ] All APIs responding (health, metrics, positions, orders, logs, advisories, analyses)
- [ ] Trading engine started
- [ ] Alpaca connected ($133k equity, 10 positions)
- [ ] Supabase connected
- [ ] OpenRouter configured (3 models)
- [ ] Perplexity configured

### Frontend
- [ ] Frontend running on port 5173
- [ ] Connected to backend (no red banner)
- [ ] Real data displaying (not simulator)
- [ ] No console errors

## UAT Test Cases

### 1. Dashboard Display ✅
**Expected:**
- [ ] Equity: $133,166.07 (real from Alpaca)
- [ ] Daily P/L: Real trading performance
- [ ] Win Rate: Calculated from real trades
- [ ] Profit Factor: Real metrics
- [ ] Open Positions: 10 positions displayed
- [ ] Performance chart showing real data
- [ ] Data updates every 5 seconds

**Test:**
1. Open http://localhost:5173
2. Verify all metrics match backend
3. Wait 5 seconds, verify data refreshes
4. Check browser console for errors

### 2. Positions Table ✅
**Expected:**
- [ ] 10 real positions from Alpaca
- [ ] Each position shows: symbol, qty, side, entry price, current price, P/L
- [ ] Close button works

**Test:**
1. Verify all 10 positions display
2. Check P/L calculations are correct
3. Click "Close" on a position (DON'T ACTUALLY CLOSE IN PRODUCTION!)
4. Verify API call is made

### 3. Orders Table ✅
**Expected:**
- [ ] Real orders from Alpaca
- [ ] Each order shows: symbol, qty, side, type, status
- [ ] Cancel button works

**Test:**
1. Verify orders display
2. Check order status is accurate
3. Click "Cancel" on an order (if any)
4. Verify API call is made

### 4. Logs Panel ✅
**Expected:**
- [ ] System logs display
- [ ] Logs update in real-time
- [ ] Shows trading events, errors, info

**Test:**
1. Verify logs are visible
2. Check log levels (INFO, ERROR, WARNING)
3. Verify timestamps are recent
4. Wait for new logs to appear

### 5. Advisories Panel ✅
**Expected:**
- [ ] AI advisories display
- [ ] Shows trade analysis from OpenRouter
- [ ] Includes confidence scores

**Test:**
1. Verify advisories display
2. Check content is relevant
3. Verify model names shown
4. Check timestamps

### 6. Trade Analyses ✅
**Expected:**
- [ ] Recent trade analyses display
- [ ] Shows entry/exit analysis
- [ ] Includes P/L for completed trades

**Test:**
1. Verify analyses display
2. Check analysis content
3. Verify P/L calculations
4. Check timestamps

### 7. Chat Copilot ✅
**Expected:**
- [ ] Chat input works
- [ ] Sends message to backend
- [ ] Receives AI response
- [ ] Response is contextual

**Test:**
1. Type "What's my current performance?"
2. Send message
3. Verify response from OpenRouter
4. Check response mentions real metrics
5. Try: "Should I take more positions?"
6. Verify contextual response

### 8. Real-Time Updates ✅
**Expected:**
- [ ] Data refreshes every 5 seconds
- [ ] Positions update
- [ ] Metrics update
- [ ] Logs append
- [ ] No flickering or errors

**Test:**
1. Watch dashboard for 30 seconds
2. Verify data updates smoothly
3. Check network tab for API calls
4. Verify no errors in console

### 9. Connection Status ✅
**Expected:**
- [ ] Shows "Connected" when backend is up
- [ ] Shows error banner when backend is down
- [ ] Reconnects automatically

**Test:**
1. Verify no error banner initially
2. Stop backend: `kill <BACKEND_PID>`
3. Verify red error banner appears
4. Restart backend
5. Verify banner disappears

### 10. Trading Controls ✅
**Expected:**
- [ ] Can place orders
- [ ] Can close positions
- [ ] Can cancel orders
- [ ] Risk manager validates

**Test:**
1. Try placing a small order (1 share)
2. Verify risk check passes/fails appropriately
3. Check order appears in orders table
4. Verify backend logs the action

## Performance Tests

### Load Test
- [ ] Dashboard loads in < 2 seconds
- [ ] API calls complete in < 500ms
- [ ] No memory leaks after 5 minutes
- [ ] Smooth scrolling and interactions

### Stress Test
- [ ] Multiple rapid API calls don't crash
- [ ] Backend handles concurrent requests
- [ ] Frontend doesn't freeze

## Security Tests

### API Security
- [ ] CORS configured correctly
- [ ] No sensitive data in logs
- [ ] API keys not exposed in frontend
- [ ] Proper error handling

## Production Readiness

### Backend
- [ ] All integrations validated (16/16 tests passed)
- [ ] Trading engine running
- [ ] Risk management active
- [ ] Circuit breakers configured
- [ ] Logging working
- [ ] Error handling robust

### Frontend
- [ ] Connected to real backend
- [ ] All features working
- [ ] No simulator code active
- [ ] Error handling robust
- [ ] Loading states implemented
- [ ] Connection status visible

### Documentation
- [ ] README updated
- [ ] API documentation complete
- [ ] Configuration guide available
- [ ] Troubleshooting guide available

## Sign-Off

### Functional Testing
- [ ] All features work as expected
- [ ] No critical bugs
- [ ] Performance acceptable
- [ ] Security validated

### Business Requirements
- [ ] Shows real trading data
- [ ] Risk management working
- [ ] AI analysis integrated
- [ ] Real-time updates working

### Ready for Production
- [ ] All tests passed
- [ ] Documentation complete
- [ ] Monitoring in place
- [ ] Backup plan ready

## Final Approval

**Tested By:** _________________  
**Date:** _________________  
**Status:** ⬜ APPROVED ⬜ NEEDS WORK  
**Notes:** _________________

---

## Quick Start Commands

```bash
# Start everything
./start_app.sh

# Check backend
curl http://localhost:8006/health

# Check frontend
open http://localhost:5173

# View logs
tail -f backend.log
tail -f frontend.log

# Stop everything
kill <BACKEND_PID> <FRONTEND_PID>
```

## Success Criteria

✅ **READY FOR UAT** when:
1. All backend tests pass (16/16)
2. Frontend connects successfully
3. Real trading data displays
4. All features work
5. No critical errors
6. Performance acceptable

🎉 **READY FOR PRODUCTION** when:
1. All UAT tests pass
2. Security validated
3. Documentation complete
4. Monitoring configured
5. Backup plan ready
