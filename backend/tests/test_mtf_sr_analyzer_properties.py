"""
Property-Based Tests for Multi-Timeframe Support/Resistance Analyzer.

Uses Hypothesis to verify S/R position sizing properties.

**Feature: multi-timeframe-analysis**
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.mtf.sr_analyzer import SupportResistanceAnalyzer
from trading.mtf.models import SRLevels, TimeframeFeatures, MTFFeatures


settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=50)


def create_sr_levels(
    price: float,
    support_distance_pct: float = 1.0,
    resistance_distance_pct: float = 1.0,
) -> SRLevels:
    """Create SRLevels with specified distances from price."""
    return SRLevels(
        nearest_support=price * (1 - support_distance_pct / 100),
        nearest_resistance=price * (1 + resistance_distance_pct / 100),
        daily_high=price * 1.02,
        daily_low=price * 0.98,
        daily_close=price,
        swing_highs=[price * 1.01, price * 1.02],
        swing_lows=[price * 0.99, price * 0.98],
    )


class TestSRPositionSizingProperties:
    """Property tests for S/R position sizing."""

    @given(
        price=st.floats(min_value=10, max_value=1000, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_property_6_buy_near_resistance_reduces_size(self, price: float):
        """
        **Feature: multi-timeframe-analysis, Property 6: Support/Resistance Position Sizing**
        
        For any buy entry within 0.3% of a 15-minute resistance level,
        position size should be reduced by 30%.
        
        **Validates: Requirements 4.3**
        """
        analyzer = SupportResistanceAnalyzer()
        
        # Create S/R levels where resistance is within 0.3% of price
        sr_levels = SRLevels(
            nearest_support=price * 0.98,
            nearest_resistance=price * 1.002,  # 0.2% above price (within 0.3%)
            daily_high=price * 1.02,
            daily_low=price * 0.98,
            daily_close=price,
            swing_highs=[],
            swing_lows=[],
        )
        
        multiplier = analyzer.get_position_size_multiplier(price, 'buy', sr_levels)
        
        assert multiplier == 0.7, (
            f"Buy near resistance should reduce size to 0.7x, got {multiplier}"
        )

    @given(
        price=st.floats(min_value=10, max_value=1000, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_property_6_sell_near_support_reduces_size(self, price: float):
        """
        **Feature: multi-timeframe-analysis, Property 6: Support/Resistance Position Sizing**
        
        For any sell entry within 0.3% of a 15-minute support level,
        position size should be reduced by 30%.
        
        **Validates: Requirements 4.4**
        """
        analyzer = SupportResistanceAnalyzer()
        
        # Create S/R levels where support is within 0.3% of price
        sr_levels = SRLevels(
            nearest_support=price * 0.998,  # 0.2% below price (within 0.3%)
            nearest_resistance=price * 1.02,
            daily_high=price * 1.02,
            daily_low=price * 0.98,
            daily_close=price,
            swing_highs=[],
            swing_lows=[],
        )
        
        multiplier = analyzer.get_position_size_multiplier(price, 'sell', sr_levels)
        
        assert multiplier == 0.7, (
            f"Sell near support should reduce size to 0.7x, got {multiplier}"
        )

    @given(
        price=st.floats(min_value=10, max_value=1000, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_buy_not_near_resistance_full_size(self, price: float):
        """
        Test that buy not near resistance gets full position size.
        
        **Validates: Requirements 4.3**
        """
        analyzer = SupportResistanceAnalyzer()
        
        # Create S/R levels where resistance is far from price (> 0.3%)
        sr_levels = SRLevels(
            nearest_support=price * 0.98,
            nearest_resistance=price * 1.01,  # 1% above price (> 0.3%)
            daily_high=price * 1.02,
            daily_low=price * 0.98,
            daily_close=price,
            swing_highs=[],
            swing_lows=[],
        )
        
        multiplier = analyzer.get_position_size_multiplier(price, 'buy', sr_levels)
        
        assert multiplier == 1.0, (
            f"Buy not near resistance should get full size (1.0x), got {multiplier}"
        )

    @given(
        price=st.floats(min_value=10, max_value=1000, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_sell_not_near_support_full_size(self, price: float):
        """
        Test that sell not near support gets full position size.
        
        **Validates: Requirements 4.4**
        """
        analyzer = SupportResistanceAnalyzer()
        
        # Create S/R levels where support is far from price (> 0.3%)
        sr_levels = SRLevels(
            nearest_support=price * 0.99,  # 1% below price (> 0.3%)
            nearest_resistance=price * 1.02,
            daily_high=price * 1.02,
            daily_low=price * 0.98,
            daily_close=price,
            swing_highs=[],
            swing_lows=[],
        )
        
        multiplier = analyzer.get_position_size_multiplier(price, 'sell', sr_levels)
        
        assert multiplier == 1.0, (
            f"Sell not near support should get full size (1.0x), got {multiplier}"
        )


class TestSRLevelDetection:
    """Tests for S/R level detection."""

    def test_is_near_level_within_threshold(self):
        """Test that is_near_level returns True within threshold."""
        analyzer = SupportResistanceAnalyzer()
        
        price = 100.0
        level = 100.2  # 0.2% away
        
        assert analyzer.is_near_level(price, level, threshold_pct=0.3)

    def test_is_near_level_outside_threshold(self):
        """Test that is_near_level returns False outside threshold."""
        analyzer = SupportResistanceAnalyzer()
        
        price = 100.0
        level = 101.0  # 1% away
        
        assert not analyzer.is_near_level(price, level, threshold_pct=0.3)

    def test_stop_level_for_buy(self):
        """Test that stop level is below support for buy."""
        analyzer = SupportResistanceAnalyzer()
        
        price = 100.0
        sr_levels = create_sr_levels(price)
        
        stop = analyzer.get_stop_level(price, 'buy', sr_levels)
        
        assert stop < sr_levels.nearest_support, (
            f"Stop ({stop}) should be below support ({sr_levels.nearest_support})"
        )

    def test_stop_level_for_sell(self):
        """Test that stop level is above resistance for sell."""
        analyzer = SupportResistanceAnalyzer()
        
        price = 100.0
        sr_levels = create_sr_levels(price)
        
        stop = analyzer.get_stop_level(price, 'sell', sr_levels)
        
        assert stop > sr_levels.nearest_resistance, (
            f"Stop ({stop}) should be above resistance ({sr_levels.nearest_resistance})"
        )

    def test_target_level_for_buy(self):
        """Test that target is at resistance for buy."""
        analyzer = SupportResistanceAnalyzer()
        
        price = 100.0
        sr_levels = create_sr_levels(price)
        
        target = analyzer.get_target_level(price, 'buy', sr_levels)
        
        assert target == sr_levels.nearest_resistance, (
            f"Target ({target}) should be at resistance ({sr_levels.nearest_resistance})"
        )

    def test_target_level_for_sell(self):
        """Test that target is at support for sell."""
        analyzer = SupportResistanceAnalyzer()
        
        price = 100.0
        sr_levels = create_sr_levels(price)
        
        target = analyzer.get_target_level(price, 'sell', sr_levels)
        
        assert target == sr_levels.nearest_support, (
            f"Target ({target}) should be at support ({sr_levels.nearest_support})"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
