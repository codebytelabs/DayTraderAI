# Frontend-Backend Integration Requirements

## Introduction

This specification defines the requirements for completing the integration between the DayTraderAI React frontend and the FastAPI backend. The backend is fully functional with all APIs (Alpaca, Supabase, OpenRouter, Perplexity) working correctly. The frontend currently displays data but has several gaps where mock data or hardcoded values are used instead of real backend data.

## Glossary

- **Frontend Application**: The React/TypeScript single-page application that provides the user interface for DayTraderAI
- **Backend Service**: The FastAPI Python service running on port 8006 that manages trading operations and external API integrations
- **Service Health Endpoint**: REST API endpoint that returns the connection status of external services (Alpaca, Supabase, OpenRouter, Perplexity)
- **Configuration Endpoint**: REST API endpoint that returns default configuration values from the backend environment
- **Performance History Endpoint**: REST API endpoint that returns historical equity and performance metrics
- **Environment Variable**: Configuration value stored in .env files that can be accessed at build time (VITE\_\*) or runtime
- **Service Status Indicator**: UI component showing real-time connection status of external services
- **Settings Drawer**: UI panel where users configure API keys and trading parameters
- **Performance Chart**: Candlestick chart displaying portfolio equity over time

## Requirements

### Requirement 1: Dynamic Backend URL Configuration

**User Story:** As a developer, I want the frontend to support different backend URLs for development, staging, and production environments, so that I can deploy the application to multiple environments without code changes.

#### Acceptance Criteria

1. WHEN THE Frontend Application initializes, THE Frontend Application SHALL read the backend URL from environment variable VITE_BACKEND_URL
2. IF VITE_BACKEND_URL is not defined, THEN THE Frontend Application SHALL default to 'http://localhost:8006'
3. THE Frontend Application SHALL use the configured backend URL for all API requests to metrics, positions, orders, logs, advisories, analyses, performance, config, and health endpoints
4. WHERE the application is deployed to production, THE Frontend Application SHALL support HTTPS backend URLs
5. THE Frontend Application SHALL validate that the backend URL is a valid HTTP or HTTPS URL before making requests

### Requirement 2: Real-Time Service Health Monitoring

**User Story:** As a trader, I want to see the actual connection status of all external services (Alpaca, Supabase, OpenRouter, Perplexity), so that I know which services are operational before making trading decisions.

#### Acceptance Criteria

1. WHEN THE Frontend Application loads, THE Frontend Application SHALL fetch service health status from the /health/services endpoint
2. THE Frontend Application SHALL poll the /health/services endpoint every 30 seconds to update service status
3. WHEN a service status is "connected", THE Frontend Application SHALL display a green indicator LED for that service
4. WHEN a service status is "disconnected", THE Frontend Application SHALL display a red indicator LED for that service
5. WHEN a service status is "error", THE Frontend Application SHALL display a red indicator LED and log the error to the console
6. THE Frontend Application SHALL display service status for Alpaca, Supabase, OpenRouter, and Perplexity in the header
7. IF the /health/services endpoint fails to respond, THEN THE Frontend Application SHALL display all services as disconnected

### Requirement 3: Backend Configuration Loading

**User Story:** As a user, I want the settings drawer to pre-populate with configuration values from the backend, so that I don't have to manually enter values that are already configured in the backend environment.

#### Acceptance Criteria

1. WHEN THE Settings Drawer opens for the first time, THE Frontend Application SHALL fetch configuration from the /config endpoint
2. THE Frontend Application SHALL populate the Alpaca base URL field with the value from backend config
3. THE Frontend Application SHALL populate the Supabase URL field with the value from backend config
4. THE Frontend Application SHALL populate the watchlist field with comma-separated symbols from backend config
5. THE Frontend Application SHALL populate the max positions field with the value from backend config
6. THE Frontend Application SHALL populate the risk per trade percentage field with the value from backend config
7. THE Frontend Application SHALL NOT populate API keys or secrets from the backend for security reasons
8. IF the user has previously saved configuration in localStorage, THEN THE Frontend Application SHALL use the saved configuration instead of fetching from backend
9. THE Frontend Application SHALL provide a "Reset to Defaults" button that fetches fresh configuration from the /config endpoint

### Requirement 4: Historical Performance Data Display

**User Story:** As a trader, I want to see a historical equity curve showing my portfolio performance over the past 30 days, so that I can analyze trends and evaluate the trading strategy's effectiveness.

#### Acceptance Criteria

1. WHEN THE Frontend Application loads, THE Frontend Application SHALL fetch performance history from the /performance endpoint with days=30 parameter
2. THE Frontend Application SHALL transform the performance data into candlestick format with open, high, low, close values
3. THE Performance Chart SHALL display equity values on the Y-axis and timestamps on the X-axis
4. THE Performance Chart SHALL render green candlesticks when close >= open (profitable periods)
5. THE Performance Chart SHALL render red candlesticks when close < open (losing periods)
6. THE Performance Chart SHALL display a reference line showing the initial equity value
7. THE Performance Chart SHALL show tooltips with detailed metrics (open, high, low, close, P/L, win rate, profit factor) when hovering over data points
8. IF the /performance endpoint returns empty data, THEN THE Performance Chart SHALL display a message "No performance data available"
9. THE Frontend Application SHALL refresh performance data every 60 seconds to show near real-time updates

### Requirement 5: Environment-Based Frontend Configuration

**User Story:** As a developer, I want to configure the frontend using environment variables, so that I can manage different configurations for development, staging, and production without modifying code.

#### Acceptance Criteria

1. THE Frontend Application SHALL support a .env.local file in the project root for local development configuration
2. THE Frontend Application SHALL read VITE_BACKEND_URL from environment variables to configure the backend API base URL
3. THE Frontend Application SHALL read VITE_ALPACA_BASE_URL from environment variables to set the default Alpaca API URL
4. THE Frontend Application SHALL read VITE_SUPABASE_URL from environment variables to set the default Supabase project URL
5. THE Frontend Application SHALL read VITE_OPENROUTER_MODEL from environment variables to set the default OpenRouter model
6. THE Frontend Application SHALL read VITE_PERPLEXITY_MODEL from environment variables to set the default Perplexity model
7. THE Frontend Application SHALL read VITE_MAX_POSITIONS from environment variables to set the default maximum positions
8. THE Frontend Application SHALL read VITE_RISK_PER_TRADE_PCT from environment variables to set the default risk percentage
9. WHERE an environment variable is not defined, THE Frontend Application SHALL use sensible default values
10. THE Frontend Application SHALL NOT expose sensitive API keys or secrets in environment variables that are bundled into the client-side build

### Requirement 6: Backend Connection Error Handling

**User Story:** As a user, I want to see clear error messages when the backend is unavailable, so that I understand why the application is not functioning and can take appropriate action.

#### Acceptance Criteria

1. WHEN THE Backend Service is not responding, THE Frontend Application SHALL display a "Backend Disconnected" banner at the top of the page
2. THE Frontend Application SHALL display the error message "Load failed" in the banner when connection fails
3. THE Frontend Application SHALL retry the backend connection every 5 seconds automatically
4. WHEN THE Backend Service becomes available again, THE Frontend Application SHALL remove the error banner and resume normal operation
5. THE Frontend Application SHALL log all backend connection errors to the browser console for debugging
6. THE Frontend Application SHALL display a loading spinner while waiting for the initial backend connection
7. IF the backend returns a 500 error, THEN THE Frontend Application SHALL display "Server error - please try again later"
8. IF the backend returns a 404 error for an endpoint, THEN THE Frontend Application SHALL log a warning and continue with empty data for that endpoint

### Requirement 7: Real-Time Data Polling

**User Story:** As a trader, I want the frontend to automatically refresh data from the backend every few seconds, so that I see up-to-date information about positions, orders, and market conditions without manually refreshing the page.

#### Acceptance Criteria

1. THE Frontend Application SHALL poll the /metrics endpoint every 5 seconds to update portfolio statistics
2. THE Frontend Application SHALL poll the /positions endpoint every 5 seconds to update open positions
3. THE Frontend Application SHALL poll the /orders endpoint every 5 seconds to update order status
4. THE Frontend Application SHALL poll the /logs endpoint every 5 seconds to fetch new log entries (limit=100)
5. THE Frontend Application SHALL poll the /advisories endpoint every 5 seconds to fetch new advisory messages (limit=50)
6. THE Frontend Application SHALL poll the /analyses endpoint every 5 seconds to fetch new trade analyses (limit=50)
7. THE Frontend Application SHALL poll the /performance endpoint every 60 seconds to update the equity curve
8. THE Frontend Application SHALL poll the /health/services endpoint every 30 seconds to update service status indicators
9. WHEN THE user navigates away from the application, THE Frontend Application SHALL stop all polling to conserve resources
10. WHEN THE user returns to the application, THE Frontend Application SHALL resume polling immediately

### Requirement 8: Settings Persistence

**User Story:** As a user, I want my configuration settings to be saved locally, so that I don't have to re-enter them every time I open the application.

#### Acceptance Criteria

1. WHEN THE user updates any setting in the Settings Drawer, THE Frontend Application SHALL save the updated configuration to localStorage
2. THE Frontend Application SHALL use the localStorage key "daytraderai.config.v1" to store configuration
3. WHEN THE Frontend Application loads, THE Frontend Application SHALL check localStorage for saved configuration before fetching from backend
4. IF saved configuration exists in localStorage, THEN THE Frontend Application SHALL use the saved values
5. IF no saved configuration exists in localStorage, THEN THE Frontend Application SHALL fetch defaults from the /config endpoint
6. THE Frontend Application SHALL provide a "Reset to Defaults" button that clears localStorage and fetches fresh configuration from backend
7. THE Frontend Application SHALL merge saved configuration with default configuration to handle new fields added in updates
8. THE Frontend Application SHALL validate saved configuration values before using them (e.g., URLs are valid, numbers are in acceptable ranges)
9. IF saved configuration is invalid or corrupted, THEN THE Frontend Application SHALL fall back to default configuration and log a warning

### Requirement 9: TypeScript Type Safety

**User Story:** As a developer, I want proper TypeScript types for all API responses and configuration objects, so that I can catch errors at compile time and have better IDE autocomplete support.

#### Acceptance Criteria

1. THE Frontend Application SHALL define TypeScript interfaces for all backend API response types (metrics, positions, orders, logs, advisories, analyses, performance, config, health)
2. THE Frontend Application SHALL define TypeScript interfaces for all configuration objects (AppConfig, AlpacaConfig, SupabaseConfig, OpenRouterConfig, PerplexityConfig, StrategyConfig, ChatConfig)
3. THE Frontend Application SHALL use strict TypeScript compiler options (strict: true, noImplicitAny: true)
4. THE Frontend Application SHALL not use 'any' type except where absolutely necessary with explicit justification
5. THE Frontend Application SHALL define proper types for all React component props
6. THE Frontend Application SHALL define proper types for all custom hooks return values
7. THE Frontend Application SHALL use TypeScript enums for fixed sets of values (OrderSide, OrderStatus, ServiceStatus, LogLevel)
8. THE Frontend Application SHALL export all types from a central types.ts file for reuse across components
9. THE Frontend Application SHALL compile without TypeScript errors or warnings

### Requirement 10: Performance Optimization

**User Story:** As a user, I want the application to load quickly and respond smoothly, so that I can make time-sensitive trading decisions without delays.

#### Acceptance Criteria

1. THE Frontend Application SHALL fetch all initial data (metrics, positions, orders, logs, advisories, analyses) in parallel using Promise.all
2. THE Frontend Application SHALL use React.memo for components that render frequently but don't need to re-render on every state change
3. THE Frontend Application SHALL use useCallback for event handlers to prevent unnecessary re-renders
4. THE Frontend Application SHALL use useMemo for expensive computations that depend on specific dependencies
5. THE Frontend Application SHALL debounce user input in search and filter fields to reduce unnecessary API calls
6. THE Frontend Application SHALL limit the number of data points displayed in the performance chart to prevent rendering performance issues
7. THE Frontend Application SHALL use virtual scrolling for long lists (logs, advisories, analyses) to improve rendering performance
8. THE Frontend Application SHALL lazy load components that are not immediately visible (e.g., settings drawer, modals)
9. THE Frontend Application SHALL display loading skeletons while fetching data to improve perceived performance
10. THE Frontend Application SHALL complete initial page load and display data within 2 seconds on a typical broadband connection
