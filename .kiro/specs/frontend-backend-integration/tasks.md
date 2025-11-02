# Implementation Tasks

## 1. Setup Infrastructure and Type Definitions

- [ ] 1.1 Create vite-env.d.ts with ImportMetaEnv interface for TypeScript support
  - Define all VITE_* environment variable types
  - Add ImportMeta interface extension
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 9.1, 9.3_

- [ ] 1.2 Create .env.local file in project root with all frontend environment variables
  - Add VITE_BACKEND_URL with default localhost:8006
  - Add VITE_ALPACA_BASE_URL, VITE_SUPABASE_URL
  - Add VITE_OPENROUTER_MODEL, VITE_PERPLEXITY_MODEL
  - Add VITE_MAX_POSITIONS, VITE_RISK_PER_TRADE_PCT
  - Add VITE_CHAT_PROVIDER, VITE_CHAT_TEMPERATURE
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9_

- [ ] 1.3 Create types/api.ts with all backend API response type definitions
  - Define MetricsResponse, PositionResponse, OrderResponse interfaces
  - Define LogResponse, AdvisoryResponse, AnalysisResponse interfaces
  - Define PerformanceResponse, BackendConfig, ServiceHealthStatus interfaces
  - Export all types for reuse
  - _Requirements: 9.1, 9.2, 9.8_

- [ ] 1.4 Create lib/apiClient.ts with centralized API client class
  - Implement ApiClient class with baseUrl from environment
  - Add URL validation in constructor
  - Implement get<T> and post<T> methods with proper error handling
  - Export singleton apiClient instance
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 6.1, 6.5_

## 2. Implement Service Health Monitoring

- [ ] 2.1 Create hooks/useServiceHealth.ts hook
  - Implement state management for service health status
  - Fetch from /health/services endpoint on mount
  - Set up 30-second polling interval
  - Handle errors by setting all services to 'error' status
  - Return health status object
  - _Requirements: 2.1, 2.2, 2.7_

- [ ] 2.2 Update components/Header.tsx to use real service health
  - Import and use useServiceHealth hook
  - Remove mock status interval code
  - Map health status ('connected'/'disconnected'/'error') to ServiceStatus enum
  - Display green LED for 'connected', red for 'disconnected'/'error'
  - _Requirements: 2.3, 2.4, 2.5, 2.6_

## 3. Implement Backend Configuration Loading

- [ ] 3.1 Create hooks/useBackendConfig.ts hook
  - Implement state for config, loading, and error
  - Fetch from /config endpoint on mount
  - Handle errors gracefully
  - Provide refetch function
  - _Requirements: 3.1_

- [ ] 3.2 Update state/ConfigContext.tsx to load backend defaults
  - Make loadInitialConfig async
  - Check localStorage first for saved config
  - If no localStorage, fetch from /config endpoint
  - Map backend config to AppConfig format (don't include secrets)
  - Merge with DEFAULT_CONFIG
  - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 8.4, 8.5_

- [ ] 3.3 Add "Reset to Defaults" functionality in settings
  - Add resetToBackendDefaults function in ConfigContext
  - Clear localStorage
  - Fetch fresh config from /config endpoint
  - Update state with backend defaults
  - _Requirements: 3.9, 8.6_

## 4. Implement Performance History Display

- [ ] 4.1 Update hooks/useBackendTrading.ts to fetch performance data
  - Replace hardcoded API_BASE with apiClient.getBaseUrl()
  - Add /performance?days=30 to Promise.all fetch array
  - Parse performance response
  - Transform to PerformanceDataPoint[] format with OHLC values
  - Store in performanceData state
  - _Requirements: 1.3, 4.1, 4.2_

- [ ] 4.2 Update performance data polling interval
  - Change performance fetch to separate 60-second interval
  - Keep other data at 5-second interval
  - _Requirements: 4.9, 7.7_

- [ ] 4.3 Update components/PerformanceChart.tsx to handle historical data
  - Accept performanceData prop with multiple data points
  - Render candlesticks with proper OHLC values
  - Display green candles for close >= open
  - Display red candles for close < open
  - Show reference line for initial equity
  - Display "No performance data available" if empty
  - _Requirements: 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

## 5. Implement Error Handling and Connection Management

- [ ] 5.1 Create components/ErrorBoundary.tsx component
  - Implement React error boundary class component
  - Catch and display errors with fallback UI
  - Provide "Try Again" button to reset error state
  - Log errors to console
  - _Requirements: 6.5_

- [ ] 5.2 Add connection error banner to Dashboard
  - Display banner when isConnected is false
  - Show error message from backend hook
  - Style as prominent warning at top of page
  - Auto-hide when connection restored
  - _Requirements: 6.1, 6.2, 6.4_

- [ ] 5.3 Implement automatic retry logic in useBackendTrading
  - Retry failed requests automatically every 5 seconds
  - Log connection errors to console
  - Update isConnected state based on success/failure
  - _Requirements: 6.3, 6.5_

- [ ] 5.4 Add error handling for individual endpoints
  - Wrap each endpoint fetch in try-catch
  - Continue with empty data if endpoint fails
  - Log 404 warnings for missing endpoints
  - Display user-friendly messages for 500 errors
  - _Requirements: 6.6, 6.7, 6.8_

## 6. Implement Settings Persistence

- [ ] 6.1 Verify localStorage save functionality in ConfigContext
  - Ensure updateConfig saves to localStorage with key "daytraderai.config.v1"
  - Verify config is saved on every settings change
  - _Requirements: 8.1, 8.2_

- [ ] 6.2 Implement config validation
  - Validate URLs are valid HTTP/HTTPS
  - Validate numbers are in acceptable ranges
  - Fall back to defaults if validation fails
  - Log warnings for invalid config
  - _Requirements: 8.8, 8.9_

- [ ] 6.3 Implement config merging for new fields
  - Merge saved config with DEFAULT_CONFIG to handle new fields
  - Preserve user values for existing fields
  - Add default values for new fields
  - _Requirements: 8.7_

## 7. Optimize Performance

- [ ] 7.1 Add React.memo to frequently rendered components
  - Wrap PerformanceChart in React.memo
  - Wrap StatusIndicator in React.memo
  - Wrap table row components in React.memo
  - _Requirements: 10.2_

- [ ] 7.2 Optimize useCallback usage in hooks
  - Wrap closePosition, cancelOrder, placeOrder in useCallback
  - Wrap fetchData in useCallback with proper dependencies
  - _Requirements: 10.3_

- [ ] 7.3 Optimize useMemo usage for expensive computations
  - Memoize activeProviderLabel in Header
  - Memoize chart data transformations
  - Memoize filtered/sorted table data
  - _Requirements: 10.4_

- [ ] 7.4 Implement data limiting
  - Limit performanceData to last 100 points
  - Limit logs to 100 entries
  - Limit advisories to 50 entries
  - Limit analyses to 50 entries
  - _Requirements: 10.6_

- [ ] 7.5 Implement visibility-based polling
  - Use document.visibilityState to detect tab visibility
  - Pause all polling intervals when tab is hidden
  - Resume polling when tab becomes visible
  - _Requirements: 7.9, 7.10_

## 8. Update TODO.md and Documentation

- [ ] 8.1 Update TODO.md with completed items
  - Mark frontend-backend integration as complete
  - Add any new discovered tasks
  - Update status of existing tasks
  - _Requirements: All_

- [ ] 8.2 Update README.md with environment setup instructions
  - Document .env.local configuration
  - List all VITE_* environment variables
  - Explain how to configure for different environments
  - _Requirements: 5.1-5.10_

## 9. Testing and Validation

- [ ]* 9.1 Write unit tests for apiClient
  - Test URL validation
  - Test get and post methods
  - Test error handling
  - _Requirements: 1.5, 6.5_

- [ ]* 9.2 Write unit tests for useServiceHealth hook
  - Test initial state
  - Test successful fetch
  - Test error handling
  - Test polling interval
  - _Requirements: 2.1-2.7_

- [ ]* 9.3 Write unit tests for useBackendConfig hook
  - Test config loading
  - Test error handling
  - Test refetch functionality
  - _Requirements: 3.1-3.9_

- [ ]* 9.4 Perform manual testing checklist
  - Test backend URL configuration
  - Test service status indicators
  - Test settings pre-population
  - Test performance chart with real data
  - Test data polling
  - Test error handling
  - Test settings persistence
  - Test TypeScript compilation
  - Test page load performance
  - _Requirements: All_

## 10. Final Polish and Deployment Prep

- [ ] 10.1 Fix all TypeScript errors and warnings
  - Run tsc --noEmit to check for errors
  - Fix any remaining type issues
  - Ensure strict mode compliance
  - _Requirements: 9.3, 9.4, 9.9_

- [ ] 10.2 Add loading states to all data fetches
  - Show loading spinners while fetching initial data
  - Show skeleton loaders for tables and charts
  - Improve perceived performance
  - _Requirements: 10.9_

- [ ] 10.3 Create .env.example file
  - Document all VITE_* variables
  - Provide example values
  - Add comments explaining each variable
  - _Requirements: 5.1-5.10_

- [ ] 10.4 Test in different environments
  - Test with localhost backend
  - Test with remote backend URL
  - Test with HTTPS backend
  - Verify CORS configuration
  - _Requirements: 1.4, 1.5_

- [ ] 10.5 Performance profiling
  - Measure initial page load time
  - Verify < 2 second load time
  - Profile React component renders
  - Optimize any bottlenecks
  - _Requirements: 10.10_
