import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  useEffect,
} from "react";
import { apiClient } from "../lib/apiClient";
import { BackendConfig } from "../types/api";

export type LLMProvider = "openrouter" | "perplexity" | "none";

export interface AppConfig {
  alpaca: {
    baseUrl: string;
    key: string;
    secret: string;
  };
  supabase: {
    url: string;
    anonKey: string;
    serviceRoleKey: string;
  };
  openRouter: {
    apiKey: string;
    model: string;
    fallbackModel: string;
  };
  perplexity: {
    apiKey: string;
    model: string;
  };
  strategy: {
    watchlist: string;
    riskPerTradePct: number;
    maxPositions: number;
  };
  chat: {
    provider: LLMProvider;
    temperature: number;
  };
  backend: {
    apiBaseUrl: string;
  };
  brackets: {
    enabled: boolean;
    takeProfitPct: number;
    stopLossPct: number;
  };
}

const STORAGE_KEY = "daytraderai.config.v1";

const resolveStoredBackendUrl = (): string | undefined => {
  if (typeof window === "undefined") {
    return undefined;
  }

  try {
    const persisted = window.localStorage.getItem(STORAGE_KEY);
    if (persisted) {
      const parsed = JSON.parse(persisted) as Partial<AppConfig>;
      const storedUrl = parsed?.backend?.apiBaseUrl;
      if (storedUrl) {
        return storedUrl;
      }
    }
  } catch (error) {
    console.warn("Failed to parse stored backend config", error);
  }

  try {
    return window.localStorage.getItem("daytraderai.backend_url") ?? undefined;
  } catch (error) {
    console.warn("Failed to read legacy backend URL", error);
    return undefined;
  }
};

const DEFAULT_BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL ?? resolveStoredBackendUrl() ?? "http://localhost:8006";

const DEFAULT_CONFIG: AppConfig = {
  alpaca: {
    baseUrl:
      import.meta.env.VITE_ALPACA_BASE_URL ??
      "https://paper-api.alpaca.markets/v2",
    key: "",
    secret: "",
  },
  supabase: {
    url: import.meta.env.VITE_SUPABASE_URL ?? "",
    anonKey: "",
    serviceRoleKey: "",
  },
  openRouter: {
    apiKey: "",
    model: import.meta.env.VITE_OPENROUTER_MODEL ?? "openai/gpt-4.1-mini",
    fallbackModel:
      import.meta.env.VITE_OPENROUTER_FALLBACK_MODEL ?? "openai/gpt-4o-mini",
  },
  perplexity: {
    apiKey: "",
    model: import.meta.env.VITE_PERPLEXITY_MODEL ?? "sonar-pro",
  },
  strategy: {
    watchlist: "SPY,QQQ,AAPL,MSFT,NVDA",
    riskPerTradePct: 0.01,
    maxPositions: 5, // Will be overridden by backend config on load
  },
  chat: {
    provider:
      (import.meta.env.VITE_CHAT_PROVIDER as LLMProvider) ?? "openrouter",
    temperature: Number(import.meta.env.VITE_CHAT_TEMPERATURE ?? 0.2),
  },
  backend: {
    apiBaseUrl: DEFAULT_BACKEND_URL,
  },
  brackets: {
    enabled:
      (import.meta.env.VITE_BRACKET_ORDERS_ENABLED ?? "true").toString() ===
      "true",
    takeProfitPct: Number(import.meta.env.VITE_DEFAULT_TAKE_PROFIT_PCT ?? 2.0),
    stopLossPct: Number(import.meta.env.VITE_DEFAULT_STOP_LOSS_PCT ?? 1.0),
  },
};

interface ConfigContextValue {
  config: AppConfig;
  updateConfig: (changes: Partial<AppConfig>) => void;
  resetConfig: () => void;
}

const ConfigContext = createContext<ConfigContextValue | undefined>(undefined);

const mergeConfig = (
  prev: AppConfig,
  changes: Partial<AppConfig>
): AppConfig => {
  return {
    ...prev,
    alpaca: { ...prev.alpaca, ...changes.alpaca },
    supabase: { ...prev.supabase, ...changes.supabase },
    openRouter: { ...prev.openRouter, ...changes.openRouter },
    perplexity: { ...prev.perplexity, ...changes.perplexity },
    strategy: { ...prev.strategy, ...changes.strategy },
    chat: { ...prev.chat, ...changes.chat },
    backend: { ...prev.backend, ...changes.backend },
    brackets: { ...prev.brackets, ...changes.brackets },
  };
};

const loadInitialConfig = async (): Promise<AppConfig> => {
  // Always fetch from backend first (single source of truth)
  try {
    const backendConfig = await apiClient.get<BackendConfig>("/config");
    const backendMappedConfig: Partial<AppConfig> = {
      alpaca: {
        baseUrl: backendConfig.alpaca_base_url || DEFAULT_CONFIG.alpaca.baseUrl,
        key: "",
        secret: "",
      },
      supabase: {
        url: backendConfig.supabase_url || DEFAULT_CONFIG.supabase.url,
        anonKey: "",
        serviceRoleKey: "",
      },
      strategy: {
        watchlist: backendConfig.watchlist.join(","),
        maxPositions: backendConfig.max_positions,
        riskPerTradePct: backendConfig.risk_per_trade_pct,
      },
      backend: {
        apiBaseUrl:
          backendConfig.backend_url ||
          resolveStoredBackendUrl() ||
          apiClient.getBaseUrl(),
      },
      brackets: {
        enabled: backendConfig.bracket_orders_enabled,
        takeProfitPct: backendConfig.default_take_profit_pct,
        stopLossPct: backendConfig.default_stop_loss_pct,
      },
    };

    // Then merge with localStorage for user-specific settings (API keys, etc.)
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<AppConfig>;
        // Backend config takes precedence for strategy settings
        const merged = mergeConfig(DEFAULT_CONFIG, parsed);
        merged.strategy = backendMappedConfig.strategy!;
        return merged;
      }
    } catch (error) {
      console.warn("Failed to parse saved config", error);
    }

    return mergeConfig(DEFAULT_CONFIG, backendMappedConfig);
  } catch (error) {
    console.warn(
      "Failed to fetch backend config, falling back to localStorage",
      error
    );

    // Fallback to localStorage if backend is unavailable
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<AppConfig>;
        return mergeConfig(DEFAULT_CONFIG, parsed);
      }
    } catch (error) {
      console.warn("Failed to parse saved config", error);
    }

    return DEFAULT_CONFIG;
  }
};

export const ConfigProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [config, setConfig] = useState<AppConfig>(DEFAULT_CONFIG);

  // Load config on mount
  useEffect(() => {
    loadInitialConfig()
      .then((initial) => {
        setConfig(initial);
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(initial));
        } catch (error) {
          console.warn("Failed to persist initial config", error);
        }
      })
      .catch((error) => {
        console.error("Failed to bootstrap config", error);
      });
  }, []);

  const updateConfig = useCallback((changes: Partial<AppConfig>) => {
    setConfig((prev) => {
      const next = mergeConfig(prev, changes);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const resetConfig = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setConfig(DEFAULT_CONFIG);
  }, []);

  const value = useMemo(
    () => ({
      config,
      updateConfig,
      resetConfig,
    }),
    [config, resetConfig, updateConfig]
  );

  return (
    <ConfigContext.Provider value={value}>{children}</ConfigContext.Provider>
  );
};

export const useConfig = (): ConfigContextValue => {
  const context = useContext(ConfigContext);
  if (!context) {
    throw new Error("useConfig must be used within ConfigProvider");
  }
  return context;
};
