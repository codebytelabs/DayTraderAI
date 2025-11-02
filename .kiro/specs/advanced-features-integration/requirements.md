# Advanced Features Integration Requirements

## Introduction

This specification defines the requirements for integrating the advanced backend capabilities (streaming, bracket orders, options trading, and news intelligence) into the production DayTraderAI workflow. These features exist in isolation but are not yet orchestrated by the trading engine or surfaced through the frontend.

## Glossary

- **Stream Manager** – backend component (`backend/streaming/stream_manager.py`) that manages live market data subscriptions.
- **BracketOrderBuilder** – backend helper (`backend/orders/bracket_orders.py`) that generates take-profit/stop-loss orders.
- **Options Client** – backend component (`backend/options/options_client.py`) that requests options chains and quotes.
- **News Client** – backend component (`backend/news/news_client.py`) that aggregates Alpaca news and sentiment.
- **Trading Engine** – orchestrator (`backend/trading/trading_engine.py`) running strategy, execution, and monitoring loops.
- **Realtime WebSocket Endpoint** – FastAPI route delivering streaming updates to the frontend.
- **LLM Copilot** – enhanced `/chat` endpoint using OpenRouter and Perplexity with full trading context.

## Requirement 1: Real-Time Streaming Activation

**User Story:** As a trader, I want the system to update positions, orders, and charts instantly when the market moves, so that I can react without manual refreshes.

1. WHEN streaming is enabled in configuration, THEN the Trading Engine SHALL initialise the `StreamManager` and subscribe to watchlist symbols at startup.
2. WHEN a quote or trade message is received, THEN the system SHALL update the in-memory state (`trading_state`) within 200 ms of receipt.
3. WHEN a streaming connection drops, THEN the system SHALL attempt reconnection within 5 seconds and log the event with severity `WARN`.
4. WHEN reconnection fails after three attempts, THEN the system SHALL fall back to polling and emit an alert to the copilot context.

## Requirement 2: Frontend WebSocket Delivery

**User Story:** As a frontend user, I want the dashboard to reflect backend updates in near real time, so that the UI stays consistent with trading state.

1. WHEN the backend exposes a WebSocket endpoint, THEN the frontend SHALL establish a persistent connection within 1 second of load.
2. WHEN a streaming payload arrives, THEN the frontend SHALL update metrics, positions, orders, logs, advisories, and performance charts without a full re-fetch.
3. WHEN the WebSocket connection closes unexpectedly, THEN the frontend SHALL display a “Reconnecting…” banner and retry with exponential backoff up to 30 seconds.
4. WHEN the connection is restored, THEN the banner SHALL disappear and the UI SHALL reconcile by requesting latest snapshots.
5. WHEN WebSocket streaming is disabled via configuration, THEN the frontend SHALL revert to polling every 10 seconds.

## Requirement 3: Bracket Orders Integration

**User Story:** As a risk-conscious trader, I want every trade to carry automatic take-profit and stop-loss orders, so that losses are limited and profits are secured.

1. WHEN the strategy submits an entry order, THEN the `OrderManager` SHALL generate matching bracket legs using `BracketOrderBuilder`.
2. WHEN configuration overrides default TP/SL percentages, THEN the system SHALL apply those values for all new entries within the same trading session.
3. WHEN a take-profit or stop-loss leg is filled, THEN the corresponding position SHALL be closed and the remaining leg SHALL be cancelled automatically.
4. WHEN a user toggles bracket orders off, THEN the system SHALL not attach additional legs and SHALL note the override in the audit log.

## Requirement 4: Strategy TP/SL Awareness

**User Story:** As a strategist, I want the EMA-based engine to anticipate TP/SL levels, so that sizing and risk checks are consistent.

1. WHEN the strategy evaluates a signal, THEN it SHALL calculate the projected TP/SL prices based on ATR or configured percentages.
2. WHEN position sizing is computed, THEN the risk manager SHALL validate that the projected stop distance respects `risk_per_trade_pct`.
3. WHEN a position already carries TP/SL values, THEN the dashboard SHALL display them and update when trailing logic adjusts targets.
4. WHEN TP/SL adjustments occur, THEN the change SHALL persist in Supabase for audit and recovery.

## Requirement 5: Options Trading Enablement

**User Story:** As a trader seeking leverage, I want to execute options trades with defined risk, so that I can express bullish or bearish views with smaller capital.

1. WHEN options trading is enabled, THEN the Options Client SHALL fetch chains for watchlist symbols on demand and cache them for 5 minutes.
2. WHEN the strategy selects an options contract, THEN the risk manager SHALL enforce options-specific limits (`MAX_OPTIONS_POSITIONS`, `OPTIONS_RISK_PER_TRADE_PCT`).
3. WHEN an options position is opened, THEN its Greeks, expiry date, and strike SHALL be stored in Supabase and surfaced on the dashboard.
4. WHEN options positions approach expiration (≤ 2 days), THEN the copilot context SHALL include a warning in the highlights.

## Requirement 6: Options UI Extensions

**User Story:** As an operator, I want to review and close options positions from the dashboard, so that I can manage risk without leaving the app.

1. WHEN the backend reports options positions, THEN the frontend SHALL render them in a dedicated table with contract details, Greeks, and P/L.
2. WHEN a user requests to close an options position, THEN the frontend SHALL call the new backend route and surface success/failure messages.
3. WHEN the options chain hook loads, THEN the UI SHALL provide filters (expiry, strike, call/put) and display bid/ask/IV values.
4. WHEN an options trade executes, THEN the frontend SHALL emit a toast summarising entry price, break-even, and TP/SL (if configured).

## Requirement 7: News Intelligence Infusion

**User Story:** As a trader, I want timely news and sentiment to augment trading decisions, so that I can anticipate catalysts and avoid surprises.

1. WHEN news integration is enabled, THEN the News Client SHALL fetch symbol-specific articles every `NEWS_UPDATE_INTERVAL` seconds.
2. WHEN the copilot builds context, THEN it SHALL include the top five articles (headline, summary, sentiment, source) for open positions and watchlist focus symbols.
3. WHEN the frontend news panel renders, THEN it SHALL group articles by symbol, include sentiment badges, and link to sources.
4. WHEN a symbol experiences a surge in mentions (> `min_mentions` threshold), THEN the trending detector SHALL raise an advisory entry with confidence score.

## Requirement 8: Configuration Surface

**User Story:** As an administrator, I want to toggle advanced features without redeploying code, so that I can control rollout easily.

1. WHEN new configuration fields are introduced (`STREAMING_ENABLED`, `BRACKET_ORDERS_ENABLED`, `OPTIONS_ENABLED`, `NEWS_ENABLED`, and associated tuning values), THEN `config.py` SHALL expose them with sensible defaults and `.env.example` SHALL be updated.
2. WHEN the frontend settings drawer loads, THEN it SHALL present toggles and numeric inputs for the advanced features, scoped to client-side storage only (no secrets).
3. WHEN feature toggles change, THEN the backend SHALL respond immediately (on next loop iteration) without requiring a restart.
4. WHEN the copilot detects a feature disabled state, THEN it SHALL exclude related data from context summaries to reduce noise.

## Requirement 9: Telemetry & Monitoring

**User Story:** As an engineer, I want visibility into advanced feature health, so that I can detect failures quickly.

1. WHEN streaming reconnects, THEN a metric counter (`stream_reconnects_total`) SHALL be incremented and exposed via `/metrics`.
2. WHEN bracket orders are attached, THEN the audit log SHALL include entry IDs, TP/SL prices, and activation status.
3. WHEN options or news integrations fail (API errors), THEN the system SHALL log with severity `ERROR` and bubble the error to the copilot notes.
4. WHEN performance data is emitted, THEN latency statistics for streaming, TP/SL handling, options quote retrieval, and news fetch SHALL be recorded.

## Requirement 10: Acceptance & Validation

**User Story:** As a project lead, I want clear acceptance criteria for the integrated features, so that I can sign off confidently.

1. WHEN all integration features are implemented, THEN automated integration tests SHALL verify streaming updates, bracket order flows, options trades, and news advisories end-to-end.
2. WHEN manual QA runs paper trading scenarios for 5 market days, THEN no unchecked errors SHALL appear in logs related to advanced features.
3. WHEN the frontend runs with features toggled on and off, THEN toggles SHALL behave deterministically and persist across reloads.
4. WHEN the product review is conducted, THEN the copilot SHALL summarise advanced feature status accurately using the new context fields.
