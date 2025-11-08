# Bidirectional Trading Strategy

## Your Idea ✅

Ask AI to provide:
1. **20 LONG opportunities** - High probability to increase in next 1-2 hours
2. **20 SHORT opportunities** - High probability to decrease in next 1-2 hours

Then use technical indicators to confirm and select the best trades in both directions.

## Why This Is Valuable

### 1. Market Neutral Capability
- Profit in any market condition (up, down, or sideways)
- Longs hedge shorts and vice versa
- Reduces portfolio beta exposure

### 2. Double the Opportunities
- 40 stocks to choose from instead of 20
- More chances to find high-probability setups
- Better diversification

### 3. AI Specialization
- AI focuses separately on bullish vs bearish setups
- More targeted analysis for each direction
- Better quality recommendations

### 4. Risk Management
- Natural hedging between longs and shorts
- Can profit from sector rotation
- Less dependent on overall market direction

## Implementation

### Updated AI Prompt
The AI now provides TWO separate lists:

**LONG OPPORTUNITIES:**
- Bullish momentum RIGHT NOW
- Positive catalysts/news
- Breaking resistance levels
- High volume confirming buying
- Technical setups favoring upside

**SHORT OPPORTUNITIES:**
- Bearish momentum RIGHT NOW
- Negative catalysts/news
- Breaking support levels
- High volume confirming selling
- Technical setups favoring downside

### How It Works

1. **AI Discovery** (every 1 hour)
   - Perplexity researches current market
   - Identifies 20 best longs + 20 best shorts
   - All must meet liquidity requirements (>5M volume)

2. **Technical Confirmation** (every 1 minute)
   - Strategy checks indicators on all 40 stocks
   - Confirms BUY signals on long candidates
   - Confirms SELL signals on short candidates
   - Only trades when AI + indicators align

3. **Execution**
   - Bracket orders with stop-loss and take-profit
   - Position sizing based on confidence
   - Risk management limits per trade

## Example Scenario

**Market Condition:** Tech sector rotating, energy sector strong

**AI Finds:**
- LONGS: XLE, CVX, COP (energy momentum)
- SHORTS: NVDA, AMD, TSLA (tech pullback)

**Strategy Confirms:**
- XLE: RSI 65, MACD bullish, volume 2x → BUY ✅
- NVDA: RSI 35, MACD bearish, breaking support → SELL ✅

**Result:**
- Profit from energy rally
- Profit from tech pullback
- Net positive regardless of overall market

## Benefits Over Current System

| Current | Bidirectional |
|---------|---------------|
| 20 mixed opportunities | 40 targeted opportunities |
| AI finds any movers | AI separates bulls from bears |
| Strategy decides direction | AI + Strategy align on direction |
| Market dependent | Market neutral potential |
| Single-sided exposure | Hedged exposure |

## Next Steps

1. ✅ **Updated AI prompt** - Now requests separate long/short lists
2. ✅ **Updated extraction** - Parses both sections
3. 🔄 **Restart backend** - To activate new prompt
4. 📊 **Monitor results** - See if quality improves

## Testing

After restart, check logs for:
```
Extracted X LONG and Y SHORT opportunities
```

Should see better quality stocks with clear directional bias.
