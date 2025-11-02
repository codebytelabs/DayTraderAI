# Requirements Document - Copilot Intelligence Enhancement

## Introduction

The DayTraderAI Copilot Intelligence Enhancement transforms the basic chat interface into a sophisticated AI trading assistant with complete system awareness. The enhanced copilot will have full context about the user's portfolio, positions, trade history, performance metrics, market conditions, and recent news. It will intelligently route queries to specialized AI models (Perplexity for research, OpenRouter for analysis) and provide actionable, context-aware trading advice.

This enhancement is critical for maximizing the value of the advanced features (streaming, options, bracket orders, news) by creating an intelligent interface that can understand and leverage all system capabilities.

## Glossary

- **Copilot System**: The AI-powered chat assistant that provides trading advice and system interaction
- **Context Builder**: Backend service that aggregates all relevant system state and market data
- **Query Router**: Component that classifies user queries and routes them to appropriate AI models
- **Perplexity AI**: Real-time research AI specialized in news analysis and market research
- **OpenRouter AI**: Analysis AI specialized in trade recommendations and portfolio advice
- **Trading Engine**: Core system that executes trades and manages positions
- **Position Manager**: Component that tracks open positions with P/L and risk metrics
- **Market Data Manager**: Service that provides price data and technical indicators
- **News Client**: Service that fetches market news and sentiment analysis
- **Bracket Order**: Order type with automatic take-profit and stop-loss levels
- **Risk Manager**: Component that validates trades against risk limits

## Requirements

### Requirement 1: Context Aggregation

**User Story:** As a trader, I want the copilot to know my complete portfolio state, so that it can provide personalized advice based on my actual positions and risk exposure.

#### Acceptance Criteria

1. WHEN the Copilot System receives a chat query, THE Context Builder SHALL aggregate current account state including equity, cash, buying power, and total P/L
2. WHEN the Context Builder aggregates account state, THE Context Builder SHALL include all open positions with entry price, current price, unrealized P/L, and position size
3. WHEN the Context Builder includes positions, THE Context Builder SHALL include take-profit and stop-loss levels for each position where bracket orders are active
4. WHEN the Context Builder aggregates data, THE Context Builder SHALL include recent trade history with the last 20 completed trades showing entry, exit, P/L, and outcome
5. WHEN the Context Builder includes trade history, THE Context Builder SHALL calculate and include performance metrics including win rate, profit factor, average win, average loss, and Sharpe ratio

### Requirement 2: Market Context Integration

**User Story:** As a trader, I want the copilot to understand current market conditions and technical indicators, so that its advice considers the broader market environment.

#### Acceptance Criteria

1. WHEN the Context Builder aggregates market data, THE Context Builder SHALL include technical indicators for all watchlist symbols including EMA-9, EMA-21, RSI, ATR, and current price
2. WHEN the Context Builder includes technical indicators, THE Context Builder SHALL identify and flag bullish or bearish signals based on EMA crossovers and momentum
3. WHEN the Context Builder aggregates market conditions, THE Context Builder SHALL include SPY trend direction and VIX level to indicate overall market sentiment
4. WHEN a user query mentions a specific symbol, THE Context Builder SHALL include detailed technical analysis for that symbol including support/resistance levels
5. WHEN the Context Builder aggregates data, THE Context Builder SHALL include timestamp of last data update to ensure freshness

### Requirement 3: News and Sentiment Integration

**User Story:** As a trader, I want the copilot to be aware of recent market news and sentiment, so that it can factor breaking events into its recommendations.

#### Acceptance Criteria

1. WHEN the Context Builder aggregates news data, THE News Client SHALL fetch recent news for symbols in the user's positions and watchlist
2. WHEN the News Client fetches news, THE News Client SHALL include sentiment scores (positive, negative, neutral) for each news item
3. WHEN the Context Builder includes news, THE Context Builder SHALL prioritize news from the last 24 hours for maximum relevance
4. WHEN a user query mentions a specific symbol, THE Context Builder SHALL include all recent news for that symbol with sentiment analysis
5. WHEN the Context Builder aggregates news, THE Context Builder SHALL identify trending symbols with significant news volume or sentiment changes

### Requirement 4: Risk Context Awareness

**User Story:** As a trader, I want the copilot to understand my current risk exposure and limits, so that it only recommends trades that fit within my risk parameters.

#### Acceptance Criteria

1. WHEN the Context Builder aggregates risk data, THE Context Builder SHALL include current risk exposure as percentage of total equity
2. WHEN the Context Builder includes risk exposure, THE Context Builder SHALL calculate remaining risk capacity before hitting position limits
3. WHEN the Context Builder aggregates risk data, THE Context Builder SHALL include circuit breaker status showing daily P/L and distance to trigger threshold
4. WHEN the Context Builder includes risk metrics, THE Context Builder SHALL show number of open positions and remaining capacity before max position limit
5. WHEN the Context Builder aggregates risk data, THE Context Builder SHALL include risk per trade percentage and maximum position size allowed

### Requirement 5: Intelligent Query Routing

**User Story:** As a trader, I want my questions to be answered by the most appropriate AI model, so that I get the best possible response for each type of query.

#### Acceptance Criteria

1. WHEN the Query Router receives a user query, THE Query Router SHALL classify the query type as news-research, trade-advice, or complex-analysis
2. WHEN the Query Router classifies a query as news-research, THE Query Router SHALL route the query to Perplexity AI with relevant news context
3. WHEN the Query Router classifies a query as trade-advice, THE Query Router SHALL route the query to OpenRouter AI with full portfolio and market context
4. WHEN the Query Router classifies a query as complex-analysis, THE Query Router SHALL implement chaining by first querying Perplexity AI for research then OpenRouter AI for analysis
5. IF the Query Router cannot classify a query with confidence above 70 percent, THEN THE Query Router SHALL default to OpenRouter AI with full context

### Requirement 6: Context-Aware Response Generation

**User Story:** As a trader, I want the copilot's responses to reference my specific situation and provide actionable recommendations, so that I can make informed trading decisions quickly.

#### Acceptance Criteria

1. WHEN the Copilot System generates a response, THE Copilot System SHALL include specific references to the user's current positions and available capital
2. WHEN the Copilot System recommends a trade, THE Copilot System SHALL calculate and include specific entry price, take-profit target, stop-loss level, and position size
3. WHEN the Copilot System provides trade recommendations, THE Copilot System SHALL include risk-reward ratio and verify the trade fits within risk limits
4. WHEN the Copilot System references market data, THE Copilot System SHALL cite specific technical indicators and their current values
5. WHEN the Copilot System uses news in its analysis, THE Copilot System SHALL include source citations and sentiment scores

### Requirement 7: Response Transparency

**User Story:** As a trader, I want to know which AI model answered my question and how confident it is, so that I can assess the reliability of the advice.

#### Acceptance Criteria

1. WHEN the Copilot System returns a response, THE Copilot System SHALL include metadata indicating which AI model was used (Perplexity or OpenRouter)
2. WHEN the Copilot System uses Perplexity AI, THE Copilot System SHALL include source citations for all factual claims and news references
3. WHEN the Copilot System provides trade recommendations, THE Copilot System SHALL include confidence score based on signal strength and market conditions
4. WHEN the Copilot System uses multiple AI models in a chain, THE Copilot System SHALL indicate the routing path and contribution of each model
5. WHEN the Copilot System encounters errors or missing data, THE Copilot System SHALL clearly communicate limitations in the response

### Requirement 8: Frontend Integration

**User Story:** As a trader, I want the chat interface to display rich information about AI responses, so that I can quickly understand the reasoning and sources behind recommendations.

#### Acceptance Criteria

1. WHEN the Chat Panel displays a copilot response, THE Chat Panel SHALL show an indicator badge for which AI model was used
2. WHEN the Chat Panel displays responses with citations, THE Chat Panel SHALL render source links as clickable references
3. WHEN the Chat Panel displays trade recommendations, THE Chat Panel SHALL highlight key metrics (entry, TP, SL, R:R) in a structured format
4. WHEN the Chat Panel displays confidence scores, THE Chat Panel SHALL use visual indicators (colors, icons) to represent confidence levels
5. WHEN the Chat Panel is loading a response, THE Chat Panel SHALL show which AI model is processing the query and estimated response time

### Requirement 9: Performance and Reliability

**User Story:** As a trader, I want the copilot to respond quickly and reliably, so that I can get timely advice during fast-moving market conditions.

#### Acceptance Criteria

1. WHEN the Context Builder aggregates data, THE Context Builder SHALL complete aggregation within 500 milliseconds for typical queries
2. WHEN the Query Router classifies a query, THE Query Router SHALL complete classification within 100 milliseconds
3. WHEN the Copilot System queries Perplexity AI, THE Copilot System SHALL implement a timeout of 10 seconds with fallback to cached data
4. WHEN the Copilot System queries OpenRouter AI, THE Copilot System SHALL implement a timeout of 15 seconds with fallback to error message
5. IF any component fails during context building, THEN THE Copilot System SHALL continue with partial context and note missing data in the response

### Requirement 10: Configuration and Control

**User Story:** As a trader, I want to configure copilot behavior and enable/disable features, so that I can customize the assistant to my preferences.

#### Acceptance Criteria

1. WHERE copilot context building is enabled, THE Copilot System SHALL aggregate full context for every query
2. WHERE hybrid routing is enabled, THE Copilot System SHALL use the Query Router to select appropriate AI models
3. WHERE trade execution is enabled, THE Copilot System SHALL include executable trade buttons in recommendations
4. WHEN the user disables context building, THE Copilot System SHALL use only the query text without additional context
5. WHEN the user changes copilot configuration, THE Copilot System SHALL apply changes immediately without requiring restart
