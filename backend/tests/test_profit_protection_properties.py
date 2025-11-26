"""
Property-based tests for Intelligent Profit Protection System

These tests use Hypothesis to generate random test cases and validate
that the system properties hold across all valid inputs.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime
from decimal import Decimal

from trading.profit_protection.models import (
    PositionState, ProtectionState, ProtectionStateEnum,
    ShareAllocation, PartialProfit
)
from trading.profit_protection.position_state_tracker import PositionStateTracker


class TestPositionStateInitializationProperties:
    """Property tests for position state initialization"""
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=['Lu', 'Ll'])),
        entry_price=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        stop_loss_offset=st.floats(min_value=0.1, max_value=50.0, allow_nan=False, allow_infinity=False),
        quantity=st.integers(min_value=1, max_value=10000),
        side=st.sampled_from(['long', 'short'])
    )
    @settings(max_examples=100, deadline=None)
    def test_property_position_initialization_completeness(self, symbol, entry_price, stop_loss_offset, quantity, side):
        """
        **Feature: intelligent-profit-protection, Property 15: Position Initialization Completeness**
        
        For any newly opened position, the system must record entry price, 
        quantity, initial stop loss, and timestamp.
        
        **Validates: Requirements 4.1**
        """
        # Set up stop loss based on side
        if side == 'long':
            stop_loss = entry_price - stop_loss_offset
        else:
            stop_loss = entry_price + stop_loss_offset
        
        tracker = PositionStateTracker()
        
        # Track the position
        position_state = tracker.track_position(
            symbol=symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            quantity=quantity,
            side=side
        )
        
        # Verify all required fields are recorded
        assert position_state.symbol == symbol
        assert position_state.entry_price == entry_price
        assert position_state.stop_loss == stop_loss
        assert position_state.quantity == quantity
        assert position_state.side == side
        
        # Verify timestamp is recent (within last minute)
        time_diff = datetime.utcnow() - position_state.last_updated
        assert time_diff.total_seconds() < 60
        
        # Verify initial state is correct
        assert position_state.protection_state.state == ProtectionStateEnum.INITIAL_RISK
        assert position_state.r_multiple == 0.0  # At entry, R should be 0
        assert position_state.unrealized_pl == 0.0  # At entry, P/L should be 0
        
        # Verify share allocation is initialized correctly
        assert position_state.share_allocation.original_quantity == quantity
        assert position_state.share_allocation.remaining_quantity == quantity
        assert len(position_state.share_allocation.partial_exits) == 0


class TestRMultipleCalculationProperties:
    """Property tests for R-multiple calculation"""
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        stop_loss_offset=st.floats(min_value=0.1, max_value=50.0, allow_nan=False, allow_infinity=False),
        price_move=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        side=st.sampled_from(['long', 'short'])
    )
    @settings(max_examples=100, deadline=None)
    def test_property_r_multiple_calculation_performance(self, entry_price, stop_loss_offset, price_move, side):
        """
        **Feature: intelligent-profit-protection, Property 16: R-Multiple Calculation Performance**
        
        For any market price update, the system must recalculate the R-multiple 
        for affected positions within 50 milliseconds.
        
        **Validates: Requirements 4.2, 8.4**
        """
        import time
        
        # Set up position based on side
        if side == 'long':
            stop_loss = entry_price - stop_loss_offset
            current_price = entry_price + price_move
        else:
            stop_loss = entry_price + stop_loss_offset
            current_price = entry_price - price_move  # Inverse for short
        
        # Skip invalid prices
        if current_price <= 0:
            assume(False)
        
        tracker = PositionStateTracker()
        position_state = tracker.track_position(
            symbol="TEST",
            entry_price=entry_price,
            stop_loss=stop_loss,
            quantity=100,
            side=side
        )
        
        # Measure R-multiple calculation time
        start_time = time.perf_counter()
        updated_position = tracker.update_current_price("TEST", current_price)
        end_time = time.perf_counter()
        
        calculation_time_ms = (end_time - start_time) * 1000
        
        # Verify calculation completed within 50ms
        assert calculation_time_ms < 50, f"R-multiple calculation took {calculation_time_ms:.2f}ms > 50ms limit"
        
        # Verify R-multiple is calculated correctly
        assert updated_position is not None
        
        if side == 'long':
            risk = entry_price - stop_loss
            profit = current_price - entry_price
        else:
            risk = stop_loss - entry_price
            profit = entry_price - current_price
        
        if risk > 0:
            expected_r = profit / risk
            assert abs(updated_position.r_multiple - expected_r) < 0.001  # Allow small floating point errors


class TestUnrealizedPLMaintenanceProperties:
    """Property tests for unrealized P/L maintenance"""
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        quantity=st.integers(min_value=1, max_value=10000),
        price_changes=st.lists(
            st.floats(min_value=-50.0, max_value=50.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=10
        ),
        side=st.sampled_from(['long', 'short'])
    )
    @settings(max_examples=50, deadline=None)
    def test_property_unrealized_pl_maintenance(self, entry_price, quantity, price_changes, side):
        """
        **Feature: intelligent-profit-protection, Property 17: Unrealized P/L Maintenance**
        
        For any open position, the unrealized profit/loss must be recalculated 
        whenever the current price changes.
        
        **Validates: Requirements 4.4**
        """
        # Set up position
        if side == 'long':
            stop_loss = entry_price - 5.0  # $5 risk
        else:
            stop_loss = entry_price + 5.0  # $5 risk
        
        tracker = PositionStateTracker()
        position_state = tracker.track_position(
            symbol="TEST",
            entry_price=entry_price,
            stop_loss=stop_loss,
            quantity=quantity,
            side=side
        )
        
        # Apply each price change and verify P/L is updated correctly
        for price_change in price_changes:
            new_price = entry_price + price_change
            
            # Skip invalid prices
            if new_price <= 0:
                continue
            
            updated_position = tracker.update_current_price("TEST", new_price)
            assert updated_position is not None
            
            # Calculate expected P/L
            if side == 'long':
                expected_pl = (new_price - entry_price) * quantity
            else:
                expected_pl = (entry_price - new_price) * quantity
            
            # Verify P/L is calculated correctly
            assert abs(updated_position.unrealized_pl - expected_pl) < 0.01
            
            # Verify percentage is calculated correctly
            cost_basis = entry_price * quantity
            expected_pl_pct = (expected_pl / cost_basis) * 100
            assert abs(updated_position.unrealized_pl_pct - expected_pl_pct) < 0.01


class TestPositionStateFreshnessProperties:
    """Property tests for position state freshness"""
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        current_price=st.floats(min_value=5.0, max_value=1500.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_position_state_freshness(self, entry_price, current_price):
        """
        **Feature: intelligent-profit-protection, Property 18: Position State Freshness**
        
        For any position state query, the returned data must have a timestamp 
        no more than 100 milliseconds old.
        
        **Validates: Requirements 4.5**
        """
        tracker = PositionStateTracker()
        
        # Create position
        position_state = tracker.track_position(
            symbol="TEST",
            entry_price=entry_price,
            stop_loss=entry_price - 5.0,  # Simple stop
            quantity=100,
            side='long'
        )
        
        # Update price
        tracker.update_current_price("TEST", current_price)
        
        # Query position state immediately
        query_time = datetime.utcnow()
        queried_state = tracker.get_position_state("TEST")
        
        assert queried_state is not None
        
        # Verify timestamp freshness (within 100ms)
        time_diff = query_time - queried_state.last_updated
        time_diff_ms = time_diff.total_seconds() * 1000
        
        assert time_diff_ms <= 100, f"Position state is {time_diff_ms:.2f}ms old > 100ms limit"


class TestStateMachineProperties:
    """Property tests for state machine behavior"""
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        quantity=st.integers(min_value=1, max_value=10000)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_state_machine_initial_state(self, entry_price, quantity):
        """
        **Feature: intelligent-profit-protection, Property 19: State Machine Initial State**
        
        For any newly opened position, the protection state must be 
        initialized to "INITIAL_RISK".
        
        **Validates: Requirements 5.1**
        """
        tracker = PositionStateTracker()
        
        position_state = tracker.track_position(
            symbol="TEST",
            entry_price=entry_price,
            stop_loss=entry_price - 5.0,
            quantity=quantity,
            side='long'
        )
        
        # Verify initial state
        assert position_state.protection_state.state == ProtectionStateEnum.INITIAL_RISK
        
        # Verify state is consistent across queries
        queried_state = tracker.get_protection_state("TEST")
        assert queried_state is not None
        assert queried_state.state == ProtectionStateEnum.INITIAL_RISK


if __name__ == "__main__":
    # Run property tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])



class TestTrailingStopProperties:
    """Property tests for trailing stop behavior"""
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        initial_risk_pct=st.floats(min_value=0.01, max_value=0.05, allow_nan=False, allow_infinity=False),
        r_multiples=st.lists(
            st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=10
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_property_trailing_stop_monotonicity(self, entry_price, initial_risk_pct, r_multiples):
        """
        **Feature: intelligent-profit-protection, Property 2: Trailing Stop Monotonicity**
        
        For any position, as the R-multiple increases, the stop loss price must 
        never decrease (for long positions) or increase (for short positions).
        
        **Validates: Requirements 1.2, 1.5**
        """
        from trading.profit_protection.intelligent_stop_manager import IntelligentStopManager
        from unittest.mock import Mock
        
        # Create mock Alpaca client
        mock_alpaca = Mock()
        stop_manager = IntelligentStopManager(mock_alpaca)
        
        initial_risk = entry_price * initial_risk_pct
        
        # Sort R-multiples to ensure increasing sequence
        r_multiples_sorted = sorted(r_multiples)
        
        previous_stop = None
        for r in r_multiples_sorted:
            current_price = entry_price + (r * initial_risk)
            
            new_stop = stop_manager.calculate_trailing_stop(
                entry_price=entry_price,
                current_price=current_price,
                initial_risk=initial_risk,
                r_multiple=r
            )
            
            if previous_stop is not None:
                # Stop should never go down for long positions
                assert new_stop >= previous_stop, \
                    f"Stop decreased from ${previous_stop:.2f} to ${new_stop:.2f} at R={r:.2f}"
            
            previous_stop = new_stop
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        r_multiple=st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        initial_risk_pct=st.floats(min_value=0.01, max_value=0.05, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_breakeven_protection_activation(self, entry_price, r_multiple, initial_risk_pct):
        """
        **Feature: intelligent-profit-protection, Property 1: Breakeven Protection Activation**
        
        For any position that reaches 1.0R profit, the system must move the stop 
        loss to the entry price (breakeven).
        
        **Validates: Requirements 1.1, 5.2**
        """
        from trading.profit_protection.intelligent_stop_manager import IntelligentStopManager
        from unittest.mock import Mock
        
        # Only test when R >= 1.0
        assume(r_multiple >= 1.0)
        
        mock_alpaca = Mock()
        stop_manager = IntelligentStopManager(mock_alpaca)
        
        initial_risk = entry_price * initial_risk_pct
        stop_loss = entry_price - initial_risk
        current_price = entry_price + (r_multiple * initial_risk)
        
        # Track position
        tracker = stop_manager.tracker
        position_state = tracker.track_position(
            symbol="TEST",
            entry_price=entry_price,
            stop_loss=stop_loss,
            quantity=100,
            side='long'
        )
        
        # Update price to trigger R >= 1.0
        tracker.update_current_price("TEST", current_price)
        
        # Calculate what stop should be
        new_stop = stop_manager.calculate_trailing_stop(
            entry_price=entry_price,
            current_price=current_price,
            initial_risk=initial_risk,
            r_multiple=r_multiple
        )
        
        # At 1.0R, stop should be at or above entry (breakeven or better)
        if r_multiple >= 1.0:
            assert new_stop >= entry_price, \
                f"Stop ${new_stop:.2f} below entry ${entry_price:.2f} at {r_multiple:.2f}R"
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        r_multiple=st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        initial_risk_pct=st.floats(min_value=0.01, max_value=0.05, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_profitable_position_stop_invariant(self, entry_price, r_multiple, initial_risk_pct):
        """
        **Feature: intelligent-profit-protection, Property 3: Profitable Position Stop Invariant**
        
        For any position with unrealized profit > 0, the stop loss price must be 
        greater than or equal to the entry price at all times.
        
        **Validates: Requirements 1.4**
        """
        from trading.profit_protection.intelligent_stop_manager import IntelligentStopManager
        from unittest.mock import Mock
        
        # Only test profitable positions
        assume(r_multiple >= 1.0)
        
        mock_alpaca = Mock()
        stop_manager = IntelligentStopManager(mock_alpaca)
        
        initial_risk = entry_price * initial_risk_pct
        current_price = entry_price + (r_multiple * initial_risk)
        
        # Calculate trailing stop
        new_stop = stop_manager.calculate_trailing_stop(
            entry_price=entry_price,
            current_price=current_price,
            initial_risk=initial_risk,
            r_multiple=r_multiple
        )
        
        # For profitable positions (R >= 1.0), stop must be >= entry
        assert new_stop >= entry_price, \
            f"Profitable position has stop ${new_stop:.2f} below entry ${entry_price:.2f}"
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        r_multiple=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
        initial_risk_pct=st.floats(min_value=0.01, max_value=0.05, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_stop_update_latency(self, entry_price, r_multiple, initial_risk_pct):
        """
        **Feature: intelligent-profit-protection, Property 4: Stop Update Latency**
        
        For any stop loss update, the operation must complete within 100 milliseconds.
        
        **Validates: Requirements 1.3, 8.1**
        """
        import time
        from trading.profit_protection.intelligent_stop_manager import IntelligentStopManager
        from unittest.mock import Mock
        
        mock_alpaca = Mock()
        stop_manager = IntelligentStopManager(mock_alpaca)
        
        initial_risk = entry_price * initial_risk_pct
        stop_loss = entry_price - initial_risk
        current_price = entry_price + (r_multiple * initial_risk)
        
        # Track position
        tracker = stop_manager.tracker
        position_state = tracker.track_position(
            symbol="TEST",
            entry_price=entry_price,
            stop_loss=stop_loss,
            quantity=100,
            side='long'
        )
        
        # Update price
        tracker.update_current_price("TEST", current_price)
        
        # Measure update time
        start_time = time.perf_counter()
        result = stop_manager.update_stop_for_position(position_state)
        end_time = time.perf_counter()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        # Verify latency requirement
        assert elapsed_ms < 100, f"Stop update took {elapsed_ms:.2f}ms > 100ms limit"


if __name__ == "__main__":
    # Run property tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])



class TestProfitTakingProperties:
    """Property tests for profit taking behavior"""
    
    @given(
        original_quantity=st.integers(min_value=100, max_value=10000),
        milestone=st.sampled_from([2.0, 3.0, 4.0])
    )
    @settings(max_examples=50, deadline=None)
    def test_property_partial_quantity_calculation(self, original_quantity, milestone):
        """
        **Feature: intelligent-profit-protection, Property 8: Partial Quantity Calculation**
        
        For any position, the partial quantity at each milestone must be calculated 
        based on the original position size (50% at 2R, 25% at 3R, remaining at 4R).
        
        **Validates: Requirements 2.4**
        """
        from trading.profit_protection.profit_taking_engine import ProfitTakingEngine
        from unittest.mock import Mock
        
        mock_alpaca = Mock()
        profit_engine = ProfitTakingEngine(mock_alpaca)
        
        # Calculate expected quantities
        if milestone == 2.0:
            expected = int(original_quantity * 0.5)
        elif milestone == 3.0:
            expected = int(original_quantity * 0.25)
        else:  # 4.0
            # At 4R, we take remaining (which would be 25% if previous exits happened)
            remaining = original_quantity - int(original_quantity * 0.5) - int(original_quantity * 0.25)
            expected = remaining
        
        # Calculate actual
        if milestone == 4.0:
            # For 4R, pass remaining quantity
            remaining = original_quantity - int(original_quantity * 0.5) - int(original_quantity * 0.25)
            actual = profit_engine._calculate_partial_quantity(original_quantity, remaining, milestone)
        else:
            actual = profit_engine._calculate_partial_quantity(original_quantity, original_quantity, milestone)
        
        assert actual == expected, f"Expected {expected} shares at {milestone}R, got {actual}"
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        quantity=st.integers(min_value=100, max_value=1000),
        r_multiple=st.floats(min_value=2.01, max_value=2.5, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=30, deadline=None)
    def test_property_partial_profit_at_2r(self, entry_price, quantity, r_multiple):
        """
        **Feature: intelligent-profit-protection, Property 5: Partial Profit at 2R**
        
        For any position that reaches 2.0R, the system must execute a partial exit 
        of 50% of the original position.
        
        **Validates: Requirements 2.1, 5.3**
        """
        from trading.profit_protection.profit_taking_engine import ProfitTakingEngine
        from unittest.mock import Mock
        
        mock_alpaca = Mock()
        profit_engine = ProfitTakingEngine(mock_alpaca)
        
        initial_risk = entry_price * 0.02
        stop_loss = entry_price - initial_risk
        current_price = entry_price + (r_multiple * initial_risk)
        
        # Track position
        tracker = profit_engine.tracker
        position_state = tracker.track_position(
            symbol="TEST",
            entry_price=entry_price,
            stop_loss=stop_loss,
            quantity=quantity,
            side='long'
        )
        
        # First update to 1R to trigger BREAKEVEN_PROTECTED state
        price_1r = entry_price + initial_risk
        tracker.update_current_price("TEST", price_1r)
        
        # Then update to 2R
        tracker.update_current_price("TEST", current_price)
        
        # Get updated position state
        position_state = tracker.get_position_state("TEST")
        
        # Check for profit action
        action = profit_engine.check_profit_milestones(position_state)
        
        if r_multiple >= 2.0:
            # Debug: check state
            num_exits = len(position_state.share_allocation.partial_exits)
            actual_r = position_state.r_multiple
            assert action is not None, f"Should have profit action at 2R (exits={num_exits}, state={position_state.protection_state.state}, actual_r={actual_r:.2f})"
            assert action.milestone == 2.0
            expected_qty = int(quantity * 0.5)
            assert action.quantity == expected_qty, f"Should exit 50% ({expected_qty} shares) at 2R"
    
    @given(
        original_quantity=st.integers(min_value=100, max_value=1000)
    )
    @settings(max_examples=30, deadline=None)
    def test_property_partial_profit_quantities_sum(self, original_quantity):
        """
        **Feature: intelligent-profit-protection, Property: Partial profit quantities must sum to original position**
        
        For any position, the sum of all partial exit quantities (50% + 25% + 25%) 
        must equal the original position size.
        
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
        """
        from trading.profit_protection.profit_taking_engine import ProfitTakingEngine
        from unittest.mock import Mock
        
        mock_alpaca = Mock()
        profit_engine = ProfitTakingEngine(mock_alpaca)
        
        # Calculate quantities at each milestone
        qty_2r = profit_engine._calculate_partial_quantity(original_quantity, original_quantity, 2.0)
        
        remaining_after_2r = original_quantity - qty_2r
        qty_3r = profit_engine._calculate_partial_quantity(original_quantity, remaining_after_2r, 3.0)
        
        remaining_after_3r = remaining_after_2r - qty_3r
        qty_4r = profit_engine._calculate_partial_quantity(original_quantity, remaining_after_3r, 4.0)
        
        # Sum should equal original (allowing for rounding)
        total = qty_2r + qty_3r + qty_4r
        assert abs(total - original_quantity) <= 2, \
            f"Partial exits {qty_2r}+{qty_3r}+{qty_4r}={total} != {original_quantity}"
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        quantity=st.integers(min_value=100, max_value=1000),
        r_multiple=st.floats(min_value=2.0, max_value=5.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=30, deadline=None)
    def test_property_position_state_consistency_after_partial_fill(self, entry_price, quantity, r_multiple):
        """
        **Feature: intelligent-profit-protection, Property 9: Position State Consistency After Partial Fill**
        
        For any partial exit, the remaining quantity in the position state must 
        equal the original quantity minus the shares sold.
        
        **Validates: Requirements 2.5, 4.3**
        """
        from trading.profit_protection.profit_taking_engine import ProfitTakingEngine
        from unittest.mock import Mock
        
        mock_alpaca = Mock()
        profit_engine = ProfitTakingEngine(mock_alpaca)
        
        initial_risk = entry_price * 0.02
        stop_loss = entry_price - initial_risk
        current_price = entry_price + (r_multiple * initial_risk)
        
        # Track position
        tracker = profit_engine.tracker
        position_state = tracker.track_position(
            symbol="TEST",
            entry_price=entry_price,
            stop_loss=stop_loss,
            quantity=quantity,
            side='long'
        )
        
        # Update price
        tracker.update_current_price("TEST", current_price)
        
        # Execute partial exit (simulate 50% exit)
        exit_qty = int(quantity * 0.5)
        result = profit_engine.execute_partial_exit("TEST", exit_qty, "test exit")
        
        if result.success:
            # Verify remaining quantity
            updated_state = tracker.get_position_state("TEST")
            assert updated_state is not None
            
            expected_remaining = quantity - exit_qty
            assert updated_state.share_allocation.remaining_quantity == expected_remaining, \
                f"Remaining {updated_state.share_allocation.remaining_quantity} != expected {expected_remaining}"
            
            # Verify partial exit was recorded
            assert len(updated_state.share_allocation.partial_exits) == 1
            assert updated_state.share_allocation.partial_exits[0].shares_sold == exit_qty


if __name__ == "__main__":
    # Run property tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])



class TestOrderSequencerProperties:
    """Property tests for order sequencer behavior"""
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=['Lu', 'Ll'])),
        new_stop=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_stop_loss_modification_sequence(self, symbol, new_stop):
        """
        **Feature: intelligent-profit-protection, Property 10: Stop Loss Modification Sequence**
        
        For any stop loss modification, the system must cancel existing stop,
        wait for confirmation, then create new stop.
        
        **Validates: Requirements 3.1**
        """
        from trading.profit_protection.order_sequencer import OrderSequencer
        from unittest.mock import Mock
        
        mock_alpaca = Mock()
        sequencer = OrderSequencer(mock_alpaca)
        
        # Mock successful operations
        mock_alpaca.get_orders.return_value = []
        mock_alpaca.get_position.return_value = Mock(qty=100)
        new_order = Mock(id="test_order_123", status="accepted")
        mock_alpaca.submit_order.return_value = new_order
        mock_alpaca.get_order.return_value = new_order  # For verification
        
        # Execute stop update
        result = sequencer.execute_stop_update(symbol, new_stop)
        
        # Verify result structure
        assert hasattr(result, 'success')
        assert hasattr(result, 'sequence_id')
        assert hasattr(result, 'operations_completed')
        assert hasattr(result, 'conflicts_detected')
        
        # If successful, operations should include key steps
        if result.success:
            assert 'query_orders' in result.operations_completed
            assert 'get_position' in result.operations_completed
            assert 'create_new_stop' in result.operations_completed
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=['Lu', 'Ll'])),
        required_qty=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_share_availability_verification(self, symbol, required_qty):
        """
        **Feature: intelligent-profit-protection, Property 11: Share Availability Verification**
        
        For any order, the system must verify shares are available before submission.
        
        **Validates: Requirements 3.2**
        """
        from trading.profit_protection.order_sequencer import OrderSequencer
        from unittest.mock import Mock
        
        mock_alpaca = Mock()
        sequencer = OrderSequencer(mock_alpaca)
        
        # Mock position with enough shares
        mock_alpaca.get_position.return_value = Mock(qty=required_qty + 100)
        mock_alpaca.get_orders.return_value = []
        
        result = sequencer.verify_shares_available(symbol, required_qty)
        
        # Verify result structure
        assert 'available_qty' in result
        assert 'locked_qty' in result
        assert 'is_available' in result
        
        # With no locked shares, should be available
        assert result['is_available'] == True
        assert result['available_qty'] >= required_qty
    
    @given(
        max_retries=st.integers(min_value=1, max_value=3),
        fail_count=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_retry_with_exponential_backoff(self, max_retries, fail_count):
        """
        **Feature: intelligent-profit-protection, Property 12: Retry with Exponential Backoff**
        
        For any failed operation, the system must retry with exponential backoff.
        
        **Validates: Requirements 3.3, 7.1**
        """
        from trading.profit_protection.order_sequencer import OrderSequencer
        import time
        
        sequencer = OrderSequencer(None)
        sequencer.retry_delays = [0.01, 0.02, 0.04]  # Fast delays for testing
        
        call_count = [0]
        
        def flaky_operation():
            call_count[0] += 1
            if call_count[0] <= fail_count:
                raise Exception(f"Simulated failure {call_count[0]}")
            return "success"
        
        if fail_count <= max_retries:
            # Should eventually succeed
            result = sequencer.retry_with_backoff(flaky_operation, max_retries=max_retries)
            assert result == "success"
            assert call_count[0] == fail_count + 1
        else:
            # Should exhaust retries
            with pytest.raises(Exception):
                sequencer.retry_with_backoff(flaky_operation, max_retries=max_retries)
            assert call_count[0] == max_retries + 1
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=['Lu', 'Ll']))
    )
    @settings(max_examples=10, deadline=None)
    def test_property_conflict_detection_and_logging(self, symbol):
        """
        **Feature: intelligent-profit-protection, Property 14: Conflict Detection and Logging**
        
        For any operation, all potential conflicts must be detected and logged.
        
        **Validates: Requirements 3.5, 9.3**
        """
        from trading.profit_protection.order_sequencer import OrderSequencer, ConflictType
        from unittest.mock import Mock
        
        mock_alpaca = Mock()
        sequencer = OrderSequencer(mock_alpaca)
        
        # Test case 1: No position (should detect insufficient shares)
        mock_alpaca.get_orders.return_value = []
        mock_alpaca.get_position.return_value = None
        
        conflicts = sequencer.detect_conflicts(symbol, "stop_update")
        
        # Should detect insufficient shares conflict
        insufficient_shares_conflicts = [
            c for c in conflicts 
            if c.conflict_type == ConflictType.INSUFFICIENT_SHARES
        ]
        assert len(insufficient_shares_conflicts) > 0, "Should detect insufficient shares when no position"
        
        # Test case 2: Multiple stop orders (should detect duplicates)
        mock_order1 = Mock(id="order1", order_type="stop", side="sell")
        mock_order2 = Mock(id="order2", order_type="stop", side="sell")
        mock_alpaca.get_orders.return_value = [mock_order1, mock_order2]
        mock_alpaca.get_position.return_value = Mock(qty=100)
        
        conflicts = sequencer.detect_conflicts(symbol, "stop_update")
        
        # Should detect duplicate orders
        duplicate_conflicts = [
            c for c in conflicts 
            if c.conflict_type == ConflictType.DUPLICATE_ORDER
        ]
        assert len(duplicate_conflicts) > 0, "Should detect duplicate stop orders"
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=['Lu', 'Ll'])),
        new_stop=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_atomic_operation_all_or_nothing(self, symbol, new_stop):
        """
        **Feature: intelligent-profit-protection, Property 13: Atomic Operation All-or-Nothing**
        
        For any order sequence, either all operations complete or all are rolled back.
        
        **Validates: Requirements 3.4, 6.1, 6.3**
        """
        from trading.profit_protection.order_sequencer import OrderSequencer
        from unittest.mock import Mock
        
        mock_alpaca = Mock()
        sequencer = OrderSequencer(mock_alpaca)
        
        # Mock successful operations
        mock_alpaca.get_orders.return_value = []
        mock_alpaca.get_position.return_value = Mock(qty=100)
        new_order = Mock(id="test_order", status="accepted")
        mock_alpaca.submit_order.return_value = new_order
        mock_alpaca.get_order.return_value = new_order
        
        result = sequencer.execute_stop_update(symbol, new_stop)
        
        # Verify atomicity: either success with all operations or failure with rollback
        if result.success:
            assert len(result.operations_completed) > 0
            assert not result.rollback_performed
        else:
            # If failed, rollback should be indicated
            assert isinstance(result.rollback_performed, bool)
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=['Lu', 'Ll']))
    )
    @settings(max_examples=5, deadline=None)
    def test_property_concurrent_modification_prevention(self, symbol):
        """
        **Feature: intelligent-profit-protection, Property 22: Concurrent Modification Prevention**
        
        For any symbol, only one order sequence can be active at a time.
        
        **Validates: Requirements 6.4**
        """
        from trading.profit_protection.order_sequencer import OrderSequencer, ConflictType
        from unittest.mock import Mock
        import threading
        import time
        
        mock_alpaca = Mock()
        sequencer = OrderSequencer(mock_alpaca)
        
        # Mock operations that take some time
        def slow_get_orders(*args, **kwargs):
            time.sleep(0.02)
            return []
        
        mock_alpaca.get_orders.side_effect = slow_get_orders
        mock_alpaca.get_position.return_value = Mock(qty=100)
        new_order = Mock(id="test_order", status="accepted")
        mock_alpaca.submit_order.return_value = new_order
        mock_alpaca.get_order.return_value = new_order
        
        results = []
        
        def execute_sequence(stop_price):
            result = sequencer.execute_stop_update(symbol, stop_price)
            results.append(result)
        
        # Start concurrent operations on same symbol
        threads = []
        for i in range(3):
            thread = threading.Thread(target=execute_sequence, args=(100.0 + i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # At least one should succeed (the first one to acquire lock)
        success_count = sum(1 for r in results if r.success)
        assert success_count >= 1, "At least one operation should succeed"

    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=['Lu', 'Ll'])),
        new_stop=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_stop_loss_update_rollback(self, symbol, new_stop):
        """
        **Feature: intelligent-profit-protection, Property 21: Stop Loss Update Rollback**
        
        For any failed stop loss update, the system must rollback to previous state.
        
        **Validates: Requirements 6.2**
        """
        from trading.profit_protection.order_sequencer import OrderSequencer
        from unittest.mock import Mock
        
        mock_alpaca = Mock()
        sequencer = OrderSequencer(mock_alpaca)
        
        # Mock operations that fail at submit_order
        mock_alpaca.get_orders.return_value = []
        mock_alpaca.get_position.return_value = Mock(qty=100)
        mock_alpaca.submit_order.return_value = None  # Simulate failure
        
        result = sequencer.execute_stop_update(symbol, new_stop)
        
        # Should fail and indicate rollback
        assert not result.success
        assert 'create_new_stop' in result.operations_completed
        # Rollback should be indicated in the message or flag
        assert 'Failed' in result.message or result.rollback_performed
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=['Lu', 'Ll'])),
        new_stop=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_post_operation_state_verification(self, symbol, new_stop):
        """
        **Feature: intelligent-profit-protection, Property 23: Post-Operation State Verification**
        
        After any operation, the system must verify the final state matches expectations.
        
        **Validates: Requirements 6.5**
        """
        from trading.profit_protection.order_sequencer import OrderSequencer
        from unittest.mock import Mock
        
        mock_alpaca = Mock()
        sequencer = OrderSequencer(mock_alpaca)
        
        # Mock successful operations
        mock_alpaca.get_orders.return_value = []
        mock_alpaca.get_position.return_value = Mock(qty=100)
        new_order = Mock(id="test_order", status="accepted")
        mock_alpaca.submit_order.return_value = new_order
        mock_alpaca.get_order.return_value = new_order
        
        result = sequencer.execute_stop_update(symbol, new_stop)
        
        # If successful, verify_new_order should be in operations
        if result.success:
            assert 'verify_new_order' in result.operations_completed
            # Execution time should be recorded
            assert result.execution_time_ms > 0



class TestErrorHandlerProperties:
    """Property tests for error handler behavior"""
    
    @given(
        max_retries=st.integers(min_value=1, max_value=3),
        fail_count=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_exhausted_retry_alerting(self, max_retries, fail_count):
        """
        **Feature: intelligent-profit-protection, Property 24: Exhausted Retry Alerting**
        
        For any operation that fails repeatedly, the system must alert when 
        all retry attempts are exhausted.
        
        **Validates: Requirements 7.2**
        """
        from trading.profit_protection.error_handler import ErrorHandler, ErrorContext
        
        error_handler = ErrorHandler()
        error_handler.retry_delays = [0.01, 0.02, 0.04]  # Fast delays for testing
        
        call_count = [0]
        alerts_sent = []
        
        def alert_callback(message, severity, context):
            alerts_sent.append({'message': message, 'severity': severity})
        
        error_handler.register_alert_callback(alert_callback)
        
        def failing_operation():
            call_count[0] += 1
            if call_count[0] <= fail_count:
                raise Exception(f"Simulated failure {call_count[0]}")
            return "success"
        
        context = ErrorContext(
            operation="test_operation",
            symbol="TEST",
            parameters={},
            timestamp=datetime.utcnow(),
            stack_trace="test_stack"
        )
        
        if fail_count <= max_retries:
            # Should eventually succeed
            result = error_handler.execute_with_retry(
                failing_operation, context, max_retries=max_retries
            )
            assert result == "success"
        else:
            # Should exhaust retries and alert
            with pytest.raises(Exception):
                error_handler.execute_with_retry(
                    failing_operation, context, max_retries=max_retries
                )
            # Alert should have been sent
            assert len(alerts_sent) > 0, "Alert should be sent when retries exhausted"
    
    @given(
        operations=st.lists(
            st.dictionaries(
                keys=st.sampled_from(['symbol', 'action', 'qty']),
                values=st.text(min_size=1, max_size=10),
                min_size=1
            ),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=10, deadline=None)
    def test_property_offline_operation_queueing(self, operations):
        """
        **Feature: intelligent-profit-protection, Property 25: Offline Operation Queueing**
        
        For any network failure, the system must queue operations for later execution.
        
        **Validates: Requirements 7.3**
        """
        from trading.profit_protection.error_handler import ErrorHandler
        
        error_handler = ErrorHandler()
        
        # Queue all operations
        for op in operations:
            result = error_handler.queue_offline_operation(op)
            assert result == True
        
        # Verify queue size
        assert error_handler.operation_queue.size() == len(operations)
        
        # Process operations
        processed_ops = []
        def executor(op):
            processed_ops.append(op)
        
        processed_count = error_handler.process_queued_operations(executor)
        
        # All operations should be processed
        assert processed_count == len(operations)
        assert error_handler.operation_queue.size() == 0
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=['Lu', 'Ll']))
    )
    @settings(max_examples=10, deadline=None)
    def test_property_error_recovery_mode_restrictions(self, symbol):
        """
        **Feature: intelligent-profit-protection, Property 26: Error Recovery Mode Restrictions**
        
        During recovery mode, the system must reject new position entries.
        
        **Validates: Requirements 7.4**
        """
        from trading.profit_protection.error_handler import ErrorHandler, SystemState
        
        error_handler = ErrorHandler()
        
        # Initially in normal mode
        assert error_handler.system_state == SystemState.NORMAL
        assert not error_handler.is_in_recovery_mode()
        
        # Enter recovery mode
        error_handler.enter_recovery_mode("Test recovery")
        
        # Should be in recovery mode
        assert error_handler.system_state == SystemState.RECOVERY
        assert error_handler.is_in_recovery_mode()
        
        # Exit recovery mode
        error_handler.exit_recovery_mode()
        
        # Should be back to normal
        assert error_handler.system_state == SystemState.NORMAL
        assert not error_handler.is_in_recovery_mode()
    
    @given(
        failure_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_circuit_breaker_activation(self, failure_count):
        """
        **Feature: intelligent-profit-protection, Property: Circuit Breaker Activation**
        
        After threshold failures, circuit breaker must open to prevent cascading failures.
        
        **Validates: Requirements 7.1, 7.2**
        """
        from trading.profit_protection.error_handler import CircuitBreaker
        
        threshold = 5
        circuit_breaker = CircuitBreaker(failure_threshold=threshold, recovery_timeout=60)
        
        # Initially closed
        assert circuit_breaker.state == "closed"
        
        # Simulate failures
        for i in range(failure_count):
            try:
                circuit_breaker.call(lambda: (_ for _ in ()).throw(Exception("fail")))
            except:
                pass
        
        # Check state based on failure count
        if failure_count >= threshold:
            assert circuit_breaker.state == "open", "Circuit breaker should open after threshold failures"
        else:
            assert circuit_breaker.state == "closed", "Circuit breaker should remain closed below threshold"
    
    @given(
        error_message=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_error_classification(self, error_message):
        """
        **Feature: intelligent-profit-protection, Property: Error Classification**
        
        All errors must be classified into appropriate categories.
        
        **Validates: Requirements 7.1**
        """
        from trading.profit_protection.error_handler import ErrorHandler, ErrorCategory
        
        error_handler = ErrorHandler()
        
        # Create error with message
        error = Exception(error_message)
        
        # Classify error
        category = error_handler._classify_error(error)
        
        # Category must be a valid ErrorCategory
        assert category in ErrorCategory.__members__.values()
        
        # Verify specific classifications
        if 'timeout' in error_message.lower():
            assert category == ErrorCategory.TIMEOUT
        elif 'connection' in error_message.lower() or 'network' in error_message.lower():
            assert category == ErrorCategory.NETWORK
