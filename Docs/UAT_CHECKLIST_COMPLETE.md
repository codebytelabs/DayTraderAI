# 🎯 COMPLETE UAT CHECKLIST - DayTraderAI

## Test this before going live!

**Date:** _____________
**Tester:** _____________

---

## ✅ **QUICK START TESTS** (30 minutes)

### **1. System Startup**
- [ ] Backend starts without errors
- [ ] Frontend loads successfully
- [ ] All services show "Connected"
- [ ] WebSocket shows "Live" status

### **2. Basic Trading**
- [ ] Place a buy order → Success
- [ ] Place a sell order → Success
- [ ] Close a position → Success
- [ ] Cancel an order → Success

### **3. Bracket Orders**
- [ ] TP/SL shown in positions table
- [ ] TP/SL prices are reasonable
- [ ] Bracket orders created automatically

### **4. Copilot**
- [ ] Ask "What's my status?" → Gets response
- [ ] Model badge shown
- [ ] Confidence score shown

### **5. Real-Time**
- [ ] P/L updates in real-time
- [ ] Order status changes instantly
- [ ] No delays or lag

---

## 🎯 **FULL UAT** (2-3 hours)

See `UAT_CHECKLIST.md` for comprehensive testing.

---

## 💰 **PAPER TRADING VALIDATION** (2 weeks)

### **Week 1:**
- [ ] System runs 5 days without crashes
- [ ] All trades execute correctly
- [ ] Risk management working
- [ ] No critical bugs

### **Week 2:**
- [ ] Win rate > 50%
- [ ] Profit factor > 1.0
- [ ] Max drawdown < 15%
- [ ] Ready for live trading

---

## ✅ **SIGN-OFF**

- [ ] All tests passed
- [ ] Paper trading successful
- [ ] Ready for live deployment

**Approved:** _____________________ Date: _____

