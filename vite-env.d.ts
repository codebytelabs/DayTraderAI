/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BACKEND_URL: string;
  readonly VITE_ALPACA_BASE_URL: string;
  readonly VITE_SUPABASE_URL: string;
  readonly VITE_OPENROUTER_MODEL: string;
  readonly VITE_OPENROUTER_FALLBACK_MODEL: string;
  readonly VITE_PERPLEXITY_MODEL: string;
  readonly VITE_MAX_POSITIONS: string;
  readonly VITE_RISK_PER_TRADE_PCT: string;
  readonly VITE_CHAT_PROVIDER: string;
  readonly VITE_CHAT_TEMPERATURE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
