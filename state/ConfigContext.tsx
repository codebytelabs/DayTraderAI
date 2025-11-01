import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

export type LLMProvider = 'openrouter' | 'perplexity' | 'none';

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
}

const DEFAULT_CONFIG: AppConfig = {
  alpaca: {
    baseUrl: import.meta.env.VITE_ALPACA_BASE_URL ?? 'https://paper-api.alpaca.markets/v2',
    key: '',
    secret: '',
  },
  supabase: {
    url: import.meta.env.VITE_SUPABASE_URL ?? '',
    anonKey: '',
    serviceRoleKey: '',
  },
  openRouter: {
    apiKey: '',
    model: import.meta.env.VITE_OPENROUTER_MODEL ?? 'openai/gpt-4.1-mini',
    fallbackModel: import.meta.env.VITE_OPENROUTER_FALLBACK_MODEL ?? 'openai/gpt-4o-mini',
  },
  perplexity: {
    apiKey: '',
    model: import.meta.env.VITE_PERPLEXITY_MODEL ?? 'sonar-pro',
  },
  strategy: {
    watchlist: 'SPY,QQQ,AAPL,MSFT,NVDA',
    riskPerTradePct: Number(import.meta.env.VITE_RISK_PER_TRADE_PCT ?? 0.01),
    maxPositions: Number(import.meta.env.VITE_MAX_POSITIONS ?? 5),
  },
  chat: {
    provider: (import.meta.env.VITE_CHAT_PROVIDER as LLMProvider) ?? 'openrouter',
    temperature: Number(import.meta.env.VITE_CHAT_TEMPERATURE ?? 0.2),
  },
};

interface ConfigContextValue {
  config: AppConfig;
  updateConfig: (changes: Partial<AppConfig>) => void;
  resetConfig: () => void;
}

const STORAGE_KEY = 'daytraderai.config.v1';

const ConfigContext = createContext<ConfigContextValue | undefined>(undefined);

const mergeConfig = (prev: AppConfig, changes: Partial<AppConfig>): AppConfig => {
  return {
    ...prev,
    alpaca: { ...prev.alpaca, ...changes.alpaca },
    supabase: { ...prev.supabase, ...changes.supabase },
    openRouter: { ...prev.openRouter, ...changes.openRouter },
    perplexity: { ...prev.perplexity, ...changes.perplexity },
    strategy: { ...prev.strategy, ...changes.strategy },
    chat: { ...prev.chat, ...changes.chat },
  };
};

const loadInitialConfig = (): AppConfig => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_CONFIG;
    const parsed = JSON.parse(raw) as Partial<AppConfig>;
    return mergeConfig(DEFAULT_CONFIG, parsed);
  } catch (error) {
    console.warn('Failed to parse saved config, falling back to defaults', error);
    return DEFAULT_CONFIG;
  }
};

export const ConfigProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [config, setConfig] = useState<AppConfig>(loadInitialConfig);

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
    [config, resetConfig, updateConfig],
  );

  return <ConfigContext.Provider value={value}>{children}</ConfigContext.Provider>;
};

export const useConfig = (): ConfigContextValue => {
  const context = useContext(ConfigContext);
  if (!context) {
    throw new Error('useConfig must be used within ConfigProvider');
  }
  return context;
};

