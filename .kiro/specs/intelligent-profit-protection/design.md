# Intelligent Profit Protection System - Design Document

## Overview

The Intelligent Profit Protection System replaces the current static stop-loss architecture with a dynamic, R-multiple based profit protection system. The current system has critical flaws where profitable positions (like RIG at +1.42R) have stop losses below entry prices, allowing winners to turn into losers. This design implements trailing stops, systematic profit taking, and intelligent order conflict resolution to ensure profits are protected and locked in.

### Current System Problems

1. **Static Stop Losses**: Stops remain at initial levels regardless of profit
2. **No Trailing**: Profitable positions don't have stops that move up with price
3. **Order Conflicts**: "Shares locked by SL" errors prevent take-profit orders
4. **Missing Profit Taking**: No systematic partial profit taking at milestones
5. **Poor Order Sequencing**: Bracket order recreation causes conflicts

### Design Goals

1. **Zero Profitable Losses**: No position with unrealized profit should ever close at a loss
2. **Systematic Protection**: Automatic trailing stops and profit taking without manual intervention
3. **Conflict-Free Operations**: Intelligent order sequencing prevents "shares locked" errors
4. **Real-Time Responsiveness**: Sub-second reaction to price movements
5. **Backward Compatible**: Works with existing positions immediately

## Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Trading Engine                            │
│  (Orchestrates all components, runs monitoring loops)        │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──────────────────────────────────────────────────┐
             │                                                  │
┌────────────▼──────────────┐                 ┌────────────────▼──────────────┐
│   Position State Tracker   │                 │  Intelligent Stop Manager     │
│  - Real-time R-multiple    │◄────────────────┤  - Dynamic trailing stops     │
│  - P/L calculation         │                 │  - Breakeven protection       │
│  - State machine           │                 │  - Conflict-free updates      │
└────────────┬───────────────┘                 └────────────────┬──────────────┘
             │                                                   │
             │                 ┌─────────────────────────────────┘
             │                 │
┌────────────▼─────────────────▼──────────────┐
│        Profit Taking Engine                  │
│  - Milestone detection (2R, 3R, 4R)         │
│  - Partial exit execution                    │
│  - Share allocation management               │
└────────────┬─────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────┐
│         Order Sequencer                       │
│  - Conflict detection & resolution           │
│  - Atomic operations                         │
│  - Rollback capability                       │
└────────────┬─────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────┐
│         Alpaca API Client                     │
│  - Order submission                          │
│  - Position queries                          │
│  - Order status tracking                     │
└──────────────────────────────────────────────┘
```

### Component Integration

The system integrates with existing components:

- **Position Manager**: Enhanced with intelligent protection calls
- **Trading Engine**: Adds profit protection monitoring loop
- **Stop Loss Protection**: Replaced with new dynamic system
- **Order Manager**: Enhanced with conflict resolution

## Components and Interfaces

### 1. Position State Tracker

**Purpose**: Maintain real-time state for all open positions including R-multiple, profit levels, and protection status.

**Interface**:
```python
class PositionStateTracker:
    def track_position(self, symbol: str, entry_price: float, 
                      stop_loss: float, quantity: int, side: str) -> PositionState
    
    def update_current_price(self, symbol: str, current_price: float) -> PositionState
    
    def get_r_multiple(self, symbol: str) -> float
    
    def get_protection_state(self, symbol: str) -> ProtectionState
    
    def remove_position(self, symbol: str) -> None
```

**State Machine**:
```
INITIAL_RISK (0-1R)
    ↓ (reaches 1.0R)
BREAKEVEN_PROTECTED (1-2R)
    ↓ (reaches 2.0R)
PARTIAL_PROFIT_TAKEN (2-3R)
    ↓ (reaches 3.0R)
ADVANCED_PROFIT_TAKEN (3-4R)
    ↓ (reaches 4.0R)
FINAL_PROFIT_TAKEN (4R+)
```

**Data Model**:
```python
@dataclass
class PositionState:
    symbol: str
    entry_price: float
    current_price: float
    stop_loss: float
    quantity: int
    side: str  # 'long' or 'short'
    r_multiple: float
    unrealized_pl: float
    unrealized_pl_pct: float
    protection_state: ProtectionState
    last_updated: datetime
    
@dataclass
class ProtectionState:
    state: str  # INITIAL_RISK, BREAKEVEN_PROTECTED, etc.
    stop_loss_price: float
    trailing_active: bool
    partial_profits_taken: List[PartialProfit]
    last_stop_update: datetime
```

### 2. Intelligent Stop Manager

**Purpose**: Dynamically adjust stop losses based on position profitability and market conditions.

**Interface**:
```python
class IntelligentStopManager:
    def update_stop_for_position(self, position_state: PositionState) -> StopUpdateResult
    
    def calculate_trailing_stop(self, entry: float, current: float, 
                                risk: float, r_multiple: float) -> float
    
    def move_to_breakeven(self, symbol: str) -> bool
    
    def cancel_and_replace_stop(self, symbol: str, new_stop: float) -> bool
```

**Trailing Stop Logic**:
```
At 1.0R: Move stop to breakeven (entry price)
At 1.5R: Trail at 0.5R below current (lock in 0.5R profit)
At 2.0R: Trail at 1.0R below current (lock in 1.0R profit)
At 3.0R: Trail at 1.5R below current (lock in 1.5R profit)
At 4.0R+: Trail at 2.0R below current (lock in 2.0R profit)
```

**Stop Update Algorithm**:
```python
def calculate_new_stop(entry, current, initial_risk, r_multiple):
    if r_multiple < 1.0:
        # Below breakeven - keep initial stop
        return entry - initial_risk
    elif r_multiple < 1.5:
        # At breakeven - move stop to entry
        return entry
    elif r_multiple < 2.0:
        # Trail at 0.5R
        return entry + (0.5 * initial_risk)
    elif r_multiple < 3.0:
        # Trail at 1.0R
        return entry + (1.0 * initial_risk)
    elif r_multiple < 4.0:
        # Trail at 1.5R
        return entry + (1.5 * initial_risk)
    else:
        # Trail at 2.0R
        return entry + (2.0 * initial_risk)
```

### 3. Profit Taking Engine

**Purpose**: Execute systematic partial profit taking at predefined R-multiple milestones.

**Interface**:
```python
class ProfitTakingEngine:
    def check_profit_milestones(self, position_state: PositionState) -> Optional[ProfitAction]
    
    def execute_partial_exit(self, symbol: str, quantity: int, 
                            reason: str) -> ExecutionResult
    
    def calculate_remaining_position(self, symbol: str) -> int
    
    def record_partial_profit(self, symbol: str, quantity: int, 
                             price: float, profit: float) -> None
```

**Profit Taking Schedule**:
```
2.0R: Sell 50% of position (lock in 1.0R profit on half)
3.0R: Sell 25% of original position (lock in 2.0R profit on quarter)
4.0R: Sell final 25% of original position (lock in 3.0R profit on quarter)
```

**Share Allocation Tracking**:
```python
@dataclass
class PartialProfit:
    r_multiple: float
    shares_sold: int
    price: float
    profit_amount: float
    timestamp: datetime
    
class ShareAllocation:
    original_quantity: int
    remaining_quantity: int
    partial_exits: List[PartialProfit]
    
    def calculate_next_exit_quantity(self, milestone: float) -> int:
        if milestone == 2.0:
            return int(self.original_quantity * 0.5)
        elif milestone == 3.0:
            return int(self.original_quantity * 0.25)
        elif milestone == 4.0:
            return self.remaining_quantity  # Close remaining
```

### 4. Order Sequencer

**Purpose**: Ensure all order modifications execute atomically without conflicts.

**Interface**:
```python
class OrderSequencer:
    def execute_stop_update(self, symbol: str, new_stop: float) -> SequenceResult
    
    def execute_partial_exit_with_stop_update(self, symbol: str, 
                                              exit_qty: int, 
                                              new_stop: float) -> SequenceResult
    
    def rollback_sequence(self, sequence_id: str) -> bool
    
    def detect_conflicts(self, symbol: str) -> List[OrderConflict]
```

**Order Sequence for Stop Update**:
```
1. Query current orders for symbol
2. If stop loss exists:
   a. Cancel existing stop loss order
   b. Wait for cancellation confirmation (max 2 seconds)
3. Submit new stop loss order
4. Verify new order is active
5. If verification fails, retry from step 1 (max 3 attempts)
```

**Order Sequence for Partial Exit + Stop Update**:
```
1. Query current orders for symbol
2. Cancel ALL exit orders (stop loss + take profit)
3. Wait for cancellations (max 2 seconds)
4. Submit market order for partial exit
5. Wait for fill confirmation (max 5 seconds)
6. Calculate new position size
7. Submit new stop loss for remaining position
8. Submit new take profit for remaining position
9. Verify all orders active
10. If any step fails, rollback and retry
```

**Conflict Detection**:
```python
class OrderConflict:
    conflict_type: str  # 'shares_locked', 'duplicate_order', 'invalid_price'
    symbol: str
    conflicting_orders: List[str]  # Order IDs
    resolution_strategy: str
    
def detect_shares_locked_conflict(symbol: str) -> bool:
    """
    Detect if shares are locked by existing orders.
    Returns True if total order quantity >= position quantity.
    """
    position = get_position(symbol)
    orders = get_open_orders(symbol)
    
    total_order_qty = sum(order.quantity for order in orders 
                         if order.side == 'sell')
    
    return total_order_qty >= position.quantity
```

## Data Models

### Position Tracking Table
```sql
CREATE TABLE position_states (
    symbol VARCHAR(10) PRIMARY KEY,
    entry_price DECIMAL(10, 2) NOT NULL,
    current_price DECIMAL(10, 2) NOT NULL,
    stop_loss DECIMAL(10, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    side VARCHAR(5) NOT NULL,
    r_multiple DECIMAL(10, 2) NOT NULL,
    unrealized_pl DECIMAL(10, 2) NOT NULL,
    protection_state VARCHAR(30) NOT NULL,
    trailing_active BOOLEAN DEFAULT FALSE,
    last_stop_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Partial Profits Table
```sql
CREATE TABLE partial_profits (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    r_multiple DECIMAL(10, 2) NOT NULL,
    shares_sold INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    profit_amount DECIMAL(10, 2) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (symbol) REFERENCES position_states(symbol)
);
```

### Stop Loss History Table
```sql
CREATE TABLE stop_loss_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    old_stop DECIMAL(10, 2),
    new_stop DECIMAL(10, 2) NOT NULL,
    r_multiple DECIMAL(10, 2) NOT NULL,
    reason VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Breakeven Protection Activation
*For any* position that reaches 1.0R profit, the stop loss must be moved to the entry price (breakeven), ensuring the position can no longer result in a loss.
**Validates: Requirements 1.1, 5.2**

### Property 2: Trailing Stop Monotonicity
*For any* position above 1.0R profit, each stop loss update must result in a stop price that is greater than or equal to the previous stop price (stops only move up, never down).
**Validates: Requirements 1.2, 1.5**

### Property 3: Profitable Position Stop Invariant
*For any* position with unrealized profit > 0, the stop loss price must be greater than or equal to the entry price at all times.
**Validates: Requirements 1.4**

### Property 4: Stop Update Latency
*For any* favorable price movement that triggers a trailing stop update, the system must submit the stop loss modification order within 100 milliseconds.
**Validates: Requirements 1.3, 8.1**

### Property 5: Partial Profit at 2R
*For any* position that reaches 2.0R profit, the system must execute a sell order for exactly 50% of the original position quantity.
**Validates: Requirements 2.1, 5.3**

### Property 6: Partial Profit at 3R
*For any* position that reaches 3.0R profit, the system must execute a sell order for exactly 25% of the original position quantity.
**Validates: Requirements 2.2, 5.4**

### Property 7: Partial Profit at 4R
*For any* position that reaches 4.0R profit, the system must execute a sell order for the remaining position quantity.
**Validates: Requirements 2.3**

### Property 8: Partial Quantity Calculation
*For any* partial profit execution, the share quantity must be calculated based on the original position size, not the current remaining size.
**Validates: Requirements 2.4**

### Property 9: Position State Consistency After Partial Fill
*For any* partial profit order that fills, the position tracking must immediately reflect the reduced quantity (original_qty - filled_qty).
**Validates: Requirements 2.5, 4.3**

### Property 10: Stop Loss Modification Sequence
*For any* stop loss update operation, the system must cancel the existing stop loss order before creating the new stop loss order.
**Validates: Requirements 3.1**

### Property 11: Share Availability Verification
*For any* take-profit order creation attempt, the system must verify that sufficient unlocked shares are available before submitting the order.
**Validates: Requirements 3.2**

### Property 12: Retry with Exponential Backoff
*For any* failed order operation, the system must retry up to 3 times with exponentially increasing delays between attempts.
**Validates: Requirements 3.3, 7.1**

### Property 13: Atomic Operation All-or-Nothing
*For any* multi-step order operation, either all steps must succeed or all changes must be rolled back, leaving the system in the pre-operation state.
**Validates: Requirements 3.4, 6.1, 6.3**

### Property 14: Conflict Detection and Logging
*For any* detected order conflict, the system must log the conflict type, conflicting order IDs, and resolution attempt.
**Validates: Requirements 3.5, 9.3**

### Property 15: Position Initialization Completeness
*For any* newly opened position, the system must record entry price, quantity, initial stop loss, and timestamp.
**Validates: Requirements 4.1**

### Property 16: R-Multiple Calculation Performance
*For any* market price update, the system must recalculate the R-multiple for affected positions within 50 milliseconds.
**Validates: Requirements 4.2, 8.4**

### Property 17: Unrealized P/L Maintenance
*For any* open position, the unrealized profit/loss must be recalculated whenever the current price changes.
**Validates: Requirements 4.4**

### Property 18: Position State Freshness
*For any* position state query, the returned data must have a timestamp no more than 100 milliseconds old.
**Validates: Requirements 4.5**

### Property 19: State Machine Initial State
*For any* newly opened position, the protection state must be initialized to "INITIAL_RISK".
**Validates: Requirements 5.1**

### Property 20: State Transition Triggers Actions
*For any* state transition, the system must trigger the corresponding profit protection actions (e.g., move to breakeven at 1.0R, take partial profits at 2.0R).
**Validates: Requirements 5.5**

### Property 21: Stop Loss Update Rollback
*For any* failed stop loss update in a bracket modification, any related take-profit modifications must be rolled back.
**Validates: Requirements 6.2**

### Property 22: Concurrent Modification Prevention
*For any* position, while an atomic operation is in progress, concurrent modification attempts must be blocked or queued.
**Validates: Requirements 6.4**

### Property 23: Post-Operation State Verification
*For any* completed atomic operation, the system must verify that all orders are in the expected state before marking the operation as successful.
**Validates: Requirements 6.5**

### Property 24: Exhausted Retry Alerting
*For any* operation where all retry attempts fail, the system must generate an operator alert and log the failure with full context.
**Validates: Requirements 7.2**

### Property 25: Offline Operation Queueing
*For any* order modification attempted during network connectivity loss, the operation must be queued for execution when connectivity is restored.
**Validates: Requirements 7.3**

### Property 26: Error Recovery Mode Restrictions
*For any* time period while the system is in error recovery mode, attempts to open new positions must be rejected.
**Validates: Requirements 7.4**

### Property 27: Recovery Validation
*For any* error recovery completion, the system must validate all position states before resuming normal trading operations.
**Validates: Requirements 7.5**

### Property 28: Profit Milestone Execution Latency
*For any* position reaching a profit milestone (2R, 3R, 4R), the profit-taking order must be submitted within 200 milliseconds.
**Validates: Requirements 8.2**

### Property 29: Monitoring Frequency
*For any* one-second time window while positions are open, the system must check for profit protection triggers at least once.
**Validates: Requirements 8.3**

### Property 30: Concurrent Update Performance
*For any* set of concurrent position updates, the system must maintain sub-second response times for all updates.
**Validates: Requirements 8.5**

### Property 31: Trailing Stop Logging Completeness
*For any* trailing stop update, the log entry must contain the old stop price, new stop price, and reason for the update.
**Validates: Requirements 9.1**

### Property 32: Partial Profit Logging Completeness
*For any* partial profit execution, the log entry must contain the R-multiple, shares sold, and profit amount realized.
**Validates: Requirements 9.2**

### Property 33: Metrics Exposure
*For any* open position, the system must expose real-time metrics including current R-multiple and protection state.
**Validates: Requirements 9.4**

### Property 34: State Transition Event Emission
*For any* state transition, the system must emit an event containing the old state, new state, and trigger reason.
**Validates: Requirements 9.5**

### Property 35: Startup Position Scanning
*For any* system startup with existing open positions, the system must scan all positions and apply appropriate profit protection rules based on current R-multiples.
**Validates: Requirements 10.1, 10.2**

### Property 36: Bracket Order Self-Healing
*For any* existing position with incorrect or missing bracket orders, the system must correct them to match current profit protection rules.
**Validates: Requirements 10.3**

### Property 37: Migration Minimal Disruption
*For any* position migration operation, the system must only modify orders that are incorrect or missing, leaving correct orders unchanged.
**Validates: Requirements 10.4**

### Property 38: Post-Migration Verification
*For any* completed migration, all positions must have both active stop loss and take profit orders in place.
**Validates: Requirements 10.5**

## Error Handling

### Error Categories

1. **Broker API Errors**
   - Order rejection (insufficient buying power, invalid price, etc.)
   - Rate limiting
   - Network timeouts
   - Service unavailable

2. **Order Conflict Errors**
   - Shares locked by existing orders
   - Duplicate order submission
   - Invalid order state transitions

3. **State Consistency Errors**
   - Position not found
   - Stale price data
   - R-multiple calculation errors

4. **Performance Errors**
   - Latency threshold exceeded
   - Queue overflow
   - Resource exhaustion

### Error Handling Strategies

**Retry with Exponential Backoff**:
```python
def retry_with_backoff(operation, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return operation()
        except RetryableError as e:
            if attempt == max_attempts - 1:
                raise
            delay = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s
            time.sleep(delay)
            logger.warning(f"Retry {attempt + 1}/{max_attempts} after {delay}s: {e}")
```

**Conflict Resolution**:
```python
def resolve_shares_locked_conflict(symbol):
    """
    Resolve shares locked conflict by canceling conflicting orders.
    """
    # 1. Get all open orders for symbol
    orders = get_open_orders(symbol)
    
    # 2. Cancel all exit orders (stop loss + take profit)
    for order in orders:
        if order.side == 'sell' and order.type in ['stop', 'limit']:
            cancel_order(order.id)
    
    # 3. Wait for cancellations to process
    time.sleep(1.0)
    
    # 4. Retry original operation
    return True
```

**State Recovery**:
```python
def recover_from_state_error(symbol):
    """
    Recover from state inconsistency by resyncing from broker.
    """
    # 1. Query fresh position data from broker
    broker_position = alpaca.get_position(symbol)
    
    # 2. Query all orders for symbol
    broker_orders = alpaca.get_orders(symbol=symbol, status='all')
    
    # 3. Rebuild local state from broker data
    local_state = rebuild_position_state(broker_position, broker_orders)
    
    # 4. Validate state consistency
    if validate_state(local_state):
        update_local_state(symbol, local_state)
        return True
    else:
        raise StateRecoveryError(f"Cannot recover consistent state for {symbol}")
```

**Circuit Breaker**:
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=300):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, operation):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpen("Circuit breaker is open")
        
        try:
            result = operation()
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise
```

## Testing Strategy

### Unit Testing

**Component-Level Tests**:
- Test each component in isolation with mocked dependencies
- Focus on business logic correctness
- Use deterministic test data

**Example Unit Tests**:
```python
def test_calculate_trailing_stop_at_2r():
    """Test trailing stop calculation at 2.0R profit."""
    manager = IntelligentStopManager()
    entry = 100.0
    current = 103.0  # 2.0R profit (1.5% risk)
    initial_risk = 1.5
    r_multiple = 2.0
    
    new_stop = manager.calculate_trailing_stop(entry, current, initial_risk, r_multiple)
    
    # At 2.0R, should trail at 1.0R (lock in 1.0R profit)
    expected_stop = entry + initial_risk  # 101.5
    assert abs(new_stop - expected_stop) < 0.01

def test_partial_profit_quantity_calculation():
    """Test partial profit quantity is based on original position."""
    engine = ProfitTakingEngine()
    original_qty = 1000
    remaining_qty = 1000
    
    # First partial at 2.0R should be 50% of original
    qty_2r = engine.calculate_partial_quantity(original_qty, remaining_qty, 2.0)
    assert qty_2r == 500
    
    # Second partial at 3.0R should be 25% of original (not 50% of remaining)
    remaining_after_2r = 500
    qty_3r = engine.calculate_partial_quantity(original_qty, remaining_after_2r, 3.0)
    assert qty_3r == 250

def test_order_sequencer_cancels_before_create():
    """Test that stop loss updates cancel existing order first."""
    sequencer = OrderSequencer(mock_alpaca_client)
    symbol = "TEST"
    new_stop = 105.0
    
    # Mock existing stop loss order
    mock_alpaca_client.get_orders.return_value = [
        MockOrder(id="stop123", symbol="TEST", type="stop", status="new")
    ]
    
    result = sequencer.execute_stop_update(symbol, new_stop)
    
    # Verify cancel was called before create
    calls = mock_alpaca_client.method_calls
    cancel_index = next(i for i, call in enumerate(calls) if call[0] == 'cancel_order')
    create_index = next(i for i, call in enumerate(calls) if call[0] == 'submit_order')
    assert cancel_index < create_index
```

### Property-Based Testing

**Property Test Framework**: Use `hypothesis` for Python to generate random test cases.

**Example Property Tests**:
```python
from hypothesis import given, strategies as st

@given(
    entry_price=st.floats(min_value=10.0, max_value=1000.0),
    r_multiple=st.floats(min_value=1.0, max_value=10.0),
    initial_risk_pct=st.floats(min_value=0.01, max_value=0.05)
)
def test_property_profitable_stop_above_entry(entry_price, r_multiple, initial_risk_pct):
    """
    Property: For any profitable position (R >= 1.0), stop loss must be >= entry price.
    **Validates: Requirements 1.4**
    """
    initial_risk = entry_price * initial_risk_pct
    current_price = entry_price + (r_multiple * initial_risk)
    
    manager = IntelligentStopManager()
    new_stop = manager.calculate_trailing_stop(entry_price, current_price, initial_risk, r_multiple)
    
    assert new_stop >= entry_price, \
        f"Stop {new_stop} below entry {entry_price} at {r_multiple}R"

@given(
    original_qty=st.integers(min_value=100, max_value=10000),
    r_multiple=st.sampled_from([2.0, 3.0, 4.0])
)
def test_property_partial_profit_quantities(original_qty, r_multiple):
    """
    Property: Partial profit quantities must sum to original position size.
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    """
    engine = ProfitTakingEngine()
    
    qty_2r = engine.calculate_partial_quantity(original_qty, original_qty, 2.0)
    remaining_after_2r = original_qty - qty_2r
    
    qty_3r = engine.calculate_partial_quantity(original_qty, remaining_after_2r, 3.0)
    remaining_after_3r = remaining_after_2r - qty_3r
    
    qty_4r = remaining_after_3r
    
    total_sold = qty_2r + qty_3r + qty_4r
    
    assert total_sold == original_qty, \
        f"Partial quantities {qty_2r}+{qty_3r}+{qty_4r}={total_sold} != {original_qty}"
    
    # Verify percentages
    assert abs(qty_2r - original_qty * 0.5) <= 1  # 50% at 2R
    assert abs(qty_3r - original_qty * 0.25) <= 1  # 25% at 3R

@given(
    stop_updates=st.lists(
        st.floats(min_value=100.0, max_value=200.0),
        min_size=2,
        max_size=10
    )
)
def test_property_trailing_stop_monotonicity(stop_updates):
    """
    Property: Trailing stops must be monotonically increasing (never decrease).
    **Validates: Requirements 1.2, 1.5**
    """
    sorted_stops = sorted(stop_updates)
    
    manager = IntelligentStopManager()
    
    for i in range(1, len(sorted_stops)):
        prev_stop = sorted_stops[i-1]
        new_stop = sorted_stops[i]
        
        # Validate that new stop is accepted only if >= previous
        is_valid = manager.validate_stop_update(prev_stop, new_stop)
        
        if new_stop >= prev_stop:
            assert is_valid, f"Valid update {prev_stop} -> {new_stop} rejected"
        else:
            assert not is_valid, f"Invalid update {prev_stop} -> {new_stop} accepted"
```

### Integration Testing

**End-to-End Scenarios**:
```python
def test_integration_full_position_lifecycle():
    """
    Test complete position lifecycle from entry to final exit.
    """
    # Setup
    alpaca = AlpacaClient()
    tracker = PositionStateTracker()
    stop_manager = IntelligentStopManager(alpaca)
    profit_engine = ProfitTakingEngine(alpaca)
    
    # 1. Open position
    symbol = "TEST"
    entry_price = 100.0
    quantity = 1000
    initial_stop = 98.5  # 1.5% risk
    
    tracker.track_position(symbol, entry_price, initial_stop, quantity, 'long')
    
    # 2. Move to 1.0R - should move stop to breakeven
    current_price = 101.5
    tracker.update_current_price(symbol, current_price)
    stop_manager.update_stop_for_position(tracker.get_state(symbol))
    
    state = tracker.get_state(symbol)
    assert state.stop_loss == entry_price
    assert state.protection_state.state == 'BREAKEVEN_PROTECTED'
    
    # 3. Move to 2.0R - should take 50% profit
    current_price = 103.0
    tracker.update_current_price(symbol, current_price)
    
    action = profit_engine.check_profit_milestones(tracker.get_state(symbol))
    assert action is not None
    assert action.quantity == 500
    
    result = profit_engine.execute_partial_exit(symbol, 500, "2.0R milestone")
    assert result.success
    
    # Update tracker with new quantity
    tracker.update_quantity(symbol, 500)
    
    # 4. Move to 3.0R - should take another 25% of original
    current_price = 104.5
    tracker.update_current_price(symbol, current_price)
    
    action = profit_engine.check_profit_milestones(tracker.get_state(symbol))
    assert action.quantity == 250
    
    # 5. Verify final state
    state = tracker.get_state(symbol)
    assert state.quantity == 250  # 25% remaining
    assert state.protection_state.state == 'ADVANCED_PROFIT_TAKEN'
```

### Performance Testing

**Latency Tests**:
```python
import time

def test_performance_stop_update_latency():
    """
    Test that stop updates complete within 100ms.
    **Validates: Requirements 1.3, 8.1**
    """
    manager = IntelligentStopManager(alpaca_client)
    symbol = "TEST"
    new_stop = 105.0
    
    start = time.time()
    result = manager.update_stop_for_position(symbol, new_stop)
    elapsed = (time.time() - start) * 1000  # Convert to ms
    
    assert result.success
    assert elapsed < 100, f"Stop update took {elapsed}ms > 100ms limit"

def test_performance_r_multiple_calculation():
    """
    Test that R-multiple calculation completes within 10ms.
    **Validates: Requirements 4.2, 8.4**
    """
    tracker = PositionStateTracker()
    
    # Setup 100 positions
    for i in range(100):
        tracker.track_position(f"TEST{i}", 100.0, 98.5, 1000, 'long')
    
    # Update all prices and measure calculation time
    start = time.time()
    for i in range(100):
        tracker.update_current_price(f"TEST{i}", 102.0)
        r_multiple = tracker.get_r_multiple(f"TEST{i}")
    elapsed = (time.time() - start) * 1000 / 100  # Average per position
    
    assert elapsed < 10, f"R-multiple calculation took {elapsed}ms > 10ms limit"
```

### Test Configuration

**Minimum Test Coverage**: 90% code coverage for all core components

**Property Test Iterations**: Minimum 100 iterations per property test

**Performance Test Thresholds**:
- Stop update latency: < 100ms (p99)
- Profit execution latency: < 200ms (p99)
- R-multiple calculation: < 10ms (p99)
- State query freshness: < 100ms (p99)

## Implementation Notes

### Phase 1: Core Infrastructure (Week 1)
- Implement PositionStateTracker with state machine
- Implement basic IntelligentStopManager with breakeven logic
- Add unit tests for core components

### Phase 2: Profit Protection (Week 2)
- Implement ProfitTakingEngine with milestone detection
- Implement trailing stop logic in IntelligentStopManager
- Add property-based tests for profit taking

### Phase 3: Order Management (Week 3)
- Implement OrderSequencer with conflict resolution
- Add atomic operation support
- Add integration tests for order sequences

### Phase 4: Error Handling & Recovery (Week 4)
- Implement retry logic with exponential backoff
- Add circuit breaker pattern
- Implement state recovery mechanisms
- Add error handling tests

### Phase 5: Performance Optimization (Week 5)
- Optimize R-multiple calculations
- Add caching for frequently accessed data
- Implement concurrent update handling
- Add performance tests

### Phase 6: Migration & Deployment (Week 6)
- Implement backward compatibility layer
- Add migration logic for existing positions
- Deploy to production with monitoring
- Verify all existing positions are protected

### Technology Stack

- **Language**: Python 3.9+
- **Property Testing**: Hypothesis
- **Unit Testing**: pytest
- **Performance Testing**: pytest-benchmark
- **Monitoring**: Prometheus + Grafana
- **Logging**: structlog
- **Database**: PostgreSQL (for state persistence)

### Dependencies

- `alpaca-trade-api`: Broker API client
- `hypothesis`: Property-based testing
- `pytest`: Unit testing framework
- `structlog`: Structured logging
- `psycopg2`: PostgreSQL adapter
- `prometheus-client`: Metrics export

### Monitoring & Alerts

**Key Metrics**:
- `profit_protection_stop_updates_total`: Counter of stop loss updates
- `profit_protection_partial_exits_total`: Counter of partial profit executions
- `profit_protection_conflicts_total`: Counter of order conflicts
- `profit_protection_latency_seconds`: Histogram of operation latencies
- `profit_protection_positions_by_state`: Gauge of positions in each protection state

**Critical Alerts**:
- Stop update latency > 100ms for 5 consecutive updates
- Profitable position with stop below entry detected
- Order conflict rate > 10% over 5 minutes
- Circuit breaker opened
- Position without stop loss protection detected

### Security Considerations

1. **API Key Management**: Store Alpaca API keys in environment variables, never in code
2. **Order Validation**: Validate all order parameters before submission
3. **Rate Limiting**: Respect Alpaca API rate limits (200 requests/minute)
4. **Audit Logging**: Log all order modifications with timestamps and reasons
5. **Access Control**: Restrict system access to authorized operators only

### Deployment Strategy

1. **Shadow Mode**: Run new system alongside existing system, log decisions without executing
2. **Canary Deployment**: Enable for 10% of positions, monitor for issues
3. **Gradual Rollout**: Increase to 50%, then 100% over 2 weeks
4. **Rollback Plan**: Keep existing system ready for immediate rollback if needed
5. **Monitoring**: 24/7 monitoring during initial deployment period

## Success Criteria

The Intelligent Profit Protection System will be considered successful when:

1. **Zero Profitable Losses**: No position with unrealized profit closes at a loss (measured over 30 days)
2. **100% Protection Coverage**: All positions have active stop loss protection at all times
3. **Systematic Profit Taking**: 95%+ of positions reaching 2R+ milestones execute partial profits
4. **Zero Order Conflicts**: "Shares locked" errors reduced to < 0.1% of operations
5. **Performance Targets Met**: All latency requirements met at p99 (99th percentile)
6. **Backward Compatibility**: Existing positions migrated without manual intervention
7. **System Reliability**: 99.9% uptime for profit protection monitoring

These criteria will be measured through automated monitoring and weekly performance reports.
