# Design Document

## Overview

The Regime-Adaptive Strategy system dynamically adjusts trading parameters based on real-time market sentiment as measured by the Fear & Greed Index. The system classifies market conditions into five distinct regimes (Extreme Fear, Fear, Neutral, Greed, Extreme Greed) and automatically adapts profit targets, position sizing, partial profit levels, and trailing stops to optimize performance in each regime.

This design addresses the core issue identified in the strategy analysis: fixed 2R profit targets were causing the bot to exit positions too early during strong trending markets (extreme fear/greed), leaving significant profits on the table. By adapting parameters to match expected market behavior in each regime, the system can capture larger moves while maintaining appropriate risk management.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Trading Engine                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Regime Manager                          │   │
│  │  - Fetches Fear & Greed Index                       │   │
│  │  - Classifies Market Regime                         │   │
│  │  - Provides Regime Parameters                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Regime-Aware Components                      │   │
│  │  ┌────────────────┐  ┌────────────────┐             │   │
│  │  │ Position Sizer │  │ Profit Taker   │             │   │
│  │  │ - Confidence   │  │ - Partial      │             │   │
│  │  │ - Regime Mult  │  │   Profits      │             │   │
│  │  └────────────────┘  └────────────────┘             │   │
│  │  ┌────────────────┐  ┌────────────────┐             │   │
│  │  │ Trailing Stops │  │ Risk Manager   │             │   │
│  │  │ - Adaptive     │  │ - Stop Loss    │             │   │
│  │  │   Distance     │  │   Validation   │             │   │
│  │  └────────────────┘  └────────────────┘             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
1. Trading Engine initializes → Creates RegimeManager
2. RegimeManager fetches Fear & Greed Index (cached 1 hour)
3. Index value classified into MarketRegime enum
4. Regime parameters retrieved from lookup table
5. Parameters passed to trading components:
   - Strategy: Uses profit_target_r for exit planning
   - Position Sizer: Uses position_size_mult for sizing
   - Profit Taker: Uses partial_profit_1_r, partial_profit_2_r
   - Trailing Stop Manager: Uses trailing_stop_r
6. Components log regime context in all decisions
```

## Components and Interfaces

### 1. RegimeManager

**Purpose**: Central authority for market regime detection and parameter management.

**Key Methods**:
```python
class RegimeManager:
    async def update_regime() -> MarketRegime:
        """Fetches latest F&G index and updates regime classification"""
        
    def get_current_regime() -> MarketRegime:
        """Returns currently cached regime"""
        
    def get_params(regime: Optional[MarketRegime] = None) -> Dict[str, Any]:
        """Returns trading parameters for specified or current regime"""
        
    def get_current_index_value() -> int:
        """Returns cached F&G index value"""
```

**Regime Classification Logic**:
- 0-20: EXTREME_FEAR
- 21-40: FEAR
- 41-60: NEUTRAL
- 61-80: GREED
- 81-100: EXTREME_GREED

**Caching Strategy**:
- TTL: 1 hour (configurable)
- On fetch failure: Maintains last known regime
- On first failure: Defaults to NEUTRAL

### 2. Strategy Module Integration

**Changes**:
- Accepts `regime_params` in signal generation
- Uses `profit_target_r` from regime params instead of fixed 2R
- Logs regime context with every trade decision

**Interface**:
```python
def generate_signal(symbol, features, regime_params):
    # Use regime_params['profit_target_r'] for target calculation
    # Log: f"Regime: {regime}, Target: {target_r}R"
```

### 3. Position Sizer Integration

**Changes**:
- Accepts `regime_data` parameter
- Applies `position_size_mult` for high-confidence trades in extreme regimes
- Includes regime in sizing reasoning

**Logic**:
```python
if confidence > 70 and regime in [EXTREME_FEAR, EXTREME_GREED]:
    base_size *= regime_params['position_size_mult']  # 1.5x
```

### 4. Profit Taker Integration

**Changes**:
- Accepts `regime_params` parameter
- Uses `partial_profit_1_r` and `partial_profit_2_r` from regime
- Adapts partial profit levels dynamically

**Example**:
- Neutral: Take 50% at 2R, 25% at 3R
- Extreme Fear: Take 50% at 3R, 25% at 5R

### 5. Trailing Stop Manager Integration

**Changes**:
- Accepts `regime_params` parameter
- Uses `trailing_stop_r` for distance calculation
- Wider stops in extreme regimes, tighter in neutral

**Calculation**:
```python
distance = risk_amount * regime_params['trailing_stop_r']
trailing_stop = current_price - distance  # for longs
```

## Data Models

### MarketRegime Enum
```python
class MarketRegime(Enum):
    EXTREME_FEAR = "extreme_fear"
    FEAR = "fear"
    NEUTRAL = "neutral"
    GREED = "greed"
    EXTREME_GREED = "extreme_greed"
```

### Regime Parameters Dictionary
```python
{
    "profit_target_r": float,        # Main profit target in R-multiples
    "partial_profit_1_r": float,     # First partial profit level
    "partial_profit_2_r": float,     # Second partial profit level
    "trailing_stop_r": float,        # Trailing stop distance in R
    "position_size_mult": float,     # Position size multiplier
    "description": str               # Human-readable description
}
```

### Regime Parameter Lookup Table

| Regime | Profit Target | Partial 1 | Partial 2 | Trailing Stop | Pos Size Mult | Rationale |
|--------|--------------|-----------|-----------|---------------|---------------|-----------|
| Extreme Fear | 4.0R | 3.0R | 5.0R | 1.5R | 1.5x | Large directional moves expected |
| Fear | 3.0R | 2.5R | 4.0R | 1.0R | 1.0x | Elevated volatility |
| Neutral | 2.0R | 2.0R | 3.0R | 0.75R | 1.0x | Normal conditions |
| Greed | 2.5R | 2.0R | 3.5R | 1.0R | 1.0x | Strong trends possible |
| Extreme Greed | 3.0R | 2.5R | 4.5R | 1.5R | 1.5x | Parabolic moves possible |

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Regime Classification Consistency
*For any* Fear & Greed Index value between 0-100, the RegimeManager SHALL classify it into exactly one of the five market regimes according to the defined boundaries.
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

### Property 2: Parameter Retrieval Completeness
*For any* market regime, the RegimeManager SHALL return a complete parameter dictionary containing all required fields (profit_target_r, partial_profit_1_r, partial_profit_2_r, trailing_stop_r, position_size_mult).
**Validates: Requirements 1.1-1.5, 3.1-3.5, 4.2-4.4**

### Property 3: Profit Target Adaptation
*For any* trade signal, the profit target SHALL be set according to the current market regime, with extreme regimes using wider targets (3R-4R) than neutral conditions (2R).
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

### Property 4: Position Size Scaling
*For any* trade signal with confidence above 70% in extreme fear or extreme greed regimes, the position size SHALL be increased by the regime multiplier (1.5x) while respecting maximum portfolio limits.
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 5: Partial Profit Regime Adaptation
*For any* open position, the partial profit levels SHALL match the current regime parameters, with extreme regimes taking first partials at higher R-multiples (3R+) than neutral conditions (2R).
**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

### Property 6: Trailing Stop Distance Adaptation
*For any* position with activated trailing stop, the stop distance SHALL be calculated using the regime-specific trailing_stop_r value, with extreme regimes using wider distances (1.5R) than neutral (0.75R).
**Validates: Requirements 4.2, 4.3, 4.4**

### Property 7: Cache Freshness Validation
*For any* regime parameter request, if the cached Fear & Greed Index is older than 1 hour, the system SHALL attempt to fetch a fresh value before returning parameters.
**Validates: Requirements 10.5**

### Property 8: Parameter Validation Bounds
*For any* regime parameters, the profit targets SHALL be between 1.5R and 10R, stop losses between 0.3% and 2%, and position sizes not exceeding 2.5% of capital.
**Validates: Requirements 10.1, 10.2, 10.3**

### Property 9: Logging Completeness
*For any* trade entry, the system SHALL log the current regime, confidence score, position size, and all target levels (profit target, partial levels, trailing stop distance).
**Validates: Requirements 9.1, 9.2, 9.4**

### Property 10: Regime Transition Isolation
*For any* regime change, new parameters SHALL apply only to new trades, and existing positions SHALL maintain their original parameters until closed.
**Validates: Requirements 8.5**

## Error Handling

### 1. Fear & Greed Index Fetch Failures

**Scenario**: API unavailable, network timeout, invalid response

**Handling**:
- Log warning with error details
- Maintain last known regime if cache exists
- Default to NEUTRAL regime if no cache (first fetch failure)
- Retry on next update cycle (1 hour)

**Code**:
```python
try:
    result = self.scraper.get_fear_greed_index()
    if result and 'value' in result:
        # Update regime
    else:
        logger.warning("Invalid F&G response, keeping previous regime")
except Exception as e:
    logger.error(f"F&G fetch failed: {e}")
    if self._last_update == datetime.min:
        self._current_regime = MarketRegime.NEUTRAL
```

### 2. Invalid Parameter Values

**Scenario**: Regime params outside safe bounds

**Handling**:
- Validate all parameters before use
- Clamp to safe ranges if out of bounds
- Log error with original and clamped values
- Use NEUTRAL regime params as fallback

**Validation Rules**:
- Profit targets: 1.5R ≤ target ≤ 10R
- Stop losses: 0.3% ≤ stop ≤ 2%
- Position sizes: size ≤ 2.5% of capital
- Trailing stops: 0.5R ≤ distance ≤ 2R

### 3. Regime Classification Edge Cases

**Scenario**: Index value exactly on boundary (e.g., 20, 40, 60, 80)

**Handling**:
- Use inclusive lower bound logic
- 20 → EXTREME_FEAR (≤ 20)
- 21 → FEAR (21-40)
- Clear documentation of boundary behavior

### 4. Concurrent Regime Updates

**Scenario**: Multiple components requesting regime update simultaneously

**Handling**:
- Cache with TTL prevents excessive API calls
- Thread-safe access to cached values
- Async update method with proper locking if needed

## Testing Strategy

### Unit Tests

**Core Functionality**:
1. Regime classification for all boundary values (0, 20, 21, 40, 41, 60, 61, 80, 81, 100)
2. Parameter retrieval for each regime
3. Cache TTL behavior
4. Error handling for fetch failures
5. Default regime on first failure

**Integration Points**:
1. Strategy module receives correct profit targets
2. Position sizer applies regime multipliers correctly
3. Profit taker uses regime-specific partial levels
4. Trailing stop manager calculates regime-aware distances
5. Logging includes regime context

**Edge Cases**:
1. Boundary value classification (exactly 20, 40, 60, 80)
2. Invalid index values (< 0, > 100)
3. Missing parameter fields
4. Stale cache behavior
5. Rapid regime transitions

### Property-Based Tests

Property-based testing will use Python's `hypothesis` library to generate random test cases and verify universal properties.

**Test Configuration**:
- Minimum 100 iterations per property
- Random seed for reproducibility
- Shrinking enabled for minimal failing examples

**Property Test 1: Classification Consistency**
```python
@given(index_value=st.integers(min_value=0, max_value=100))
def test_classification_consistency(index_value):
    """For any F&G index value, classification should be deterministic and valid"""
    manager = RegimeManager()
    regime = manager._classify_regime(index_value)
    assert regime in MarketRegime
    # Verify boundaries
    if index_value <= 20:
        assert regime == MarketRegime.EXTREME_FEAR
    elif index_value <= 40:
        assert regime == MarketRegime.FEAR
    # ... etc
```
**Feature: regime-adaptive-strategy, Property 1: Regime Classification Consistency**

**Property Test 2: Parameter Completeness**
```python
@given(regime=st.sampled_from(MarketRegime))
def test_parameter_completeness(regime):
    """For any regime, all required parameters should be present"""
    manager = RegimeManager()
    params = manager.get_params(regime)
    required_keys = ['profit_target_r', 'partial_profit_1_r', 
                     'partial_profit_2_r', 'trailing_stop_r', 
                     'position_size_mult']
    for key in required_keys:
        assert key in params
        assert isinstance(params[key], (int, float))
        assert params[key] > 0
```
**Feature: regime-adaptive-strategy, Property 2: Parameter Retrieval Completeness**

**Property Test 3: Profit Target Ordering**
```python
@given(regime=st.sampled_from(MarketRegime))
def test_profit_target_ordering(regime):
    """For any regime, partial profit levels should be ordered correctly"""
    manager = RegimeManager()
    params = manager.get_params(regime)
    assert params['partial_profit_1_r'] < params['partial_profit_2_r']
    assert params['partial_profit_1_r'] <= params['profit_target_r']
```
**Feature: regime-adaptive-strategy, Property 3: Profit Target Adaptation**

**Property Test 4: Position Size Bounds**
```python
@given(
    confidence=st.floats(min_value=0, max_value=100),
    regime=st.sampled_from(MarketRegime),
    base_size=st.floats(min_value=0.001, max_value=0.025)
)
def test_position_size_bounds(confidence, regime, base_size):
    """For any confidence and regime, position size should respect limits"""
    manager = RegimeManager()
    params = manager.get_params(regime)
    
    multiplier = 1.0
    if confidence > 70 and regime in [MarketRegime.EXTREME_FEAR, MarketRegime.EXTREME_GREED]:
        multiplier = params['position_size_mult']
    
    final_size = base_size * multiplier
    assert final_size <= 0.025  # 2.5% max
```
**Feature: regime-adaptive-strategy, Property 4: Position Size Scaling**

**Property Test 5: Trailing Stop Distance**
```python
@given(
    entry=st.floats(min_value=10, max_value=1000),
    stop=st.floats(min_value=9, max_value=999),
    current=st.floats(min_value=11, max_value=1001),
    regime=st.sampled_from(MarketRegime)
)
def test_trailing_stop_distance(entry, stop, current, regime):
    """For any price levels and regime, trailing stop should maintain correct distance"""
    assume(stop < entry < current)  # Valid long position
    
    manager = RegimeManager()
    params = manager.get_params(regime)
    
    risk = entry - stop
    expected_distance = risk * params['trailing_stop_r']
    expected_stop = current - expected_distance
    
    # Verify stop is below current price
    assert expected_stop < current
    # Verify stop is above entry (in profit)
    assert expected_stop > entry
```
**Feature: regime-adaptive-strategy, Property 6: Trailing Stop Distance Adaptation**

### Integration Tests

**End-to-End Scenarios**:
1. Full trade lifecycle in each regime
2. Regime transition during open position
3. Multiple positions across different regimes
4. Cache expiration and refresh
5. Error recovery and fallback behavior

**Performance Tests**:
1. Regime update latency
2. Parameter lookup performance
3. Memory usage with long-running cache
4. Concurrent access patterns

## Implementation Notes

### Dependencies

- `indicators.fear_greed_scraper.FearGreedScraper`: Existing component for fetching F&G index
- `trading.strategy.Strategy`: Modified to accept regime params
- `trading.position_manager.PositionManager`: Modified to pass regime params to sub-components
- `utils.dynamic_position_sizer.DynamicPositionSizer`: Modified to apply regime multipliers
- `trading.trailing_stops.TrailingStopManager`: Modified to use regime-aware distances
- `trading.profit_taker.ProfitTaker`: Modified to use regime-specific partial levels

### Configuration

New config values in `backend/config.py`:
```python
# Regime Manager Settings
REGIME_CACHE_TTL_HOURS = 1
REGIME_DEFAULT_ON_ERROR = "neutral"
REGIME_ENABLE_LOGGING = True

# Regime-Specific Overrides (optional)
REGIME_PROFIT_TARGET_OVERRIDE = None  # Override specific regime params if needed
```

### Logging Strategy

All regime-related decisions logged at INFO level:
- Regime updates: `"Market Regime Updated: EXTREME_FEAR (Index: 15)"`
- Trade entries: `"Trade Entry: AAPL | Regime: EXTREME_FEAR | Target: 4.0R | Size: 1.5x"`
- Partial profits: `"Partial Profit: AAPL | Regime: FEAR | Level: 2.5R | Remaining: 50%"`
- Trailing stops: `"Trailing Stop: AAPL | Regime: NEUTRAL | Distance: 0.75R"`

### Performance Considerations

- Cache TTL of 1 hour minimizes API calls
- Regime classification is O(1) lookup
- Parameter retrieval is O(1) dictionary access
- No database queries required for regime operations
- Minimal memory footprint (single cached regime + params)

### Backward Compatibility

- Existing code without regime params continues to work
- Default behavior: Uses NEUTRAL regime parameters
- Gradual rollout: Components can adopt regime awareness incrementally
- No breaking changes to existing interfaces
