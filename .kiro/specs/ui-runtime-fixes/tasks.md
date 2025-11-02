# Implementation Plan

- [x] 1. Add debugging and verify data flow

  - Add console logging to `useBackendTrading` hook to trace API responses and data transformations
  - Add logging to `TradingContext` to verify data is passed to components
  - Verify backend API responses in browser Network tab
  - Check React DevTools to inspect context values reaching components
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 2. Fix MarkdownRenderer component

  - [ ] 2.1 Enhance markdown pattern support

    - Improve regex patterns for bold, italic, and inline code to handle edge cases
    - Add support for blockquotes, horizontal rules, and nested lists
    - Add proper HTML escaping to prevent XSS vulnerabilities
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ] 2.2 Test markdown rendering with copilot responses
    - Test with actual copilot response patterns from chat endpoint
    - Verify headers, lists, bold text, code blocks, and links render correctly
    - Test edge cases: nested formatting, escaped characters, mixed content
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 3. Fix Portfolio Equity Curve display

  - [x] 3.1 Add loading and error states to PerformanceChart

    - Add loading indicator while fetching portfolio data
    - Add error boundary to catch chart rendering failures
    - Show fallback message when no data is available
    - _Requirements: 2.1, 2.4_

  - [x] 3.2 Fix chart domain calculation and data handling

    - Ensure chart domain calculation handles single data point
    - Verify data transformation from backend format to chart format
    - Add validation to filter out invalid data points
    - Test with actual 23-point dataset from backend
    - _Requirements: 2.2, 2.3, 2.5_

  - [x] 3.3 Verify timeframe switching functionality
    - Ensure timeframe change triggers data refetch
    - Verify chart updates with new data
    - Test all timeframes: 1Min, 1H, 1D
    - _Requirements: 2.3_

- [x] 4. Fix Trade Analysis panel

  - [x] 4.1 Verify data transformation and flow

    - Check `transformTradeAnalyses` function in `useBackendTrading`
    - Verify analyses data reaches `TradeAnalysisLog` component
    - Add console logging to trace data flow
    - _Requirements: 3.1, 3.2_

  - [x] 4.2 Ensure component renders with data
    - Verify component re-renders when `tradeAnalyses` prop changes
    - Test with actual backend data (analyses endpoint)
    - Ensure proper display of symbol, side, timestamp, rationale, and metrics
    - _Requirements: 3.2, 3.3, 3.4, 3.5_

- [x] 5. Fix Live Logs panel

  - [x] 5.1 Verify LogFeed component exists and is rendered

    - Check if `LogFeed` component is imported and rendered in Dashboard
    - Verify component receives `logs` prop from context
    - Add console logging to trace log data flow
    - _Requirements: 4.1, 4.2_

  - [x] 5.2 Ensure logs display correctly
    - Verify `transformLogs` function in `useBackendTrading`
    - Test with actual backend data (logs endpoint)
    - Ensure proper display of timestamps, levels, and messages
    - Verify color-coding based on log level
    - _Requirements: 4.2, 4.3, 4.4, 4.5_

- [ ] 6. Improve WebSocket connection stability

  - [ ] 6.1 Add connection state tracking

    - Track WebSocket connection state (connecting, connected, error, disconnected)
    - Display connection status indicator in UI
    - Add logging for connection events
    - _Requirements: 5.1, 5.5_

  - [ ] 6.2 Implement robust reconnection logic
    - Add exponential backoff for reconnection attempts
    - Handle large snapshot payloads without disconnecting
    - Ensure graceful fallback to HTTP polling on repeated failures
    - _Requirements: 5.2, 5.3, 5.4_

- [ ] 7. Manual testing and verification
  - Test all three issues are resolved: markdown rendering, portfolio chart, and empty panels
  - Verify data flows correctly from backend to all components
  - Test WebSocket stability with multiple reconnections
  - Verify timeframe switching works correctly
  - Test copilot chat with various markdown patterns
  - _Requirements: 1.1-1.5, 2.1-2.5, 3.1-3.5, 4.1-4.5, 5.1-5.5_
