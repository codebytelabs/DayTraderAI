# Implementation Plan - Copilot Intelligence Enhancement

## Overview

This implementation plan breaks down the Copilot Intelligence Enhancement into discrete, manageable coding tasks. Each task builds incrementally on previous work, with the final integration bringing all components together.

---

## Task List

- [ ] 1. Set up copilot module structure and base classes
  - Create `backend/copilot/` directory
  - Create `__init__.py` with module exports
  - Define base exception classes (ContextBuildError, AIQueryError, RoutingError)
  - Create configuration dataclass (CopilotConfig)
  - _Requirements: 10.1, 10.2, 10.3_

- [ ] 2. Implement Context Builder foundation
  - [ ] 2.1 Create ContextBuilder class with initialization
    - Define `backend/copilot/context_builder.py`
    - Implement `__init__` with dependency injection for all managers
    - Create `build_context` method skeleton with feature flags
    - Add timing instrumentation for performance tracking
    - _Requirements: 1.1, 9.1_

  - [ ] 2.2 Implement AccountStateAggregator
    - Create `aggregate_account_state` method
    - Fetch equity, cash, buying power from Alpaca client
    - Calculate total P/L and P/L percentage
    - Handle errors gracefully with partial context
    - _Requirements: 1.1_

  - [ ] 2.3 Implement PositionContextAggregator
    - Create `aggregate_positions` method
    - Fetch all open positions from Position Manager
    - Include entry price, current price, unrealized P/L
    - Extract TP/SL levels from bracket orders if available
    - Calculate position value for each position
    - _Requirements: 1.2, 1.3_

  - [ ] 2.4 Implement TradeHistoryAggregator
    - Create `aggregate_trade_history` method with limit parameter
    - Query Supabase for recent completed trades (last 20)
    - Include entry/exit times, prices, quantity, P/L
    - Classify outcome as 'win' or 'loss'
    - _Requirements: 1.4_

  - [ ] 2.5 Implement PerformanceMetricsAggregator
    - Create `aggregate_metrics` method
    - Calculate win rate, profit factor from trade history
    - Calculate average win and average loss
    - Compute Sharpe ratio and max drawdown
    - _Requirements: 1.5_

- [ ] 3. Implement Market and News Context Aggregators
  - [ ] 3.1 Implement MarketContextAggregator
    - Create `aggregate_market_context` method
    - Fetch technical indicators (EMA-9, EMA-21, RSI, ATR) for watchlist
    - Identify bullish/bearish signals from EMA crossovers
    - Include SPY trend and VIX level for market sentiment
    - Extract query symbol if mentioned in query text
    - Add detailed analysis for query symbol
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 3.2 Implement NewsContextAggregator
    - Create `aggregate_news_context` method
    - Fetch recent news (24 hours) for positions and watchlist symbols
    - Include sentiment scores from News Client
    - Identify trending symbols with high news volume
    - Create sentiment summary by symbol
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ] 3.3 Implement RiskContextAggregator
    - Create `aggregate_risk_context` method
    - Calculate current risk exposure as percentage of equity
    - Compute remaining capacity before position limits
    - Include circuit breaker status and distance to trigger
    - Show open positions count and remaining capacity
    - Include risk per trade and max position size
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 4. Implement Query Router
  - [ ] 4.1 Create QueryRouter class foundation
    - Define `backend/copilot/query_router.py`
    - Implement `__init__` with Perplexity and OpenRouter clients
    - Create `route_query` method skeleton
    - _Requirements: 5.1_

  - [ ] 4.2 Implement query classification logic
    - Create `classify_query` method with keyword matching
    - Define patterns for news/research queries
    - Define patterns for trade advice queries
    - Define patterns for complex queries
    - Return query type and confidence score
    - _Requirements: 5.1, 5.5_

  - [ ] 4.3 Implement Perplexity routing
    - Create `route_to_perplexity` method
    - Format context for Perplexity (news, market conditions, positions)
    - Call Perplexity API with timeout handling
    - Extract and format sources from response
    - _Requirements: 5.2, 7.2_

  - [ ] 4.4 Implement OpenRouter routing
    - Create `route_to_openrouter` method
    - Format full context for OpenRouter (account, positions, metrics, market, risk)
    - Call OpenRouter API with timeout handling
    - Extract trade recommendations if present
    - _Requirements: 5.3, 6.1, 6.2, 6.3_

  - [ ] 4.5 Implement chained routing
    - Create `route_chained` method
    - First query Perplexity for research
    - Add Perplexity response to context
    - Then query OpenRouter with enriched context
    - Combine responses with routing path metadata
    - _Requirements: 5.4, 7.4_

- [ ] 5. Enhance Chat Endpoint
  - [ ] 5.1 Update chat endpoint with context building
    - Modify `POST /chat` endpoint in `backend/main.py`
    - Initialize ContextBuilder with all dependencies
    - Call `build_context` before AI query
    - Add timing metrics for context building
    - _Requirements: 6.1, 9.1_

  - [ ] 5.2 Integrate Query Router
    - Initialize QueryRouter with AI clients
    - Route queries based on configuration flag
    - Handle routing errors with fallback to OpenRouter
    - _Requirements: 5.1, 5.5_

  - [ ] 5.3 Format enhanced response
    - Include model_used, query_type, confidence in response
    - Add sources array for Perplexity responses
    - Include context_used flags showing what was included
    - Add metadata with timing information
    - _Requirements: 7.1, 7.3, 7.4, 7.5_

  - [ ] 5.4 Implement error handling and fallbacks
    - Handle PartialContextError and continue with available data
    - Implement AI timeout with fallback messages
    - Handle rate limit errors with exponential backoff
    - Log errors without exposing sensitive data
    - _Requirements: 9.5_

- [ ] 6. Update Configuration
  - [ ] 6.1 Add copilot configuration to config.py
    - Add COPILOT_CONTEXT_ENABLED flag
    - Add COPILOT_HYBRID_ROUTING flag
    - Add COPILOT_TRADE_EXECUTION flag
    - Add performance tuning parameters (timeouts, cache TTL)
    - Add feature flags for each context component
    - _Requirements: 10.1, 10.2, 10.3, 10.5_

  - [ ] 6.2 Update .env.example with copilot variables
    - Add all copilot configuration variables
    - Include comments explaining each setting
    - Set sensible defaults
    - _Requirements: 10.1, 10.2, 10.3_

- [ ] 7. Frontend Integration
  - [ ] 7.1 Update ChatMessage interface
    - Add metadata field to ChatMessage type in `types.ts`
    - Include model_used, query_type, confidence
    - Add sources array for citations
    - Add trade_recommendation structure
    - _Requirements: 7.1, 7.2, 7.3, 8.1, 8.2, 8.3_

  - [ ] 7.2 Create ModelBadge component
    - Create `components/copilot/ModelBadge.tsx`
    - Display icon and label for each model type
    - Use appropriate colors (blue for Perplexity, purple for OpenRouter, green for chained)
    - _Requirements: 8.1_

  - [ ] 7.3 Create ConfidenceIndicator component
    - Create `components/copilot/ConfidenceIndicator.tsx`
    - Display confidence score visually (bar or icon)
    - Use color coding (green for high, yellow for medium, red for low)
    - _Requirements: 8.4_

  - [ ] 7.4 Create TradeRecommendationCard component
    - Create `components/copilot/TradeRecommendationCard.tsx`
    - Display action, symbol, entry, target, stop, R:R
    - Include "Execute Trade" button if trade execution enabled
    - Format metrics clearly with proper styling
    - _Requirements: 8.3_

  - [ ] 7.5 Create SourceCitations component
    - Create `components/copilot/SourceCitations.tsx`
    - Display numbered list of sources
    - Make source titles clickable links
    - Show snippet preview on hover
    - _Requirements: 8.2_

  - [ ] 7.6 Update ChatPanel to use new components
    - Import and use ModelBadge, ConfidenceIndicator, TradeRecommendationCard, SourceCitations
    - Display metadata for each assistant message
    - Show loading state with model indicator
    - Handle messages without metadata gracefully
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 8. Implement Caching Layer
  - [ ] 8.1 Create cache utility for context data
    - Create `backend/copilot/cache.py`
    - Implement in-memory cache with TTL
    - Cache market data (10 second TTL)
    - Cache news data (5 minute TTL)
    - Cache AI responses for identical queries (1 minute TTL)
    - _Requirements: 9.1, 9.3, 9.4_

  - [ ] 8.2 Integrate caching into Context Builder
    - Check cache before fetching market data
    - Check cache before fetching news
    - Update cache after successful fetches
    - _Requirements: 9.1_

  - [ ] 8.3 Integrate caching into Query Router
    - Check cache for identical queries
    - Store AI responses in cache
    - Include cache hit/miss in metadata
    - _Requirements: 9.3, 9.4_

- [ ] 9. Add Monitoring and Logging
  - [ ] 9.1 Implement performance metrics collection
    - Track context build time (p50, p95, p99)
    - Track AI query time by model
    - Track cache hit rates
    - Export metrics for monitoring dashboard
    - _Requirements: 9.1, 9.2_

  - [ ] 9.2 Add structured logging
    - Log all chat queries (sanitized, no PII)
    - Log routing decisions with query type
    - Log AI model responses (metadata only)
    - Log errors with context (sanitized)
    - _Requirements: 7.5_

  - [ ] 9.3 Create health check endpoint
    - Add `GET /copilot/health` endpoint
    - Check Context Builder components
    - Check AI client connectivity
    - Return status and component health
    - _Requirements: 9.5_

- [ ] 10. Integration and End-to-End Testing
  - [ ] 10.1 Test Context Builder with real data
    - Start trading engine with positions
    - Build context and verify all components
    - Check data accuracy and completeness
    - Verify timing meets 500ms target
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 3.1, 3.2, 4.1, 4.2, 9.1_

  - [ ] 10.2 Test Query Router classification
    - Test with sample news queries
    - Test with sample advice queries
    - Test with sample complex queries
    - Verify routing decisions are correct
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ] 10.3 Test end-to-end chat flow
    - Send various query types to chat endpoint
    - Verify context is built correctly
    - Verify routing works as expected
    - Check response format and metadata
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ] 10.4 Test frontend display
    - Send queries and verify UI updates
    - Check ModelBadge displays correctly
    - Verify ConfidenceIndicator shows proper colors
    - Test TradeRecommendationCard rendering
    - Verify SourceCitations are clickable
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ] 10.5 Test error handling and fallbacks
    - Simulate context building failures
    - Simulate AI timeout errors
    - Simulate rate limit errors
    - Verify partial context handling
    - Verify fallback mechanisms work
    - _Requirements: 9.5_

  - [ ] 10.6 Performance and load testing
    - Test with multiple concurrent queries
    - Measure context build time under load
    - Verify cache effectiveness
    - Check memory usage
    - Identify and fix bottlenecks
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 11. Documentation and Configuration
  - [ ] 11.1 Update API documentation
    - Document enhanced `/chat` endpoint
    - Document `/copilot/health` endpoint
    - Include request/response examples
    - Document configuration options
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 11.2 Create user guide for copilot features
    - Explain context awareness capabilities
    - Show example queries and responses
    - Document configuration options
    - Provide troubleshooting tips
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 11.3 Update settings UI for copilot configuration
    - Add copilot section to SettingsDrawer
    - Add toggles for context building, hybrid routing, trade execution
    - Add sliders for timeout values
    - Add checkboxes for context components
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

---

## Implementation Notes

### Execution Order
1. Start with Context Builder (tasks 1-3) - this is the foundation
2. Implement Query Router (task 4) - depends on Context Builder
3. Enhance Chat Endpoint (task 5) - integrates Context Builder and Query Router
4. Update Configuration (task 6) - needed before testing
5. Frontend Integration (task 7) - can be done in parallel with backend
6. Add Caching (task 8) - performance optimization
7. Add Monitoring (task 9) - observability
8. Integration Testing (task 10) - validate everything works
9. Documentation (task 11) - finalize

### Dependencies
- Context Builder depends on: Trading Engine, Position Manager, Market Data Manager, News Client, Risk Manager
- Query Router depends on: Perplexity Client, OpenRouter Client, Context Builder
- Chat Endpoint depends on: Context Builder, Query Router
- Frontend depends on: Enhanced Chat Endpoint API

### Testing Strategy
- Unit test each aggregator independently with mocked dependencies
- Integration test Context Builder with real system state
- End-to-end test full chat flow from frontend to AI response
- Performance test under load to verify timing requirements

### Performance Targets
- Context building: < 500ms
- Query classification: < 100ms
- Perplexity query: < 10s (with timeout)
- OpenRouter query: < 15s (with timeout)
- Total response time: < 16s worst case

### Configuration Defaults
- Context enabled: true
- Hybrid routing: true
- Trade execution: false (safety)
- Context timeout: 500ms
- AI timeout: 15s
- Cache TTL: 60s
