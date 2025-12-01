#!/usr/bin/env python3
"""
Property-Based Tests for Profit Protection (Momentum Wave Rider)

Tests correctness properties for profit protection enhancements:
- Partial profit at 2R
- Stop to breakeven after partial
- RSI divergence detection
- ADX momentum loss detection
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass


# Mock the position state for testing
@dataclass
class MockShareAllocation:
    original_quantity: int = 100
    remaining_quantity: int = 100
    partial_exits: list = None
    
    def __post_init__(self):
        if self.partial_exits is None:
            self.partial_exits = []


@dataclass
class MockProtectionState:
    state: str = "active"
    partial_profits_taken: list = None
    
    def __post_init__(self):
        if self.partial_profits_taken is None:
            self.partial_profits_taken = []


@dataclass
class MockPositionState:
    symbol: str = "TEST"
    entry_price: float = 100.0
    current_price: float = 100.0
    stop_price: float = 98.0
    initial_risk: float = 2.0  # 1R = $2 per share
    r_multiple: float = 0.0
    quantity: int = 100
    direction: str = "long"
    share_allocation: MockShareAllocation = None
    protection_state: MockProtectionState = None
    
    def __post_init__(self):
        if self.share_allocation is None:
            self.share_allocation = MockShareAllocation()
        if self.protection_state is None:
            self.protection_state = MockProtectionState()


class TestProfitProtectionWaveRider:
    """Property-based tests for profit protection enhancements."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock profit taking engine
        from trading.profit_protection.profit_taking_engine import ProfitTakingEngine
        
        mock_alpaca = Mock()
        
        # Patch the tracker
        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                "backend.trading.profit_protection.profit_taking_engine.get_position_tracker",
                lambda: Mock()
            )
            self.engine = ProfitTakingEngine(mock_alpaca)
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        r_multiple=st.floats(min_value=2.0, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    def test_partial_profit_at_2r(self, entry_price, r_multiple):
        """
        **Feature: momentum-wave-rider, Property 12: Partial Profit at 2R**
        **Validates: Requirements 6.1**
        
        For any position reaching 2R profit, the system should take 50% partial profit.
        """
        initial_risk = entry_price * 0.02  # 2% risk
        current_price = entry_price + (r_multiple * initial_risk)
        
        position = MockPositionState(
            entry_price=entry_price,
            current_price=current_price,
            initial_risk=initial_risk,
            r_multiple=r_multiple,
            share_allocation=MockShareAllocation(
                original_quantity=100,
                remaining_quantity=100,
                partial_exits=[]  # No exits yet
            )
        )
        
        action = self.engine.check_profit_milestones(position)
        
        # At 2R+ with no exits, should trigger 50% partial
        assert action is not None, f"Should trigger action at {r_multiple}R"
        assert action.milestone == 2.0, f"Milestone should be 2.0, got {action.milestone}"
        assert action.quantity == 50, f"Should take 50% (50 shares), got {action.quantity}"
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        r_multiple=st.floats(min_value=2.0, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    def test_stop_to_breakeven_after_partial(self, entry_price, r_multiple):
        """
        **Feature: momentum-wave-rider, Property 13: Stop to Breakeven After Partial**
        **Validates: Requirements 6.2**
        
        For any position after partial profit is taken, 
        the stop loss should be at entry price (breakeven).
        """
        initial_risk = entry_price * 0.02
        current_price = entry_price + (r_multiple * initial_risk)
        
        # Position with one partial exit already taken
        position = MockPositionState(
            entry_price=entry_price,
            current_price=current_price,
            stop_price=entry_price - initial_risk,  # Stop still at original
            initial_risk=initial_risk,
            r_multiple=r_multiple,
            share_allocation=MockShareAllocation(
                original_quantity=100,
                remaining_quantity=50,
                partial_exits=[{'milestone': 2.0, 'shares': 50}]  # One exit taken
            )
        )
        
        should_move = self.engine.should_move_stop_to_breakeven(position)
        
        # Should move to breakeven after 2R and partial taken
        assert should_move, f"Should move stop to breakeven at {r_multiple}R after partial"
        
        # Verify breakeven price calculation
        breakeven_stop = self.engine.calculate_stop_price_for_r_multiple(position, 0)
        assert abs(breakeven_stop - entry_price) < 0.01, (
            f"Breakeven stop should be entry price {entry_price}, got {breakeven_stop}"
        )

    @given(
        prices=st.lists(
            st.floats(min_value=90.0, max_value=110.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=10
        ),
        rsi_start=st.floats(min_value=50.0, max_value=70.0, allow_nan=False, allow_infinity=False),
        rsi_drop=st.floats(min_value=5.0, max_value=20.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    def test_rsi_divergence_detection(self, prices, rsi_start, rsi_drop):
        """
        Test RSI divergence detection (price up, RSI down).
        """
        # Create rising prices
        sorted_prices = sorted(prices)
        
        # Create falling RSI (divergence)
        rsi_values = [rsi_start - (i * rsi_drop / len(prices)) for i in range(len(prices))]
        
        # Should detect divergence when price up and RSI down
        has_divergence = self.engine.check_rsi_divergence(sorted_prices, rsi_values)
        
        # If price is rising and RSI is falling, should detect divergence
        if sorted_prices[-1] > sorted_prices[0] and rsi_values[-1] < rsi_values[0]:
            assert has_divergence, "Should detect RSI divergence"
    
    @given(
        adx=st.floats(min_value=0.0, max_value=19.9, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    def test_adx_momentum_loss(self, adx):
        """
        Test ADX momentum loss detection.
        
        When ADX < 20, momentum is lost.
        """
        has_momentum_loss = self.engine.check_adx_momentum_loss(adx)
        
        assert has_momentum_loss, f"Should detect momentum loss at ADX {adx}"
    
    @given(
        adx=st.floats(min_value=20.0, max_value=100.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    def test_adx_no_momentum_loss(self, adx):
        """
        Test that ADX >= 20 does not trigger momentum loss.
        """
        has_momentum_loss = self.engine.check_adx_momentum_loss(adx)
        
        assert not has_momentum_loss, f"Should not detect momentum loss at ADX {adx}"
    
    def test_trailing_stop_tightening_at_3r(self):
        """
        Test that trailing stop is tightened at 3R.
        """
        entry_price = 100.0
        initial_risk = 2.0
        r_multiple = 3.5
        current_price = entry_price + (r_multiple * initial_risk)
        
        position = MockPositionState(
            entry_price=entry_price,
            current_price=current_price,
            stop_price=entry_price,  # At breakeven
            initial_risk=initial_risk,
            r_multiple=r_multiple,
            direction="long"
        )
        
        should_tighten = self.engine.should_tighten_trailing_stop(position)
        
        assert should_tighten, "Should tighten trailing stop at 3R+"
        
        # Calculate expected stop (trail by 1R)
        expected_stop = self.engine.calculate_stop_price_for_r_multiple(
            position, 
            r_multiple - 1.0  # Trail by 1R
        )
        
        # At 3.5R, trailing by 1R means stop at 2.5R
        assert expected_stop > entry_price, "Trailing stop should be above entry"
    
    def test_exit_signals_combined(self):
        """
        Test combined exit signal checking.
        """
        position = MockPositionState()
        
        # Test with low ADX (should exit)
        features = {
            'adx': 15,
            'recent_prices': [100, 101, 102],
            'recent_rsi': [60, 58, 56]
        }
        
        should_exit, reason = self.engine.check_exit_signals(position, features)
        
        assert should_exit, "Should exit with low ADX"
        assert "adx" in reason.lower() or "momentum" in reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
