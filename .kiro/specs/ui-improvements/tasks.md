# Implementation Plan

- [x] 1. Remove AI model display from Header component
  - Remove the `activeProviderLabel` computed value that displays model information
  - Remove the `<div>` element that renders the model label in the header
  - Verify connection status indicators remain functional
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 2. Add portfolio history method to Alpaca client
  - [x] 2.1 Implement `get_portfolio_history()` method in `backend/core/alpaca_client.py`
    - Accept `timeframe` and `period` parameters
    - Map timeframe strings to Alpaca TimeFrame enums ("1Min", "1H", "1D")
    - Call Alpaca's `get_portfolio_history()` API
    - Handle API errors and return None on failure
    - Return list of portfolio data points with timestamps and equity values
    - _Requirements: 2.1, 2.2_

- [ ] 3. Update backend performance endpoint with real Alpaca data
  - [x] 3.1 Modify `/performance` endpoint in `backend/main.py`
    - Add `timeframe` query parameter (default: "1D")
    - Add `limit` query parameter (default: 100)
    - Call `alpaca_client.get_portfolio_history()` with timeframe
    - Transform portfolio history to OHLC format (open, high, low, close equity)
    - Calculate metrics (daily P/L, win rate, profit factor) for each data point
    - Return formatted performance data array
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [x] 3.2 Implement portfolio data transformation logic
    - Create helper function to convert Alpaca portfolio history to OHLC candlesticks
    - For each time period, calculate open (start), high (max), low (min), close (end) equity
    - Attach current trading metrics to each data point
    - Handle edge case of single data point
    - _Requirements: 2.2, 2.3_
  
  - [x] 3.3 Add fallback for unavailable portfolio history
    - If Alpaca API fails, return current equity as single data point
    - Include current timestamp and account metrics
    - Log appropriate error messages
    - _Requirements: 2.5_

- [ ] 4. Add timeframe selector to PerformanceChart component
  - [x] 4.1 Create timeframe selector UI
    - Add button group above chart with "1min", "1H", "1D" options
    - Style buttons with active/inactive states
    - Position selector in chart header area
    - _Requirements: 3.1, 3.6_
  
  - [x] 4.2 Implement timeframe state management
    - Add `selectedTimeframe` state (default: "1D")
    - Add click handlers for timeframe buttons
    - Highlight currently selected timeframe button
    - Call `onTimeframeChange` callback when timeframe changes
    - _Requirements: 3.1, 3.2, 3.5, 3.6_
  
  - [x] 4.3 Update PerformanceChart props interface
    - Add optional `onTimeframeChange` callback prop
    - Add optional `selectedTimeframe` prop
    - Maintain backward compatibility with existing usage
    - _Requirements: 3.7_

- [ ] 5. Integrate timeframe selection with data fetching
  - [x] 5.1 Update useBackendTrading hook
    - Add `timeframe` state variable (default: "1D")
    - Add `setTimeframe` function
    - Modify performance data fetch to include `timeframe` query parameter
    - Trigger data refetch when timeframe changes
    - Expose `timeframe` and `setTimeframe` in hook return value
    - _Requirements: 3.2, 3.3, 3.4_
  
  - [x] 5.2 Connect PerformanceChart to timeframe state
    - Pass `timeframe` and `setTimeframe` from useBackendTrading to PerformanceChart
    - Wire up `onTimeframeChange` callback to update timeframe state
    - Verify chart updates when timeframe changes
    - _Requirements: 3.2, 3.7_
  
  - [x] 5.3 Update Dashboard component
    - Pass timeframe props from TradingContext to PerformanceChart
    - Ensure proper data flow from hook to component
    - _Requirements: 3.7_
