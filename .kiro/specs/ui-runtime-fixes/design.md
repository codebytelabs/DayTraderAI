# Design Document

## Overview

This design addresses three frontend rendering issues in the DayTraderAI application. The backend is confirmed to be running and serving data correctly (portfolio history, positions, orders, logs, advisories, analyses), but the frontend components are not properly displaying this data. The root causes are:

1. **MarkdownRenderer** - Exists but may have rendering issues with certain markdown patterns
2. **Portfolio Equity Curve** - Data is being fetched (23 points) but chart may not be rendering correctly
3. **Trade Analysis & Live Logs** - Data is available from backend but panels show as empty

## Architecture

### Component Hierarchy

```
App
└── TradingProvider (state/TradingContext.tsx)
    └── Dashboard (components/Dashboard.tsx)
        ├── PerformanceChart (components/PerformanceChart.tsx)
        ├── TradeAnalysisLog (components/TradeAnalysisLog.tsx)
        ├── LogFeed (components/LogFeed.tsx)
        └── ChatPanel (components/ChatPanel.tsx)
            └── MarkdownRenderer (components/MarkdownRenderer.tsx)
```

### Data Flow

```
Backend API (port 8006)
    ↓
useBackendTrading hook (hooks/useBackendTrading.ts)
    ↓
TradingContext (state/TradingContext.tsx)
    ↓
Dashboard Components
```

## Components and Interfaces

### 1. MarkdownRenderer Enhancement

**Current Implementation:**
- Located at `components/MarkdownRenderer.tsx`
- Uses `dangerouslySetInnerHTML` for inline rendering
- Handles basic markdown: headers, lists, bold, italic, code, links

**Issues:**
- May not handle all markdown patterns from copilot responses
- Inline rendering with regex replacement can miss edge cases
- No support for tables, blockquotes, or horizontal rules

**Design Solution:**
- Add support for additional markdown patterns
- Improve regex patterns to handle edge cases (nested formatting, escaped characters)
- Add proper escaping to prevent XSS vulnerabilities
- Test with actual copilot response patterns

**Interface:**
```typescript
interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps>
```

### 2. Portfolio Equity Curve Fix

**Current Implementation:**
- `PerformanceChart` component receives data from `useBackendTrading`
- Backend logs show 23 portfolio history points being fetched
- Chart uses Recharts library with candlestick visualization

**Issues:**
- Data may be empty on initial render
- Chart domain calculation may fail with insufficient data
- Timeframe switching may not trigger re-fetch

**Design Solution:**
- Add loading state while fetching portfolio data
- Provide fallback single-point data when history is unavailable
- Ensure chart domain calculation handles edge cases (single point, all same values)
- Add error boundary for chart rendering failures
- Verify data transformation from backend format to chart format

**Data Model:**
```typescript
interface PerformanceDataPoint {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  pnl: number;
  winRate: number;
  profitFactor: number;
  wins: number;
  losses: number;
}
```

### 3. Trade Analysis Panel Population

**Current Implementation:**
- `TradeAnalysisLog` component receives `tradeAnalyses` array from context
- Backend `/analyses?limit=50` endpoint returns data
- Component shows "Awaiting first trade signal" when empty

**Issues:**
- Data may not be reaching component despite backend serving it
- Array transformation in `useBackendTrading` may have issues
- Component may not be re-rendering when data updates

**Design Solution:**
- Add console logging to trace data flow from API → hook → context → component
- Verify `transformTradeAnalyses` function correctly maps backend response
- Ensure component re-renders when `tradeAnalyses` prop changes
- Add loading state to distinguish between "no data yet" and "loading"

**Data Model:**
```typescript
interface TradeAnalysis {
  id: string;
  timestamp: string;
  symbol: string;
  side: OrderSide;
  action?: string;
  analysis: string;
  pnl?: number;
  pnlPct?: number;
  source?: string;
  entryPrice?: number;
  takeProfit?: number;
  stopLoss?: number;
}
```

### 4. Live Logs Panel Population

**Current Implementation:**
- `LogFeed` component receives `logs` array from context
- Backend `/logs?limit=100` endpoint returns data
- WebSocket streams new logs in real-time

**Issues:**
- Similar to Trade Analysis - data not reaching component
- WebSocket disconnections may prevent real-time updates
- Component may not exist or may not be visible in UI

**Design Solution:**
- Verify `LogFeed` component exists and is rendered in Dashboard
- Add console logging to trace log data flow
- Verify `transformLogs` function correctly maps backend response
- Ensure component handles both initial HTTP fetch and WebSocket updates
- Add visual indicator when logs are being received

**Data Model:**
```typescript
interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  source: string;
}
```

## Error Handling

### MarkdownRenderer
- **Invalid markdown syntax**: Render as plain text
- **XSS attempts**: Sanitize HTML before rendering
- **Rendering errors**: Catch with error boundary, show plain text fallback

### PerformanceChart
- **No data**: Show message "No performance data available yet"
- **Invalid data**: Filter out invalid points, show warning
- **Chart rendering error**: Error boundary with fallback message

### TradeAnalysisLog
- **Empty array**: Show "Awaiting first trade signal for AI analysis..."
- **Invalid analysis data**: Skip invalid entries, log warning
- **Rendering error**: Error boundary with fallback

### LogFeed
- **Empty array**: Show "No logs available yet"
- **WebSocket disconnection**: Show status indicator, fall back to polling
- **Invalid log data**: Skip invalid entries, log warning

## Testing Strategy

### Unit Tests
- MarkdownRenderer: Test various markdown patterns
- Data transformations: Test `transformTradeAnalyses`, `transformLogs`
- Chart data building: Test `buildPerformanceData` with edge cases

### Integration Tests
- Full data flow: API → hook → context → component
- WebSocket handling: Connection, disconnection, reconnection
- Timeframe switching: Verify data refetch and chart update

### Manual Testing
1. Start backend, verify logs show data being served
2. Start frontend, open browser console
3. Check Network tab for API calls and responses
4. Verify data appears in React DevTools context
5. Verify components render with data
6. Test markdown rendering with various copilot responses
7. Test chart with different timeframes
8. Verify logs and analyses appear in panels

## Implementation Notes

### Debugging Approach
1. Add `console.log` statements at each data transformation point
2. Use React DevTools to inspect context values
3. Use Network tab to verify API responses
4. Check browser console for rendering errors

### Key Files to Modify
- `components/MarkdownRenderer.tsx` - Enhance markdown support
- `components/PerformanceChart.tsx` - Add loading states, fix domain calculation
- `components/TradeAnalysisLog.tsx` - Add debugging, verify data flow
- `components/LogFeed.tsx` - Verify component exists and renders
- `hooks/useBackendTrading.ts` - Add logging to data transformations

### WebSocket Stability
The backend logs show WebSocket disconnections with `IncompleteReadError`. This suggests:
- Large snapshot payloads may be causing issues
- Frontend may be closing connection prematurely
- Need to handle connection errors gracefully

**Solution:**
- Add connection state tracking in frontend
- Implement exponential backoff for reconnection
- Add timeout handling for large messages
- Consider chunking large snapshots if needed

## Data Models

### Backend API Response Formats

**Performance History:**
```json
[
  {
    "timestamp": "2025-11-02T16:00:00Z",
    "equity": 133166.07,
    "daily_pl": 0.00,
    "win_rate": 0.0,
    "profit_factor": 0.0,
    "wins": 0,
    "losses": 0
  }
]
```

**Trade Analyses:**
```json
[
  {
    "id": "analysis-123",
    "timestamp": "2025-11-02T16:00:00Z",
    "symbol": "AAPL",
    "side": "buy",
    "action": "entry",
    "analysis": "Strong momentum with RSI confirmation",
    "pnl": 150.50,
    "pnl_pct": 2.5,
    "source": "OpenRouter",
    "entry_price": 175.00,
    "take_profit": 180.00,
    "stop_loss": 172.00
  }
]
```

**Logs:**
```json
[
  {
    "id": "log-456",
    "timestamp": "2025-11-02T16:00:00Z",
    "level": "info",
    "message": "Position opened: AAPL",
    "source": "trading_engine"
  }
]
```

## Success Criteria

1. **Markdown Rendering**: Copilot responses display with proper formatting (headers, lists, bold, code)
2. **Portfolio Chart**: Candlestick chart displays with 23 data points, updates on timeframe change
3. **Trade Analysis**: Panel shows recent analyses with symbol, side, rationale, and metrics
4. **Live Logs**: Panel shows recent logs with timestamps, levels, and messages
5. **WebSocket**: Stable connection with automatic reconnection on failure
