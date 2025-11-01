# DayTraderAI Execution Plan

## Mission
Build a production-grade day trading bot that actually makes money. Current state: beautiful frontend simulator. Goal: real Alpaca trading with bulletproof risk management.

## Current Status (Updated)
✅ Frontend dashboard with simulator
✅ UI for positions, orders, charts, logs
✅ Settings management
✅ Backend service (FastAPI)
✅ Alpaca integration (paper trading)
✅ Supabase integration (database)
✅ Risk management system
✅ Order management (idempotent)
✅ Strategy engine (EMA crossover)
✅ OpenRouter + Perplexity (tested models)
❌ Automation loops (market data, strategy, position monitoring)
❌ Frontend-backend integration
❌ End-to-end testing with real data

## Architecture Overview
```
Frontend (React/TS) ←→ Backend (Python/FastAPI) ←→ Alpaca API
                              ↓
                         Supabase DB
                              ↓
                    LLMs (Perplexity/OpenRouter)
```

## Phase 1: Backend Foundation (THIS WEEK)
**Goal: Get real paper trading working**

### Backend Structure
```
backend/
├── main.py                 # FastAPI server
├── config.py              # Settings from .env
├── requirements.txt       # Dependencies
├── core/
│   ├── alpaca_client.py  # Alpaca wrapper
│   ├── supabase_client.py # DB wrapper
│   └── state.py          # Shared state
├── trading/
│   ├── risk_manager.py   # Pre-trade checks
│   ├── order_manager.py  # Order execution
│   ├── position_manager.py # Position tracking
│   └── strategy.py       # EMA strategy
├── data/
│   ├── market_data.py    # Data ingestion
│   └── features.py       # Indicators
├── advisory/
│   ├── perplexity.py     # News
│   └── openrouter.py     # LLM
└── api/
    ├── routes.py         # REST API
    └── websocket.py      # Real-time updates
```

### COMPLETED ✅
- [x] Plan architecture and file structure
- [x] Setup Python backend with FastAPI
- [x] Implement Alpaca client (paper trading)
- [x] Create Supabase schema and client
- [x] Build RiskManager with core checks
- [x] Implement OrderManager with idempotency
- [x] Create feature computation engine
- [x] Build EMA strategy engine
- [x] Add REST API endpoints
- [x] OpenRouter client with tested models
- [x] Perplexity client for news
- [x] Configuration system (.env)
- [x] Test OpenRouter models (REAL testing)
- [x] Optimize model selection

### JUST COMPLETED ✅
- [x] **Market data ingestion loop** - Fetch bars continuously
- [x] **Strategy evaluation loop** - Auto-detect signals and trade
- [x] **Position monitoring loop** - Auto-close stops/targets
- [x] **Position manager module** - Track and update positions
- [x] **Trading engine** - Orchestrates all automation loops
- [x] **Metrics loop** - Calculate and store performance
- [x] **Engine control endpoints** - Start/stop/status API

### READY FOR TESTING 🧪
- [ ] **Run setup** - Install dependencies (./setup.sh)
- [ ] **Run test suite** - Automated tests (./test_suite.sh)
- [ ] **Unit tests** - Test each module independently
- [ ] **API tests** - Test all endpoints with real data
- [ ] **Integration tests** - Test full trading cycle
- [ ] **Use case tests** - Validate expected behavior
- [ ] **Fix issues** - Debug and resolve problems
- [ ] **UAT ready** - Confirm ready for user testing

### PENDING (Nice to Have - Later)
- [ ] **Frontend API integration** - Replace simulator with real backend
- [ ] **WebSocket** - Real-time updates to frontend
- [ ] **Backtesting framework** - Historical testing
- [ ] **Advanced analytics** - More metrics and charts

### Week 2 Tasks (Strategy Execution)
- [ ] Position monitoring with auto-stops
- [ ] WebSocket for real-time updates
- [ ] Performance metrics calculation
- [ ] Frontend API integration
- [ ] Replace simulator with real backend
- [ ] Add manual trading controls
- [ ] Implement emergency kill switch
- [ ] Test full trading cycle

### Week 3 Tasks (Advisory & Enhancement)
- [ ] Perplexity news integration
- [ ] OpenRouter advisory system
- [ ] Enhanced risk controls (sector, correlation)
- [ ] Backtesting framework setup
- [ ] Walk-forward validation
- [ ] Slippage and fill tracking
- [ ] Mark-to-market analytics

### Week 4 Tasks (Production Readiness)
- [ ] Comprehensive error handling
- [ ] Monitoring and alerting
- [ ] Paper→live promotion checklist
- [ ] Documentation and runbooks
- [ ] Disaster recovery procedures
- [ ] Performance optimization
- [ ] Security audit

---

## Critical Implementation Details

### Risk Management (Non-Negotiable)
Every order MUST pass these checks:
1. Position size ≤ 2% equity at risk
2. Total positions ≤ max_positions
3. Daily loss < 5% circuit breaker
4. Symbol liquidity filters (volume, spread)
5. Sufficient buying power
6. Market open and not halted

### Order Idempotency
```python
def generate_order_id(symbol, side, qty, price, timestamp_minute):
    payload = f"{symbol}|{side}|{qty}|{price:.4f}|{timestamp_minute}"
    return hashlib.sha256(payload.encode()).hexdigest()[:24]
```

### Fail-Safe Defaults
- If Alpaca API fails → halt trading
- If position sync fails → halt new trades
- If data feed gaps → skip affected symbols
- Emergency kill switch → close all positions

### Supabase Schema
```sql
-- trades: all executed trades
-- positions: current positions
-- orders: order history
-- market_data: OHLCV bars
-- features: computed indicators
-- advisories: LLM insights
-- metrics: performance stats
-- config: strategy parameters
```

---

## Milestones
- **M1 (Week 1)**: Backend running, paper trading live
- **M2 (Week 2)**: Frontend connected, full trading cycle
- **M3 (Week 3)**: Advisory system, enhanced analytics
- **M4 (Week 4)**: Production-ready, promotion gates passed

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, alpaca-py, supabase-py, pandas, numpy
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS
- **Database**: Supabase (PostgreSQL)
- **Trading**: Alpaca (paper → live)
- **LLMs**: Perplexity (news), OpenRouter (advisory)

## Environment Variables (.env)
```bash
# Alpaca
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # paper trading

# Supabase
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# LLMs
PERPLEXITY_API_KEY=your_key
OPENROUTER_API_KEY=your_key

# Strategy
WATCHLIST=SPY,QQQ,AAPL,MSFT,NVDA,TSLA,AMD,GOOG,AMZN,META
MAX_POSITIONS=5
RISK_PER_TRADE_PCT=0.01
CIRCUIT_BREAKER_PCT=0.05

# Server
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173
```

## Getting Started (After Backend Built)
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your keys
python main.py

# Frontend (separate terminal)
npm run dev
```

## References
- Blueprint: [`DayTraderAI_idea.md`](./DayTraderAI_idea.md)
- Frontend: [`README.md`](./README.md)

---

**Remember**: Paper trade extensively. Measure everything. Never risk more than you can afford to lose. This is experimental software. 🚀
