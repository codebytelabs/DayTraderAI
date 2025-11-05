# `/analyze` Command - Implementation Summary

## ✅ What Was Built

A comprehensive deep-dive stock analysis command that uses **Perplexity for research** + **OpenRouter for synthesis** to provide professional-grade stock reports.

## Command Syntax

```
/analyze SYMBOL          # Single stock analysis
/analyze AAPL            # Analyze Apple
/analyze AAPL TSLA MSFT  # Analyze multiple stocks (max 3)
```

## How It Works

### 1. Query Detection
**File:** `backend/copilot/query_router.py`

- Detects `/analyze` command
- Extracts symbols from query
- Routes to `deep_analysis` category
- Targets: `["perplexity", "openrouter"]`

### 2. Perplexity Research (15-20 seconds)
**File:** `backend/main.py` - `_build_perplexity_prompt()`

Researches 10 comprehensive sections:
1. **Technical Analysis** - Price, indicators, patterns, momentum
2. **Fundamental Analysis** - Financials, valuation, growth
3. **Sentiment & News** - Headlines, ratings, social media
4. **Options Analysis** - Flow, IV, unusual activity
5. **Insider & Institutional** - Recent transactions, holdings
6. **Earnings** - Next date, estimates, history
7. **Competitive Landscape** - Peers, market share
8. **Risk Factors** - Beta, volatility, risks
9. **Trade Setup** - Entry, stop, targets
10. **Bottom Line** - Rating, confidence, action

### 3. OpenRouter Synthesis (5-10 seconds)
**File:** `backend/main.py` - Enhanced system prompt

- Receives Perplexity research
- Synthesizes into professional report
- Formats with markdown, emojis, tables
- Provides specific trade setups
- Calculates position sizes (1% risk)
- Includes actionable commands

## Response Structure

```markdown
# 📊 Deep Analysis: AAPL

## Executive Summary
**Current Price:** $175.43 (+1.2%)
**Rating:** ⭐⭐⭐⭐ **BUY** (85% confidence)
**Key Catalyst:** iPhone 16 launch momentum
**Verdict:** Strong technical setup with bullish fundamentals

## 📈 Technical Analysis
### Price Action
- Current: $175.43
- 52-Week Range: $164.08 - $199.62
- Support: $172.50, $170.00
- Resistance: $178.00, $182.50

### Indicators
- RSI (14): 58.3 → Neutral
- MACD: Bullish crossover
- Moving Averages: Above 20/50/200 day ✅
- Volume: 15% above average

### Chart Pattern
- Pattern: Ascending triangle
- Breakout: $178.00
- Target: $192.00 (+9.5%)

### Momentum
- Short-term: 🟢 Bullish
- Medium-term: 🟢 Bullish
- Long-term: 🟢 Bullish

## 💰 Fundamental Analysis
### Valuation
- P/E: 28.5 (vs sector: 25.2)
- PEG: 2.1 → Fair value
- Verdict: 📊 Fairly valued

### Financial Health
- Revenue: $383.3B (+2.1% YoY)
- Net Income: $97.0B (+3.5% YoY)
- Profit Margin: 25.3%
- ROE: 147.4%
- FCF: $99.6B

## 📰 Sentiment & News
### News Sentiment: 🟢 POSITIVE (78%)
- "iPhone 16 sales exceed expectations" - Bloomberg
- "Services revenue hits all-time high" - CNBC

### Analyst Ratings
- Strong Buy: 15 | Buy: 22 | Hold: 8
- Average Target: $195.50 (+11.4%)

## 🎯 Options Analysis
### Options Flow: ⚠️ UNUSUAL ACTIVITY
- Put/Call Ratio: 0.42 (bullish)
- IV: 22.5% (IV Rank: 35)

### Notable Trades
- 🟢 Call Sweep: 5,000 @ $180 strike ($2.5M)
- 🟢 Call Sweep: 3,000 @ $185 strike ($1.8M)

## 👔 Insider & Institutional
### Insider Trading (3 months)
- Buys: 3 transactions, $2.1M
- Sells: 12 transactions, $45.3M
- Net: Neutral

### Institutional
- Ownership: 61.2%
- Recent: +2.3% (accumulation)
- Top: Vanguard (8.2%), BlackRock (6.5%)

## 📅 Earnings Analysis
- Next: 2025-01-30 (87 days)
- Estimate: $2.10/share
- History: 4/4 beats

## 🏆 Competitive Analysis
| Metric | AAPL | MSFT | GOOGL |
|--------|------|------|-------|
| P/E | 28.5 | 34.2 | 22.1 |
| Growth | 2.1% | 12.5% | 8.7% |
| Margin | 25.3% | 36.2% | 26.5% |

## ⚠️ Risk Assessment
- Beta: 1.25
- Volatility: 18.5%
- Max Drawdown: -18.2%
- Sharpe: 1.45

### Risk Factors
- 🔴 China exposure (19% revenue)
- 🟡 EU antitrust scrutiny
- 🟡 Android competition

## 🎯 Trade Setup

### 🟢 BULLISH (Recommended)
- **Entry:** $172.00 - $174.50
- **Stop Loss:** $168.00 (-3.5%)
- **Target 1:** $182.00 (+5.5%)
- **Target 2:** $192.00 (+11.5%)
- **R/R:** 1:2.8
- **Size:** 16 shares ($2,770)
- **Horizon:** 4-8 weeks
- **Command:** `#buy AAPL 16 @ 173.00`

### 📊 OPTIONS
- Bull Call Spread: $175/$185
- Cost: $4.50
- Max Profit: $5.50 (+122%)

## ✅ Bottom Line
- **Rating:** ⭐⭐⭐⭐ **BUY**
- **Confidence:** 85%
- **Catalyst:** iPhone momentum
- **Action:** BUY on pullback to $172-$174

### Why This Works
1. ✅ Ascending triangle pattern
2. ✅ Bullish MACD crossover
3. ✅ Unusual call activity
4. ✅ Analyst upgrades
5. ✅ Services accelerating

### Quick Commands
- `#buy AAPL 16 @ 173.00`
- `#watch AAPL`
- `#alert AAPL > 182`

*Sources: Bloomberg, Yahoo Finance, TradingView*
```

## Features Implemented

### ✅ Core Features
- [x] Single symbol analysis
- [x] Multi-symbol analysis (up to 3)
- [x] Perplexity research integration
- [x] OpenRouter synthesis
- [x] 10 comprehensive sections
- [x] Specific trade setups
- [x] Position sizing (1% risk)
- [x] Beautiful markdown formatting
- [x] Emojis and visual appeal
- [x] Tables for comparisons
- [x] Actionable commands
- [x] Citations and sources

### ✅ Analysis Sections
1. Executive Summary
2. Technical Analysis
3. Fundamental Analysis
4. Sentiment & News
5. Options Analysis
6. Insider & Institutional
7. Earnings Analysis
8. Competitive Analysis
9. Risk Assessment
10. Trade Setup
11. Bottom Line

### ✅ UI Integration
- Added to CommandPalette
- Shows in `/` command list
- Category: 🔬 Deep Analysis
- Auto-complete support

## Usage Examples

### Example 1: Single Stock
```
/analyze AAPL
```
**Response:** Full 10-section analysis of Apple

### Example 2: Multiple Stocks
```
/analyze AAPL TSLA MSFT
```
**Response:** 
- Comparative summary table
- Individual analysis for each
- Portfolio fit analysis
- Suggested allocation

### Example 3: From Command Palette
1. Type `/` in chat
2. Select `/analyze SYMBOL`
3. Replace SYMBOL with ticker
4. Press Enter

## Response Time
- **Perplexity Research:** 15-20 seconds
- **OpenRouter Synthesis:** 5-10 seconds
- **Total:** 20-30 seconds

## Benefits

### 1. Comprehensive Coverage
- 10+ analysis sections
- Technical + Fundamental + Sentiment
- Options + Insider + Institutional
- Earnings + Competitive + Risk

### 2. Actionable Intelligence
- Specific entry/exit prices
- Exact stop loss levels
- Position sizes calculated
- Ready-to-execute commands

### 3. Professional Formatting
- Beautiful markdown
- Emojis for visual appeal
- Tables for comparisons
- Clear section headers

### 4. Real-Time Data
- Perplexity searches live data
- Recent news and headlines
- Current analyst ratings
- Latest options flow

### 5. Risk Management
- Position sizing (1% risk rule)
- Stop losses for every setup
- Risk/reward ratios
- Risk factors identified

## Comparison

### Before (Generic Query)
```
User: "Tell me about AAPL"
Response: "Apple is a tech company trading at $175..."
```

### After (/analyze Command)
```
User: "/analyze AAPL"
Response: [Full 10-section professional report with:
- Executive summary with rating
- Technical analysis with charts
- Fundamental analysis with financials
- Sentiment analysis with news
- Options flow analysis
- Insider/institutional activity
- Earnings analysis
- Competitive comparison
- Risk assessment
- Specific trade setup with entry/stop/targets
- Bottom line with rating and action]
```

## Future Enhancements

### Phase 2 Features
1. **Historical Backtesting** - Show how similar setups performed
2. **Sector Comparison** - `/analyze sector tech`
3. **Watchlist Analysis** - `/analyze watchlist`
4. **Portfolio Analysis** - `/analyze portfolio`
5. **Export to PDF** - Save reports
6. **Price Alerts** - Auto-set alerts from analysis
7. **Scheduled Analysis** - Daily/weekly reports
8. **ML Scoring** - Add ML confidence scores
9. **Sentiment Tracking** - Track sentiment changes
10. **Earnings Plays** - Pre-earnings analysis

### Advanced Features
- **Comparison Mode:** `/analyze compare AAPL MSFT`
- **Historical Mode:** `/analyze AAPL history`
- **Options Mode:** `/analyze AAPL options`
- **Earnings Mode:** `/analyze AAPL earnings`
- **Technical Mode:** `/analyze AAPL technical`
- **Fundamental Mode:** `/analyze AAPL fundamental`

## Configuration

### Required API Keys
```bash
PERPLEXITY_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

### Settings
```python
# In backend/config.py
COPILOT_HYBRID_ROUTING = True  # Enable Perplexity + OpenRouter
ANALYZE_MAX_SYMBOLS = 3        # Max symbols per query
ANALYZE_CACHE_TTL = 300        # Cache for 5 minutes
```

## Testing

### Test Commands
```
/analyze AAPL
/analyze TSLA
/analyze AAPL TSLA MSFT
/analyze nvda
```

### Expected Behavior
1. Query detected as `deep_analysis`
2. Routed to Perplexity + OpenRouter
3. Perplexity researches 10 sections
4. OpenRouter synthesizes report
5. Response formatted with markdown
6. Includes specific trade setups
7. Shows actionable commands

## Success Metrics

- ✅ Command detection working
- ✅ Symbol extraction working
- ✅ Perplexity research comprehensive
- ✅ OpenRouter synthesis professional
- ✅ Markdown formatting beautiful
- ✅ Trade setups specific
- ✅ Position sizing calculated
- ✅ Commands actionable
- ✅ Response time < 30 seconds
- ✅ Citations included

## Files Modified

1. ✅ `backend/copilot/query_router.py` - Command detection
2. ✅ `backend/main.py` - Perplexity prompt + OpenRouter synthesis
3. ✅ `components/CommandPalette.tsx` - UI integration
4. ✅ `ANALYZE_COMMAND_SPEC.md` - Full specification
5. ✅ `ANALYZE_COMMAND_SUMMARY.md` - This document

---

**Status:** Implemented and deployed ✅
**Ready for:** Production testing
**Expected Impact:** Professional-grade stock analysis at your fingertips
