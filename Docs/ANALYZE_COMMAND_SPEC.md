# `/analyze` Command Specification

## Overview
Deep-dive stock analysis command that provides comprehensive research reports using Perplexity for real-time data and OpenRouter for synthesis.

## Command Syntax
```
/analyze SYMBOL
/analyze SYMBOL1 SYMBOL2 SYMBOL3
/analyze aapl tsla msft
```

## Response Structure

### 1. Executive Summary
- Current price and 24h change
- Overall rating (Strong Buy, Buy, Hold, Sell, Strong Sell)
- Key catalyst (most important factor right now)
- Quick verdict (1-2 sentences)

### 2. Technical Analysis
- **Price Action**
  - Current: $XXX.XX
  - 52-week range: $XXX - $XXX
  - Distance from 52w high/low
  - Key support levels
  - Key resistance levels

- **Indicators**
  - RSI (14): XX (overbought/oversold/neutral)
  - MACD: Bullish/Bearish crossover
  - Moving Averages: Above/below 20/50/200 day
  - Volume: Above/below average
  - Bollinger Bands: Position

- **Chart Patterns**
  - Current pattern (if any)
  - Breakout/breakdown levels
  - Pattern target

- **Momentum**
  - Short-term: Bullish/Bearish/Neutral
  - Medium-term: Bullish/Bearish/Neutral
  - Long-term: Bullish/Bearish/Neutral

### 3. Fundamental Analysis
- **Valuation**
  - P/E Ratio: XX.X (vs sector avg)
  - P/B Ratio: XX.X
  - PEG Ratio: XX.X
  - Price/Sales: XX.X
  - EV/EBITDA: XX.X
  - Verdict: Overvalued/Fair/Undervalued

- **Financial Health**
  - Revenue: $XXB (YoY growth: +XX%)
  - Net Income: $XXB (YoY growth: +XX%)
  - Profit Margin: XX%
  - ROE: XX%
  - Debt/Equity: XX%
  - Current Ratio: XX.X
  - Free Cash Flow: $XXB

- **Growth Metrics**
  - Revenue growth (5yr): XX%
  - EPS growth (5yr): XX%
  - Forward P/E: XX.X
  - PEG Ratio: XX.X

### 4. Sentiment & News
- **News Sentiment**
  - Overall: Positive/Negative/Neutral (XX% confidence)
  - Recent headlines (last 7 days)
  - Key catalysts identified

- **Analyst Ratings**
  - Strong Buy: XX
  - Buy: XX
  - Hold: XX
  - Sell: XX
  - Strong Sell: XX
  - Average target: $XXX (upside: +XX%)

- **Social Sentiment**
  - Reddit mentions: Trending/Normal
  - Twitter sentiment: Bullish/Bearish
  - StockTwits sentiment: XX% bullish

### 5. Options Analysis
- **Options Flow**
  - Unusual activity: Yes/No
  - Put/Call ratio: XX.X
  - Implied volatility: XX% (rank: XX)
  - IV percentile: XX%

- **Notable Trades**
  - Large call sweeps
  - Large put sweeps
  - Interpretation

### 6. Insider & Institutional
- **Insider Trading (Last 3 months)**
  - Buys: XX transactions, $XXM
  - Sells: XX transactions, $XXM
  - Net: Bullish/Bearish

- **Institutional Holdings**
  - Ownership: XX%
  - Recent changes: +/-XX%
  - Top holders: XXX, YYY, ZZZ

### 7. Earnings Analysis
- **Next Earnings**
  - Date: YYYY-MM-DD (XX days away)
  - Estimate: $X.XX per share
  - Whisper: $X.XX per share

- **Recent Performance**
  - Last quarter: Beat/Miss by $X.XX
  - Surprise history: X/4 beats
  - Average surprise: +/-XX%

### 8. Competitive Analysis
- **Peer Comparison**
  - Symbol vs PEER1 vs PEER2 vs PEER3
  - P/E, Revenue Growth, Margins
  - Market share
  - Competitive advantages

### 9. Risk Assessment
- **Risk Metrics**
  - Beta: X.XX (vs market)
  - Volatility (30d): XX%
  - Max drawdown (1yr): -XX%
  - Sharpe ratio: X.XX

- **Risk Factors**
  - Key risks identified
  - Regulatory concerns
  - Competition threats
  - Market risks

### 10. Trade Setup
- **Bullish Scenario**
  - Entry: $XXX-$XXX
  - Stop Loss: $XXX (-X%)
  - Target 1: $XXX (+X%)
  - Target 2: $XXX (+X%)
  - Risk/Reward: 1:X.X
  - Position size: $XXX (1% risk)
  - Time horizon: Days/Weeks/Months

- **Bearish Scenario**
  - Entry: $XXX-$XXX (short)
  - Stop Loss: $XXX (+X%)
  - Target 1: $XXX (-X%)
  - Target 2: $XXX (-X%)
  - Risk/Reward: 1:X.X

- **Options Strategy** (if applicable)
  - Strategy: Call/Put/Spread
  - Strike: $XXX
  - Expiration: YYYY-MM-DD
  - Cost: $XXX
  - Max profit: $XXX
  - Max loss: $XXX

### 11. Bottom Line
- **Overall Assessment**
  - Rating: Strong Buy/Buy/Hold/Sell/Strong Sell
  - Confidence: XX%
  - Time horizon: Short/Medium/Long term
  - Key catalyst to watch
  - Next action: Buy/Wait/Sell

- **Quick Commands**
  - `#buy SYMBOL XX` - Buy XX shares
  - `#watch SYMBOL` - Add to watchlist
  - `#alert SYMBOL > XXX` - Set price alert

## Multi-Symbol Analysis

When analyzing multiple symbols:
```
/analyze aapl tsla msft
```

Response format:
1. **Comparative Summary Table**
   - All symbols side-by-side
   - Key metrics comparison
   - Relative strength ranking

2. **Individual Deep Dives**
   - Full analysis for each symbol
   - Separated by clear dividers

3. **Portfolio Fit Analysis**
   - How they complement each other
   - Correlation analysis
   - Diversification score
   - Suggested allocation

## Perplexity Research Prompt

```
Conduct comprehensive stock analysis for [SYMBOL]:

TECHNICAL ANALYSIS:
- Current price, 52-week range, support/resistance
- RSI, MACD, moving averages, volume analysis
- Chart patterns, breakout levels
- Momentum indicators

FUNDAMENTAL ANALYSIS:
- Latest financials (revenue, earnings, margins)
- Valuation metrics (P/E, P/B, PEG, P/S)
- Growth rates (revenue, EPS, FCF)
- Balance sheet health (debt, cash, ratios)
- Profitability (ROE, ROA, margins)

SENTIMENT & NEWS:
- Recent news headlines (last 7 days)
- News sentiment analysis
- Analyst ratings and price targets
- Social media sentiment (Reddit, Twitter, StockTwits)

OPTIONS ANALYSIS:
- Unusual options activity
- Put/call ratio
- Implied volatility and IV rank
- Notable large trades

INSIDER & INSTITUTIONAL:
- Recent insider transactions (last 3 months)
- Institutional ownership changes
- Top institutional holders

EARNINGS:
- Next earnings date and estimates
- Recent earnings surprises
- Earnings trend

COMPETITIVE LANDSCAPE:
- Main competitors
- Market share
- Competitive advantages/disadvantages

RISK FACTORS:
- Beta, volatility, max drawdown
- Key risks (regulatory, competitive, market)

Provide specific numbers, dates, and sources for all data.
```

## OpenRouter Synthesis Prompt

```
You are a professional stock analyst. You have received comprehensive research on [SYMBOL].

Your task:
1. Synthesize the research into a clear, actionable report
2. Provide specific trade setups with entry/exit/stop levels
3. Calculate position sizes based on 1% risk rule
4. Give an overall rating and confidence level
5. Identify the #1 catalyst to watch
6. Format with clear sections and bullet points

Use this structure:
- Executive Summary (rating, key catalyst, verdict)
- Technical Analysis (price action, indicators, patterns)
- Fundamental Analysis (valuation, financials, growth)
- Sentiment & News (headlines, ratings, social)
- Options Analysis (flow, IV, notable trades)
- Insider & Institutional (recent activity)
- Earnings Analysis (next date, estimates, history)
- Competitive Analysis (peers, market share)
- Risk Assessment (metrics, factors)
- Trade Setup (bullish/bearish scenarios with specific prices)
- Bottom Line (rating, confidence, next action)

Be specific with numbers. Provide actionable trade setups.
```

## Implementation Notes

### Query Detection
```python
# In query_router.py
if cleaned.startswith('/analyze'):
    symbols = extract_symbols_from_query(cleaned)
    return QueryRoute(
        category="deep_analysis",
        targets=["perplexity", "openrouter"],
        confidence=1.0,
        symbols=symbols,
        notes=["Deep analysis requested for symbols"]
    )
```

### Symbol Extraction
```python
def extract_symbols_from_query(query: str) -> List[str]:
    # Remove /analyze command
    query = query.replace('/analyze', '').strip()
    # Split by spaces and uppercase
    symbols = [s.upper() for s in query.split() if s.isalpha()]
    return symbols
```

### Response Caching
- Cache analysis for 5 minutes
- Invalidate on new data (earnings, news)
- Store in Redis or memory

### Rate Limiting
- Max 3 symbols per query
- Max 10 analyses per hour per user
- Warn if exceeding limits

## Example Output

```markdown
# 📊 Deep Analysis: AAPL

## Executive Summary
**Current Price:** $175.43 (+1.2%)
**Rating:** ⭐⭐⭐⭐ **BUY** (85% confidence)
**Key Catalyst:** iPhone 16 launch momentum + Services growth
**Verdict:** Strong technical setup with bullish fundamentals. Entry opportunity on pullback to $172-$174.

---

## 📈 Technical Analysis

### Price Action
- **Current:** $175.43
- **52-Week Range:** $164.08 - $199.62
- **From 52w High:** -12.1%
- **From 52w Low:** +6.9%

**Support Levels:** $172.50, $170.00, $165.00
**Resistance Levels:** $178.00, $182.50, $190.00

### Indicators
- **RSI (14):** 58.3 → Neutral (room to run)
- **MACD:** Bullish crossover (3 days ago)
- **Moving Averages:**
  - Above 20-day MA ✅
  - Above 50-day MA ✅
  - Above 200-day MA ✅
- **Volume:** 15% above average (accumulation)
- **Bollinger Bands:** Middle band, trending up

### Chart Pattern
- **Pattern:** Ascending triangle
- **Breakout Level:** $178.00
- **Pattern Target:** $192.00 (+9.5%)

### Momentum
- **Short-term (1-2 weeks):** 🟢 Bullish
- **Medium-term (1-3 months):** 🟢 Bullish
- **Long-term (3-12 months):** 🟢 Bullish

---

## 💰 Fundamental Analysis

### Valuation
- **P/E Ratio:** 28.5 (vs sector avg: 25.2) → Slight premium
- **P/B Ratio:** 45.2
- **PEG Ratio:** 2.1 → Fair value
- **Price/Sales:** 7.8
- **EV/EBITDA:** 22.1
- **Verdict:** 📊 Fairly valued with growth premium

### Financial Health
- **Revenue:** $383.3B (YoY: +2.1%)
- **Net Income:** $97.0B (YoY: +3.5%)
- **Profit Margin:** 25.3% (industry-leading)
- **ROE:** 147.4% (exceptional)
- **Debt/Equity:** 1.8 (manageable)
- **Current Ratio:** 0.98
- **Free Cash Flow:** $99.6B (strong)

### Growth Metrics
- **Revenue Growth (5yr):** 8.2%
- **EPS Growth (5yr):** 11.5%
- **Forward P/E:** 26.8
- **Services Revenue:** +16% YoY (key driver)

---

## 📰 Sentiment & News

### News Sentiment: 🟢 **POSITIVE** (78% confidence)

**Recent Headlines:**
- "Apple iPhone 16 sales exceed expectations in China" - Bloomberg (2 days ago)
- "Services revenue hits all-time high" - CNBC (4 days ago)
- "Apple Vision Pro 2 rumors surface" - MacRumors (5 days ago)

### Analyst Ratings
- **Strong Buy:** 15
- **Buy:** 22
- **Hold:** 8
- **Sell:** 2
- **Strong Sell:** 0
- **Average Target:** $195.50 (upside: +11.4%)

### Social Sentiment
- **Reddit:** Trending (r/stocks, r/wallstreetbets)
- **Twitter:** 72% bullish mentions
- **StockTwits:** 68% bullish

---

## 🎯 Options Analysis

### Options Flow: ⚠️ **UNUSUAL ACTIVITY DETECTED**
- **Put/Call Ratio:** 0.42 (bullish)
- **Implied Volatility:** 22.5% (IV Rank: 35)
- **IV Percentile:** 42%

### Notable Trades (Today)
- 🟢 **Call Sweep:** 5,000 contracts @ $180 strike, Dec expiry ($2.5M premium)
- 🟢 **Call Sweep:** 3,000 contracts @ $185 strike, Jan expiry ($1.8M premium)
- 🔴 **Put Buy:** 2,000 contracts @ $170 strike, Nov expiry (hedge)

**Interpretation:** Smart money positioning for upside into year-end.

---

## 👔 Insider & Institutional

### Insider Trading (Last 3 Months)
- **Buys:** 3 transactions, $2.1M
- **Sells:** 12 transactions, $45.3M (routine diversification)
- **Net:** Neutral (scheduled sales)

### Institutional Holdings
- **Ownership:** 61.2%
- **Recent Changes:** +2.3% (accumulation)
- **Top Holders:** Vanguard (8.2%), BlackRock (6.5%), Berkshire (5.8%)

---

## 📅 Earnings Analysis

### Next Earnings
- **Date:** 2025-01-30 (87 days away)
- **Estimate:** $2.10 per share
- **Whisper:** $2.15 per share

### Recent Performance
- **Last Quarter:** Beat by $0.08 (Q4 2024)
- **Surprise History:** 4/4 beats (last year)
- **Average Surprise:** +4.2%

---

## 🏆 Competitive Analysis

### Peer Comparison
| Metric | AAPL | MSFT | GOOGL | META |
|--------|------|------|-------|------|
| P/E | 28.5 | 34.2 | 22.1 | 25.8 |
| Revenue Growth | 2.1% | 12.5% | 8.7% | 22.3% |
| Profit Margin | 25.3% | 36.2% | 26.5% | 35.1% |
| Market Share | #1 | #2 | #3 | #4 |

**Competitive Advantages:**
- Ecosystem lock-in (iOS, Mac, Services)
- Brand loyalty (highest in tech)
- Services recurring revenue
- Supply chain mastery

---

## ⚠️ Risk Assessment

### Risk Metrics
- **Beta:** 1.25 (25% more volatile than market)
- **Volatility (30d):** 18.5%
- **Max Drawdown (1yr):** -18.2%
- **Sharpe Ratio:** 1.45 (good risk-adjusted returns)

### Risk Factors
- 🔴 **China Exposure:** 19% of revenue (geopolitical risk)
- 🟡 **Regulatory:** EU antitrust scrutiny
- 🟡 **Competition:** Android gaining share in emerging markets
- 🟢 **Market Risk:** Tech sector correlation

---

## 🎯 Trade Setup

### 🟢 BULLISH SCENARIO (Recommended)
- **Entry Zone:** $172.00 - $174.50 (on pullback)
- **Stop Loss:** $168.00 (-3.5%)
- **Target 1:** $182.00 (+5.5%) - Resistance
- **Target 2:** $192.00 (+11.5%) - Pattern target
- **Risk/Reward:** 1:2.8
- **Position Size:** $2,770 (1% risk = $1,385)
- **Shares:** 16 shares
- **Time Horizon:** 4-8 weeks
- **Command:** `#buy AAPL 16 @ 173.00`

### 🔴 BEARISH SCENARIO (Alternative)
- **Entry:** $178.50 (short on resistance rejection)
- **Stop Loss:** $182.00 (+2%)
- **Target:** $168.00 (-6%)
- **Risk/Reward:** 1:3.0
- **Not recommended** (trend is bullish)

### 📊 OPTIONS STRATEGY
- **Strategy:** Bull Call Spread
- **Buy:** $175 Call, Dec expiry
- **Sell:** $185 Call, Dec expiry
- **Net Cost:** $4.50 per spread
- **Max Profit:** $5.50 (+122%)
- **Max Loss:** $4.50 (-100%)
- **Breakeven:** $179.50

---

## ✅ Bottom Line

### Overall Assessment
- **Rating:** ⭐⭐⭐⭐ **BUY**
- **Confidence:** 85%
- **Time Horizon:** Medium-term (4-8 weeks)
- **Key Catalyst:** iPhone 16 momentum + Services growth
- **Next Action:** **BUY on pullback to $172-$174**

### Why This Trade Works
1. ✅ Strong technical setup (ascending triangle)
2. ✅ Bullish MACD crossover
3. ✅ Above all major moving averages
4. ✅ Unusual call options activity
5. ✅ Analyst upgrades and positive sentiment
6. ✅ Services revenue accelerating
7. ✅ Institutional accumulation

### What Could Go Wrong
1. ⚠️ China tensions escalate
2. ⚠️ Broader market selloff
3. ⚠️ iPhone demand disappoints

### Quick Commands
- `#buy AAPL 16 @ 173.00` - Enter position
- `#watch AAPL` - Add to watchlist
- `#alert AAPL > 182` - Set price alert for target

---

*Analysis generated: 2025-11-04 16:15 PST*
*Sources: Bloomberg, Yahoo Finance, TradingView, Unusual Whales, SEC Filings*
```

## Additional Features to Consider

1. **Comparison Mode:** `/analyze compare AAPL MSFT` - Side-by-side comparison
2. **Historical Analysis:** `/analyze AAPL history` - Past performance analysis
3. **Sector Analysis:** `/analyze sector tech` - Analyze entire sector
4. **Watchlist Analysis:** `/analyze watchlist` - Analyze all watchlist symbols
5. **Portfolio Analysis:** `/analyze portfolio` - Analyze all current positions
6. **Export:** Save analysis as PDF or markdown file
7. **Alerts:** Set alerts based on analysis triggers
8. **Backtesting:** Show how similar setups performed historically

## Success Metrics

- ✅ Comprehensive coverage (10+ analysis sections)
- ✅ Specific trade setups with exact prices
- ✅ Real-time data from Perplexity
- ✅ Clear formatting with emojis and tables
- ✅ Actionable commands included
- ✅ Risk assessment and position sizing
- ✅ Multi-symbol support
- ✅ Response time < 30 seconds
- ✅ Citations and sources provided
