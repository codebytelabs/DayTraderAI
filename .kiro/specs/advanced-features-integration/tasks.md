# Advanced Features Integration – Implementation Tasks

## Sprint Alignment

- **Sprint 1 (Weeks 1-2):** Streaming foundation + spec finalisation
- **Sprint 2 (Weeks 3-4):** Bracket orders integration + config updates
- **Sprint 3 (Weeks 5-6):** Options trading workflow
- **Sprint 4 (Weeks 7-8):** News intelligence + UI enhancements
- **Sprint 5 (Weeks 9-10):** Regression and integration test hardening (see comprehensive-testing spec)

## Task Breakdown

### 0. Spec Finalisation (Pre-Sprint 1)

- [ ] Review `requirements.md` with stakeholders; capture sign-off.
- [ ] Update `SPECS_STATUS.md` entry to “In Progress”.
- [ ] Link spec sections to `TODO.md` sprint plan.

### 1. Streaming Integration (Sprint 1)

| Task | Owner | Status |
| --- | --- | --- |
| Wire StreamManager start/stop into TradingEngine | Backend | ☑ |
| Implement state broadcaster + FastAPI `/ws` endpoint | Backend | ☑ |
| Add polling fallback + telemetry (`STREAMING_ENABLED`) | Backend | ☑ |
| Build React `useStreamingTrading` hook with reconnect logic | Frontend | ☑ |
| Update contexts/UI for live updates & status banner | Frontend | ☑ |

1.1 Backend
- [ ] Wire `StreamManager` initialisation within `TradingEngine.start`.
- [ ] Register callbacks for quotes/trades/bars; normalise payloads.
- [ ] Implement WebSocket broadcaster utility with asyncio queue.
- [ ] Add FastAPI `/ws` route streaming JSON payloads with heartbeat.
- [ ] Add fallback polling when streaming disabled.

1.2 Frontend
- [ ] Create `useStreamingTrading` hook handling WebSocket lifecycle.
- [ ] Update contexts to ingest streaming payloads and reconcile state.
- [ ] Display connection status badge + reconnect banner.
- [ ] Maintain polling fallback for browsers without WS support.

1.3 Configuration & Telemetry
- [x] Expose `STREAMING_ENABLED`, `STREAM_RECONNECT_DELAY` in config + `.env.example`.
- [ ] Add Prometheus-style counters for reconnect attempts, update latency.

1.4 QA / Definition of Done
- [ ] WS connection established within 1 s of page load.
- [ ] Frontend updates metrics/positions/orders without manual refresh.
- [ ] Simulated disconnect triggers reconnect and fallback behaviour.

### 2. Bracket Orders (Sprint 2)

2.1 Backend
- [x] Integrate `BracketOrderBuilder` into `OrderManager.submit_order`.
- [x] Ensure idempotency to prevent duplicate bracket legs.
- [x] Persist TP/SL values to Supabase and `trading_state`.
- [x] Update strategy to compute projected TP/SL prior to submissions.

2.2 Frontend
- [x] Display TP/SL columns in positions table with formatting.
- [ ] Add order form toggle for bracket orders (future manual controls).
- [ ] Show notifications when bracket legs trigger.

2.3 Configuration
- [x] Add `BRACKET_ORDERS_ENABLED`, `DEFAULT_TAKE_PROFIT_PCT`, `DEFAULT_STOP_LOSS_PCT` to config + settings drawer.

2.4 QA / DoD
- [ ] Entry orders automatically attach TP/SL legs.
- [ ] TP/SL updates visible across backend, frontend, and database.
- [ ] Disabling bracket toggle prevents attachments.

### 3. Options Trading (Sprint 3)

3.1 Backend
- [ ] Implement `OptionsStrategy` leveraging EMA signals + options client.
- [ ] Extend risk manager for options sizing and position caps.
- [ ] Expand `core/state.Position` to include options metadata.
- [ ] Persist options trades and positions to Supabase.

3.2 Frontend
- [ ] Create Options table (contract, strike, expiry, Greeks, P/L).
- [ ] Build options chain explorer (filters, quotes).
- [ ] Allow manual close of options positions with confirmation.

3.3 Configuration
- [ ] Add `OPTIONS_ENABLED`, `MAX_OPTIONS_POSITIONS`, `OPTIONS_RISK_PER_TRADE_PCT` to settings.

3.4 QA / DoD
- [ ] Options trades executed and tracked end-to-end.
- [ ] Risk manager blocks trades exceeding limits.
- [ ] Copilot highlights options exposure and approaching expiries.

### 4. News Intelligence (Sprint 4)

4.1 Backend
- [ ] Schedule periodic `NewsClient` fetches for watchlist and open positions.
- [ ] Integrate sentiment analysis placeholders; mark TODO for advanced model.
- [ ] Push news advisories to Supabase + trading state.
- [ ] Update copilot context builder to include recent news and trending symbols.

4.2 Frontend
- [ ] Add news feed panel grouping articles by symbol.
- [ ] Display sentiment badges and link to sources.
- [ ] Surface trending symbols / catalysts notifications.

4.3 Configuration
- [ ] Add `NEWS_ENABLED`, `NEWS_UPDATE_INTERVAL`, `NEWS_MIN_MENTIONS` (if needed) fields.

4.4 QA / DoD
- [ ] News articles refresh at configured interval without rate limiting.
- [ ] Copilot references latest news in responses.
- [ ] Trending detector produces advisories when thresholds exceeded.

### 5. Documentation & Handover

- [ ] Update `README.md`, `FRONTEND_INTEGRATION_COMPLETE.md`, `ENHANCEMENTS_SUMMARY.md` with integration details.
- [ ] Document new API endpoints (WebSocket, options, news) in pending API reference.
- [ ] Produce runbook covering toggles, fallbacks, and known issues.

### 6. Acceptance Gate

- [ ] Conduct end-to-end demo covering streaming, bracket orders, options, news flows.
- [ ] Capture sign-off in `SPECS_STATUS.md` (move to “Implemented”).
- [ ] Log retrospective notes for future optimisation sprints.

## Dependencies

- Copilot enhancements (Sprint 0) completed and stable.
- Supabase schema ready for options/news fields (add migrations if missing).
- Upcoming `comprehensive-testing` spec (Sprint 5) to reference tasks above.

## Risks & Mitigations

- **Streaming instability:** keep polling fallback and log metrics.
- **Bracket order mismatch:** ensure bracket builder is idempotent and handles partial fills.
- **Options API limits:** implement caching and backoff; allow quick disable via config.
- **News rate limits:** respect API quotas, cache results, degrade gracefully.
