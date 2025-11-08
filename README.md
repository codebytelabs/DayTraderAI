# 🤖 DayTraderAI - Autonomous AI-Powered Trading System

> **A fully autonomous, AI-driven day trading system that combines real-time market analysis, machine learning, and intelligent risk management to execute high-probability trades 24/7.**

[![Status](https://img.shields.io/badge/status-production-success)]()
[![Python](https://img.shields.io/badge/python-3.10+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
4. [How It Works](#how-it-works)
5. [AI & Intelligence Layers](#ai--intelligence-layers)
6. [Trading Strategy](#trading-strategy)
7. [Risk Management](#risk-management)
8. [Configuration & Controls](#configuration--controls)
9. [APIs & Integrations](#apis--integrations)
10. [Installation & Setup](#installation--setup)
11. [Usage](#usage)
12. [Monitoring & Analytics](#monitoring--analytics)
13. [Advanced Features](#advanced-features)
14. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

**DayTraderAI** is a sophisticated algorithmic trading system that autonomously:
- Discovers trading opportunities using AI (Perplexity)
- Analyzes market sentiment in real-time
- Executes trades with intelligent position sizing
- Manages risk with multi-layer protection
- Learns from every trade (ML Shadow Mode)
- Adapts to changing market conditions

### What Makes It Special

- **🤖 AI-Powered Discovery**: Uses Perplexity AI to scan markets and find opportunities
- **🧠 Dual-Source Sentiment**: Combines AI analysis with VIX for market direction
- **📊 Multi-Cap Strategy**: Trades large, mid, and small-cap stocks
- **🎯 Quality Over Quantity**: Strict filters ensure only high-probability trades
- **🛡️ Intelligent Risk Management**: Dynamic position sizing based on confidence
- **📈 ML Learning System**: Continuously improves from historical performance
- **⚡ Real-Time Execution**: Sub-second trade execution with bracket orders

---

## 🚀 Key Features

### Core Trading Features

#### 1. **AI Opportunity Discovery**
- Perplexity AI scans entire market hourly
- Discovers 50-100 opportunities across all market caps
- Provides fundamental catalysts and technical setups
- Real-time news and sentiment integration

#### 2. **Multi-Layer Quality Filtering**
```
Stage 1: AI Discovery (50-100 candidates)
    ↓
Stage 2: Technical Scoring (25-30 pass, score 80+)
    ↓
Stage 3: Signal Confirmation (15-20 pass, 70% confidence, 3/4 indicators)
    ↓
Stage 4: Risk Checks (10-15 pass, position limits, buying power)
    ↓
Stage 5: Execution (5-10 trades, highest quality only)
```

#### 3. **Intelligent Position Sizing**
- **Confidence-Based**: 70% confidence = 1.0% risk, 90% = 2.0% risk
- **Dynamic Adjustment**: Scales with market conditions
- **Risk-Adjusted**: Considers volatility, sentiment, regime
- **Capital Efficient**: Optimal allocation across positions

#### 4. **Automated Risk Management**
- **Bracket Orders**: Every trade has stop-loss and take-profit
- **Circuit Breaker**: Halts trading if daily loss exceeds 5%
- **Position Limits**: Max 20 positions, 10% per position
- **Trade Frequency Limits**: 30 trades/day, 2 per symbol
- **Market Direction Filter**: Blocks shorts in uptrends

#### 5. **Real-Time Market Data**
- Live streaming via Alpaca WebSocket
- 1-minute bar updates
- Quote and trade data
- Volume and price action monitoring

---


## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  Dashboard | Charts | Orders | Positions | Command Palette      │
└────────────────────────┬────────────────────────────────────────┘
                         │ WebSocket + REST API
┌────────────────────────┴────────────────────────────────────────┐
│                    Backend (FastAPI + Python)                    │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Trading Engine (Core)                       │   │
│  │  • Strategy Loop (1 min)                                │   │
│  │  • Position Monitor (15 sec)                            │   │
│  │  • Market Data Loop (1 min)                             │   │
│  │  • Scanner Loop (1 hour)                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ AI Discovery │  │  Sentiment   │  │  ML Shadow   │         │
│  │  (Perplexity)│  │  Aggregator  │  │    Mode      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Strategy   │  │     Risk     │  │   Position   │         │
│  │   (EMA 9/21) │  │   Manager    │  │    Manager   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    Order     │  │   Market     │  │  Streaming   │         │
│  │   Manager    │  │     Data     │  │   Manager    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└───────────────────────┬──────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
   │ Alpaca  │    │Supabase │    │Perplexity│
   │  API    │    │   DB    │    │   AI    │
   └─────────┘    └─────────┘    └─────────┘
```

### Module Breakdown

#### **Core Modules**

1. **Trading Engine** (`backend/trading/trading_engine.py`)
   - Orchestrates all trading operations
   - Runs 4 concurrent loops (strategy, monitor, data, scanner)
   - Manages watchlist and position tracking
   - Coordinates all subsystems

2. **Strategy** (`backend/trading/strategy.py`)
   - EMA(9/21) crossover with multi-indicator confirmation
   - Signal generation and validation
   - Position sizing logic
   - Entry/exit decision making

3. **Risk Manager** (`backend/trading/risk_manager.py`)
   - Pre-trade risk checks
   - Circuit breaker monitoring
   - Position limit enforcement
   - Sentiment-adjusted risk

4. **Order Manager** (`backend/trading/order_manager.py`)
   - Order submission and tracking
   - Bracket order creation
   - Order status monitoring
   - Execution logging

5. **Position Manager** (`backend/trading/position_manager.py`)
   - Position synchronization with Alpaca
   - P&L tracking
   - Position lifecycle management
   - Exit monitoring

#### **AI & Intelligence Modules**

6. **AI Opportunity Finder** (`backend/scanner/ai_opportunity_finder.py`)
   - Perplexity AI integration
   - Market-wide opportunity discovery
   - Multi-cap analysis (large/mid/small)
   - Catalyst and technical analysis

7. **Sentiment Aggregator** (`backend/indicators/sentiment_aggregator.py`)
   - Dual-source sentiment (Perplexity + VIX)
   - Market direction determination
   - Fear/Greed index integration
   - Sentiment scoring (0-100)

8. **Opportunity Scanner** (`backend/scanner/opportunity_scanner.py`)
   - Coordinates AI discovery
   - Filters and scores opportunities
   - Generates dynamic watchlist
   - Market-aware scanning

9. **Opportunity Scorer** (`backend/scanner/opportunity_scorer.py`)
   - 120-point scoring system
   - Technical, momentum, volume, volatility analysis
   - Market regime and sentiment integration
   - Grade assignment (A+ to F)

10. **ML Shadow Mode** (`backend/ml/shadow_mode.py`)
    - Makes predictions for all trades
    - Logs predictions to database
    - Tracks accuracy vs actual outcomes
    - Zero impact on trading (learning only)

#### **Data & Indicators**

11. **Market Data Manager** (`backend/data/market_data.py`)
    - Historical and real-time data fetching
    - Bar aggregation and caching
    - Feature calculation coordination
    - Data quality management

12. **Feature Engine** (`backend/data/features.py`)
    - Technical indicator calculation
    - Signal detection and confirmation
    - Multi-indicator analysis
    - Feature caching

13. **Indicators** (`backend/indicators/`)
    - **Trend**: EMA, SMA, trend detection
    - **Momentum**: RSI, MACD, ADX, DMI
    - **Volume**: Volume ratio, OBV, spikes
    - **VWAP**: Volume-weighted average price
    - **Market Regime**: Trending/ranging/choppy detection
    - **Market Sentiment**: Fear/greed analysis

#### **Streaming & Real-Time**

14. **Stream Manager** (`backend/streaming/stream_manager.py`)
    - WebSocket connection management
    - Real-time data distribution
    - Reconnection handling
    - Stream health monitoring

15. **Stock Stream** (`backend/streaming/stock_stream.py`)
    - Quote, trade, and bar subscriptions
    - Data parsing and validation
    - Event broadcasting
    - Buffer management

16. **Broadcaster** (`backend/streaming/broadcaster.py`)
    - WebSocket server for frontend
    - Real-time updates to UI
    - Event queuing and delivery
    - Connection management

---

## 🔄 How It Works

### Complete Trading Workflow

#### **Phase 1: Market Analysis (Every Hour)**

```
1. AI Discovery Trigger
   ↓
2. Sentiment Aggregator
   • Queries Perplexity for market sentiment
   • Checks VIX for fear/greed
   • Calculates composite score (0-100)
   • Determines market direction (bullish/bearish/neutral)
   ↓
3. AI Opportunity Finder
   • Sends query to Perplexity AI
   • Requests opportunities across all market caps
   • Receives 50-100 candidates with:
     - Symbol and price
     - Fundamental catalyst
     - Technical setup
     - Direction (long/short)
     - Market cap tier
   ↓
4. Opportunity Scanner
   • Fetches market data for all candidates
   • Calculates technical indicators
   • Scores each opportunity (0-120)
   • Filters by minimum score (80+)
   • Generates top 20-25 watchlist
   ↓
5. Watchlist Update
   • Updates trading engine watchlist
   • Subscribes to real-time data streams
   • Logs opportunities to database
```

#### **Phase 2: Signal Generation (Every Minute)**

```
1. Market Data Update
   • Fetches latest 1-min bars for watchlist
   • Updates technical indicators
   • Calculates features (EMA, RSI, MACD, etc.)
   ↓
2. Strategy Evaluation (for each symbol)
   • Checks if already in position (skip if yes)
   • Detects EMA(9/21) crossover
   • Validates with 4 confirmations:
     a. RSI (30-70 range)
     b. MACD (histogram alignment)
     c. VWAP (price position)
     d. Volume (above average)
   ↓
3. Quality Filters
   • Confidence ≥ 70% (75% for shorts)
   • Confirmations ≥ 3 out of 4
   • Market sentiment check (block shorts if >55)
   • Trade frequency limits (30/day, 2/symbol)
   ↓
4. Signal Generated
   • Signal type: BUY or SELL
   • Confidence score: 70-100%
   • Confirmations: List of aligned indicators
   • Market regime: trending/ranging/choppy
```

#### **Phase 3: Risk Assessment**

```
1. Position Sizing
   • Base risk: 1.0% of equity
   • Confidence multiplier:
     - 70-75%: 1.0x (1.0% risk)
     - 75-80%: 1.2x (1.2% risk)
     - 80-85%: 1.5x (1.5% risk)
     - 85-90%: 1.8x (1.8% risk)
     - 90-100%: 2.0x (2.0% risk)
   • Calculate shares: risk_amount / stop_distance
   ↓
2. Risk Manager Checks
   • Circuit breaker status (< 5% daily loss)
   • Position count (< 20 positions)
   • Position size (< 10% of equity)
   • Buying power available
   • Market regime multiplier
   • Sentiment multiplier
   ↓
3. Final Validation
   • All checks pass → Proceed
   • Any check fails → Reject trade
```

#### **Phase 4: Order Execution**

```
1. Bracket Order Creation
   • Entry: Market order
   • Stop-Loss: 2x ATR below entry (longs) or above (shorts)
   • Take-Profit: 4x ATR above entry (longs) or below (shorts)
   • Minimum stop distance: 1% of price
   ↓
2. ML Shadow Mode Prediction (if enabled)
   • Makes prediction for trade outcome
   • Logs prediction to database
   • No impact on execution
   ↓
3. Order Submission
   • Submit to Alpaca API
   • Receive order ID
   • Log to database
   • Update trade counters
   ↓
4. Order Tracking
   • Monitor order status
   • Wait for fill confirmation
   • Update position manager
   • Broadcast to frontend
```

#### **Phase 5: Position Management (Every 15 Seconds)**

```
1. Position Sync
   • Fetch all positions from Alpaca
   • Update local state
   • Calculate unrealized P&L
   ↓
2. Exit Monitoring
   • Check if stop-loss hit
   • Check if take-profit hit
   • Check for manual exit signals
   ↓
3. Bracket Order Management
   • Monitor bracket order status
   • Handle partial fills
   • Update stop/target if needed
   ↓
4. P&L Tracking
   • Calculate position P&L
   • Update daily P&L
   • Check circuit breaker threshold
```

---


## 🧠 AI & Intelligence Layers

### Layer 1: Strategic Intelligence (Sentiment Analysis)

**Purpose**: Determine overall market direction and strategy

**Components**:
- **Perplexity AI**: Real-time market analysis
- **VIX Integration**: Fear/greed measurement
- **Dual-Source Validation**: Cross-reference for accuracy

**Output**:
- Sentiment score: 0-100 (0=extreme fear, 100=extreme greed)
- Market direction: Bullish/Bearish/Neutral
- Strategy recommendation: Aggressive/Balanced/Defensive
- Market cap preference: Large/Mid/Small

**Impact on Trading**:
```python
if sentiment < 40:  # Bearish
    - Focus on shorts and defensive plays
    - Prefer large-caps (safer)
    - Reduce position sizes
    
elif sentiment > 60:  # Bullish
    - Focus on longs and growth plays
    - All market caps acceptable
    - Normal position sizes
    
else:  # Neutral (40-60)
    - Balanced long/short approach
    - All market caps
    - Standard risk management
```

### Layer 2: Opportunity Discovery (AI Scanner)

**Purpose**: Find tradeable opportunities across entire market

**Process**:
1. **Query Construction**
   ```
   "Find day trading opportunities for [DATE] across large-cap, 
   mid-cap, and small-cap stocks. Include both long and short setups.
   Provide: symbol, price, catalyst, technical setup, direction."
   ```

2. **AI Analysis** (Perplexity)
   - Scans news and market data
   - Identifies catalysts (earnings, news, technical)
   - Analyzes technical setups
   - Provides price targets

3. **Response Parsing**
   - Extracts 50-100 opportunities
   - Categorizes by market cap
   - Separates longs and shorts
   - Validates data quality

**Output Format**:
```json
{
  "symbol": "AAPL",
  "price": 185.50,
  "direction": "long",
  "market_cap": "LARGE",
  "catalyst": "Earnings beat, iPhone sales strong",
  "technical": "Breaking out of consolidation, RSI 65",
  "confidence": "MEDIUM",
  "target": 192.00
}
```

### Layer 3: Technical Scoring (Opportunity Scorer)

**Purpose**: Score opportunities based on technical quality

**Scoring System** (0-120 points):

1. **Technical Setup** (40 points)
   - EMA alignment: 15 pts
   - RSI position: 10 pts
   - MACD strength: 10 pts
   - VWAP position: 5 pts

2. **Momentum** (25 points)
   - ADX strength: 10 pts
   - Directional movement: 10 pts
   - Price momentum: 5 pts

3. **Volume** (20 points)
   - Volume ratio: 10 pts
   - Volume spike: 5 pts
   - OBV direction: 5 pts

4. **Volatility** (15 points)
   - ATR level: 10 pts
   - Volume Z-score: 5 pts

5. **Market Regime** (10 points)
   - Trending: 10 pts
   - Transitional: 9 pts
   - Ranging: 8 pts

6. **Sentiment Alignment** (10 points)
   - Aligned with market: 8-10 pts
   - Neutral: 5 pts
   - Against market: 0-3 pts

**Grade Assignment**:
- 90-120: A+ to A (Excellent)
- 80-89: A- to B+ (Good)
- 70-79: B to B- (Fair)
- 60-69: C+ to C (Marginal)
- <60: D to F (Poor)

**Filtering**: Only scores ≥80 (A- or better) proceed to trading

### Layer 4: Signal Confirmation (Strategy)

**Purpose**: Validate trade signals with multiple indicators

**Confirmation Checklist** (4 indicators):

1. **RSI Bullish/Bearish**
   ```python
   Bullish: 30 < RSI < 70 and rising
   Bearish: 30 < RSI < 70 and falling
   ```

2. **MACD Alignment**
   ```python
   Bullish: MACD > Signal and histogram > 0
   Bearish: MACD < Signal and histogram < 0
   ```

3. **VWAP Position**
   ```python
   Bullish: Price > VWAP
   Bearish: Price < VWAP
   ```

4. **Volume Confirmation**
   ```python
   Volume > 1.0x average (any direction)
   ```

**Requirements**:
- **Longs**: ≥3 out of 4 confirmations + 70% confidence
- **Shorts**: ≥3 out of 4 confirmations + 75% confidence

**Confidence Calculation**:
```python
base_confidence = 50.0
if ema_crossover: base_confidence += 20
if confirmations >= 3: base_confidence += 10
if confirmations == 4: base_confidence += 10
if strong_trend (ADX > 25): base_confidence += 10

final_confidence = min(base_confidence, 100.0)
```

### Layer 5: ML Learning (Shadow Mode)

**Purpose**: Learn from every trade to improve future decisions

**Process**:
1. **Pre-Trade Prediction**
   - Extracts features from signal
   - Makes prediction: Win/Loss probability
   - Logs prediction to database

2. **Trade Execution**
   - Trade executes normally
   - No impact from ML prediction
   - ML weight = 0.0 (learning only)

3. **Outcome Tracking**
   - Monitors trade result
   - Records actual outcome
   - Calculates prediction accuracy

4. **Model Training** (Future)
   - Accumulates training data
   - Retrains model periodically
   - Improves predictions over time

**Features Used**:
- Signal confidence
- Number of confirmations
- Market sentiment
- Volatility (ATR)
- Volume ratio
- Time of day
- Market regime
- Historical win rate for symbol

**Future Integration**:
When ML proves accurate (>60% prediction accuracy):
```python
ml_weight = 0.2  # 20% influence
final_confidence = (signal_confidence * 0.8) + (ml_prediction * 0.2)
```

---

## 📊 Trading Strategy

### Core Strategy: EMA Crossover with Multi-Indicator Confirmation

**Entry Signals**:

**LONG Entry**:
```
1. EMA(9) crosses above EMA(21)
2. Price > VWAP
3. RSI between 30-70 and rising
4. MACD histogram > 0
5. Volume > average
6. Market sentiment > 45 (not too bearish)
7. Confidence ≥ 70%
8. 3+ confirmations
```

**SHORT Entry**:
```
1. EMA(9) crosses below EMA(21)
2. Price < VWAP
3. RSI between 30-70 and falling
4. MACD histogram < 0
5. Volume > average
6. Market sentiment < 55 (not too bullish)
7. Confidence ≥ 75% (higher bar for shorts)
8. 3+ confirmations
```

**Exit Signals**:

**Automatic Exits** (Bracket Orders):
```
Stop-Loss: Entry ± (2.0 × ATR)
Take-Profit: Entry ± (4.0 × ATR)
Risk/Reward Ratio: 1:2
```

**Manual Exit Triggers**:
- EMA crossover reversal
- RSI extreme (>80 or <20)
- Volume spike with reversal
- Major news event
- Circuit breaker triggered

### Position Sizing Formula

```python
# Step 1: Calculate base risk
base_risk_pct = 1.0%  # of total equity

# Step 2: Apply confidence multiplier
if confidence >= 90:
    multiplier = 2.0
elif confidence >= 85:
    multiplier = 1.8
elif confidence >= 80:
    multiplier = 1.5
elif confidence >= 75:
    multiplier = 1.2
else:  # 70-75
    multiplier = 1.0

adjusted_risk_pct = base_risk_pct * multiplier

# Step 3: Apply market conditions
regime_mult = {
    'trending': 1.0,
    'transitional': 0.8,
    'choppy': 0.5
}

sentiment_mult = {
    'extreme_fear': 0.7,  # <30
    'fear': 0.8,          # 30-45
    'neutral': 1.0,       # 45-55
    'greed': 0.8,         # 55-70
    'extreme_greed': 0.7  # >70
}

final_risk_pct = adjusted_risk_pct * regime_mult * sentiment_mult

# Step 4: Calculate position size
risk_amount = equity * final_risk_pct
stop_distance = abs(entry_price - stop_price)
shares = risk_amount / stop_distance

# Step 5: Apply limits
max_position_value = equity * 0.10  # 10% max
if shares * entry_price > max_position_value:
    shares = max_position_value / entry_price

# Step 6: Check buying power
if shares * entry_price > buying_power:
    shares = buying_power / entry_price
```

### Trade Frequency Controls

**Daily Limits**:
- Maximum 30 trades per day
- Maximum 2 trades per symbol per day
- Resets at market open each day

**Cooldown Periods**:
- 15 minutes between trades in same symbol
- Prevents chasing and overtrading

**Position Limits**:
- Maximum 20 open positions
- Maximum 10% of equity per position
- Maximum 50% of equity in all positions

---


## 🛡️ Risk Management

### Multi-Layer Protection System

#### Layer 1: Pre-Trade Risk Checks

**Before every trade**:
```python
1. Circuit Breaker Check
   - Daily loss < 5% of starting equity
   - If exceeded: HALT all trading
   
2. Position Count Check
   - Current positions < 20
   - If at limit: Reject new trades
   
3. Position Size Check
   - New position < 10% of equity
   - If exceeded: Reduce size or reject
   
4. Buying Power Check
   - Sufficient cash available
   - If insufficient: Reject trade
   
5. Trade Frequency Check
   - Daily trades < 30
   - Symbol trades < 2
   - If at limit: Reject trade
   
6. Market Direction Check (Shorts)
   - Sentiment < 55 for shorts
   - If too bullish: Block short
```

#### Layer 2: Position-Level Risk

**Every position has**:
```
1. Stop-Loss Order
   - Automatically placed
   - 2x ATR from entry
   - Minimum 1% from entry
   - Cannot be cancelled
   
2. Take-Profit Order
   - Automatically placed
   - 4x ATR from entry
   - 2:1 risk/reward ratio
   - Adjustable if needed
   
3. Maximum Hold Time
   - Intraday: Close by 3:55 PM
   - Swing: Max 5 days
   - Auto-exit if exceeded
```

#### Layer 3: Portfolio-Level Risk

**Portfolio constraints**:
```
1. Maximum Exposure
   - Total position value < 50% of equity
   - Remaining 50% in cash
   
2. Sector Diversification
   - Max 30% in any sector
   - Prevents concentration risk
   
3. Market Cap Distribution
   - Large-cap: 40-60%
   - Mid-cap: 20-40%
   - Small-cap: 10-20%
   
4. Long/Short Balance
   - Prefer net long in bull markets
   - Balanced in neutral markets
   - Can be net short in bear markets
```

#### Layer 4: System-Level Protection

**System safeguards**:
```
1. Connection Monitoring
   - Alpaca API health check
   - Supabase connection check
   - Auto-reconnect on failure
   
2. Data Quality Checks
   - Validate all market data
   - Reject stale data (>5 min old)
   - Cross-reference multiple sources
   
3. Order Validation
   - Verify order parameters
   - Check for duplicate orders
   - Confirm order acceptance
   
4. Emergency Controls
   - Manual kill switch
   - Close all positions command
   - Pause trading command
```

### Risk Metrics Monitored

**Real-time tracking**:
```
1. Daily P&L
   - Current: $X,XXX.XX
   - Percentage: +X.XX%
   - vs Circuit Breaker: X.XX% remaining
   
2. Position Metrics
   - Open positions: X / 20
   - Total exposure: $XXX,XXX (XX%)
   - Largest position: $XX,XXX (X%)
   
3. Trade Metrics
   - Trades today: X / 30
   - Win rate: XX%
   - Average win: $XXX
   - Average loss: $XXX
   
4. Risk Metrics
   - Portfolio beta: X.XX
   - Sharpe ratio: X.XX
   - Max drawdown: X.XX%
   - Value at Risk (VaR): $X,XXX
```

---

## ⚙️ Configuration & Controls

### Environment Variables (.env)

**Required API Keys**:
```bash
# Alpaca Trading
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Supabase Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_KEY=your_service_key

# Perplexity AI
PERPLEXITY_API_KEY=your_perplexity_key

# OpenRouter (Optional)
OPENROUTER_API_KEY=your_openrouter_key
```

### Trading Configuration (backend/config.py)

**Strategy Parameters**:
```python
# Core Strategy
ema_short: int = 9              # Fast EMA period
ema_long: int = 21              # Slow EMA period
stop_loss_atr_mult: float = 2.0 # Stop distance (ATR multiplier)
take_profit_atr_mult: float = 4.0 # Target distance (ATR multiplier)

# Risk Management
risk_per_trade_pct: float = 0.01  # 1% risk per trade
max_position_pct: float = 0.10    # 10% max per position
circuit_breaker_pct: float = 0.05 # 5% daily loss limit
min_stop_distance_pct: float = 0.01 # 1% minimum stop

# Position Limits
max_positions: int = 20           # Maximum open positions
max_trades_per_day: int = 30      # Daily trade limit
max_trades_per_symbol_per_day: int = 2 # Per-symbol limit
trade_cooldown_minutes: int = 15  # Cooldown between trades

# Quality Filters
scanner_min_score: float = 80.0   # Minimum opportunity score (A-)
# Note: Confidence thresholds are in strategy.py:
#   - Longs: 70% minimum
#   - Shorts: 75% minimum
#   - Confirmations: 3 out of 4 required
```

**Scanner Configuration**:
```python
# Opportunity Scanner
use_dynamic_watchlist: bool = True  # Enable AI discovery
scanner_interval_hours: int = 1     # Scan frequency
scanner_watchlist_size: int = 20    # Watchlist size
```

**Streaming Configuration**:
```python
# Real-Time Data
streaming_enabled: bool = True      # Enable WebSocket
stream_reconnect_delay: int = 5     # Reconnect delay (seconds)
```

### User-Controllable Parameters

**Via Configuration File**:

1. **Risk Tolerance**
   ```python
   # Conservative
   risk_per_trade_pct = 0.005  # 0.5%
   max_position_pct = 0.05     # 5%
   
   # Moderate (Default)
   risk_per_trade_pct = 0.01   # 1.0%
   max_position_pct = 0.10     # 10%
   
   # Aggressive
   risk_per_trade_pct = 0.02   # 2.0%
   max_position_pct = 0.15     # 15%
   ```

2. **Trading Frequency**
   ```python
   # Low Frequency
   max_trades_per_day = 10
   scanner_min_score = 90.0  # A+ only
   
   # Medium Frequency (Default)
   max_trades_per_day = 30
   scanner_min_score = 80.0  # A- or better
   
   # High Frequency
   max_trades_per_day = 50
   scanner_min_score = 70.0  # B or better
   ```

3. **Market Cap Focus**
   ```python
   # In scanner/opportunity_scanner.py
   # Modify get_strategy_from_sentiment()
   
   # Large-cap focus
   allowed_caps = ['LARGE']
   
   # Balanced (Default)
   allowed_caps = ['LARGE', 'MID', 'SMALL']
   
   # Small-cap focus
   allowed_caps = ['SMALL', 'MID']
   ```

4. **Strategy Aggressiveness**
   ```python
   # In trading/strategy.py
   
   # Conservative (require 4/4 confirmations)
   if confirmation_count < 4:
       return None
   
   # Moderate (Default: 3/4 confirmations)
   if confirmation_count < 3:
       return None
   
   # Aggressive (2/4 confirmations)
   if confirmation_count < 2:
       return None
   ```

**Via API/UI** (Future):
- Pause/Resume trading
- Adjust position sizes
- Change watchlist
- Set custom alerts
- Override risk limits (with confirmation)

---

## 🔌 APIs & Integrations

### 1. Alpaca Markets API

**Purpose**: Trading execution and market data

**Endpoints Used**:
```python
# Trading
POST /v2/orders              # Submit orders
GET /v2/orders               # Get order status
DELETE /v2/orders/{id}       # Cancel order
GET /v2/positions            # Get positions
DELETE /v2/positions/{symbol} # Close position

# Account
GET /v2/account              # Account info
GET /v2/account/portfolio/history # Portfolio history

# Market Data
GET /v2/stocks/{symbol}/bars # Historical bars
WS /stream                   # Real-time data stream
```

**Rate Limits**:
- 200 requests per minute (trading)
- Unlimited (market data with subscription)

**Data Feed**: IEX (free for paper trading)

### 2. Perplexity AI API

**Purpose**: Market analysis and opportunity discovery

**Endpoint**:
```python
POST https://api.perplexity.ai/chat/completions
```

**Model**: `sonar-pro` (real-time web search)

**Request Format**:
```json
{
  "model": "sonar-pro",
  "messages": [
    {
      "role": "system",
      "content": "You are a day trading analyst..."
    },
    {
      "role": "user",
      "content": "Find trading opportunities for Nov 8, 2025..."
    }
  ],
  "temperature": 0.2,
  "max_tokens": 4000
}
```

**Response**: Structured text with opportunities, citations, and analysis

**Rate Limits**: 50 requests per minute

**Cost**: ~$0.01 per request

### 3. Supabase Database

**Purpose**: Data persistence and logging

**Tables**:
```sql
-- Trading logs
trades (id, symbol, side, qty, price, timestamp, ...)
orders (id, symbol, status, filled_qty, ...)
positions (id, symbol, qty, entry_price, ...)

-- Analytics
opportunities (id, symbol, score, confidence, ...)
ml_predictions (id, trade_id, prediction, actual, ...)
daily_metrics (date, pnl, trades, win_rate, ...)

-- System logs
system_logs (timestamp, level, module, message, ...)
```

**Features Used**:
- Real-time subscriptions
- Row-level security
- Automatic timestamps
- JSON columns for flexibility

### 4. OpenRouter API (Optional)

**Purpose**: Alternative AI models for copilot

**Models**:
- Primary: `openai/gpt-oss-safeguard-20b`
- Secondary: `google/gemini-2.5-flash-preview-09-2025`
- Tertiary: `openai/gpt-oss-120b`

**Use Case**: Chat-based trading assistant

---


## 🚀 Installation & Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 16 or higher
- Alpaca Markets account (paper trading)
- Supabase account
- Perplexity API key

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/DayTraderAI.git
cd DayTraderAI
```

### Step 2: Backend Setup

```bash
# Create virtual environment
cd backend
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Environment Configuration

Create `backend/.env`:
```bash
# Copy template
cp .env.example .env

# Edit with your API keys
nano .env
```

Required variables:
```bash
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_KEY=your_service_key

PERPLEXITY_API_KEY=your_perplexity_key
```

### Step 4: Database Setup

```bash
# Run migrations
cd backend
python apply_ml_migration.py
python apply_phase2_migration.py

# Verify tables created
# Check Supabase dashboard
```

### Step 5: Frontend Setup

```bash
# Install dependencies
cd frontend  # or root directory if package.json is there
npm install

# Configure environment
cp .env.example .env.local
# Edit with backend URL
```

### Step 6: Start Services

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend**:
```bash
npm run dev
```

### Step 7: Verify Installation

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8006/health
   # Should return: {"status": "healthy"}
   ```

2. **Frontend Access**:
   - Open browser: `http://localhost:5173`
   - Should see dashboard

3. **Check Logs**:
   ```bash
   # Backend logs should show:
   ✅ Backend initialized successfully
   ✅ Trading engine started
   📊 Trade limits: 30/day, 2/symbol/day
   ```

---

## 📖 Usage

### Starting the System

1. **Start Backend**:
   ```bash
   cd backend
   source venv/bin/activate
   python main.py
   ```

2. **Start Frontend**:
   ```bash
   npm run dev
   ```

3. **Monitor Logs**:
   - Backend: Terminal output
   - Frontend: Browser console
   - Database: Supabase dashboard

### Daily Operation

**Pre-Market (6:30 AM - 9:30 AM ET)**:
- System performs initial scan
- Discovers 25-30 opportunities
- Prepares watchlist
- Waits for market open

**Market Hours (9:30 AM - 4:00 PM ET)**:
- Evaluates signals every minute
- Executes 15-30 high-quality trades
- Monitors positions every 15 seconds
- Adjusts stops/targets as needed

**After Hours (4:00 PM - 8:00 PM ET)**:
- Closes remaining positions
- Calculates daily P&L
- Logs performance metrics
- Prepares for next day

**Overnight**:
- System can run 24/7
- Minimal activity when market closed
- Hourly scans continue
- Ready for pre-market

### Monitoring Performance

**Dashboard Metrics**:
```
Portfolio Value: $XXX,XXX.XX
Daily P&L: +$X,XXX.XX (+X.XX%)
Open Positions: X / 20
Today's Trades: X / 30
Win Rate: XX%
```

**Key Indicators to Watch**:
1. **Win Rate**: Target 55-65%
2. **Daily P&L**: Target +1.5-2.5%
3. **Trade Count**: Should be 15-30/day
4. **Position Count**: Should be 8-15 typically
5. **Largest Loss**: Should be <2% of equity

### Common Operations

**View Current Positions**:
```bash
# Via API
curl http://localhost:8006/api/positions

# Via UI
Dashboard → Positions Tab
```

**Check Today's Trades**:
```bash
# Via script
cd backend
python get_daily_trades.py

# Via UI
Dashboard → Orders Tab
```

**Generate Daily Report**:
```bash
cd backend
python generate_daily_summary.py
# Creates TRADING_SUMMARY_[DATE].md
```

**Analyze Performance**:
```bash
cd backend
python analyze_today_trading.py
# Creates detailed analysis report
```

### Emergency Controls

**Pause Trading**:
```python
# Via API
POST http://localhost:8006/api/trading/pause

# Via UI
Dashboard → Settings → Pause Trading
```

**Close All Positions**:
```python
# Via API
POST http://localhost:8006/api/positions/close-all

# Via script
cd backend
python close_all_positions.py
```

**Stop System**:
```bash
# Graceful shutdown
Ctrl+C in backend terminal

# Force stop
pkill -f "python main.py"
```

---

## 📊 Monitoring & Analytics

### Real-Time Dashboard

**Main Dashboard** (`http://localhost:5173`):
```
┌─────────────────────────────────────────────────────┐
│  Portfolio: $XXX,XXX  |  P&L: +$X,XXX (+X.XX%)     │
├─────────────────────────────────────────────────────┤
│  📈 Performance Chart                                │
│  [Interactive chart showing equity curve]            │
├─────────────────────────────────────────────────────┤
│  📊 Positions (X/20)                                 │
│  Symbol | Qty | Entry | Current | P&L | %           │
│  AAPL   | 50  | $185  | $187    | +$100 | +1.08%   │
│  ...                                                 │
├─────────────────────────────────────────────────────┤
│  📋 Recent Orders                                    │
│  Time | Symbol | Side | Qty | Price | Status        │
│  10:30| AAPL   | BUY  | 50  | $185  | Filled        │
│  ...                                                 │
├─────────────────────────────────────────────────────┤
│  📰 Trade Log                                        │
│  [Real-time feed of trading activity]               │
└─────────────────────────────────────────────────────┘
```

### Performance Metrics

**Daily Metrics**:
```python
{
  "date": "2025-11-08",
  "starting_equity": 137500.00,
  "ending_equity": 139800.00,
  "pnl": 2300.00,
  "pnl_pct": 1.67,
  "trades": 25,
  "wins": 16,
  "losses": 9,
  "win_rate": 64.0,
  "avg_win": 225.00,
  "avg_loss": -125.00,
  "largest_win": 450.00,
  "largest_loss": -200.00,
  "sharpe_ratio": 2.1,
  "max_drawdown": -1.2
}
```

**Weekly Metrics**:
```python
{
  "week": "2025-W45",
  "total_pnl": 8500.00,
  "total_pnl_pct": 6.5,
  "total_trades": 125,
  "avg_daily_pnl": 1700.00,
  "best_day": 2800.00,
  "worst_day": -400.00,
  "win_rate": 62.0,
  "sharpe_ratio": 2.3
}
```

### Logging System

**Log Levels**:
```python
DEBUG: Detailed diagnostic information
INFO: General informational messages
WARNING: Warning messages (non-critical)
ERROR: Error messages (recoverable)
CRITICAL: Critical errors (system halt)
```

**Log Locations**:
```
Backend Logs: Terminal output + Supabase
Frontend Logs: Browser console
System Logs: backend/logs/system.log
Trade Logs: Supabase trades table
```

**Key Log Messages**:
```
✅ Backend initialized successfully
📊 Trade limits: 30/day, 2/symbol/day
🔍 Running AI-powered opportunity scan...
📈 Signal detected: BUY AAPL
💰 Position sizing: Confidence 75% → Risk 1.2%
✅ Stock order submitted for AAPL
⛔ Trade limit reached for TSLA
```

### Database Queries

**Get Today's Performance**:
```sql
SELECT 
  COUNT(*) as trades,
  SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
  AVG(pnl) as avg_pnl,
  SUM(pnl) as total_pnl
FROM trades
WHERE DATE(timestamp) = CURRENT_DATE;
```

**Get Best Performing Symbols**:
```sql
SELECT 
  symbol,
  COUNT(*) as trades,
  AVG(pnl) as avg_pnl,
  SUM(pnl) as total_pnl,
  AVG(CASE WHEN pnl > 0 THEN 1.0 ELSE 0.0 END) as win_rate
FROM trades
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY symbol
ORDER BY total_pnl DESC
LIMIT 10;
```

**Get ML Prediction Accuracy**:
```sql
SELECT 
  AVG(CASE WHEN prediction = actual THEN 1.0 ELSE 0.0 END) as accuracy,
  COUNT(*) as total_predictions
FROM ml_predictions
WHERE timestamp > NOW() - INTERVAL '7 days';
```

---

## 🎯 Advanced Features

### 1. Command Palette (Copilot)

**Access**: Press `Cmd+K` (Mac) or `Ctrl+K` (Windows)

**Commands**:
```
"What's my P&L today?"
"Show me my best trades"
"Close all positions"
"What's the market sentiment?"
"Find opportunities in tech sector"
"Analyze AAPL"
"Set stop loss for TSLA at $180"
```

**Features**:
- Natural language processing
- Context-aware responses
- Trade execution capability
- Portfolio analysis
- Market insights

### 2. ML Shadow Mode

**Purpose**: Learn from trades without affecting execution

**How It Works**:
1. Before each trade, ML makes prediction
2. Trade executes normally (ML has 0% influence)
3. Outcome is recorded
4. Prediction accuracy is tracked

**Monitoring**:
```bash
cd backend
python check_ml_status.py
```

**Output**:
```
ML Shadow Mode Status:
- Active: Yes
- Weight: 0.0% (learning only)
- Predictions: 1,234
- Accuracy: 58.3%
- Ready for activation: No (need 60%+)
```

**Activation** (Future):
When accuracy > 60% for 1000+ predictions:
```python
# In config.py
ml_shadow_mode_weight = 0.2  # 20% influence
```

### 3. Adaptive Risk Management

**Dynamic Adjustments**:
```python
# Market regime adjustment
if regime == 'choppy':
    risk_multiplier *= 0.5  # Reduce risk 50%
elif regime == 'trending':
    risk_multiplier *= 1.0  # Normal risk

# Sentiment adjustment
if sentiment < 30 or sentiment > 70:  # Extreme
    risk_multiplier *= 0.7  # Reduce risk 30%

# Volatility adjustment
if vix > 30:  # High volatility
    risk_multiplier *= 0.8  # Reduce risk 20%
```

### 4. Portfolio Correlation Analysis

**Purpose**: Avoid correlated positions

**Analysis**:
```python
# Check correlation between positions
correlations = calculate_correlations(positions)

# If correlation > 0.7, reduce position size
if correlation(AAPL, MSFT) > 0.7:
    reduce_position_size(MSFT, factor=0.5)
```

### 5. Pattern Detection

**Patterns Monitored**:
- Head and shoulders
- Double top/bottom
- Triangle formations
- Cup and handle
- Flag patterns

**Integration**:
```python
# Adds confidence boost if pattern detected
if detect_pattern(symbol) == 'bullish_flag':
    confidence += 10
```

### 6. News Integration (Future)

**Planned Features**:
- Real-time news monitoring
- Sentiment analysis of headlines
- Earnings calendar integration
- Economic data releases
- Automatic position adjustment on news

---


## 🔧 Troubleshooting

### Common Issues

#### 1. Backend Won't Start

**Error**: `ValidationError: Field required`

**Solution**:
```bash
# Check .env file exists
ls backend/.env

# Verify all required keys present
cat backend/.env | grep -E "ALPACA|SUPABASE|PERPLEXITY"

# Copy from template if missing
cp backend/.env.example backend/.env
```

#### 2. No Trades Executing

**Possible Causes**:

**A. Market Closed**
```bash
# Check if market is open
curl http://localhost:8006/api/market/status
```

**B. Quality Filters Too Strict**
```python
# In backend/trading/strategy.py
# Temporarily lower thresholds for testing
if confidence < 65.0:  # Was 70.0
    return None
```

**C. Already at Position Limit**
```bash
# Check current positions
curl http://localhost:8006/api/positions
# If at 20, close some positions
```

**D. Trade Limit Reached**
```bash
# Check logs for:
"⛔ Daily trade limit reached: 30/30"
# Wait for next day or increase limit in config.py
```

#### 3. Perplexity API Errors

**Error**: `⚠️ Perplexity sentiment unavailable`

**Solutions**:
```bash
# Check API key
echo $PERPLEXITY_API_KEY

# Test API directly
curl -X POST https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar-pro","messages":[{"role":"user","content":"test"}]}'

# Check rate limits (50/min)
# Wait 1 minute and retry
```

#### 4. Database Connection Issues

**Error**: `Supabase client initialization failed`

**Solutions**:
```bash
# Verify Supabase URL and keys
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Test connection
python -c "from supabase import create_client; \
  client = create_client('$SUPABASE_URL', '$SUPABASE_KEY'); \
  print('Connected!')"

# Check Supabase dashboard for service status
```

#### 5. WebSocket Connection Drops

**Error**: `Stream disconnected`

**Solutions**:
```python
# System auto-reconnects after 5 seconds
# Check logs for:
"🔌 Reconnecting to stream..."

# If persistent, check network:
ping data.alpaca.markets

# Increase reconnect delay in config.py:
stream_reconnect_delay = 10  # Was 5
```

#### 6. High Memory Usage

**Symptoms**: System slows down, crashes

**Solutions**:
```bash
# Check memory usage
ps aux | grep python

# Reduce watchlist size in config.py:
scanner_watchlist_size = 10  # Was 20

# Reduce bar history in market_data.py:
limit = 100  # Was 300

# Restart system daily:
crontab -e
0 0 * * * pkill -f "python main.py" && cd /path/to/backend && python main.py
```

### Debug Mode

**Enable Detailed Logging**:
```python
# In backend/config.py
log_level = "DEBUG"  # Was "INFO"

# Restart backend
# Logs will show detailed information
```

**Check Specific Module**:
```python
# In any module file
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

### Performance Optimization

**Slow Signal Generation**:
```python
# Cache indicator calculations
# In backend/data/features.py
@lru_cache(maxsize=100)
def calculate_indicators(symbol, timestamp):
    # ... calculations
```

**Slow Database Queries**:
```sql
-- Add indexes
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_opportunities_score ON opportunities(score);
```

**High API Usage**:
```python
# Reduce scan frequency
scanner_interval_hours = 2  # Was 1

# Reduce watchlist size
scanner_watchlist_size = 15  # Was 20
```

### Getting Help

**Check Logs First**:
```bash
# Backend logs
tail -f backend/logs/system.log

# Supabase logs
# Check Supabase dashboard → Logs

# Frontend logs
# Open browser console (F12)
```

**Run Diagnostics**:
```bash
cd backend
python diagnose_system_issues.py
# Generates diagnostic report
```

**Common Log Messages**:
```
✅ = Success
⚠️ = Warning (non-critical)
❌ = Error (needs attention)
⛔ = Blocked (by design)
🔍 = Information
📊 = Metrics
💰 = Money/Trading
🤖 = AI/ML
```

---

## 📚 Additional Resources

### Documentation Files

- **START_HERE.md**: Quick start guide
- **SYSTEM_ARCHITECTURE.md**: Detailed architecture
- **TYPICAL_TRADING_DAY.md**: Day-in-the-life walkthrough
- **GuideForDummies.md**: Beginner-friendly guide
- **DOCUMENTATION_INDEX.md**: All documentation links

### Configuration Examples

**Conservative Setup** (Low Risk):
```python
# backend/config.py
risk_per_trade_pct = 0.005  # 0.5%
max_position_pct = 0.05     # 5%
max_positions = 10
max_trades_per_day = 15
scanner_min_score = 90.0    # A+ only
```

**Aggressive Setup** (High Risk):
```python
# backend/config.py
risk_per_trade_pct = 0.02   # 2.0%
max_position_pct = 0.15     # 15%
max_positions = 30
max_trades_per_day = 50
scanner_min_score = 70.0    # B or better
```

**Day Trading Focus**:
```python
# backend/config.py
# Close all positions by end of day
intraday_only = True
close_positions_at = "15:55"  # 3:55 PM ET

# Prefer liquid large-caps
# In scanner/opportunity_scanner.py
allowed_caps = ['LARGE']
min_volume = 1000000  # 1M shares/day
```

**Swing Trading Focus**:
```python
# backend/config.py
# Hold positions multiple days
max_hold_days = 5
allow_overnight = True

# Prefer trending stocks
# In trading/strategy.py
min_adx = 25  # Strong trend required
```

### Testing

**Run Unit Tests**:
```bash
cd backend
pytest tests/
```

**Test Specific Module**:
```bash
# Test strategy
python test_signal_detection.py

# Test ML system
python test_ml_integration.py

# Test opportunity scanner
python test_opportunity_scanner.py
```

**Paper Trading Verification**:
```bash
# Verify using paper account
python test_autopilot_full.py

# Check Alpaca dashboard
# https://app.alpaca.markets/paper/dashboard
```

---

## 🎓 Learning Resources

### Understanding the System

**For Beginners**:
1. Read `GuideForDummies.md`
2. Watch system run for 1 day
3. Review `TYPICAL_TRADING_DAY.md`
4. Experiment with paper trading

**For Developers**:
1. Review `SYSTEM_ARCHITECTURE.md`
2. Study core modules (trading_engine, strategy)
3. Read inline code comments
4. Modify and test in paper account

**For Traders**:
1. Understand EMA strategy basics
2. Learn about technical indicators (RSI, MACD, ADX)
3. Study risk management principles
4. Review historical performance

### Key Concepts

**EMA Crossover Strategy**:
- Fast EMA (9) crosses slow EMA (21)
- Bullish: Fast crosses above slow
- Bearish: Fast crosses below slow
- Requires confirmation from other indicators

**Technical Indicators**:
- **RSI**: Momentum indicator (0-100)
- **MACD**: Trend-following momentum
- **ADX**: Trend strength (0-100)
- **VWAP**: Volume-weighted average price
- **ATR**: Volatility measurement

**Risk Management**:
- Never risk more than 1-2% per trade
- Always use stop-losses
- Diversify across positions
- Respect position limits
- Monitor daily P&L

**Market Sentiment**:
- Fear (0-40): Defensive, prefer shorts
- Neutral (40-60): Balanced approach
- Greed (60-100): Aggressive, prefer longs

---

## 🚦 System Status & Health

### Health Check Endpoints

```bash
# Overall system health
curl http://localhost:8006/health

# Trading engine status
curl http://localhost:8006/api/status

# Market status
curl http://localhost:8006/api/market/status

# Account status
curl http://localhost:8006/api/account
```

### Status Indicators

**System Status**:
```
🟢 Healthy: All systems operational
🟡 Degraded: Some issues, trading continues
🔴 Critical: Major issues, trading halted
```

**Trading Status**:
```
✅ Active: Trading normally
⏸️ Paused: Manually paused
🛑 Halted: Circuit breaker triggered
🌙 Closed: Market closed
```

**Connection Status**:
```
🔌 Connected: All APIs connected
⚠️ Reconnecting: Temporary disconnection
❌ Disconnected: Connection failed
```

### Performance Benchmarks

**Expected Performance**:
```
Trades per day: 15-30
Win rate: 55-65%
Daily P&L: +1.5-2.5%
Max drawdown: <5%
Sharpe ratio: >2.0
```

**System Performance**:
```
Signal generation: <100ms
Order execution: <500ms
Position sync: <1s
Market data update: <1s
AI scan: <30s
```

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## ⚠️ Disclaimer

**IMPORTANT**: This software is for educational purposes only.

- **Not Financial Advice**: This system does not provide financial advice
- **Use at Your Own Risk**: Trading involves substantial risk of loss
- **Paper Trading First**: Always test thoroughly with paper trading
- **No Guarantees**: Past performance does not guarantee future results
- **Regulatory Compliance**: Ensure compliance with local regulations
- **API Costs**: Be aware of API usage costs (Perplexity, market data)

**The developers are not responsible for any financial losses incurred through the use of this software.**

---

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: See `/docs` folder
- **Logs**: Check `backend/logs/` and Supabase
- **Community**: [Discord/Slack link]

---

## 🎯 Quick Reference

### Essential Commands

```bash
# Start system
cd backend && python main.py

# Check status
curl http://localhost:8006/health

# View positions
curl http://localhost:8006/api/positions

# Generate report
python backend/analyze_today_trading.py

# Close all positions
python backend/close_all_positions.py

# Check ML status
python backend/check_ml_status.py
```

### Key Files

```
backend/
├── main.py                 # Entry point
├── config.py              # Configuration
├── trading/
│   ├── trading_engine.py  # Core engine
│   ├── strategy.py        # Trading strategy
│   └── risk_manager.py    # Risk management
├── scanner/
│   ├── ai_opportunity_finder.py  # AI discovery
│   └── opportunity_scorer.py     # Scoring system
└── indicators/
    └── sentiment_aggregator.py   # Sentiment analysis
```

### Configuration Quick Reference

```python
# Risk (config.py)
risk_per_trade_pct = 0.01      # 1% per trade
max_position_pct = 0.10        # 10% per position
circuit_breaker_pct = 0.05     # 5% daily loss limit

# Limits (config.py)
max_positions = 20             # Max open positions
max_trades_per_day = 30        # Daily trade limit
max_trades_per_symbol_per_day = 2  # Per-symbol limit

# Quality (config.py + strategy.py)
scanner_min_score = 80.0       # A- or better
# confidence >= 70% (longs)    # In strategy.py
# confidence >= 75% (shorts)   # In strategy.py
# confirmations >= 3/4         # In strategy.py

# Strategy (config.py)
ema_short = 9                  # Fast EMA
ema_long = 21                  # Slow EMA
stop_loss_atr_mult = 2.0      # Stop distance
take_profit_atr_mult = 4.0    # Target distance
```

---

**Built with ❤️ for algorithmic traders**

**Version**: 2.0.0  
**Last Updated**: November 8, 2025  
**Status**: Production Ready ✅
