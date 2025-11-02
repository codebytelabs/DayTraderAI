# Requirements Document

## Introduction

The DayTraderAI copilot currently only provides advice by passing user queries to LLM providers (OpenRouter/Perplexity) with trading context. It cannot execute actions like checking market status, placing orders, or modifying positions. This makes it feel "dumb" because it gives generic instructions instead of actually doing things. This feature will transform the copilot into an action-oriented assistant that can execute trading operations and API calls on behalf of the user.

## Glossary

- **Copilot**: The AI assistant that processes user queries and provides trading guidance
- **Action Executor**: A new component that can execute specific trading and market operations
- **Query Router**: Existing component that classifies user intent (news/analysis/status)
- **Context Builder**: Existing component that aggregates trading, market, and news data
- **Alpaca Client**: Interface to Alpaca trading API for market data and order execution
- **Trading State**: In-memory state manager tracking positions, orders, and account metrics
- **LLM Provider**: External AI service (OpenRouter/Perplexity) for generating natural language responses

## Requirements

### Requirement 1

**User Story:** As a trader, I want the copilot to check market status when I ask "is market open?", so that I get an immediate factual answer instead of instructions on how to check.

#### Acceptance Criteria

1. WHEN the user query contains market status keywords ("market open", "trading hours", "is market closed"), THE Copilot SHALL call the Alpaca clock API and return the current market status
2. THE Copilot SHALL include market open/close times in the response when market status is requested
3. THE Copilot SHALL indicate whether extended hours trading is available when market status is requested
4. THE Copilot SHALL respond within 2 seconds for market status queries
5. IF the Alpaca API call fails, THEN THE Copilot SHALL return a cached status with a staleness indicator

### Requirement 2

**User Story:** As a trader, I want the copilot to execute position management actions when I give direct commands, so that I can manage trades through natural language.

#### Acceptance Criteria

1. WHEN the user query contains close position keywords ("close TSLA", "exit my AAPL position", "sell all GOOGL"), THE Copilot SHALL identify the target symbol and execute the close operation
2. WHEN the user query contains cancel order keywords ("cancel order", "cancel all orders", "cancel MSFT order"), THE Copilot SHALL identify target orders and execute cancellation
3. THE Copilot SHALL confirm the action before execution for operations affecting more than $1000 in value
4. THE Copilot SHALL return execution status including filled quantity, price, and timestamp
5. IF the execution fails, THEN THE Copilot SHALL return the specific error message from the trading API

### Requirement 3

**User Story:** As a trader, I want the copilot to modify stop-loss and take-profit levels when I request it, so that I can adjust risk parameters through conversation.

#### Acceptance Criteria

1. WHEN the user query contains stop-loss modification keywords ("set stop loss", "move stop to", "update SL"), THE Copilot SHALL identify the target position and new stop-loss level
2. WHEN the user query contains take-profit modification keywords ("set take profit", "move TP to", "update target"), THE Copilot SHALL identify the target position and new take-profit level
3. THE Copilot SHALL validate that stop-loss levels are below current price for long positions and above for short positions
4. THE Copilot SHALL validate that take-profit levels are above current price for long positions and below for short positions
5. THE Copilot SHALL update the position's bracket orders through the Alpaca API when modifications are requested

### Requirement 4

**User Story:** As a trader, I want the copilot to provide real-time position analysis when I ask about specific stocks, so that I understand my current exposure and P/L.

#### Acceptance Criteria

1. WHEN the user query references a specific symbol in their portfolio ("how is TSLA doing", "AAPL status", "show me GOOGL"), THE Copilot SHALL retrieve current position data including entry price, current price, and unrealized P/L
2. THE Copilot SHALL include stop-loss and take-profit levels in position analysis responses
3. THE Copilot SHALL calculate and display exposure percentage relative to total equity
4. THE Copilot SHALL include recent price movement (intraday high/low) in position analysis
5. THE Copilot SHALL fetch and display latest news for the queried symbol when position analysis is requested

### Requirement 5

**User Story:** As a trader, I want the copilot to distinguish between action requests and advice requests, so that it executes when I want action and advises when I want guidance.

#### Acceptance Criteria

1. THE Copilot SHALL classify queries into three categories: action, advice, or information
2. WHEN a query is classified as "action" with confidence above 80%, THE Copilot SHALL execute the operation without LLM consultation
3. WHEN a query is classified as "advice", THE Copilot SHALL route to LLM providers with full context as currently implemented
4. WHEN a query is classified as "information", THE Copilot SHALL fetch data from APIs and format a structured response
5. THE Copilot SHALL log all action classifications and executions for audit purposes

### Requirement 6

**User Story:** As a trader, I want the copilot to handle ambiguous commands gracefully, so that I can clarify my intent when the system is uncertain.

#### Acceptance Criteria

1. WHEN the Copilot cannot determine the target symbol from a command, THE Copilot SHALL ask for clarification listing available options
2. WHEN the Copilot cannot determine the action type from a command, THE Copilot SHALL present action options to the user
3. WHEN multiple positions match a partial symbol reference, THE Copilot SHALL list all matches and request selection
4. THE Copilot SHALL maintain conversation context for follow-up clarifications
5. THE Copilot SHALL timeout clarification requests after 60 seconds and return to normal operation

### Requirement 7

**User Story:** As a trader, I want the copilot to provide execution confirmations with details, so that I can verify that actions were completed correctly.

#### Acceptance Criteria

1. THE Copilot SHALL return a structured confirmation message for all executed actions
2. THE Copilot SHALL include the action type, target symbol, quantity, price, and timestamp in confirmations
3. THE Copilot SHALL include the order ID or transaction ID in confirmations for audit trail
4. THE Copilot SHALL display before/after state for position modifications (e.g., "Stop-loss moved from $450 to $460")
5. THE Copilot SHALL include estimated P/L impact for position closures in confirmations

### Requirement 8

**User Story:** As a trader, I want the copilot to respect risk management rules when executing actions, so that automated operations don't violate my trading constraints.

#### Acceptance Criteria

1. THE Copilot SHALL check circuit breaker status before executing any trade actions
2. THE Copilot SHALL validate that position modifications don't violate maximum position size limits
3. THE Copilot SHALL prevent actions that would exceed maximum equity utilization thresholds
4. THE Copilot SHALL enforce minimum stop-loss distances based on ATR or percentage rules
5. IF a requested action violates risk rules, THEN THE Copilot SHALL explain the specific constraint and suggest alternatives
