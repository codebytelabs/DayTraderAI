# Opportunities Query Enhancement

## Overview
Enhanced the `/opportunities` command to use **Perplexity for comprehensive market research** combined with **OpenRouter for strategic analysis**, providing intelligent, diversified trading opportunities.

## What Changed

### Before
- Opportunities queries went only to OpenRouter
- Limited to analyzing existing portfolio context
- No external market research
- Generic trade ideas

### After
- Opportunities queries use **BOTH** Perplexity + OpenRouter
- Perplexity researches the entire market for best opportunities
- OpenRouter synthesizes research with portfolio context
- Specific, actionable recommendations across multiple categories

## How It Works

### 1. Query Detection
**File:** `backend/copilot/query_router.py`

Detects opportunities queries and routes to both services:
```python
opportunities_keywords = {"opportunities", "opportunity", "ideas", "signals", "setups", "trades"}
is_opportunities_query = any(kw in cleaned for kw in opportunities_keywords)

if is_opportunities_query:
    top_category = "opportunities"
    targets = ["perplexity", "openrouter"]  # BOTH services
    confidence = 0.85
```

### 2. Perplexity Research Phase
**File:** `backend/main.py` - `_build_perplexity_prompt()`

Perplexity researches the market for:

#### Categories Researched
1. **High-momentum stocks** - Strong uptrends, breakouts
2. **Undervalued stocks** - Oversold, potential reversals
3. **Sector leaders** - Strongest in their sectors
4. **Dividend/value plays** - Stable, defensive positions
5. **Options opportunities** - High IV, earnings plays

#### For Each Opportunity
- Symbol and company name
- Current price and recent price action
- Catalyst (why it's good RIGHT NOW)
- Suggested entry price range
- Suggested stop loss level
- Suggested take profit target
- Risk/reward ratio
- Position size recommendation
- Time horizon (day trade, swing, position)
- Asset class (stock, ETF, option strategy)

#### Diversification Focus
- Suggests opportunities in sectors NOT currently overweight
- Includes defensive/hedge positions
- Considers market cap diversity (large, mid, small cap)
- Includes options strategies when appropriate

#### Portfolio Context Provided
```python
"CURRENT PORTFOLIO CONTEXT:",
f"- Available cash: ${cash:,.0f}",
f"- Total equity: ${equity:,.0f}",
f"- Open positions: {len(positions)}",
"- Current sector exposure:",
"  • Tech: $XXX,XXX (XX%)",
"  • EV/Auto: $XXX,XXX (XX%)",
```

### 3. OpenRouter Analysis Phase
**File:** `backend/main.py` - Enhanced system prompt

OpenRouter receives Perplexity's research and:

1. **Validates** the opportunities
2. **Prioritizes** based on portfolio context
3. **Provides** specific trade recommendations
4. **Calculates** position sizes (1% risk per trade)
5. **Explains** how each complements existing portfolio
6. **Highlights** risks and concerns

#### Response Format
```markdown
**High Priority Opportunities** (best risk/reward, immediate action)
- Symbol: Entry, SL, TP, R/R, Position Size

**Medium Priority Opportunities** (good setups, watch for entry)
- Symbol: Entry, SL, TP, R/R, Position Size

**Defensive/Hedge Positions** (portfolio protection)
- Symbol: Entry, SL, TP, R/R, Position Size

**Options Strategies** (if applicable)
- Strategy: Details, Risk, Reward
```

## Example Flow

### User Query
```
Show me trading opportunities: new position ideas, strong signals, ML-validated opportunities, risk/reward analysis
```

### Step 1: Perplexity Research (15-20 seconds)
Searches real-time market data for:
- Trending stocks with momentum
- Undervalued stocks with catalysts
- Sector leaders
- Defensive plays
- Options opportunities

Returns 5-7 opportunities with full details and citations.

### Step 2: OpenRouter Analysis (5-10 seconds)
Receives Perplexity research + portfolio context:
- Current positions: TSLA, MSFT, AMZN, AAPL, GOOGL, NFLX
- Sector exposure: 61% Tech, 39% EV
- Available cash: $79,249

Synthesizes and provides:
```markdown
**Market Research & Opportunities**

[Perplexity's research with citations]

**Strategy Guidance**

**🎯 HIGH PRIORITY OPPORTUNITIES:**

1. **XLF (Financial Sector ETF)**
   • Entry: $42.50-$43.00
   • Stop Loss: $41.00 (-3.5%)
   • Take Profit: $46.00 (+7.5%)
   • Risk/Reward: 1:2.1
   • Position Size: $2,770 (2% of equity, 1% risk)
   • Rationale: Diversify away from tech concentration
   • Complements: Reduces correlation with existing tech positions

2. **COIN (Coinbase)**
   • Entry: $245-$250
   • Stop Loss: $235 (-5%)
   • Take Profit: $280 (+13%)
   • Risk/Reward: 1:2.6
   • Position Size: $2,770 (1% risk)
   • Rationale: High momentum, breaking resistance
   • Complements: Alternative asset exposure

**🛡️ DEFENSIVE/HEDGE POSITIONS:**

1. **TLT (20+ Year Treasury ETF)**
   • Entry: $92.00-$93.00
   • Stop Loss: $89.00 (-4%)
   • Take Profit: $98.00 (+6%)
   • Position Size: $3,000 (hedge allocation)
   • Rationale: Portfolio protection against tech selloff
   • Complements: Negative correlation with tech stocks

**📊 OPTIONS STRATEGIES:**

1. **SPY Bull Put Spread**
   • Sell 580 Put / Buy 575 Put
   • Credit: $1.50 per spread
   • Max Risk: $3.50 per spread
   • Risk/Reward: 1:0.43
   • Rationale: Generate income, bullish bias
```

## Benefits

### 1. Comprehensive Market Coverage
- Not limited to watchlist symbols
- Discovers opportunities across entire market
- Real-time market data and news

### 2. Intelligent Diversification
- Analyzes current portfolio exposure
- Suggests complementary positions
- Reduces concentration risk

### 3. Multiple Asset Classes
- Stocks (large, mid, small cap)
- ETFs (sector, defensive)
- Options strategies
- Bonds/treasuries for hedging

### 4. Risk Management
- Position sizing based on 1% risk rule
- Stop losses for every recommendation
- Risk/reward ratios calculated
- Portfolio impact analysis

### 5. Actionable Intelligence
- Specific entry prices
- Exact stop loss levels
- Clear take profit targets
- Ready-to-execute commands

## Configuration

### Enable Hybrid Routing
In `backend/config.py` or environment:
```python
COPILOT_HYBRID_ROUTING = True  # Enable Perplexity + OpenRouter
```

### API Keys Required
```bash
PERPLEXITY_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

## Testing

### Test Query
```
Show me trading opportunities: new position ideas, strong signals, ML-validated opportunities, risk/reward analysis
```

### Expected Response Time
- Perplexity research: 15-20 seconds
- OpenRouter analysis: 5-10 seconds
- Total: 20-30 seconds

### Expected Response Structure
1. **Market Research** section (from Perplexity)
   - 5-7 opportunities with details
   - Citations and sources
   
2. **Strategy Guidance** section (from OpenRouter)
   - High priority opportunities
   - Medium priority opportunities
   - Defensive/hedge positions
   - Options strategies
   - Specific entry/exit points
   - Position sizes calculated

## Comparison

### Old Response (OpenRouter Only)
```markdown
**Strategy Guidance**

Here are some trading opportunities:
- Consider buying SPY if market continues uptrend
- AAPL showing strength, could add to position
- Watch QQQ for tech sector exposure

[Generic advice, no specific prices or research]
```

### New Response (Perplexity + OpenRouter)
```markdown
**Market Intelligence**

Based on real-time market research:

1. **XLF - Financial Select Sector SPDR Fund**
   Current: $42.75 (+1.2% today)
   Catalyst: Fed rate decision this week, financials outperforming
   Technical: Breaking above 50-day MA, RSI 58 (neutral)
   [Source: Bloomberg, Yahoo Finance]

2. **COIN - Coinbase Global**
   Current: $248.50 (+3.5% today)
   Catalyst: Bitcoin above $70k, institutional adoption increasing
   Technical: Cup and handle pattern, volume surge
   [Source: CoinDesk, TradingView]

[5 more opportunities with full details and citations]

**Strategy Guidance**

**🎯 HIGH PRIORITY OPPORTUNITIES:**

1. **XLF (Financial Sector ETF)**
   • Entry: $42.50-$43.00
   • Stop Loss: $41.00 (-3.5%)
   • Take Profit: $46.00 (+7.5%)
   • Risk/Reward: 1:2.1
   • Position Size: $2,770 (2% of equity, 1% risk)
   • Command: `/order BUY XLF 65 @ 42.75`
   • Rationale: Your portfolio is 61% tech - this adds financial sector diversification
   • Risk: Fed policy uncertainty

[Specific, actionable recommendations with exact numbers]
```

## Success Metrics

- ✅ Opportunities queries route to both Perplexity + OpenRouter
- ✅ Perplexity researches 5-7 opportunities across categories
- ✅ OpenRouter provides specific entry/exit points
- ✅ Position sizes calculated based on 1% risk
- ✅ Diversification recommendations based on current portfolio
- ✅ Citations and sources provided
- ✅ Ready-to-execute commands included

## Future Enhancements

1. **ML Validation** - Score opportunities using trained models
2. **Backtesting** - Show historical performance of similar setups
3. **Sentiment Analysis** - Incorporate social media sentiment
4. **Earnings Calendar** - Highlight upcoming earnings plays
5. **Technical Screeners** - Automated pattern recognition
6. **Sector Rotation** - Identify rotating sectors
7. **Correlation Matrix** - Show how opportunities correlate with portfolio

---

**Status:** Enhanced and deployed ✅
**Ready for:** Production testing
**Expected Impact:** Significantly better opportunity discovery and portfolio diversification
