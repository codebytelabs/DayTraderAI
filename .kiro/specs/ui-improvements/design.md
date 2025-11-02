# Design Document

## Overview

This design addresses two UI improvements for the DayTraderAI application:
1. Simplifying the header by removing AI model configuration displays (since the backend manages model selection)
2. Implementing a real portfolio equity curve chart with Alpaca data and multiple timeframe support

The changes involve modifications to the Header component, PerformanceChart component, backend performance endpoint, and the Alpaca client integration.

## Architecture

### Component Architecture

```
Frontend:
  Header.tsx (modified)
    - Remove model display logic
    - Keep connection status indicators
  
  PerformanceChart.tsx (modified)
    - Add timeframe selector UI
    - Handle timeframe state
    - Request data based on selected timeframe
  
  useBackendTrading.ts (modified)
    - Accept timeframe parameter for performance data
    - Pass timeframe to API request

Backend:
  main.py (modified)
    - Update /performance endpoint to accept timeframe parameter
    - Integrate with Alpaca portfolio history API
    - Transform Alpaca data to OHLC format
  
  core/alpaca_client.py (modified)
    - Add method to fetch portfolio history
    - Support different timeframes (1Min, 1Hour, 1Day)
```

### Data Flow

1. User selects timeframe in PerformanceChart component
2. Frontend calls `/performance?timeframe=1D` endpoint
3. Backend fetches portfolio history from Alpaca API
4. Backend aggregates data into OHLC candlesticks
5. Backend returns formatted performance data
6. Frontend renders candlestick chart with new data

## Components and Interfaces

### Frontend Changes

#### Header Component

**Modifications:**
- Remove `activeProviderLabel` computed value
- Remove the `<div>` that displays the model label
- Keep all connection status indicators unchanged
- Maintain Settings button functionality

**Interface:** No interface changes needed

#### PerformanceChart Component

**New Props:**
```typescript
interface PerformanceChartProps {
  data: PerformanceDataPoint[];
  onTimeframeChange?: (timeframe: string) => void;
  selectedTimeframe?: string;
}
```

**UI Elements:**
- Add timeframe selector buttons above the chart
- Buttons: "1min", "1H", "1D"
- Highlight selected timeframe
- Default to "1D"

#### useBackendTrading Hook

**Modifications:**
- Add `timeframe` state variable (default: "1D")
- Add `setTimeframe` function
- Modify performance data fetch to include timeframe parameter
- Expose `timeframe` and `setTimeframe` in return value

**New Interface:**
```typescript
interface BackendTradingData {
  // ... existing fields
  timeframe: string;
  setTimeframe: (timeframe: string) => void;
}
```

### Backend Changes

#### Performance Endpoint

**Updated Signature:**
```python
@app.get("/performance")
async def get_performance_history(
    timeframe: str = "1D",  # "1Min", "1H", "1D"
    limit: int = 100
):
```

**Logic:**
1. Map timeframe string to Alpaca TimeFrame enum
2. Call `alpaca_client.get_portfolio_history(timeframe, limit)`
3. Transform portfolio history to OHLC format
4. Calculate metrics for each data point
5. Return formatted data

**Response Format:**
```python
[
  {
    "timestamp": "2025-11-02T10:00:00Z",
    "equity": 100000.0,
    "daily_pl": 500.0,
    "daily_pl_pct": 0.5,
    "win_rate": 0.65,
    "profit_factor": 1.8,
    "wins": 10,
    "losses": 5
  },
  ...
]
```

#### Alpaca Client

**New Method:**
```python
def get_portfolio_history(
    self,
    timeframe: str = "1D",
    period: str = "1M"
) -> Optional[List[Dict]]:
    """
    Fetch portfolio equity history from Alpaca.
    
    Args:
        timeframe: "1Min", "1H", or "1D"
        period: Time period (e.g., "1M" for 1 month, "1W" for 1 week)
    
    Returns:
        List of portfolio history data points with timestamp and equity
    """
```

**Implementation:**
- Use Alpaca's `get_portfolio_history()` API
- Map timeframe to Alpaca's timeframe format
- Handle API errors gracefully
- Return None if data unavailable

## Data Models

### PerformanceDataPoint (Frontend)

No changes needed - existing interface already supports OHLC:

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

### Portfolio History Transformation

Backend transforms Alpaca portfolio history to OHLC format:

```python
def transform_portfolio_to_ohlc(
    portfolio_data: List[Dict],
    current_metrics: Dict
) -> List[Dict]:
    """
    Transform Alpaca portfolio history to OHLC candlestick format.
    
    For each time period:
    - open: equity at period start
    - high: max equity during period
    - low: min equity during period
    - close: equity at period end
    """
```

## Error Handling

### Frontend

1. **Timeframe Selection Errors:**
   - If API request fails, keep displaying previous data
   - Show error message in console
   - Revert to previous timeframe selection

2. **Empty Data:**
   - Display "No data available" message in chart area
   - Maintain chart structure

### Backend

1. **Alpaca API Unavailable:**
   - Log error
   - Return current equity as single data point
   - Include error flag in response

2. **Invalid Timeframe:**
   - Default to "1D" if invalid timeframe provided
   - Log warning

3. **No Portfolio History:**
   - Return current account metrics as single point
   - Set appropriate timestamp

## Testing Strategy

### Frontend Testing

1. **Header Component:**
   - Verify model label is not rendered
   - Verify connection statuses still display
   - Verify Settings button works

2. **PerformanceChart Component:**
   - Test timeframe button clicks
   - Verify selected timeframe is highlighted
   - Test chart updates when data changes
   - Test with empty data
   - Test with single data point

3. **Integration:**
   - Test timeframe changes trigger API calls
   - Verify correct timeframe parameter sent to backend
   - Test data refresh on timeframe change

### Backend Testing

1. **Performance Endpoint:**
   - Test with each timeframe ("1Min", "1H", "1D")
   - Test with invalid timeframe
   - Test with Alpaca API unavailable
   - Test response format matches expected schema

2. **Alpaca Client:**
   - Test portfolio history fetch
   - Test timeframe mapping
   - Test error handling
   - Mock Alpaca API responses

3. **Data Transformation:**
   - Test OHLC calculation from portfolio data
   - Test metrics calculation
   - Test edge cases (single point, empty data)

### Manual Testing

1. Load application and verify header shows no model info
2. Verify default chart shows 1D timeframe
3. Click each timeframe button and verify:
   - Chart updates with appropriate data
   - Selected button is highlighted
   - Data granularity matches timeframe
4. Test during market hours and after hours
5. Test with paper trading account

## Implementation Notes

### Alpaca Portfolio History API

Alpaca provides portfolio history via:
```python
api.get_portfolio_history(
    period="1M",
    timeframe="1D",
    extended_hours=False
)
```

Returns:
- `timestamp`: List of timestamps
- `equity`: List of equity values
- `profit_loss`: List of P/L values
- `profit_loss_pct`: List of P/L percentages

### Timeframe Mapping

```python
TIMEFRAME_MAP = {
    "1Min": "1Min",
    "1H": "1H", 
    "1D": "1D"
}

PERIOD_MAP = {
    "1Min": "1D",  # Last day of minute data
    "1H": "1W",    # Last week of hourly data
    "1D": "1M"     # Last month of daily data
}
```

### Performance Considerations

1. **Caching:** Consider caching portfolio history data for 1-5 minutes to reduce API calls
2. **Limit Data Points:** Cap at 100-200 points to keep chart responsive
3. **Lazy Loading:** Only fetch data when timeframe is selected
4. **Debouncing:** Prevent rapid timeframe switching from overwhelming API

## Design Decisions

### Why Remove Model Display from Header?

- Backend manages AI model selection via configuration
- Users configure models in Settings drawer
- Header should focus on system health monitoring
- Reduces visual clutter
- Model info is not actionable from header

### Why Use Alpaca Portfolio History?

- Provides accurate, real account equity data
- Eliminates synthetic/mock data
- Matches what users see in Alpaca dashboard
- Supports multiple timeframes natively
- More reliable than calculating from trade history

### Why These Specific Timeframes?

- **1Min:** Intraday monitoring for active trading
- **1H:** Medium-term pattern analysis
- **1D:** Long-term performance trends
- Matches common trading analysis intervals
- Supported by Alpaca API

### Fallback Strategy

If Alpaca portfolio history is unavailable:
1. Use current account equity as single point
2. Display message: "Limited data available"
3. Still show current metrics
4. Graceful degradation maintains functionality
