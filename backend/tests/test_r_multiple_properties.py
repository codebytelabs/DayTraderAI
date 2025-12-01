#!/usr/bin/env python3
"""
Property-Based Tests for R-Multiple Calculation

Tests correctness properties for R-multiple logging:
- R-multiple calculation accuracy
- Sign correctness (positive for profit, negative for loss)

**Feature: momentum-wave-rider, Property 17: R-Multiple Logging**
**Validates: Requirements 8.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import MagicMock
from datetime import datetime


class TestRMultipleProperties:
    """Property-based tests for R-multiple calculation."""
    
    def setup_method(self):
        """Set up test fixtures with mocked dependencies."""
        # Create mock position
        self.mock_position = MagicMock()
        self.mock_position.side = 'buy'
        self.mock_position.entry_time = datetime.now()
        
        # Create mock dependencies
        self.mock_alpaca = MagicMock()
        self.mock_supabase = MagicMock()
        
        # Import and create PositionManager with mocks
        from trading.position_manager import PositionManager
        self.position_manager = PositionManager(
            alpaca_client=self.mock_alpaca,
            supabase_client=self.mock_supabase
        )
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        exit_price=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        stop_distance_pct=st.floats(min_value=0.01, max_value=0.10, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=5000)
    def test_r_multiple_calculation_long(self, entry_price, exit_price, stop_distance_pct):
        """
        **Feature: momentum-wave-rider, Property 17: R-Multiple Logging**
        **Validates: Requirements 8.4**
        
        For any long position, R-multiple should be:
        - Positive when exit > entry
        - Negative when exit < entry
        - Proportional to (exit - entry) / (entry - stop)
        """
        # Set up mock position
        self.mock_position.side = 'buy'
        self.mock_position.avg_entry_price = entry_price
        self.mock_position.current_price = exit_price
        self.mock_position.stop_loss = entry_price * (1 - stop_distance_pct)
        
        # Calculate R-multiple
        r_multiple = self.position_manager._calculate_r_multiple(self.mock_position)
        
        # Calculate expected R-multiple
        risk = entry_price - self.mock_position.stop_loss
        reward = exit_price - entry_price
        expected_r = reward / risk if risk > 0 else 0
        
        # Verify sign correctness
        if exit_price > entry_price:
            assert r_multiple > 0, f"R-multiple should be positive for profit, got {r_multiple}"
        elif exit_price < entry_price:
            assert r_multiple < 0, f"R-multiple should be negative for loss, got {r_multiple}"
        
        # Verify calculation accuracy (within rounding tolerance)
        assert abs(r_multiple - round(expected_r, 2)) < 0.01, (
            f"R-multiple {r_multiple} doesn't match expected {expected_r:.2f}"
        )


    @given(
        entry_price=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        exit_price=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        stop_distance_pct=st.floats(min_value=0.01, max_value=0.10, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=5000)
    def test_r_multiple_calculation_short(self, entry_price, exit_price, stop_distance_pct):
        """
        For any short position, R-multiple should be:
        - Positive when exit < entry (profit on short)
        - Negative when exit > entry (loss on short)
        """
        # Set up mock position for short
        self.mock_position.side = 'sell'
        self.mock_position.avg_entry_price = entry_price
        self.mock_position.current_price = exit_price
        self.mock_position.stop_loss = entry_price * (1 + stop_distance_pct)
        
        # Calculate R-multiple
        r_multiple = self.position_manager._calculate_r_multiple(self.mock_position)
        
        # Verify sign correctness for short positions
        if exit_price < entry_price:
            assert r_multiple > 0, f"Short R-multiple should be positive for profit, got {r_multiple}"
        elif exit_price > entry_price:
            assert r_multiple < 0, f"Short R-multiple should be negative for loss, got {r_multiple}"
    
    def test_r_multiple_no_stop_loss(self):
        """
        Test R-multiple calculation when no stop loss is set.
        Should use default 1.5% stop distance.
        """
        self.mock_position.side = 'buy'
        self.mock_position.avg_entry_price = 100.0
        self.mock_position.current_price = 103.0  # 3% profit
        self.mock_position.stop_loss = None
        
        r_multiple = self.position_manager._calculate_r_multiple(self.mock_position)
        
        # With 1.5% default stop, 3% profit = 2R
        # Risk = 100 * 0.015 = 1.5
        # Reward = 3
        # R = 3 / 1.5 = 2.0
        assert abs(r_multiple - 2.0) < 0.1, f"Expected ~2.0R, got {r_multiple}"
    
    def test_r_multiple_exact_stop_hit(self):
        """
        Test R-multiple when exit price equals stop loss.
        Should be exactly -1R.
        """
        self.mock_position.side = 'buy'
        self.mock_position.avg_entry_price = 100.0
        self.mock_position.stop_loss = 98.0  # 2% stop
        self.mock_position.current_price = 98.0  # Exit at stop
        
        r_multiple = self.position_manager._calculate_r_multiple(self.mock_position)
        
        # Exit at stop = -1R
        assert abs(r_multiple - (-1.0)) < 0.01, f"Expected -1.0R at stop, got {r_multiple}"
    
    def test_r_multiple_2r_profit(self):
        """
        Test R-multiple for 2R profit scenario.
        """
        self.mock_position.side = 'buy'
        self.mock_position.avg_entry_price = 100.0
        self.mock_position.stop_loss = 98.0  # 2% stop = $2 risk
        self.mock_position.current_price = 104.0  # $4 profit = 2R
        
        r_multiple = self.position_manager._calculate_r_multiple(self.mock_position)
        
        assert abs(r_multiple - 2.0) < 0.01, f"Expected 2.0R, got {r_multiple}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
