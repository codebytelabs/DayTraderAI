# DayTraderAI Execution Plan

## Mission
Deliver the production-grade "Ultimate Expert Day-Trading Bot" in phased releases. The dashboard already hosts a rich simulator; the next sprints wire it into real Alpaca/Supabase/LLM services, enforce deterministic risk, and automate promotion gates.

## Squad Setup (4 Parallel Agents)
- **Agent Alpha – Core Services & OMS**
  - Owns backend services (Python/Node), Alpaca execution bridge, websockets, order/state reconciliation, secrets handling.
- **Agent Beta – Data, Features & Risk Science**
  - Drives ingestion (bars, corporate actions, calendars), feature store, supervised gatekeeper, risk analytics, walk-forward experiments.
- **Agent Gamma – Frontend & Copilot UX**
  - Evolves the React console, copilot orchestration, actionable insights, and monitoring dashboards.
- **Agent Delta – Ops, QA & Automation**
  - Focuses on CI/CD, infrastructure-as-code, alerting, runbooks, simulations, and compliance tooling.

Each agent works from separate branches, syncs daily via shared Supabase board, and contributes to weekly demo builds.

---

## Stream A – Backend & OMS (Agent Alpha)
- [ ] Scaffold backend service (FastAPI or Node/Express) with modular layers: ingestion, strategy evaluation, risk checks, execution.
- [ ] Implement secrets management: load from `.env`, rotate via CLI, never expose to frontend.
- [ ] Build Alpaca REST/WebSocket client with deterministic `client_order_id`, position reconciliation on restart, and bracket maintenance.
- [ ] Expose GraphQL/REST endpoints for dashboard (positions, orders, metrics, logs, controls) + SSE/WebSocket channel for real-time events.
- [ ] Mirror simulator strategy in backend (EMA breakout) with unit tests, enabling easy swap to advanced strategies later.
- [ ] Add command ingestion endpoint so the copilot can delegate actions server-side (close/cancel/place orders, toggle risk limits).

## Stream B – Data, Features & Risk (Agent Beta)
- [ ] Integrate Alpaca/Polygon historical data with corporate-action hygiene (split/dividend modes as per blueprint).
- [ ] Populate Supabase `features`, `metrics`, `trades`, `advisories` tables; design retention policies & indexes.
- [ ] Implement feature pipelines (ATR, volume z-score, regime detectors) and scheduled walk-forward retraining harness (VectorBT/Backtrader).
- [ ] Train and version the supervised gatekeeper model; define feature schema freeze, evaluation metrics, and promotion policy.
- [ ] Engineering for risk rails: position sizing ≤2% capital, daily 5% breaker, sector/ correlation caps, short locate handling.
- [ ] Develop performance analytics jobs: mark-outs, slippage tiers, fill-rate tracking, latency distributions.

## Stream C – Frontend & Copilot UX (Agent Gamma)
- [ ] Connect dashboard to backend API (replace simulator state with live endpoints while keeping offline demo mode).
- [ ] Enhance copilot prompt orchestration: chain-of-thought scratchpad, structured JSON response parser, explicit action confirmation steps.
- [ ] Add news timeline (Perplexity) with source verification + veto toggles.
- [ ] Visualise readiness checklist from live metrics; include drill progress, uptime, and alert counters.
- [ ] Implement strategy configuration editor (per-strategy parameters, gatekeeper thresholds, retrain cadence).
- [ ] Add unit tests for hooks/components (React Testing Library, Vitest) and capture storybook scenarios.

## Stream D – Ops, QA & Automation (Agent Delta)
- [ ] Define IaC (Terraform/ Pulumi) to provision Supabase, server runtime, secret vault, observability stack.
- [ ] Configure CI: lint, type-check, unit/integration suites, contract tests against mock Alpaca.
- [ ] Build synthetic market replay harness for regression testing (intraday scenarios w/ halts, splits, earnings). 
- [ ] Instrument OpenTelemetry tracing + metrics ingestion (Prometheus/Grafana or Supabase-edge triggers).
- [ ] Draft incident runbooks (Alpaca outage, Supabase failover, model degradation) and automate notification routing (Slack/email/SMS).
- [ ] Execute quarterly disaster-recovery drill: backup restore, key rotation, fallback to simulator-only mode.

---

## Cross-Cutting Milestones
- **M1: Backend MVP (2 weeks)** – live Alpaca paper trading, Supabase persistence, dashboard consuming real data.
- **M2: Gatekeeper & Walk-Forward (4 weeks)** – supervised filter live in shadow mode, automated walk-forward/backtest pipeline, readiness checklist drawing from actual metrics.
- **M3: Ops Hardening (6 weeks)** – monitoring/alerting complete, runbooks tested, compliance tooling in place, pilot live trading under capital throttle.

## Dependencies & References
- Blueprint: [`DayTraderAI_idea.md`](./DayTraderAI_idea.md)
- Frontend guide: [`README.md`](./README.md)
- Keys/Secrets: maintain via `.env` (backend) and Settings drawer (frontend demo)

## Daily Rituals
- 10:00 UTC stand-up (15m) – each agent posts blockers & achievements.
- Async status board in Supabase/Notion; update milestones at EOD.
- Weekly Friday release candidate cut, Monday retro.

Stay ruthless about measurement, fail-safe defaults, and deterministic recoveries—every promotion gate must be earned with data. 🚀
