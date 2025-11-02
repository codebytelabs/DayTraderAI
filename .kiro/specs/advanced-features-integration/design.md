# Design Document – Advanced Features Integration

## Overview

This document describes how to integrate the existing advanced subsystems—streaming, bracket orders, options trading, and news intelligence—into the live DayTraderAI workflow across backend services, frontend UI, and configuration.

## Goals

- Deliver sub-second market updates via WebSockets while retaining polling as a fallback.
- Attach bracket orders to every supported trade with configurable TP/SL levels.
- Extend the trading engine to execute options strategies and surface results in the UI.
- Ingest market news/sentiment, enrich copilot responses, and display insights.
- Provide configuration toggles to enable/disable features without code changes.
- Instrument the stack for monitoring, enabling comprehensive test coverage.

## Non-Goals

- Designing new trading strategies beyond integrating the existing EMA + options logic.
- Building advanced analytics or optimisation (covered under Phase 2).
- Implementing production monitoring infrastructure (scheduled for Phase 3).

## Architecture

### High-Level Flow

```
 Alpaca Streams ──▶ StreamManager ──▶ TradingEngine ──▶ trading_state
                                           │                  │
                                           │                  └──▶ Supabase (positions/orders/metrics)
                                           │
                                           ├─▶ OrderManager ──▶ BracketOrderBuilder ──▶ Alpaca REST
                                           │
                                           ├─▶ OptionsStrategy ─▶ OptionsClient ─▶ Alpaca Options API
                                           │
                                           └─▶ NewsClient ──▶ Advisory Pipeline ──▶ Copilot Context

 trading_state ──▶ FastAPI REST + WS ──▶ Frontend WebSocket Hook ──▶ React Dashboard
 trading_state ──▶ Copilot Context Builder ──▶ Query Router ──▶ LLM Providers
```

### Components & Responsibilities

| Component | Module | Updates Needed |
| --- | --- | --- |
| `StreamManager` | `backend/streaming/stream_manager.py` | Wire to TradingEngine; emit structured payloads for WS broadcast. |
| WebSocket endpoint | `backend/main.py` | New `/ws` route streaming state diffs; authentication optional. |
| WebSocket publisher | new util | Serialise state updates (metrics, positions, orders, logs, advisories, performance). |
| Frontend hook | `hooks/useBackendTrading.ts` (or new) | Replace polling with WS; fallback logic. |
| Bracket order execution | `backend/trading/order_manager.py` | Invoke `BracketOrderBuilder`, ensure idempotency. |
| Strategy TP/SL | `backend/trading/strategy.py` | Compute TP/SL before orders; store in state + Supabase. |
| Options integration | `backend/options/options_client.py`, new `OptionsStrategy` | Select contracts, execute trades, track Greks/expiry. |
| Options risk | `backend/trading/risk_manager.py` | Additional constraints for options positions. |
| Options state | `core/state.py`, Supabase tables | Extend dataclasses for options data, persist to DB. |
| News ingestion | `backend/news/news_client.py`, trading loops | Periodic fetch; push to advisory system + WS updates. |
| Copilot | `backend/copilot/context_builder.py` | Include news/trending info; warn on options expiry. |
| Settings | `backend/config.py`, `components/SettingsDrawer.tsx` | Add toggles/limits; ensure immediate effect. |
| Telemetry | `utils/logger`, new metrics | Counters/histogram instrumentation. |

## Data Model Changes

- Extend `core/state.Position` to include optional fields for options data (`contract_id`, `strike`, `expiry`, `type`, `greeks`).
- Add streaming state snapshot structure (e.g., `StreamingUpdate` dataclass) for consistent WebSocket payloads.
- Supabase tables to include new columns for TP/SL, options metadata, news advisories (if not already present).

## WebSocket Payload Format

```json
{
  "type": "snapshot|delta",
  "timestamp": "ISO-8601",
  "metrics": {...},
  "positions": [...],
  "orders": [...],
  "logs": [...],
  "advisories": [...],
  "performance": {...},
  "feature_flags": {
    "streaming": true,
    "bracket_orders": true,
    "options": false,
    "news": true
  }
}
```

## Sequence Diagrams

### Streaming Update

```
Client WS ──connect──▶ FastAPI /ws
StreamManager ─NewQuote─▶ TradingEngine
TradingEngine ─update─▶ trading_state
FastAPI broadcaster ◀── state diff
FastAPI broadcaster ─payload─▶ Client WS Hook
Client Hook ─state update─▶ React contexts
```

### Bracket Order Entry

```
Strategy ─signal─▶ OrderManager
OrderManager ─build──▶ BracketOrderBuilder
BracketOrderBuilder ─orders──▶ Alpaca
Alpaca ─confirmation──▶ OrderManager
OrderManager ─record──▶ trading_state + Supabase
FastAPI broadcaster ─order update─▶ Frontend
```

### Options Trade

```
OptionsStrategy ─select contract─▶ OptionsClient
OptionsClient ─quote data─▶ OptionsStrategy
OptionsStrategy ─risk check─▶ RiskManager
RiskManager ─approve─▶ OptionsStrategy
OptionsStrategy ─order─▶ OrderManager
OrderManager ─execute─▶ Alpaca
```

### News Advisory

```
NewsClient ─fetch─▶ Alpaca News API
NewsClient ─sentiment─▶ NewsClient.analyze_sentiment
NewsClient ─payload─▶ Advisory pipeline
Supabase ─store─▶ advisories table
Copilot Context Builder ◀── advisories
FastAPI broadcaster ─news update─▶ Frontend panel
```

## Configuration

| Setting | Backend Key | Frontend Control | Default |
| --- | --- | --- | --- |
| Streaming toggle | `STREAMING_ENABLED` | Settings drawer toggle | `true` |
| Reconnect delay | `STREAM_RECONNECT_DELAY` | Numeric input | `5` |
| Bracket orders toggle | `BRACKET_ORDERS_ENABLED` | Settings toggle | `true` |
| Default TP % | `DEFAULT_TAKE_PROFIT_PCT` | Numeric input | `2.0` |
| Default SL % | `DEFAULT_STOP_LOSS_PCT` | Numeric input | `1.0` |
| Options toggle | `OPTIONS_ENABLED` | Settings toggle | `false` |
| Options max positions | `MAX_OPTIONS_POSITIONS` | Numeric input | `5` |
| Options risk pct | `OPTIONS_RISK_PER_TRADE_PCT` | Numeric input | `0.02` |
| News toggle | `NEWS_ENABLED` | Settings toggle | `true` |
| News interval | `NEWS_UPDATE_INTERVAL` | Numeric input | `300` |

Configuration changes must apply without restart—use shared config object and watchers or check toggles inside loops.

## Error Handling

- WebSocket: heartbeat/ping support; fallback to polling on repeated failures.
- Bracket orders: ensure partial fills handled gracefully; cancel orphan legs.
- Options: fall back to equities if options client returns empty chain, log warning.
- News: catch API rate-limit errors, backoff and notify copilot.

## Telemetry

- Prometheus metrics (or similar) for streaming reconnects, average update latency, bracket order success/failure counts, options trade volume, news fetch latency.
- Structured logs with correlation IDs for complex flows (options, bracket orders).

## Security Considerations

- WebSocket endpoint should enforce CORS/domains; optional auth token in Phase 3.
- No secrets in frontend env; toggles use non-sensitive values.
- Validate all user-triggered close/cancel requests to prevent unintended actions.

## Testing Strategy (High-Level)

- Unit tests for streaming reconnection logic, bracket builder, options selection, news sentiment pipeline.
- Integration tests for each feature verifying state propagation from backend to frontend.
- Soak tests for WebSocket under high message volume.

## Deployment Notes

- Feature toggles default to conservative settings (streaming on, bracket orders on, options off, news on).
- Ensure CI deploy scripts migrate new Supabase schema changes before enabling options/news in production.
