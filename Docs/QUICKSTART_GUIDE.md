# DayTraderAI - Quick Start Guide

## 🚀 Get Trading in 15 Minutes

This guide gets you from zero to paper trading as fast as possible.

---

## Prerequisites Checklist

- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Alpaca Paper Trading account created
- [ ] Supabase account created
- [ ] Git installed

---

## Step 1: Clone & Setup (5 minutes)

```bash
# Clone repository
git clone <your-repo-url>
cd DayTraderAI

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ..
npm install
```

---

## Step 2: Configure API Keys (5 minutes)

### Get Alpaca Keys
1. Go to https://alpaca.markets
2. Sign up for paper trading account
3. Navigate to "Your API Keys"
4. Copy API Key and Secret Key

### Get Supabase Keys
1. Go to https://supabase.com
2. Create new project
3. Go to Settings → API
4. Copy URL, anon key, and service_role key
5. Go to SQL Editor
6. Run the schema from `backend/supabase_schema.sql`

### Get AI Keys (Optional but Recommended)
1. **OpenRouter**: https://openrouter.ai → Get API key
2. **Perplexity**: https://perplexity.ai → Get API key

### Configure .env

```bash
cd backend
cp .env.example .env
nano .env  # or use your favorite editor
```

Edit `.env`:
```bash
# Alpaca (REQUIRED)
ALPACA_API_KEY=your_alpaca_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Supabase (REQUIRED)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here

# OpenRouter (OPTIONAL - for AI analysis)
OPENROUTER_API_KEY=your_openrouter_key_here

# Perplexity (OPTIONAL - for news)
PERPLEXITY_API_KEY=your_perplexity_key_here

# Strategy (DEFAULTS - can customize later)
WATCHLIST=SPY,QQQ,AAPL,MSFT,NVDA
MAX_POSITIONS=20
RISK_PER_TRADE_PCT=0.01
CIRCUIT_BREAKER_PCT=0.05
```

---

## Step 3: Start Trading (2 minutes)

```bash
# From project root
./start_app.sh
```

This starts:
- Backend API on http://localhost:8000
- Frontend UI on http://localhost:5173

---

## Step 4: Verify Everything Works (3 minutes)

### Check Backend
1. Open http://localhost:8000/docs
2. Try `/health` endpoint
3. Should see: `{"status": "healthy"}`

### Check Frontend
1. Open http://localhost:5173
2. Should see dashboard with:
   - Connection status (green)
   - KPI cards (Today's P/L, Win Rate, etc.)
   - Empty positions table
   - Chat interface

### Check Connections
Look for these status indicators in the UI header:
- 🟢 Alpaca: Connected
- 🟢 Supabase: Connected
- 🟢 OpenRouter: Connected (if key provided)
- 🟢 Perplexity: Connected (if key provided)
- 🟢 Streaming: Connected

---

## Step 5: Watch It Trade (Ongoing)

### During Market Hours (9:30 AM - 4:00 PM ET)

**What to Expect**:
- System checks for signals every 60 seconds
- When EMA(9) crosses EMA(21), it generates a signal
- Order submitted automatically
- Position appears in "Open Positions" table
- Trade analysis appears in "Trade Analysis & Rationale"
- Live logs show all activity

**First Trade Timeline**:
```
9:30 AM - Market opens, system activates
9:31 AM - First market data update
10:15 AM - Signal detected on NVDA (example)
10:15 AM - Order submitted
10:15 AM - Order filled
10:15 AM - Position appears in dashboard
10:15 AM - AI generates trade analysis
```

### Outside Market Hours

System will show:
- "Market closed, skipping strategy evaluation" in logs
- No new trades
- Existing positions remain (if any)
- Dashboard still accessible

---

## Step 6: Interact with Copilot

### Try These Commands

**Get Status**:
```
You: status
Copilot: System running. Market open. 3 positions open. Daily P/L: +$245 (+0.18%)
```

**Ask Questions**:
```
You: What's the market doing?
Copilot: SPY trending up (+0.5%), VIX low at 14.2. Bullish sentiment...
```

**Manual Control**:
```
You: close AAPL
Copilot: Closing AAPL position... Done. P/L: +$125 (+0.71%)
```

**Get Help**:
```
You: help
Copilot: Available commands: status, positions, orders, close, buy, sell...
```

---

## Common Issues & Solutions

### Issue: "Backend Disconnected"

**Solution**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not running, restart
cd backend
source venv/bin/activate
python main.py
```

### Issue: "Alpaca: Disconnected"

**Solution**:
- Check API keys in `.env`
- Verify paper trading account is active
- Check Alpaca status: https://status.alpaca.markets

### Issue: "No trades happening"

**Possible Reasons**:
1. Market is closed (only trades 9:30 AM - 4:00 PM ET)
2. No signals detected yet (EMA crossovers are rare)
3. Risk limits reached (max 20 positions)
4. Circuit breaker triggered (-5% daily loss)

**Check**:
- Look at "Live Logs" for activity
- Check "Strategy Guidance" in chat
- Ask copilot: "why no trades?"

### Issue: "Streaming: Disabled"

**Solution**:
- This is normal, system falls back to polling
- Streaming requires additional setup
- Trading still works fine without it

---

## What to Monitor

### Daily (5 minutes)
- [ ] Check dashboard for overall status
- [ ] Review open positions
- [ ] Check daily P/L
- [ ] Read trade analyses

### Weekly (15 minutes)
- [ ] Review win rate trend
- [ ] Check profit factor
- [ ] Review trade journal
- [ ] Adjust watchlist if needed

### Monthly (30 minutes)
- [ ] Full performance review
- [ ] Strategy effectiveness analysis
- [ ] Risk metrics validation
- [ ] Parameter optimization

---

## Next Steps

### Week 1: Observe & Learn
- Let system run automatically
- Watch how it trades
- Read AI analysis for each trade
- Get comfortable with the interface

### Week 2-3: Fill Critical Gaps
Follow [TODO.md](TODO.md) to implement:
1. Trailing stops
2. Dynamic watchlist screener
3. News sentiment filter
4. Auto-recovery system

### Week 4-6: Build ML System
Follow [TODO.md](TODO.md) to implement:
1. Data collection
2. Feature engineering
3. Model training
4. Online learning

### Month 2-3: Validate Performance
- Collect 300+ trades
- Achieve 60%+ win rate
- Validate all metrics
- Prepare for live trading

---

## Emergency Procedures

### Stop All Trading Immediately

**Method 1: UI**
- Click red "Emergency Stop" button
- Confirms all positions closed
- Trading disabled

**Method 2: Chat**
```
You: close all positions
Copilot: Closing all positions... Done.

You: disable trading
Copilot: Trading disabled.
```

**Method 3: Backend**
```bash
curl -X POST http://localhost:8000/emergency/stop
```

### Restart System

```bash
# Stop
pkill -f "python main.py"
pkill -f "npm run dev"

# Start
./start_app.sh
```

### Check Logs

```bash
# Backend logs
tail -f backend/backend.log

# Or in Supabase
# Go to your Supabase project → Table Editor → logs
```

---

## Performance Expectations

### First Week (Learning Phase)
- **Trades**: 5-15 trades
- **Win Rate**: 50-60% (rule-based only)
- **Daily P/L**: -$100 to +$300
- **Purpose**: Data collection

### First Month (Bootstrap Phase)
- **Trades**: 50-100 trades
- **Win Rate**: 55-65%
- **Daily P/L**: -$200 to +$500
- **Purpose**: Build ML training set

### Month 2-3 (ML Active Phase)
- **Trades**: 200-300 trades
- **Win Rate**: 60-70% (ML filtering)
- **Daily P/L**: +$200 to +$800
- **Purpose**: Validate ML improvements

### Month 4+ (Production Phase)
- **Trades**: 300+ trades
- **Win Rate**: 65-75%
- **Daily P/L**: +$500 to +$1500
- **Purpose**: Consistent profitability

**Note**: These are targets, not guarantees. Actual results vary.

---

## Tips for Success

### Do's ✅
- ✅ Start with paper trading
- ✅ Let system run continuously
- ✅ Monitor daily but don't interfere
- ✅ Trust the process
- ✅ Collect 300+ trades before going live
- ✅ Read and understand every trade
- ✅ Keep detailed notes
- ✅ Adjust parameters gradually

### Don'ts ❌
- ❌ Don't use real money yet
- ❌ Don't manually override frequently
- ❌ Don't change strategies mid-testing
- ❌ Don't panic on losing days
- ❌ Don't skip the validation phase
- ❌ Don't ignore risk limits
- ❌ Don't rush to live trading

---

## Getting Help

### Documentation
1. **README.md**: Overview and features
2. **ARCHITECTURE.md**: System design
3. **TODO.md**: Implementation roadmap
4. **This file**: Quick start guide

### Troubleshooting
1. Check logs: `backend/backend.log`
2. Check Supabase logs table
3. Ask copilot: "what's wrong?"
4. Review API docs: http://localhost:8000/docs

### Community
- Open GitHub issue
- Check existing issues
- Share your results

---

## Success Checklist

### Day 1
- [ ] System installed and running
- [ ] All connections green
- [ ] Dashboard accessible
- [ ] Copilot responding

### Week 1
- [ ] First trade executed
- [ ] Trade analysis generated
- [ ] No critical errors
- [ ] Comfortable with interface

### Month 1
- [ ] 50+ trades collected
- [ ] Win rate calculated
- [ ] Performance tracked
- [ ] ML data collection working

### Month 3
- [ ] 300+ trades collected
- [ ] Win rate ≥ 60%
- [ ] Profit factor ≥ 1.5
- [ ] Ready for live trading consideration

---

## Final Checklist Before Live Trading

- [ ] 300+ paper trades completed
- [ ] Win rate ≥ 60%
- [ ] Profit factor ≥ 1.5
- [ ] Max drawdown ≤ 15%
- [ ] Sharpe ratio ≥ 1.0
- [ ] ML models trained and validated
- [ ] All safety systems tested
- [ ] Emergency procedures documented
- [ ] Comfortable with system behavior
- [ ] Financial advisor consulted
- [ ] Risk capital allocated (money you can afford to lose)
- [ ] Regulatory compliance verified

---

## Remember

> **"The goal is not to trade perfectly, but to trade consistently and improve continuously."**

- Start small
- Learn constantly
- Trust the process
- Stay disciplined
- Manage risk first
- Profits will follow

---

**You're now ready to start paper trading!**

Open http://localhost:5173 and watch your autonomous trading system in action.

Good luck! 🚀📈
