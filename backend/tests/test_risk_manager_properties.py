#!/usr/bin/env python3
"""
Property-Based Tests for RiskManager

Tests correctness properties for momentum wave rider risk management:
- Minimum stop distance enforcement (1.5%)
- Max risk per trade limit (1%)
- Stop loss invariant (always present)

**Feature: momentum-wave-rider**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import MagicMock, patch


class TestRiskManagerProperties:
    """Property-based tests for RiskManager momentum enhancements."""
    
    def setup_method(self):
        """Set up test fixtures with mocked dependencies."""
        # Mock the AlpacaClient
        self.mock_alpaca = MagicMock()
        self.mock_alpaca.is_market_open.return_value = True
        
        # Mock account
        mock_account = MagicMock()
        mock_account.equity = "100000.00"
        mock_account.cash = "50000.00"
        mock_account.buying_power = "200000.00"
        mock_account.daytrading_buying_power = "400000.00"
        mock_account.pattern_day_trader = True
        self.mock_alpaca.get_account.return_value = mock_account
        
        # Mock latest bars
        mock_bar = MagicMock()
        mock_bar.close = 100.0
        self.mock_alpaca.get_latest_bars.return_value = {'TEST': mock_bar}
        
        # Import and create RiskManager with mocks
        with patch('trading.risk_manager.get_regime_detector') as mock_regime:
            mock_regime.return_value = MagicMock()
            mock_regime.return_value.detect_regime.return_value = {
                'regime': 'trending',
                'volatility_level': 'normal'
            }
            mock_regime.return_value.last_update = None
            
            from trading.risk_manager import RiskManager
            self.risk_manager = RiskManager(self.mock_alpaca)
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        atr=st.floats(min_value=0.01, max_value=5.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=5000)
    def test_minimum_stop_distance_enforcement(self, entry_price, atr):
        """
        **Feature: momentum-wave-rider, Property 14: Minimum Stop Distance**
        **Validates: Requirements 6.1**
        
        For any entry price and ATR, the calculated stop price must be
        at least 1.5% away from entry.
        """
        # Calculate stop for long position
        stop_price = self.risk_manager.calculate_stop_price(entry_price, 'buy', atr)
        
        # Calculate actual distance
        stop_distance = entry_price - stop_price
        stop_distance_pct = stop_distance / entry_price
        
        # Must be at least 1.5%
        min_distance_pct = self.risk_manager.MIN_STOP_DISTANCE_PCT
        
        assert stop_distance_pct >= min_distance_pct - 0.0001, (
            f"Stop distance {stop_distance_pct*100:.2f}% is below "
            f"minimum {min_distance_pct*100:.1f}% for entry ${entry_price:.2f}"
        )
        
        # Also test short position
        stop_price_short = self.risk_manager.calculate_stop_price(entry_price, 'sell', atr)
        stop_distance_short = stop_price_short - entry_price
        stop_distance_pct_short = stop_distance_short / entry_price
        
        assert stop_distance_pct_short >= min_distance_pct - 0.0001, (
            f"Short stop distance {stop_distance_pct_short*100:.2f}% is below "
            f"minimum {min_distance_pct*100:.1f}%"
        )


    @given(
        equity=st.floats(min_value=10000.0, max_value=1000000.0, allow_nan=False, allow_infinity=False),
        entry_price=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        stop_distance_pct=st.floats(min_value=0.015, max_value=0.10, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=5000)
    def test_risk_per_trade_limit(self, equity, entry_price, stop_distance_pct):
        """
        **Feature: momentum-wave-rider, Property 15: Risk Per Trade Limit**
        **Validates: Requirements 6.2**
        
        For any equity and position, the risk per trade must not exceed 1%.
        """
        stop_price = entry_price * (1 - stop_distance_pct)
        stop_distance = entry_price - stop_price
        
        # Calculate max position size
        max_shares = self.risk_manager.get_max_position_size(
            entry_price=entry_price,
            stop_price=stop_price,
            equity=equity
        )
        
        # Calculate actual risk
        actual_risk = max_shares * stop_distance
        actual_risk_pct = actual_risk / equity
        
        # Risk must not exceed 1% (with small tolerance for rounding)
        max_risk_pct = self.risk_manager.MAX_RISK_PER_TRADE_PCT
        
        assert actual_risk_pct <= max_risk_pct + 0.001, (
            f"Risk per trade {actual_risk_pct*100:.2f}% exceeds "
            f"maximum {max_risk_pct*100:.1f}%"
        )
    
    @given(
        entry_price=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        stop_price=st.floats(min_value=5.0, max_value=495.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_stop_loss_validation(self, entry_price, stop_price):
        """
        **Feature: momentum-wave-rider, Property 16: Stop Loss Invariant**
        **Validates: Requirements 6.5**
        
        For any entry and stop price, validation correctly identifies
        whether the stop distance meets minimum requirements.
        """
        assume(stop_price < entry_price)  # Valid long stop
        
        is_valid, reason = self.risk_manager.validate_stop_distance(entry_price, stop_price)
        
        stop_distance_pct = (entry_price - stop_price) / entry_price
        min_distance_pct = self.risk_manager.MIN_STOP_DISTANCE_PCT
        
        if stop_distance_pct >= min_distance_pct:
            assert is_valid, f"Should be valid: {stop_distance_pct*100:.2f}% >= {min_distance_pct*100:.1f}%"
        else:
            assert not is_valid, f"Should be invalid: {stop_distance_pct*100:.2f}% < {min_distance_pct*100:.1f}%"
    
    def test_consecutive_loss_tracking(self):
        """
        Test that consecutive losses are tracked correctly.
        """
        # Initially zero
        assert self.risk_manager.get_consecutive_losses() == 0
        
        # Record 3 losses
        self.risk_manager.record_trade_result(is_win=False)
        assert self.risk_manager.get_consecutive_losses() == 1
        
        self.risk_manager.record_trade_result(is_win=False)
        assert self.risk_manager.get_consecutive_losses() == 2
        
        self.risk_manager.record_trade_result(is_win=False)
        assert self.risk_manager.get_consecutive_losses() == 3
        
        # Win resets counter
        self.risk_manager.record_trade_result(is_win=True)
        assert self.risk_manager.get_consecutive_losses() == 0
    
    def test_consecutive_loss_size_reduction(self):
        """
        Test that position size is reduced after consecutive losses.
        """
        equity = 100000.0
        entry_price = 100.0
        stop_price = 98.0  # 2% stop
        
        # Get normal position size
        normal_size = self.risk_manager.get_max_position_size(
            entry_price=entry_price,
            stop_price=stop_price,
            equity=equity
        )
        
        # Record 3 consecutive losses
        for _ in range(3):
            self.risk_manager.record_trade_result(is_win=False)
        
        # Get reduced position size
        reduced_size = self.risk_manager.get_max_position_size(
            entry_price=entry_price,
            stop_price=stop_price,
            equity=equity
        )
        
        # Should be reduced by 50%
        expected_reduction = self.risk_manager.CONSECUTIVE_LOSS_REDUCTION
        expected_size = int(normal_size * expected_reduction)
        
        assert reduced_size <= expected_size + 1, (
            f"Position size should be reduced to ~{expected_size} shares, got {reduced_size}"
        )
    
    def test_daily_loss_circuit_breaker(self):
        """
        Test daily loss circuit breaker detection.
        """
        # Mock trading state metrics
        with patch('trading.risk_manager.trading_state') as mock_state:
            mock_metrics = MagicMock()
            mock_metrics.daily_pl_pct = -2.5  # 2.5% loss
            mock_state.get_metrics.return_value = mock_metrics
            
            is_reached, daily_pnl = self.risk_manager.is_daily_loss_limit_reached()
            
            assert is_reached, "Should trigger circuit breaker at 2.5% loss"
            assert daily_pnl == -0.025, f"Daily PnL should be -2.5%, got {daily_pnl*100}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
