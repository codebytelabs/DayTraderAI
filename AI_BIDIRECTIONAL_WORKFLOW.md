# AI Bidirectional Trading Workflow

**How 20 Long + 20 Short Opportunities Flow Through the System**

---

## 🔄 Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    STEP 1: AI DISCOVERY                      │
│                  (Every 1 hour via Scanner Loop)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │      Perplexity AI Research              │
        │  Query: "Find 20 longs + 20 shorts"      │
        │  • Analyzes current market conditions    │
        │  • Reviews news & catalysts              │
        │  • Checks technical setups               │
        │  • Evaluates volume & liquidity          │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │      AI Response Processing              │
        │  • Extracts LONG section (20 symbols)    │
        │  • Extracts SHORT section (20 symbols)   │
        │  • Validates symbols                     │
        │  • Returns combined list (40 total)      │
        └─────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STEP 2: OPPORTUNITY SCORING               │
│                  (OpportunityScanner processes all 40)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   For Each Symbol (40 total):            │
        │   1. Fetch market data (1 day, 5-min)    │
        │   2. Calculate features (EMA, RSI, etc)  │
        │   3. Score opportunity (110 points)      │
        │      • Technical: 30 pts                 │
        │      • Momentum: 25 pts                  │
        │      • Volume: 20 pts                    │
        │      • Volatility: 20 pts                │
        │      • Regime: 15 pts                    │
        │   4. Assign grade (A+ to F)              │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │      Filter & Sort Results               │
        │  • Filter: score >= 60 (B- or better)    │
        │  • Sort: highest score first             │
        │  • Result: ~20-30 qualified symbols      │
        └─────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STEP 3: WATCHLIST UPDATE                  │
│                  (Trading Engine updates symbols)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   Update Dynamic Watchlist               │
        │  • Take top 20 symbols (or max_positions)│
        │  • Mix of longs and shorts               │
        │  • Update trading_engine.watchlist       │
        │  • Log changes (added/removed)           │
        └─────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STEP 4: SIGNAL DETECTION                  │
│                  (Strategy Loop checks each symbol)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   For Each Watchlist Symbol:             │
        │   1. Get latest features                 │
        │   2. Detect signal (buy/sell)            │
        │      • EMA crossover OR                  │
        │      • Clear trend (EMA separation)      │
        │   3. Multi-indicator confirmation        │
        │      • RSI momentum                      │
        │      • MACD confirmation                 │
        │      • Volume confirmation               │
        │      • VWAP alignment                    │
        └─────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STEP 5: RISK MANAGEMENT                   │
│                  (Enhanced with Market Regime)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   Risk Manager Checks:                   │
        │   1. Market regime (skip if choppy) 🆕   │
        │   2. Trading enabled                     │
        │   3. Circuit breaker                     │
        │   4. Market open                         │
        │   5. Position limits                     │
        │   6. Buying power                        │
        │   7. ADX >= 20 (volatility filter) 🆕    │
        │   8. Volume >= 1.5x (liquidity) 🆕       │
        │   9. Adaptive position sizing 🆕          │
        │      • Base risk × regime multiplier     │
        └─────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STEP 6: ORDER EXECUTION                   │
│                  (Bracket orders with stops)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   Execute Trade:                         │
        │   • Calculate position size (adaptive)   │
        │   • Set stop loss (ATR-based)            │
        │   • Set take profit (2:1 R/R)            │
        │   • Submit bracket order                 │
        │   • Track position                       │
        └─────────────────────────────────────────┘
```

---

## 📊 Detailed Flow: AI Discovery

### Input Query to Perplexity
```
"As of [current time], provide TWO SEPARATE LISTS for INTRADAY DAY TRADING:

📈 LIST 1: TOP 20 LONG OPPORTUNITIES
Stocks with:
- Strong bullish momentum RIGHT NOW
- Positive catalysts/news
- Breaking resistance levels
- High volume confirming buying pressure

📉 LIST 2: TOP 20 SHORT OPPORTUNITIES
Stocks with:
- Strong bearish momentum RIGHT NOW
- Negative catalysts/news
- Breaking support levels
- High volume confirming selling pressure

LIQUIDITY REQUIREMENTS:
- Average daily volume > 5M shares
- Market cap > $5B
- Tight bid-ask spreads

FOCUS ON: Large cap tech, major ETFs, high-volume growth stocks"
```

### AI Response Processing
```python
# ai_opportunity_finder.py

def _extract_symbols(content):
    # 1. Find LONG section
    long_start = content.find("LONG OPPORTUNITIES")
    short_start = content.find("SHORT OPPORTUNITIES")
    
    # 2. Extract from each section
    long_section = content[long_start:short_start]
    short_section = content[short_start:]
    
    # 3. Parse symbols from each
    long_symbols = extract_from_text(long_section)   # e.g., ['NVDA', 'TSLA', 'AAPL', ...]
    short_symbols = extract_from_text(short_section) # e.g., ['XYZ', 'ABC', 'DEF', ...]
    
    # 4. Combine: longs first, then shorts
    all_symbols = long_symbols + short_symbols  # 40 total
    
    return all_symbols
```

### Example AI Response
```
LONG OPPORTUNITIES:
1. NVDA - Up 3% on AI chip news, breaking $205 resistance, volume 2x
2. TSLA - Delivery beat, strong momentum, institutional buying
3. AAPL - iPhone sales strong, breaking out of consolidation
4. AMD - Data center growth, technical breakout
5. MSFT - Cloud revenue beat, bullish trend
...
20. PLTR - Government contracts, high volume

SHORT OPPORTUNITIES:
1. XYZ - Down 5% on earnings miss, breaking support
2. ABC - Negative analyst downgrade, weak technicals
3. DEF - Regulatory concerns, selling pressure
...
20. GHI - Overvalued, technical breakdown
```

---

## 🎯 How Symbols Are Processed

### 1. AI Discovery (40 symbols)
```
Input:  None (AI discovers)
Output: ['NVDA', 'TSLA', 'AAPL', ..., 'XYZ', 'ABC', 'DEF', ...]
        └─ 20 longs ─┘  └─ 20 shorts ─┘
```

### 2. Opportunity Scoring (40 → ~25)
```
For each symbol:
  - Fetch data ✓
  - Calculate features ✓
  - Score (0-110) ✓
  - Filter (>= 60) ✓

Result: ~25 qualified symbols
  - Some longs scored high
  - Some shorts scored high
  - Some filtered out (low score)
```

### 3. Watchlist Selection (25 → 20)
```
Take top 20 by score:
  - Mix of longs and shorts
  - Best opportunities regardless of direction
  - Example: 12 longs + 8 shorts (varies by market)
```

### 4. Signal Detection (20 → 5-10 signals)
```
For each watchlist symbol:
  - Check for signal (buy/sell)
  - LONG symbols → look for BUY signals
  - SHORT symbols → look for SELL signals
  
Result: 5-10 actual signals per hour
```

### 5. Trade Execution (5-10 → 3-5 trades)
```
For each signal:
  - Risk management filters
  - Adaptive position sizing
  - Execute if approved
  
Result: 3-5 actual trades per hour
```

---

## 🔍 Key Points

### Bidirectional Nature
```
AI provides BOTH directions:
  ✓ 20 LONG opportunities (bullish bias)
  ✓ 20 SHORT opportunities (bearish bias)

System evaluates ALL 40:
  ✓ Scores each independently
  ✓ Takes best 20 regardless of direction
  ✓ Trades both longs and shorts

Result: Market-neutral capability
  ✓ Can profit in any market condition
  ✓ Not dependent on market direction
  ✓ Diversified opportunity set
```

### Signal Detection Logic
```
For LONG opportunities (from AI):
  - Look for BUY signals
  - EMA short > EMA long (uptrend)
  - RSI > 50 (bullish momentum)
  - MACD > 0 (bullish)
  - Volume > 1.5x (confirmation)

For SHORT opportunities (from AI):
  - Look for SELL signals
  - EMA short < EMA long (downtrend)
  - RSI < 50 (bearish momentum)
  - MACD < 0 (bearish)
  - Volume > 1.5x (confirmation)
```

### Adaptive Sizing
```
Market Regime affects ALL trades:
  - Broad bullish: 1.5x size (good for longs)
  - Broad bearish: 1.5x size (good for shorts)
  - Narrow: 0.7x size (risky for both)
  - Choppy: 0.5x size or skip (bad for both)
```

---

## 📈 Example Scenario

### Hour 1: AI Discovery
```
AI finds:
  LONGS:  NVDA, TSLA, AAPL, AMD, MSFT, ... (20 total)
  SHORTS: XYZ, ABC, DEF, GHI, JKL, ... (20 total)
```

### Hour 1: Scoring
```
Scored results (top 10):
  1. NVDA  - 85 (A)  - LONG
  2. TSLA  - 82 (A)  - LONG
  3. XYZ   - 78 (B+) - SHORT
  4. AAPL  - 75 (B+) - LONG
  5. ABC   - 73 (B)  - SHORT
  6. AMD   - 71 (B)  - LONG
  7. DEF   - 69 (B)  - SHORT
  8. MSFT  - 67 (B)  - LONG
  9. GHI   - 65 (B-) - SHORT
  10. PLTR - 63 (B-) - LONG
```

### Hour 1: Watchlist
```
Top 20 selected:
  - 12 LONG opportunities
  - 8 SHORT opportunities
```

### Hour 1: Signals Detected
```
BUY signals (from LONG opportunities):
  - NVDA: EMA crossover, RSI 65, MACD bullish
  - TSLA: Strong uptrend, volume 2x
  - AAPL: Breaking resistance

SELL signals (from SHORT opportunities):
  - XYZ: EMA crossover down, RSI 35, MACD bearish
  - ABC: Breaking support, volume 2x
```

### Hour 1: Trades Executed
```
Market regime: broad_bullish (1.5x multiplier)

LONG trades (1.5x size):
  ✓ BUY NVDA 50 shares @ $205 (approved)
  ✓ BUY TSLA 30 shares @ $245 (approved)
  ✓ BUY AAPL 40 shares @ $185 (approved)

SHORT trades (1.5x size):
  ✓ SELL XYZ 100 shares @ $50 (approved)
  ✓ SELL ABC 80 shares @ $75 (approved)

Result: 5 trades (3 long, 2 short)
```

---

## 🎯 Summary

### The Flow
```
1. AI discovers 40 symbols (20 long + 20 short)
2. System scores all 40 independently
3. Top 20 become watchlist (mixed directions)
4. Strategy detects signals on watchlist
5. Risk manager filters with regime + volatility
6. Orders executed with adaptive sizing
```

### Key Features
```
✓ Bidirectional: Can trade both directions
✓ AI-powered: Discovers best opportunities
✓ Scored: Only trades high-quality setups
✓ Adaptive: Sizes based on market regime
✓ Filtered: ADX and volume requirements
✓ Market-neutral: Profits in any condition
```

### Why This Works
```
✓ AI finds opportunities humans might miss
✓ Scoring ensures quality control
✓ Bidirectional captures all market moves
✓ Adaptive sizing protects capital
✓ Filters prevent bad trades
✓ Market regime awareness
```

---

*The system is designed to find and trade the best opportunities in BOTH directions!* 📈📉

---

*Last Updated: November 6, 2025*
