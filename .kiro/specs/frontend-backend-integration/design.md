# Frontend-Backend Integration Design

## Overview

This design document outlines the technical approach for completing the integration between the DayTraderAI React frontend and FastAPI backend. The design focuses on replacing mock/hardcoded data with real backend API calls, implementing proper environment configuration, and ensuring type safety throughout the application.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend (Vite)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Environment Configuration                  │ │
│  │  (.env.local → import.meta.env.VITE_*)                │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                 Custom Hooks Layer                      │ │
│  │  • useBackendTrading (data polling)                    │ │
│  │  • useServiceHealth (health monitoring)                │ │
│  │  • useBackendConfig (config loading)                   │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              React Context Providers                    │ │
│  │  • ConfigProvider (settings management)                │ │
│  │  • TradingProvider (trading data state)                │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  UI Components                          │ │
│  │  • Header (service status)                             │ │
│  │  • Dashboard (KPIs, charts, tables)                    │ │
│  │  • SettingsDrawer (configuration)                      │ │
│  │  • PerformanceChart (equity curve)                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Port 8006)                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    REST API Endpoints                   │ │
│  │  • /metrics, /positions, /orders                       │ │
│  │  • /logs, /advisories, /analyses                       │ │
│  │  • /performance, /config, /health/services             │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Initial Load**: Frontend fetches config from `/config`, then loads all data endpoints in parallel
2. **Polling Loop**: Frontend polls data endpoints every 5s, health every 30s, performance every 60s
3. **User Actions**: User interactions (close position, cancel order) trigger POST requests, then refresh data
4. **Configuration**: Settings are saved to localStorage and merged with backend defaults

## Components and Interfaces

### 1. Environment Configuration

**File**: `.env.local` (project root)

```env
# Backend Configuration
VITE_BACKEND_URL=http://localhost:8006

# Default API URLs
VITE_ALPACA_BASE_URL=https://paper-api.alpaca.markets
VITE_SUPABASE_URL=https://your-project.supabase.co

# Default Models
VITE_OPENROUTER_MODEL=openai/gpt-4-turbo
VITE_PERPLEXITY_MODEL=sonar-pro

# Strategy Defaults
VITE_MAX_POSITIONS=5
VITE_RISK_PER_TRADE_PCT=0.01
VITE_CHAT_PROVIDER=openrouter
VITE_CHAT_TEMPERATURE=0.2
```

**Implementation Notes**:
- Vite only exposes variables prefixed with `VITE_`
- Access via `import.meta.env.VITE_*`
- Never store secrets in frontend env vars (they're bundled into the build)

### 2. API Client Module

**File**: `lib/apiClient.ts` (new file)

```typescript
// Centralized API client with environment-based URL
export class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8006';
    this.validateUrl();
  }

  private validateUrl(): void {
    try {
      new URL(this.baseUrl);
    } catch {
      console.error(`Invalid backend URL: ${this.baseUrl}`);
      this.baseUrl = 'http://localhost:8006';
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`);
    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  async post<T>(endpoint: string, body?: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }
}

export const apiClient = new ApiClient();
```

### 3. Service Health Hook

**File**: `hooks/useServiceHealth.ts` (new file)

```typescript
import { useState, useEffect } from 'react';
import { apiClient } from '../lib/apiClient';

export interface ServiceHealthStatus {
  alpaca: 'connected' | 'disconnected' | 'error';
  supabase: 'connected' | 'disconnected' | 'error';
  openrouter: 'connected' | 'disconnected' | 'error';
  perplexity: 'connected' | 'disconnected' | 'error';
  timestamp?: string;
}

export const useServiceHealth = () => {
  const [health, setHealth] = useState<ServiceHealthStatus>({
    alpaca: 'disconnected',
    supabase: 'disconnected',
    openrouter: 'disconnected',
    perplexity: 'disconnected',
  });

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await apiClient.get<ServiceHealthStatus>('/health/services');
        setHealth(data);
      } catch (error) {
        console.error('Failed to fetch service health:', error);
        setHealth({
          alpaca: 'error',
          supabase: 'error',
          openrouter: 'error',
          perplexity: 'error',
        });
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

  return health;
};
```

### 4. Backend Config Hook

**File**: `hooks/useBackendConfig.ts` (new file)

```typescript
import { useState, useEffect } from 'react';
import { apiClient } from '../lib/apiClient';

export interface BackendConfig {
  alpaca_base_url: string;
  supabase_url: string;
  watchlist: string[];
  max_positions: number;
  risk_per_trade_pct: number;
  backend_url: string;
}

export const useBackendConfig = () => {
  const [config, setConfig] = useState<BackendConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<BackendConfig>('/config');
      setConfig(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch backend config:', err);
      setError(err instanceof Error ? err.message : 'Failed to load config');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  return { config, loading, error, refetch: fetchConfig };
};
```

### 5. Updated useBackendTrading Hook

**File**: `hooks/useBackendTrading.ts` (modifications)

**Changes**:
1. Replace hardcoded `API_BASE` with `apiClient.getBaseUrl()`
2. Add `/performance` endpoint fetch
3. Transform performance history data properly
4. Add error boundary for each endpoint

**Key modifications**:
```typescript
import { apiClient } from '../lib/apiClient';

// Replace const API_BASE = 'http://localhost:8006';
// with: const API_BASE = apiClient.getBaseUrl();

// Add performance fetch to Promise.all:
const [metricsRes, positionsRes, ordersRes, logsRes, advisoriesRes, analysesRes, performanceRes] = 
  await Promise.all([
    fetch(`${API_BASE}/metrics`),
    fetch(`${API_BASE}/positions`),
    fetch(`${API_BASE}/orders`),
    fetch(`${API_BASE}/logs?limit=100`),
    fetch(`${API_BASE}/advisories?limit=50`),
    fetch(`${API_BASE}/analyses?limit=50`),
    fetch(`${API_BASE}/performance?days=30`),
  ]);

// Transform performance data:
const performanceHistory = performanceRes.ok ? await performanceRes.json() : [];
const performanceData: PerformanceDataPoint[] = performanceHistory.map((p: any) => ({
  timestamp: new Date(p.timestamp).getTime(),
  open: p.equity,
  high: p.equity * 1.001,
  low: p.equity * 0.999,
  close: p.equity,
  pnl: p.daily_pl,
  winRate: p.win_rate,
  profitFactor: p.profit_factor,
  wins: p.wins || 0,
  losses: p.losses || 0,
}));
```

### 6. Updated Header Component

**File**: `components/Header.tsx` (modifications)

**Changes**:
1. Remove mock status interval
2. Use `useServiceHealth` hook
3. Map health status to ServiceStatus enum

```typescript
import { useServiceHealth } from '../hooks/useServiceHealth';

export const Header: React.FC<HeaderProps> = ({ onOpenSettings }) => {
  const health = useServiceHealth();
  const { config } = useConfig();

  // Map health status to ServiceStatus enum
  const statuses: ConnectionStatuses = {
    alpaca: health.alpaca === 'connected' ? ServiceStatus.CONNECTED : 
            health.alpaca === 'error' ? ServiceStatus.DISCONNECTED : ServiceStatus.DEGRADED,
    supabase: health.supabase === 'connected' ? ServiceStatus.CONNECTED : 
              health.supabase === 'error' ? ServiceStatus.DISCONNECTED : ServiceStatus.DEGRADED,
    perplexity: health.perplexity === 'connected' ? ServiceStatus.CONNECTED : 
                health.perplexity === 'error' ? ServiceStatus.DISCONNECTED : ServiceStatus.DEGRADED,
    openRouter: health.openrouter === 'connected' ? ServiceStatus.CONNECTED : 
                health.openrouter === 'error' ? ServiceStatus.DISCONNECTED : ServiceStatus.DEGRADED,
  };

  // Remove the mock useEffect interval
  // ... rest of component
};
```

### 7. Updated ConfigContext

**File**: `state/ConfigContext.tsx` (modifications)

**Changes**:
1. Use `useBackendConfig` to fetch defaults
2. Merge backend config with localStorage
3. Add proper TypeScript types for import.meta.env

**Add vite-env.d.ts**:
```typescript
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BACKEND_URL: string;
  readonly VITE_ALPACA_BASE_URL: string;
  readonly VITE_SUPABASE_URL: string;
  readonly VITE_OPENROUTER_MODEL: string;
  readonly VITE_PERPLEXITY_MODEL: string;
  readonly VITE_MAX_POSITIONS: string;
  readonly VITE_RISK_PER_TRADE_PCT: string;
  readonly VITE_CHAT_PROVIDER: string;
  readonly VITE_CHAT_TEMPERATURE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

**Modified loadInitialConfig**:
```typescript
const loadInitialConfig = async (): Promise<AppConfig> => {
  // First check localStorage
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<AppConfig>;
      return mergeConfig(DEFAULT_CONFIG, parsed);
    }
  } catch (error) {
    console.warn('Failed to parse saved config', error);
  }

  // If no localStorage, fetch from backend
  try {
    const backendConfig = await apiClient.get<BackendConfig>('/config');
    const mappedConfig: Partial<AppConfig> = {
      alpaca: {
        baseUrl: backendConfig.alpaca_base_url,
        key: '',
        secret: '',
      },
      supabase: {
        url: backendConfig.supabase_url,
        anonKey: '',
        serviceRoleKey: '',
      },
      strategy: {
        watchlist: backendConfig.watchlist.join(','),
        maxPositions: backendConfig.max_positions,
        riskPerTradePct: backendConfig.risk_per_trade_pct,
      },
    };
    return mergeConfig(DEFAULT_CONFIG, mappedConfig);
  } catch (error) {
    console.warn('Failed to fetch backend config', error);
    return DEFAULT_CONFIG;
  }
};
```

## Data Models

### API Response Types

**File**: `types/api.ts` (new file)

```typescript
// Backend API response types
export interface MetricsResponse {
  equity: number;
  cash: number;
  buying_power: number;
  daily_pl: number;
  daily_pl_pct: number;
  total_pl: number;
  win_rate: number;
  profit_factor: number;
  wins: number;
  losses: number;
  total_trades: number;
  open_positions: number;
  circuit_breaker_triggered: boolean;
}

export interface PositionResponse {
  symbol: string;
  qty: number;
  side: string;
  avg_entry_price: number;
  current_price: number;
  unrealized_pl: number;
  unrealized_pl_pct: number;
  market_value: number;
  take_profit?: number;
  stop_loss?: number;
}

export interface OrderResponse {
  order_id: string;
  symbol: string;
  qty: number;
  side: string;
  type: string;
  status: string;
  filled_qty: number;
  filled_avg_price?: number;
  submitted_at: string;
}

export interface LogResponse {
  id: string;
  timestamp: string;
  level: string;
  message: string;
  source: string;
}

export interface AdvisoryResponse {
  id: string;
  timestamp: string;
  type: string;
  symbol: string;
  content: string;
  model?: string;
  source?: string;
  confidence?: number;
}

export interface AnalysisResponse {
  id: string;
  timestamp: string;
  symbol: string;
  side: string;
  action: string;
  analysis: string;
  pnl?: number;
  pnl_pct?: number;
  source?: string;
  model?: string;
  entry_price?: number;
  take_profit?: number;
  stop_loss?: number;
}

export interface PerformanceResponse {
  timestamp: string;
  equity: number;
  daily_pl: number;
  daily_pl_pct: number;
  win_rate: number;
  profit_factor: number;
  wins: number;
  losses: number;
}
```

## Error Handling

### Error Boundary Component

**File**: `components/ErrorBoundary.tsx` (new file)

```typescript
import React, { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error boundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-4 bg-red-900/20 border border-red-500 rounded-lg">
          <h2 className="text-xl font-bold text-red-500 mb-2">Something went wrong</h2>
          <p className="text-red-300">{this.state.error?.message}</p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="mt-4 px-4 py-2 bg-red-500 hover:bg-red-600 rounded"
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### API Error Handling Strategy

1. **Network Errors**: Display "Backend Disconnected" banner, retry automatically
2. **4xx Errors**: Log warning, display user-friendly message, continue with empty data
3. **5xx Errors**: Display "Server Error" message, retry with exponential backoff
4. **Timeout**: Set 10s timeout for all requests, display timeout message

## Testing Strategy

### Unit Tests

**Test Files**:
- `hooks/__tests__/useBackendTrading.test.ts`
- `hooks/__tests__/useServiceHealth.test.ts`
- `hooks/__tests__/useBackendConfig.test.ts`
- `lib/__tests__/apiClient.test.ts`

**Test Coverage**:
- API client URL validation
- Hook data transformation
- Error handling paths
- Polling intervals
- localStorage persistence

### Integration Tests

**Test Scenarios**:
1. Full data flow from backend to UI
2. Service health status updates
3. Configuration loading and merging
4. Performance chart rendering with real data
5. Settings persistence across page reloads

### Manual Testing Checklist

- [ ] Backend URL configurable via .env
- [ ] Service status LEDs show real health
- [ ] Settings pre-populate from backend
- [ ] Performance chart shows 30-day history
- [ ] All data updates every 5 seconds
- [ ] Error banner appears when backend down
- [ ] Settings persist in localStorage
- [ ] No TypeScript errors in console
- [ ] Page loads in < 2 seconds

## Performance Considerations

### Optimization Techniques

1. **Parallel Data Fetching**: Use `Promise.all` for initial load
2. **Memoization**: Use `React.memo`, `useMemo`, `useCallback` appropriately
3. **Debouncing**: Debounce search/filter inputs
4. **Virtual Scrolling**: For long lists (logs, advisories)
5. **Code Splitting**: Lazy load settings drawer and modals
6. **Data Limiting**: Cap performance data at 100 points, logs at 100 entries

### Polling Strategy

- **High Priority** (5s): metrics, positions, orders, logs, advisories, analyses
- **Medium Priority** (30s): service health
- **Low Priority** (60s): performance history
- **Pause on Blur**: Stop polling when tab is not visible

## Deployment Considerations

### Environment-Specific Configuration

**Development** (`.env.local`):
```env
VITE_BACKEND_URL=http://localhost:8006
```

**Staging** (`.env.staging`):
```env
VITE_BACKEND_URL=https://staging-api.daytraderai.com
```

**Production** (`.env.production`):
```env
VITE_BACKEND_URL=https://api.daytraderai.com
```

### Build Process

1. Vite reads `.env.production` during build
2. Environment variables are embedded in bundle
3. No runtime configuration needed
4. CORS must be configured on backend for production domain

## Migration Path

### Phase 1: Infrastructure (Completed in this design)
- Create API client module
- Add environment configuration
- Create new hooks (useServiceHealth, useBackendConfig)
- Add TypeScript type definitions

### Phase 2: Component Updates
- Update Header with real service health
- Update ConfigContext with backend config loading
- Update useBackendTrading with performance endpoint
- Update PerformanceChart with historical data

### Phase 3: Polish
- Add error boundaries
- Add loading states
- Add retry logic
- Optimize performance

### Phase 4: Testing
- Write unit tests
- Perform integration testing
- Manual UAT
- Performance profiling

## Success Criteria

The integration is complete when:
1. ✅ All 10 requirements are implemented
2. ✅ No hardcoded URLs or mock data remain
3. ✅ TypeScript compiles without errors
4. ✅ All tests pass
5. ✅ Manual testing checklist is complete
6. ✅ Performance metrics are met (< 2s load time)
7. ✅ Application works in dev, staging, and production environments
