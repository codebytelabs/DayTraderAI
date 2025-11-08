# AI-Powered Opportunity Discovery System

## Overview

Your trading system now uses **Perplexity AI** to discover the best trading opportunities every hour, replacing the static watchlist with dynamic AI-driven recommendations.

## How It Works

### Every Hour:

1. **AI Research** 🤖
   - Perplexity AI analyzes current market conditions
   - Reviews news, catalysts, momentum, volume
   - Identifies top 20 best day trading opportunities
   - Considers technical setups, liquidity, volatility

2. **Watchlist Update** 📊
   - System updates watchlist with AI-discovered symbols
   - Replaces old static list with fresh opportunities
   - Streams real-time data for new symbols

3. **Technical Analysis** 📈
   - Calculates indicators for each AI-recommended stock
   - Scores opportunities (now more permissive)
   - Ranks by total score

4. **Order Placement** 💰
   - Places bracket orders on best setups
   - Uses ATR-based stop loss and take profit
   - Manages risk with position sizing

## Key Features

### AI Discovery (`ai_opportunity_finder.py`)
- **Comprehensive Research**: AI analyzes market conditions, news, catalysts
- **Smart Extraction**: Extracts stock symbols from AI response
- **Validation**: Filters out invalid symbols and false positives
- **Fallback**: Uses default watchlist if AI fails

### Enhanced Scoring (`opportunity_scorer.py`)
- **More Permissive**: Baseline score ~92/110 (was ~30/110)
- **Focus on Risk Management**: Less restrictive entry, better exits
- **All Regimes Tradeable**: Works in trending, ranging, transitional markets

### Integration (`opportunity_scanner.py`)
- **Async AI Calls**: Non-blocking Perplexity API requests
- **Hybrid Mode**: Falls back to traditional scanning if AI fails
- **Caching**: Stores last discovery for reference

## Testing

```bash
cd backend
python test_ai_discovery.py
```

This will:
1. Ask AI to discover opportunities
2. Show the recommended symbols
3. Display AI reasoning
4. Show market overview

## Configuration

The system is **enabled by default**. To disable AI discovery:

```python
# In trading_engine.py initialization
scanner = OpportunityScanner(market_data_manager, use_ai=False)
```

## What Changed

### Before:
- Static watchlist: SPY, QQQ, AAPL, MSFT, NVDA, etc.
- Scanned same stocks every hour
- Strict scoring (many stocks scored <60)
- No AI research

### After:
- **Dynamic AI-discovered watchlist**
- **Fresh opportunities every hour**
- **Permissive scoring** (most stocks score 85-95)
- **AI-powered research and analysis**

## Monitoring

Watch the logs for:
- `🤖 AI discovering trading opportunities...` - AI research starting
- `✅ AI discovered X opportunities` - AI found symbols
- `📊 Top 5 AI-Discovered Opportunities` - Best picks
- `✓ Watchlist updated: X AI-discovered symbols` - Watchlist refreshed

## Benefits

1. **Always Fresh**: New opportunities every hour based on current conditions
2. **News-Driven**: AI considers breaking news and catalysts
3. **Adaptive**: Responds to changing market conditions
4. **Comprehensive**: Analyzes more factors than technical indicators alone
5. **Intelligent**: Uses real-time research, not historical patterns

## Next Steps

The system is ready to use! Just restart your backend:

```bash
cd backend
source ../venv/bin/activate
python main.py
```

The first AI scan will run immediately, then every hour after that.

## Troubleshooting

**If AI discovery fails:**
- System automatically falls back to default watchlist
- Check Perplexity API key in `.env`
- Check logs for error messages

**If no opportunities found:**
- Scoring is now very permissive (baseline ~92/110)
- Check minimum score threshold (default: 60)
- Verify market data is available

## Future Enhancements

- Symbol-specific AI analysis before entry
- AI-powered exit timing
- Sentiment analysis integration
- Multi-timeframe AI recommendations
