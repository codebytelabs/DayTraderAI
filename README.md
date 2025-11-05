# DayTraderAI - Autonomous AI-Powered Day Trading System

> **⚠️ IMPORTANT**: This system is currently in **PAPER TRADING** mode. Do not use with real money until completing the full validation process outlined in TODO.md.

## 🎯 Vision

A fully autonomous AI-powered day trading system that learns and improves continuously with minimal user intervention. The system trades automatically, learns from every trade, and optimizes itself over time.

## 📊 Current Status

- **Paper Trading**: ✅ 85% Ready (can start now)
- **ML Learning System**: ❌ 0% Complete (to be built)
- **Live Trading**: ❌ 60% Ready (needs validation)

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Alpaca Paper Trading Account
- Supabase Account

### Installation

```bash
# Clone repository
git clone <repository-url>
cd DayTraderAI

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# Frontend setup
cd ..
npm install

# Start system
./start_app.sh
```

### Access
- **Dashboard**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Dashboard   │  │    Charts    │  │  AI Copilot  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                   Trading Engine                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Market Data  │  │  Strategy    │  │  Position    │     │
│  │    Loop      │  │    Loop      │  │   Monitor    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                  ML Learning System                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Data      │  │   Models     │  │   Online     │     │
│  │  Collector   │  │  Training    │  │  Learning    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│              External Services                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Alpaca     │  │  Supabase    │  │  OpenRouter  │     │
│  │   Markets    │  │   Database   │  │  Perplexity  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

For detailed architecture diagrams and explanations, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 🤖 How It Works

### Autonomous Trading Flow

1. **Market Opens** (9:30 AM ET)
   - System automatically activates
   - Begins monitoring watchlist symbols

2. **Signal Detection** (Every 60 seconds)
   - Checks for EMA crossovers
   - ML validates signal quality (when trained)
   - Filters low-confidence signals

3. **Order Execution** (Automatic)
   - Calculates position size (1% risk)
   - ML optimizes stop/target (when trained)
   - Submits bracket order to Alpaca

4. **Position Monitoring** (Every 10 seconds)
   - Updates prices in real-time
   - Checks stop loss / take profit
   - Auto-closes when triggered

5. **Learning** (Continuous)
   - Collects trade data
   - Extracts features
   - Retrains models every 100 trades
   - Deploys improvements automatically

6. **Market Closes** (4:00 PM ET)
   - Saves daily metrics
   - Generates performance report
   - Prepares for next day

### User Interaction Levels

**Level 0: Zero Intervention (Default)**
- System runs fully automatically
- User only monitors dashboard
- No action required

**Level 1: Chat Commands**
```
User: "What's the market doing?"
Copilot: "SPY trending up, VIX low, 8 positions open..."

User: "close NVDA"
Copilot: "Closing NVDA position... Done. P/L: +$450"
```

**Level 2: Manual Override**
```
User: "buy 50 AAPL"
Copilot: "Submitting order... Filled at $175.50"
```

**Level 3: Emergency Stop**
- Red button closes all positions
- Trading halted until re-enabled

## 🧠 ML Learning System

### Learning Phases

**Phase 1: Bootstrap (Trades 1-100)**
- Collect data with rule-based strategy
- Build initial training set
- No ML filtering yet

**Phase 2: Initial Training (Trades 100-200)**
- Train first models
- Start filtering signals (70% confidence)
- Validate improvements

**Phase 3: Active Learning (Trades 200-500)**
- Lower threshold to 65%
- Retrain every 100 trades
- Optimize parameters

**Phase 4: Continuous Improvement (Trades 500+)**
- Full ML integration
- Adaptive thresholds
- Strategy optimization
- Auto-parameter tuning

### ML Models

1. **Signal Quality Predictor**
   - Predicts win probability
   - Filters low-quality signals
   - Target: 75% win rate (vs 60% baseline)

2. **Exit Optimizer**
   - Optimizes stop/target placement
   - Adapts to volatility
   - Target: 30% profit factor improvement

3. **Regime Classifier**
   - Detects market regime
   - Selects best strategy
   - Target: Works in all conditions

4. **Risk Predictor**
   - Predicts trade risk
   - Adjusts position size
   - Target: 20% drawdown reduction

### Data Collected Per Trade

- **Technical**: 20 indicators (EMA, RSI, ATR, MACD, etc.)
- **Market Context**: 15 features (SPY, VIX, sector, etc.)
- **Sentiment**: 5 features (news, social, analysts)
- **Temporal**: 5 features (time, day, earnings)
- **Position**: 5 features (exposure, correlation)
- **Outcome**: P/L, hold time, exit reason

**Total**: 50+ features per trade

## 📈 Strategies

### Current (Implemented)

**EMA Crossover**
- Entry: EMA(9) crosses EMA(21)
- Stop: 2× ATR below entry
- Target: 4× ATR above entry
- Best for: Trending markets

### Planned (To Be Implemented)

**Mean Reversion**
- Entry: RSI < 30 or > 70
- Exit: Return to mean
- Best for: Ranging markets

**Breakout**
- Entry: Price breaks resistance + volume
- Exit: Trailing stop
- Best for: Volatile markets

**Options**
- Covered calls (income)
- Protective puts (hedging)
- Best for: Risk management

## 🛡️ Risk Management

### Position Sizing
- Base: 1% risk per trade
- ML-adjusted: 0.5% - 2% based on confidence
- Max: 5% per position

### Exposure Limits
- Max 20 positions simultaneously
- Max 40% in single sector
- Max 60% total capital deployed

### Circuit Breaker
- Triggers at -5% daily drawdown
- Halts new trades
- Existing positions remain (with stops)
- Auto-resets next day

### Stop Loss
- ATR-based (2× ATR)
- Trailing stops (when implemented)
- Never moves against position

## 💬 Chat Commands

### Status & Information
```
status              - Overall system status
positions           - Show open positions
orders              - Show pending orders
performance         - Show today's performance
help                - List available commands
```

### Trading Actions
```
close all           - Close all positions
close AAPL          - Close specific position
cancel order <id>   - Cancel order
buy 50 NVDA         - Manual buy order
sell 25 MSFT        - Manual sell order
```

### Configuration
```
set risk 0.5%       - Adjust risk per trade
set max positions 15 - Adjust max positions
add TSLA            - Add to watchlist
remove QQQ          - Remove from watchlist
enable trading      - Enable trading
disable trading     - Disable trading
```

### Analysis
```
why did you buy AAPL?        - Explain trade reasoning
what's the market sentiment? - Market analysis
show me NVDA analysis        - Symbol-specific analysis
what's the ML confidence?    - ML model status
```

## 📊 Performance Metrics

### Target Metrics (Paper Trading)
- **Win Rate**: ≥ 60%
- **Profit Factor**: ≥ 1.5
- **Max Drawdown**: ≤ 15%
- **Sharpe Ratio**: ≥ 1.0
- **Total Trades**: ≥ 300

### Current Metrics (Live Dashboard)
- Daily P/L
- Win rate
- Profit factor
- Open positions
- Circuit breaker status

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Alpaca
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Supabase
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
SUPABASE_SERVICE_KEY=your_service_key

# OpenRouter (AI)
OPENROUTER_API_KEY=your_key

# Perplexity (News)
PERPLEXITY_API_KEY=your_key

# Strategy
WATCHLIST=SPY,QQQ,AAPL,MSFT,NVDA
MAX_POSITIONS=20
RISK_PER_TRADE_PCT=0.01
CIRCUIT_BREAKER_PCT=0.05

# ML
ML_ENABLED=true
ML_CONFIDENCE_THRESHOLD=0.65
ML_RETRAIN_INTERVAL=100
```

### Adjustable Parameters

**Risk Settings**:
- `risk_per_trade_pct`: 0.5% - 2% (default: 1%)
- `max_positions`: 10 - 30 (default: 20)
- `circuit_breaker_pct`: 3% - 10% (default: 5%)

**Strategy Settings**:
- `ema_short`: 5 - 15 (default: 9)
- `ema_long`: 15 - 30 (default: 21)
- `stop_loss_atr_mult`: 1.5 - 3.0 (default: 2.0)
- `take_profit_atr_mult`: 3.0 - 6.0 (default: 4.0)

**ML Settings**:
- `ml_confidence_threshold`: 0.6 - 0.8 (default: 0.65)
- `ml_retrain_interval`: 50 - 200 (default: 100)

## 📁 Project Structure

```
DayTraderAI/
├── backend/
│   ├── advisory/          # AI analysis (OpenRouter, Perplexity)
│   ├── copilot/           # Chat interface logic
│   ├── core/              # Core clients (Alpaca, Supabase)
│   ├── data/              # Market data management
│   ├── ml/                # ML learning system (TO BE BUILT)
│   │   ├── data_collector.py
│   │   ├── feature_engineer.py
│   │   ├── models/
│   │   │   ├── signal_predictor.py
│   │   │   ├── exit_optimizer.py
│   │   │   ├── regime_classifier.py
│   │   │   └── risk_predictor.py
│   │   └── learning/
│   │       ├── online_learner.py
│   │       ├── performance_tracker.py
│   │       └── strategy_optimizer.py
│   ├── news/              # News fetching and sentiment
│   ├── options/           # Options trading (disabled)
│   ├── screening/         # Stock screener (TO BE BUILT)
│   ├── trading/           # Trading strategies and execution
│   │   ├── trading_engine.py
│   │   ├── strategy.py
│   │   ├── risk_manager.py
│   │   ├── order_manager.py
│   │   └── position_manager.py
│   ├── config.py          # Configuration
│   └── main.py            # FastAPI application
├── components/            # React UI components
│   ├── Dashboard.tsx
│   ├── ChatPanel.tsx
│   ├── PositionsTable.tsx
│   ├── PerformanceChart.tsx
│   └── ...
├── ARCHITECTURE.md        # Detailed architecture documentation
├── TODO.md                # Implementation roadmap
└── README.md              # This file
```

## 🚦 Getting Started

### Step 1: Paper Trading Setup (Week 1)

1. **Install and configure**
   ```bash
   ./setup.sh
   # Edit .env with your API keys
   ```

2. **Start system**
   ```bash
   ./start_app.sh
   ```

3. **Monitor dashboard**
   - Open http://localhost:5173
   - Watch for signals and trades
   - Review AI analysis

4. **Let it run**
   - System trades automatically
   - Collects data for ML training
   - No intervention needed

### Step 2: Fill Critical Gaps (Week 2-3)

Implement in order:
1. Trailing stops
2. Dynamic watchlist screener
3. News sentiment filter
4. Auto-recovery system

See [TODO.md](TODO.md) for detailed tasks.

### Step 3: Build ML System (Week 4-6)

1. Data collection infrastructure
2. Feature engineering
3. Model training
4. Online learning

See [TODO.md](TODO.md) for detailed tasks.

### Step 4: Extended Paper Trading (Month 2-3)

- Run system continuously
- Collect 300+ trades
- Validate performance
- Let ML models improve

### Step 5: Live Trading (Month 4+)

- Complete readiness checklist
- Start with small capital ($1,000)
- Gradually increase if successful
- Monitor closely

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Complete system architecture with diagrams
- **[TODO.md](TODO.md)**: Detailed implementation roadmap
- **API Docs**: http://localhost:8000/docs (when running)

## 🔒 Safety Features

### Multiple Safety Layers

1. **Position Limits**: Max 20 positions, 5% per position
2. **Exposure Limits**: Max 40% per sector, 60% total
3. **Stop Losses**: Every position has automatic stop
4. **Circuit Breaker**: Halts trading at -5% daily loss
5. **Risk Manager**: Validates every trade
6. **ML Filtering**: Rejects low-confidence signals
7. **Emergency Stop**: Manual override button
8. **Auto-Recovery**: Reconciles positions on restart

### What Can Go Wrong?

**System Crashes**
- ✅ Auto-restarts via systemd
- ✅ Positions reconciled on startup
- ✅ No orphaned positions

**Bad Trades**
- ✅ Stop losses limit losses
- ✅ Circuit breaker prevents cascading losses
- ✅ Position limits prevent overexposure

**ML Model Fails**
- ✅ Falls back to rule-based strategy
- ✅ Model validation before deployment
- ✅ Automatic rollback on degradation

**API Failures**
- ✅ Retry logic with exponential backoff
- ✅ Fallback to polling if streaming fails
- ✅ Graceful degradation

## 🎓 Learning Resources

### Understanding the System

1. **Start Here**: Read this README
2. **Architecture**: Review ARCHITECTURE.md
3. **Implementation**: Check TODO.md
4. **Code**: Explore backend/trading/

### Trading Concepts

- **EMA Crossover**: Moving average strategy
- **ATR**: Average True Range (volatility measure)
- **Risk Management**: Position sizing and stops
- **Bracket Orders**: Entry + stop + target in one

### ML Concepts

- **Supervised Learning**: Learning from labeled examples
- **Online Learning**: Continuous model updates
- **Feature Engineering**: Extracting predictive features
- **Model Validation**: Preventing overfitting

## ⚠️ Disclaimers

### Risk Warning

**Trading involves substantial risk of loss.**

- This system is provided for educational purposes
- Past performance does not guarantee future results
- You can lose more than your initial investment
- Only trade with money you can afford to lose
- Paper trading results may not reflect live trading
- Consult a financial advisor before live trading

### No Guarantees

- No guarantee of profits
- No guarantee of specific performance
- No guarantee of system uptime
- No guarantee of ML improvements
- Use at your own risk

### Regulatory Compliance

- Ensure compliance with local regulations
- Pattern day trading rules may apply (US)
- Tax implications vary by jurisdiction
- Consult legal and tax professionals

## 🤝 Contributing

This is a personal project, but suggestions are welcome:

1. Open an issue for bugs or feature requests
2. Submit pull requests for improvements
3. Share your paper trading results
4. Contribute to documentation

## 📞 Support

For issues or questions:

1. Check [ARCHITECTURE.md](ARCHITECTURE.md) for design details
2. Check [TODO.md](TODO.md) for implementation status
3. Review logs in `backend/backend.log`
4. Check Supabase for historical data
5. Open a GitHub issue

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

- **Alpaca Markets**: Paper trading API
- **Supabase**: Database and logging
- **OpenRouter**: AI analysis
- **Perplexity**: News and research
- **React**: UI framework
- **FastAPI**: Backend framework

---

## 🎯 Next Steps

1. **Read** [ARCHITECTURE.md](ARCHITECTURE.md) for system design
2. **Review** [TODO.md](TODO.md) for implementation plan
3. **Start** paper trading to collect data
4. **Build** ML system while trading
5. **Validate** with 300+ trades
6. **Go Live** gradually with small capital

**Remember**: This is a marathon, not a sprint. Take time to validate, learn, and improve before risking real capital.

---

**Current Version**: 0.8.5 (Paper Trading Ready)  
**Last Updated**: January 2025  
**Status**: 🟡 Paper Trading Active, 🔴 Live Trading Not Ready
