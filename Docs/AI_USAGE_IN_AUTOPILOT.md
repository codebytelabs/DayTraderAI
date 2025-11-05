# AI Usage in Autopilot Mode

## TL;DR: No, Autopilot Does NOT Use OpenRouter or Perplexity

The automated trading system (autopilot) **does not call any AI services**. It uses pure technical analysis (EMA crossovers, ATR, etc.).

## What Uses AI Services?

### OpenRouter & Perplexity are ONLY used for:

1. **Copilot Chat** - When you ask questions in the UI
2. **Manual Analysis** - When you request market research
3. **Command Responses** - When you use slash commands

### What Autopilot Actually Uses:

✅ **Technical Indicators**:
- EMA (Exponential Moving Average)
- ATR (Average True Range)
- Volume analysis
- Price action

✅ **Risk Management**:
- Position sizing calculations
- Stop loss placement
- Take profit targets
- Circuit breakers

✅ **Market Data**:
- Real-time price feeds from Alpaca
- Historical bars for calculations
- No AI interpretation

## Cost Breakdown

### Autopilot (24/7 Running):
- **OpenRouter**: $0.00/day
- **Perplexity**: $0.00/day
- **Total**: $0.00/day

The autopilot is completely free to run (except Alpaca data, which is free for paper trading).

### Copilot Chat (When You Use It):
- **OpenRouter**: ~$0.001-0.01 per query (depends on model)
- **Perplexity**: ~$0.005-0.02 per search
- **Total**: Only when you actively chat

## Example: Typical Day

### Autopilot Running All Day:
```
06:00 - Market data fetched (free)
06:01 - Features calculated (free)
06:02 - Strategy evaluated (free)
...
20:00 - Market closed
Total AI cost: $0.00
```

### You Ask Copilot 10 Questions:
```
"What's happening with TSLA?" - $0.01
"Analyze SPY" - $0.02 (uses Perplexity)
"Show my positions" - $0.00 (no AI needed)
...
Total AI cost: ~$0.10-0.30
```

## How to Verify

Check your logs - you'll see:

### Autopilot Logs (No AI):
```
✓ Fetched 174 bars for TSLA
✓ Updated features for 10 symbols
✓ Evaluating 10 symbols
✓ Signal detected for MSFT
```

### Copilot Logs (Uses AI):
```
✓ Perplexity search completed: 5 citations
✓ OpenRouter response received (model: gpt-oss-safeguard-20b)
```

## Configuration

If you want to disable AI services entirely:

```bash
# In .env file
OPENROUTER_API_KEY=""
PERPLEXITY_API_KEY=""
```

The autopilot will continue working fine. You just won't be able to use the copilot chat feature.

## Summary

| Feature | Uses AI | Cost |
|---------|---------|------|
| Autopilot Trading | ❌ No | $0 |
| Signal Detection | ❌ No | $0 |
| Position Management | ❌ No | $0 |
| Risk Checks | ❌ No | $0 |
| Copilot Chat | ✅ Yes | ~$0.01-0.02/query |
| Market Research | ✅ Yes | ~$0.01-0.03/query |

**Bottom Line**: Your autopilot can run 24/7 without any AI costs. AI is only used when you actively interact with the copilot chat.
