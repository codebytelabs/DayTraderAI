# 🤖 Copilot Enhancement Plan - Full System Intelligence

## 🎯 Goal
Transform the copilot from a simple chat interface into an intelligent trading assistant with full system awareness and hybrid LLM capabilities.

---

## 📊 Current State Analysis

### What Works ✅
- Basic chat interface in frontend
- OpenRouter integration for responses
- Simple message/response flow

### What's Missing ❌
- **No system context** - Copilot doesn't know account state, positions, or history
- **No technical analysis** - Can't see indicators or market conditions
- **No news context** - Unaware of recent market events
- **Single LLM only** - Only uses OpenRouter, missing Perplexity's strengths
- **No query routing** - All queries go to same model regardless of type

---

## 🏗️ Enhanced Architecture

### Hybrid LLM Approach

```
User Query
    ↓
Query Classifier
    ├─ News/Research → Perplexity (real-time web search, citations)
    ├─ Analysis/Advice → OpenRouter (reasoning, recommendations)
    └─ Complex → Chain Both (Perplexity context → OpenRouter analysis)
    ↓
Context Builder (adds full system state)
    ↓
LLM Processing
    ↓
Enhanced Response
```

### Context Builder Components

```python
def build_copilot_context():
    return {
        # Account State
        "equity": current_equity,
        "cash": available_cash,
        "buying_power": buying_power,
        "daily_pl": daily_profit_loss,
        "daily_pl_pct": daily_pl_percentage,
        
        # Current Positions
        "positions": [
            {
                "symbol": "AAPL",
                "qty": 100,
                "entry_price": 175.00,
                "current_price": 177.50,
                "unrealized_pl": 250.00,
                "take_profit": 180.00,
                "stop_loss": 173.00
            }
        ],
        
        # Recent Trades (last 10)
        "recent_trades": [
            {
                "symbol": "TSLA",
                "side": "BUY",
                "qty": 50,
                "entry": 250.00,
                "exit": 255.00,
                "pl": 250.00,
                "outcome": "WIN"
            }
        ],
        
        # Performance Metrics
        "metrics": {
            "win_rate": 0.65,
            "profit_factor": 2.1,
            "total_trades": 150,
            "wins": 98,
            "losses": 52,
            "sharpe_ratio": 1.8
        },
        
        # Technical Analysis
        "technical_indicators": {
            "AAPL": {
                "ema_9": 176.50,
                "ema_21": 174.20,
                "rsi": 62.5,
                "atr": 2.80,
                "trend": "BULLISH"
            }
        },
        
        # Market Conditions
        "market": {
            "spy_trend": "BULLISH",
            "vix": 15.2,
            "market_open": True
        },
        
        # Recent News (last 5 articles)
        "news": [
            {
                "symbol": "AAPL",
                "headline": "Apple announces record earnings",
                "sentiment": "POSITIVE",
                "timestamp": "2025-11-02T10:30:00Z"
            }
        ],
        
        # Risk Status
        "risk": {
            "current_risk_pct": 8.5,
            "max_risk_pct": 10.0,
            "circuit_breaker_triggered": False,
            "positions_count": 10,
            "max_positions": 20
        }
    }
```

---

## 🔀 Query Routing Logic

### Classification Patterns

**Route to Perplexity (News/Research):**
- Keywords: "what's happening", "latest news", "why did", "what caused"
- Patterns: "news about X", "market update", "earnings for X"
- Examples:
  - "What's happening with AAPL today?"
  - "Latest news on tech stocks"
  - "Why did TSLA drop?"

**Route to OpenRouter (Analysis/Advice):**
- Keywords: "should I", "recommend", "analyze", "what do you think"
- Patterns: "buy or sell", "portfolio analysis", "risk assessment"
- Examples:
  - "Should I buy AAPL at current price?"
  - "Analyze my portfolio risk"
  - "What's my best trade right now?"

**Chain Both (Complex Queries):**
- Patterns: Questions requiring both context and analysis
- Examples:
  - "Given recent AAPL news, should I increase my position?"
  - "What's the market saying about tech and how should I position?"

### Implementation

```python
class CopilotRouter:
    def classify_query(self, query: str) -> str:
        """Classify query type."""
        query_lower = query.lower()
        
        # News/Research patterns
        news_keywords = ["news", "happening", "latest", "why did", "what caused"]
        if any(kw in query_lower for kw in news_keywords):
            return "news"
        
        # Analysis/Advice patterns
        advice_keywords = ["should i", "recommend", "analyze", "think about"]
        if any(kw in query_lower for kw in advice_keywords):
            return "advice"
        
        # Default to advice
        return "advice"
    
    async def route_query(self, query: str, context: dict) -> str:
        """Route query to appropriate LLM."""
        query_type = self.classify_query(query)
        
        if query_type == "news":
            # Use Perplexity for news/research
            return await self.perplexity_query(query, context)
        
        elif query_type == "advice":
            # Use OpenRouter for analysis/advice
            return await self.openrouter_query(query, context)
        
        else:
            # Chain both for complex queries
            news_context = await self.perplexity_query(query, context)
            return await self.openrouter_query(
                f"{query}\n\nMarket Context: {news_context}",
                context
            )
```

---

## 📝 Implementation Tasks

### Phase 1: Context Builder (Week 1)

**Backend:**
- [ ] Create `backend/copilot/context_builder.py`
- [ ] Implement account state aggregation
- [ ] Add position details with TP/SL
- [ ] Include recent trade history
- [ ] Add performance metrics
- [ ] Fetch technical indicators
- [ ] Include market conditions
- [ ] Add recent news
- [ ] Include risk status

**API:**
- [ ] Create `/copilot/context` endpoint
- [ ] Return full context JSON
- [ ] Cache context for 30 seconds
- [ ] Update `/chat` endpoint to use context

### Phase 2: Query Router (Week 1)

**Backend:**
- [ ] Create `backend/copilot/query_router.py`
- [ ] Implement query classification
- [ ] Add Perplexity routing
- [ ] Add OpenRouter routing
- [ ] Implement chaining logic
- [ ] Add fallback handling

**Integration:**
- [ ] Update `/chat` endpoint to use router
- [ ] Test routing with different query types
- [ ] Verify context is passed correctly

### Phase 3: Enhanced Responses (Week 2)

**Backend:**
- [ ] Format context for LLM consumption
- [ ] Add system prompts for each LLM
- [ ] Implement response formatting
- [ ] Add source citations (from Perplexity)
- [ ] Include confidence scores

**Frontend:**
- [ ] Update ChatPanel to show sources
- [ ] Add loading states for different query types
- [ ] Display confidence indicators
- [ ] Show which LLM was used

### Phase 4: Testing (Week 2)

**Unit Tests:**
- [ ] Test context builder with mock data
- [ ] Test query classification
- [ ] Test routing logic
- [ ] Test response formatting

**Integration Tests:**
- [ ] Test end-to-end chat flow
- [ ] Test with real account data
- [ ] Test Perplexity queries
- [ ] Test OpenRouter queries
- [ ] Test chained queries

---

## 🎯 Expected Improvements

### Before Enhancement:
```
User: "Should I buy AAPL?"
Copilot: "AAPL is a strong company with good fundamentals..."
(Generic response, no context)
```

### After Enhancement:
```
User: "Should I buy AAPL?"
Copilot: "Based on your current portfolio:
- You have $50,000 buying power available
- AAPL is showing bullish momentum (EMA 9 > EMA 21)
- Recent news: Apple announced record earnings (POSITIVE)
- Your current risk exposure: 8.5% (safe to add)
- Technical setup: RSI at 62 (not overbought)

Recommendation: YES, consider buying 100 shares at current price $177.50
- Entry: $177.50
- Take Profit: $182.00 (+2.5%)
- Stop Loss: $175.00 (-1.4%)
- Risk/Reward: 1:1.8 ✅

This trade fits your strategy and risk parameters."
(Specific, actionable, context-aware)
```

---

## 🔬 Testing Strategy

### Test Scenarios

**1. Account State Queries:**
- "What's my current P/L?"
- "How many positions do I have?"
- "What's my buying power?"

**2. Position Analysis:**
- "Analyze my AAPL position"
- "Should I close my TSLA position?"
- "What's my best performing stock?"

**3. News Queries:**
- "What's happening with tech stocks?"
- "Latest news on AAPL"
- "Why did the market drop today?"

**4. Trade Recommendations:**
- "Should I buy NVDA?"
- "What should I trade next?"
- "Any good opportunities right now?"

**5. Risk Assessment:**
- "Am I over-exposed?"
- "What's my risk level?"
- "Should I reduce positions?"

**6. Performance Analysis:**
- "How am I doing this week?"
- "What's my win rate?"
- "Am I profitable?"

---

## 📊 Success Metrics

### Quantitative:
- Response relevance: >90%
- Context accuracy: 100%
- Query routing accuracy: >95%
- Response time: <3 seconds
- User satisfaction: >4.5/5

### Qualitative:
- Responses are specific and actionable
- Copilot understands portfolio state
- Recommendations align with strategy
- News context is current and relevant
- Risk awareness is accurate

---

## 🚀 Deployment Plan

### Week 1:
- Build context builder
- Implement query router
- Test with mock data

### Week 2:
- Integrate with chat endpoint
- Add frontend enhancements
- Comprehensive testing

### Week 3:
- User acceptance testing
- Performance optimization
- Documentation

### Week 4:
- Production deployment
- Monitor and iterate
- Collect feedback

---

## 💡 Future Enhancements

### Phase 2 Features:
- Voice input/output
- Multi-turn conversations with memory
- Proactive alerts ("AAPL hit your target!")
- Strategy backtesting via chat
- Portfolio optimization suggestions

### Phase 3 Features:
- Multi-language support
- Custom copilot personalities
- Integration with external research
- Automated trade execution via chat
- Learning from user preferences

---

## ⚠️ Important Notes

### Context Privacy:
- Never log sensitive account data
- Sanitize context before sending to LLMs
- Use secure API connections
- Comply with data regulations

### LLM Costs:
- Perplexity: ~$5 per 1M tokens
- OpenRouter: Varies by model
- Implement caching to reduce costs
- Monitor usage and set limits

### Reliability:
- Always have fallback to OpenRouter
- Handle API failures gracefully
- Cache responses when appropriate
- Monitor LLM availability

---

This enhanced copilot will transform the user experience from basic chat to intelligent trading assistant!
