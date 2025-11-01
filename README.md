# DayTraderAI Ops Console

An interactive command centre for the “Ultimate Expert Day-Trading Bot” blueprint. The current build runs a high-fidelity paper-trading simulator with risk rails, live dashboards, configurable API credentials, and an AI Ops copilot that can act on your instructions.

> ⚠️ **Personal-use only.** Keys are stored in browser local storage. Do not use production credentials without moving secrets server-side.

## Highlights

- **Settings-first configuration** – manage Alpaca, Supabase, OpenRouter, Perplexity, and risk preferences directly in the UI; values are persisted locally and honoured by the simulator.
- **Shared trading state** – positions, orders, logs, analytics, and advisories flow through a single context so every component (including the copilot) sees the same truth.
- **Ops copilot chatbox** – ask for status recaps, close or open trades, cancel orders, or request strategy guidance. When OpenRouter or Perplexity keys are provided the copilot uses those LLMs; otherwise it falls back to deterministic summaries.
- **Deterministic risk rails** – simulator respects max-position and risk-per-trade settings, tracks drawdown, and surfaces a dynamic paper→live readiness checklist.
- **Composable UI** – modern React/Tailwind dashboard with KPIs, performance charting, trade analysis log, advisories, readiness checklist, and copilot pane.

## Quickstart

```bash
git clone https://github.com/codebytelabs/DayTraderAI.git
cd DayTraderAI
npm install
npm run dev
```

Visit `http://localhost:5173` and open **Settings** (top-right) to configure your stack.

### Configuration Options

Settings are stored in browser local storage. You can optionally supply defaults via environment variables before `npm run dev`:

| Purpose                     | UI Field                            | Optional env (prefixed with `VITE_`)          |
|-----------------------------|-------------------------------------|-----------------------------------------------|
| Alpaca REST base URL        | `Alpaca Base URL`                   | `ALPACA_BASE_URL`                             |
| Alpaca key / secret         | `Alpaca Key` / `Alpaca Secret`      | `ALPACA_KEY`, `ALPACA_SECRET`                 |
| Supabase project + keys     | `Supabase URL`, `Anon Key`, `Service Role Key` | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` |
| Perplexity key/model        | `Perplexity API Key`, `Model`       | `PERPLEXITY_MODEL`                            |
| OpenRouter key/models       | `OpenRouter API Key`, `Primary Model`, `Fallback Model` | `OPENROUTER_MODEL`, `OPENROUTER_FALLBACK_MODEL` |
| Strategy watchlist & risk   | `Default Watchlist`, `Risk %`, `Max Positions` | `RISK_PER_TRADE_PCT`, `MAX_POSITIONS`         |
| Copilot provider & tone     | `Provider`, `Temperature`           | `CHAT_PROVIDER`, `CHAT_TEMPERATURE`           |

Leave keys blank to keep services disabled; the UI and simulator continue to function with mock data.

### Copilot Commands

Type `help` inside the chat panel for the full list. Highlights:

- `status` – quick performance summary
- `close all positions` or `close NVDA`
- `cancel order <id>` or `cancel orders for NVDA`
- `buy 50 MSFT` / `sell 20 TSLA`

The copilot automatically attaches the latest positions, orders, advisories, and logs to every LLM call so responses stay anchored in live context.

## Project Structure

```
DayTraderAI/
├── App.tsx                     # Shell with providers + layout
├── components/                 # Dashboard, chat, settings, widgets
├── services/copilot.ts         # OpenRouter/Perplexity client + fallback summariser
├── simulation/useTradingSimulator.ts
│                               # Deterministic paper-trading engine (EMA breakout)
├── state/ConfigContext.tsx     # Settings provider + localStorage persistence
├── state/TradingContext.tsx    # Shared trading state derived from simulator
├── TODO.md                     # Detailed roadmap & multi-agent plan
└── README.md                   # (this file)
```

Key flows:

1. **ConfigProvider** hydrates user settings and exposes update/reset helpers.
2. **TradingProvider** feeds watchlist & risk parameters into the simulator and broadcasts unified state (`positions`, `orders`, `logs`, etc.).
3. **Dashboard** renders KPIs, charts, readiness checklist, advisories, and log feed from shared state.
4. **ChatPanel** consumes shared state + config to execute automation commands and optionally call OpenRouter/Perplexity for natural-language guidance.

## Roadmap Snapshot

See [`TODO.md`](./TODO.md) for a multi-agent execution plan aligned with the blueprint. Major upcoming milestones:

1. Harden a Python/Node backend service for Alpaca execution, Supabase persistence, and LLM proxying (so secrets never touch the browser).
2. Replace simulator-generated metrics with live data: Alpaca websocket ingestion, Supabase analytics, and Perplexity news ingestion.
3. Implement the supervised gatekeeper, walk-forward scheduler, and automated promotion gates outlined in `DayTraderAI_idea.md`.
4. Build ops automation: alert routing, incident runbooks, recovery drills, and compliance reporting.

## Contributing

1. Create a fresh branch.
2. Follow the tasks in `TODO.md`, claiming a workstream (Agent Alpha–Delta) to avoid overlap.
3. Run `npm run lint` (TBA) and `npm run build` before opening a PR.
4. Document any new configuration in **Settings** and update the README/TODO as necessary.

## FAQ

- **Where are my API keys stored?** In `localStorage` under `daytraderai.config.v1`. Use the reset button in Settings to clear them.
- **Can I run this without OpenRouter/Perplexity?** Yes. The copilot falls back to deterministic summaries and still executes local automation commands.
- **How do I switch to live trading?** Wire up the backend per `TODO.md`: migrate execution to a server process, enforce secrets management, and integrate genuine Alpaca/Supabase endpoints.
- **Does this match the blueprint?** The UI embodies the monitoring/advisory layer. The next iteration (tracked in `TODO.md`) builds out the production-grade backend, risk manager, and deployment pipeline described in `DayTraderAI_idea.md`.

Happy trading (and experimenting)! 🧠📈

