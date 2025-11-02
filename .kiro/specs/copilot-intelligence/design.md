# Design Document - Copilot Intelligence Enhancement

## Overview

The Copilot Intelligence Enhancement transforms the basic chat interface into a sophisticated AI trading assistant by implementing three core components:

1. **Context Builder** - Aggregates all system state, market data, and news into a comprehensive context object
2. **Query Router** - Classifies user queries and intelligently routes them to specialized AI models
3. **Enhanced Chat Endpoint** - Orchestrates context building, query routing, and response generation

The design leverages existing infrastructure (Trading Engine, Position Manager, Market Data, News Client) and integrates with proven AI services (Perplexity for research, OpenRouter for analysis) to create an intelligent assistant that understands the complete trading system state.

## Architecture

### High-Level Architecture

```
User Query
    ↓
Chat Endpoint (/chat)
    ↓
┌─────────────────────────────────────┐
│     Context Builder                 │
│  ┌──────────────────────────────┐  │
│  │ Account State Aggregator     │  │
│  │ - Equity, cash, buying power │  │
│  │ - Total P/L                  │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │ Position Context Aggregator  │  │
│  │ - Open positions with P/L    │  │
│  │ - TP/SL levels               │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │ Trade History Aggregator     │  │
│  │ - Recent 20 trades           │  │
│  │ - Performance metrics        │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │ Market Context Aggregator    │  │
│  │ - Technical indicators       │  │
│  │ - Signals and trends         │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │ News Context Aggregator      │  │
│  │ - Recent news with sentiment │  │
│  │ - Trending symbols           │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │ Risk Context Aggregator      │  │
│  │ - Current exposure           │  │
│  │ - Remaining capacity         │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
    ↓
Query Router
    ↓
┌─────────────────────────────────────┐
│  Query Classification               │
│  - News/Research → Perplexity       │
│  - Trade Advice → OpenRouter        │
│  - Complex → Chain both             │
└─────────────────────────────────────┘
    ↓
AI Model Execution
    ↓
Response Formatting
    ↓
Frontend Display
```

### Component Interaction

```
┌──────────────┐
│ Trading      │
│ Engine       │──┐
└──────────────┘  │
                  │
┌──────────────┐  │
│ Position     │  │
│ Manager      │──┤
└──────────────┘  │
                  │
┌──────────────┐  │    ┌──────────────┐
│ Market Data  │  │───→│ Context      │
│ Manager      │──┤    │ Builder      │
└──────────────┘  │    └──────────────┘
                  │           ↓
┌──────────────┐  │    ┌──────────────┐
│ News Client  │──┤    │ Query        │
└──────────────┘  │    │ Router       │
                  │    └──────────────┘
┌──────────────┐  │           ↓
│ Risk         │  │    ┌──────────────┐
│ Manager      │──┘    │ Perplexity   │
└──────────────┘       │ OpenRouter   │
                       └──────────────┘
```

## Components and Interfaces

### 1. Context Builder (`backend/copilot/context_builder.py`)

**Purpose:** Aggregates all relevant system state and market data into a structured context object.

#### Class: `ContextBuilder`

```python
class ContextBuilder:
    """Builds comprehensive context for AI copilot queries."""
    
    def __init__(
        self,
        trading_engine: TradingEngine,
        position_manager: PositionManager,
        market_data: MarketDataManager,
        news_client: NewsClient,
        risk_manager: RiskManager
    ):
        """Initialize with references to core system components."""
        
    async def build_context(
        self,
        query: str,
        include_account: bool = True,
        include_positions: bool = True,
        include_history: bool = True,
        include_market: bool = True,
        include_news: bool = True,
        include_risk: bool = True
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for a query.
        
        Returns:
            {
                "account": {...},
                "positions": [...],
                "history": [...],
                "metrics": {...},
                "market": {...},
                "news": [...],
                "risk": {...},
                "timestamp": "2024-01-15T10:30:00Z"
            }
        """
```

#### Sub-Components

**AccountStateAggregator**
```python
async def aggregate_account_state(self) -> Dict[str, Any]:
    """
    Returns:
        {
            "equity": 105000.00,
            "cash": 45000.00,
            "buying_power": 90000.00,
            "total_pl": 5000.00,
            "total_pl_pct": 5.0
        }
    """
```

**PositionContextAggregator**
```python
async def aggregate_positions(self) -> List[Dict[str, Any]]:
    """
    Returns:
        [
            {
                "symbol": "AAPL",
                "qty": 100,
                "entry_price": 175.50,
                "current_price": 177.80,
                "unrealized_pl": 230.00,
                "unrealized_pl_pct": 1.31,
                "take_profit": 179.01,
                "stop_loss": 173.75,
                "position_value": 17780.00
            },
            ...
        ]
    """
```

**TradeHistoryAggregator**
```python
async def aggregate_trade_history(self, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Returns:
        [
            {
                "symbol": "TSLA",
                "entry_time": "2024-01-15T09:30:00Z",
                "exit_time": "2024-01-15T10:15:00Z",
                "entry_price": 245.00,
                "exit_price": 248.50,
                "qty": 50,
                "pl": 175.00,
                "pl_pct": 1.43,
                "outcome": "win"
            },
            ...
        ]
    """
```

**PerformanceMetricsAggregator**
```python
async def aggregate_metrics(self, trades: List[Dict]) -> Dict[str, Any]:
    """
    Returns:
        {
            "total_trades": 150,
            "winning_trades": 85,
            "losing_trades": 65,
            "win_rate": 56.67,
            "profit_factor": 1.85,
            "avg_win": 125.50,
            "avg_loss": -75.30,
            "sharpe_ratio": 2.15,
            "max_drawdown": -3.5
        }
    """
```

**MarketContextAggregator**
```python
async def aggregate_market_context(
    self,
    symbols: List[str],
    query_symbol: Optional[str] = None
) -> Dict[str, Any]:
    """
    Returns:
        {
            "spy_trend": "bullish",
            "vix": 14.5,
            "symbols": {
                "AAPL": {
                    "price": 177.80,
                    "ema_9": 176.50,
                    "ema_21": 175.20,
                    "rsi": 62.5,
                    "atr": 2.85,
                    "signal": "bullish",
                    "momentum": "strong"
                },
                ...
            },
            "query_symbol_detail": {...}  # If query mentions specific symbol
        }
    """
```

**NewsContextAggregator**
```python
async def aggregate_news_context(
    self,
    symbols: List[str],
    hours: int = 24
) -> Dict[str, Any]:
    """
    Returns:
        {
            "recent_news": [
                {
                    "symbol": "AAPL",
                    "headline": "Apple announces new product line",
                    "summary": "...",
                    "sentiment": "positive",
                    "sentiment_score": 0.85,
                    "source": "Reuters",
                    "published": "2024-01-15T08:30:00Z"
                },
                ...
            ],
            "trending_symbols": ["NVDA", "TSLA"],
            "sentiment_summary": {
                "AAPL": "positive",
                "TSLA": "neutral",
                ...
            }
        }
    """
```

**RiskContextAggregator**
```python
async def aggregate_risk_context(self) -> Dict[str, Any]:
    """
    Returns:
        {
            "current_exposure_pct": 8.5,
            "remaining_capacity_pct": 11.5,
            "open_positions": 8,
            "max_positions": 20,
            "remaining_positions": 12,
            "daily_pl": 450.00,
            "daily_pl_pct": 0.43,
            "circuit_breaker_threshold": -5.0,
            "distance_to_breaker": 5.43,
            "risk_per_trade_pct": 2.0,
            "max_position_size": 2100.00
        }
    """
```

### 2. Query Router (`backend/copilot/query_router.py`)

**Purpose:** Classifies user queries and routes them to the most appropriate AI model.

#### Class: `QueryRouter`

```python
class QueryRouter:
    """Routes queries to appropriate AI models based on classification."""
    
    def __init__(
        self,
        perplexity_client: PerplexityClient,
        openrouter_client: OpenRouterClient
    ):
        """Initialize with AI client references."""
        
    async def route_query(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Classify query and route to appropriate AI model(s).
        
        Returns:
            {
                "response": "...",
                "model_used": "perplexity" | "openrouter" | "chained",
                "query_type": "news" | "advice" | "complex",
                "confidence": 0.95,
                "sources": [...],  # If Perplexity used
                "routing_path": ["perplexity", "openrouter"]  # If chained
            }
        """
```

#### Query Classification Logic

```python
def classify_query(self, query: str) -> Tuple[str, float]:
    """
    Classify query type using keyword matching and patterns.
    
    News/Research indicators:
    - "news", "what happened", "why", "latest", "recent"
    - "earnings", "announcement", "report"
    - Questions about events or reasons
    
    Trade Advice indicators:
    - "should I buy", "should I sell", "recommend"
    - "what do you think about", "is it a good time"
    - "entry", "exit", "target", "stop"
    
    Complex indicators:
    - Multiple questions
    - Requires both research and analysis
    - "analyze", "evaluate", "compare"
    
    Returns:
        ("news" | "advice" | "complex", confidence_score)
    """
```

#### Routing Strategies

**News/Research Route**
```python
async def route_to_perplexity(
    self,
    query: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Route to Perplexity for news research.
    
    Context included:
    - Recent news for relevant symbols
    - Market conditions
    - User's positions (for relevance)
    """
```

**Trade Advice Route**
```python
async def route_to_openrouter(
    self,
    query: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Route to OpenRouter for trade analysis.
    
    Full context included:
    - Account state and buying power
    - All positions with P/L
    - Performance metrics
    - Technical indicators
    - Risk limits and exposure
    """
```

**Complex/Chained Route**
```python
async def route_chained(
    self,
    query: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Chain Perplexity (research) → OpenRouter (analysis).
    
    1. Query Perplexity for news/research
    2. Add Perplexity response to context
    3. Query OpenRouter with enriched context
    4. Return combined response
    """
```

### 3. Enhanced Chat Endpoint (`backend/main.py`)

**Purpose:** Orchestrate context building, query routing, and response generation.

#### Endpoint: `POST /chat`

```python
@app.post("/chat")
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Enhanced chat endpoint with full context awareness.
    
    Request:
        {
            "message": "Should I buy AAPL?",
            "include_context": true,
            "use_routing": true
        }
    
    Response:
        {
            "response": "Based on your portfolio...",
            "model_used": "openrouter",
            "query_type": "advice",
            "confidence": 0.92,
            "sources": [],
            "context_used": {
                "account": true,
                "positions": true,
                "market": true,
                "news": true
            },
            "metadata": {
                "response_time_ms": 1250,
                "context_build_time_ms": 450,
                "ai_query_time_ms": 800
            }
        }
    """
    
    # 1. Build context
    context = await context_builder.build_context(
        query=request.message,
        include_account=config.COPILOT_CONTEXT_ENABLED,
        include_positions=config.COPILOT_CONTEXT_ENABLED,
        include_history=config.COPILOT_CONTEXT_ENABLED,
        include_market=config.COPILOT_CONTEXT_ENABLED,
        include_news=config.COPILOT_CONTEXT_ENABLED,
        include_risk=config.COPILOT_CONTEXT_ENABLED
    )
    
    # 2. Route query
    if config.COPILOT_HYBRID_ROUTING:
        result = await query_router.route_query(request.message, context)
    else:
        # Default to OpenRouter with context
        result = await openrouter_client.query(request.message, context)
    
    # 3. Format response
    return ChatResponse(**result)
```

### 4. Frontend Integration (`components/ChatPanel.tsx`)

**Purpose:** Display rich, context-aware AI responses with transparency.

#### Enhanced Chat Message Display

```typescript
interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  metadata?: {
    model_used?: 'perplexity' | 'openrouter' | 'chained';
    query_type?: 'news' | 'advice' | 'complex';
    confidence?: number;
    sources?: Array<{
      title: string;
      url: string;
      snippet: string;
    }>;
    trade_recommendation?: {
      action: 'buy' | 'sell';
      symbol: string;
      entry: number;
      take_profit: number;
      stop_loss: number;
      position_size: number;
      risk_reward: number;
    };
  };
}
```

#### UI Components

**Model Badge**
```typescript
function ModelBadge({ model }: { model: string }) {
  const badges = {
    perplexity: { icon: '🔍', color: 'blue', label: 'Research' },
    openrouter: { icon: '🧠', color: 'purple', label: 'Analysis' },
    chained: { icon: '🔗', color: 'green', label: 'Deep Analysis' }
  };
  // Render badge with icon and color
}
```

**Confidence Indicator**
```typescript
function ConfidenceIndicator({ score }: { score: number }) {
  const level = score > 0.8 ? 'high' : score > 0.6 ? 'medium' : 'low';
  const colors = { high: 'green', medium: 'yellow', low: 'red' };
  // Render confidence bar or icon
}
```

**Trade Recommendation Card**
```typescript
function TradeRecommendationCard({ rec }: { rec: TradeRecommendation }) {
  return (
    <div className="trade-card">
      <h4>{rec.action.toUpperCase()} {rec.symbol}</h4>
      <div className="metrics">
        <div>Entry: ${rec.entry}</div>
        <div>Target: ${rec.take_profit} (+{rec.profit_pct}%)</div>
        <div>Stop: ${rec.stop_loss} (-{rec.loss_pct}%)</div>
        <div>R:R: 1:{rec.risk_reward}</div>
      </div>
      {config.COPILOT_TRADE_EXECUTION && (
        <button onClick={() => executeTrade(rec)}>
          Execute Trade
        </button>
      )}
    </div>
  );
}
```

**Source Citations**
```typescript
function SourceCitations({ sources }: { sources: Source[] }) {
  return (
    <div className="sources">
      <h5>Sources:</h5>
      {sources.map((source, i) => (
        <a key={i} href={source.url} target="_blank">
          [{i + 1}] {source.title}
        </a>
      ))}
    </div>
  );
}
```

## Data Models

### Context Object Schema

```typescript
interface CopilotContext {
  account: {
    equity: number;
    cash: number;
    buying_power: number;
    total_pl: number;
    total_pl_pct: number;
  };
  positions: Array<{
    symbol: string;
    qty: number;
    entry_price: number;
    current_price: number;
    unrealized_pl: number;
    unrealized_pl_pct: number;
    take_profit?: number;
    stop_loss?: number;
    position_value: number;
  }>;
  history: Array<{
    symbol: string;
    entry_time: string;
    exit_time: string;
    entry_price: number;
    exit_price: number;
    qty: number;
    pl: number;
    pl_pct: number;
    outcome: 'win' | 'loss';
  }>;
  metrics: {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    profit_factor: number;
    avg_win: number;
    avg_loss: number;
    sharpe_ratio: number;
    max_drawdown: number;
  };
  market: {
    spy_trend: 'bullish' | 'bearish' | 'neutral';
    vix: number;
    symbols: Record<string, {
      price: number;
      ema_9: number;
      ema_21: number;
      rsi: number;
      atr: number;
      signal: 'bullish' | 'bearish' | 'neutral';
      momentum: 'strong' | 'weak' | 'neutral';
    }>;
  };
  news: {
    recent_news: Array<{
      symbol: string;
      headline: string;
      summary: string;
      sentiment: 'positive' | 'negative' | 'neutral';
      sentiment_score: number;
      source: string;
      published: string;
    }>;
    trending_symbols: string[];
    sentiment_summary: Record<string, string>;
  };
  risk: {
    current_exposure_pct: number;
    remaining_capacity_pct: number;
    open_positions: number;
    max_positions: number;
    remaining_positions: number;
    daily_pl: number;
    daily_pl_pct: number;
    circuit_breaker_threshold: number;
    distance_to_breaker: number;
    risk_per_trade_pct: number;
    max_position_size: number;
  };
  timestamp: string;
}
```

## Error Handling

### Context Building Errors

```python
class ContextBuildError(Exception):
    """Base exception for context building errors."""
    pass

class PartialContextError(ContextBuildError):
    """Raised when some context components fail but others succeed."""
    def __init__(self, context: Dict, failed_components: List[str]):
        self.context = context
        self.failed_components = failed_components
```

**Strategy:** Continue with partial context and note missing data in response.

### AI Query Errors

```python
class AIQueryError(Exception):
    """Base exception for AI query errors."""
    pass

class AITimeoutError(AIQueryError):
    """Raised when AI query exceeds timeout."""
    pass

class AIRateLimitError(AIQueryError):
    """Raised when AI service rate limit is hit."""
    pass
```

**Strategy:** Implement exponential backoff and fallback to cached responses or error messages.

### Routing Errors

```python
class RoutingError(Exception):
    """Base exception for query routing errors."""
    pass

class ClassificationError(RoutingError):
    """Raised when query classification fails."""
    pass
```

**Strategy:** Default to OpenRouter with full context when classification fails.

## Testing Strategy

### Unit Tests

**Context Builder Tests**
- Test each aggregator independently
- Mock external dependencies (Trading Engine, Position Manager, etc.)
- Verify correct data structure and completeness
- Test error handling for missing data

**Query Router Tests**
- Test classification accuracy with sample queries
- Verify correct routing for each query type
- Test chaining logic
- Test fallback behavior

**Chat Endpoint Tests**
- Test with various query types
- Verify context building is called correctly
- Test with context enabled/disabled
- Test with routing enabled/disabled

### Integration Tests

**End-to-End Context Flow**
- Start with real system state
- Build context
- Verify all components are included
- Check data accuracy

**AI Model Integration**
- Test Perplexity queries with context
- Test OpenRouter queries with context
- Test chained queries
- Verify response formatting

**Frontend Integration**
- Test chat message display
- Verify metadata rendering
- Test trade recommendation cards
- Test source citations

### Performance Tests

**Context Building Performance**
- Measure aggregation time for each component
- Test with varying amounts of data (positions, history)
- Verify 500ms target is met
- Identify bottlenecks

**AI Query Performance**
- Measure Perplexity response time
- Measure OpenRouter response time
- Test timeout handling
- Verify fallback mechanisms

## Configuration

### Environment Variables

```bash
# Copilot Configuration
COPILOT_CONTEXT_ENABLED=true
COPILOT_HYBRID_ROUTING=true
COPILOT_TRADE_EXECUTION=false

# Performance Tuning
COPILOT_CONTEXT_TIMEOUT_MS=500
COPILOT_AI_TIMEOUT_MS=15000
COPILOT_CACHE_TTL_SECONDS=60

# Feature Flags
COPILOT_INCLUDE_ACCOUNT=true
COPILOT_INCLUDE_POSITIONS=true
COPILOT_INCLUDE_HISTORY=true
COPILOT_INCLUDE_MARKET=true
COPILOT_INCLUDE_NEWS=true
COPILOT_INCLUDE_RISK=true
```

### Runtime Configuration

```python
class CopilotConfig:
    """Runtime configuration for copilot system."""
    
    context_enabled: bool = True
    hybrid_routing: bool = True
    trade_execution: bool = False
    
    context_timeout_ms: int = 500
    ai_timeout_ms: int = 15000
    cache_ttl_seconds: int = 60
    
    include_account: bool = True
    include_positions: bool = True
    include_history: bool = True
    include_market: bool = True
    include_news: bool = True
    include_risk: bool = True
    
    max_history_trades: int = 20
    news_lookback_hours: int = 24
```

## Security Considerations

### Data Privacy
- Never log full context objects (may contain sensitive financial data)
- Sanitize context before sending to external AI services
- Implement request/response encryption for AI queries

### Rate Limiting
- Implement per-user rate limits for chat endpoint
- Track AI service usage to avoid rate limit violations
- Cache responses when appropriate

### Input Validation
- Sanitize user queries before processing
- Validate context data before sending to AI
- Prevent injection attacks in query strings

## Performance Optimization

### Caching Strategy
- Cache market data for 10 seconds (reduce API calls)
- Cache news for 5 minutes (reduce API calls)
- Cache AI responses for identical queries (1 minute TTL)

### Parallel Execution
- Aggregate context components in parallel
- Use asyncio.gather for concurrent data fetching
- Implement timeout for slow components

### Database Optimization
- Index trade history by timestamp for fast queries
- Use connection pooling for Supabase
- Implement query result caching

## Monitoring and Observability

### Metrics to Track
- Context build time (p50, p95, p99)
- AI query time by model
- Query classification accuracy
- Error rates by component
- Cache hit rates

### Logging
- Log all chat queries (sanitized)
- Log routing decisions
- Log AI model responses (metadata only)
- Log errors with full context

### Alerts
- Alert on context build time > 1 second
- Alert on AI query failures > 5%
- Alert on classification errors > 10%
- Alert on rate limit violations

## Future Enhancements

### Advanced Features
- Multi-turn conversations with memory
- Proactive alerts based on context changes
- Voice interface for hands-free trading
- Custom query templates for common questions

### AI Improvements
- Fine-tune classification model
- Implement semantic search for similar queries
- Add sentiment analysis to user queries
- Implement confidence calibration

### Context Enhancements
- Add sector/industry context
- Include correlation analysis
- Add options Greeks for options positions
- Include economic calendar events
