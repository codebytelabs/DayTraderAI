"""
Property-Based Tests for MTF Confidence Calculator.

Uses Hypothesis to verify timeframe weight calculation properties.

**Feature: multi-timeframe-analysis**
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.mtf.confidence_calculator import MTFConfidenceCalculator
from trading.mtf.models import TimeframeFeatures, MTFFeatures, TrendBias, TrendDirection, MTFConfig


settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=50)


def create_timeframe_features(timeframe: str, adx: float = 25.0) -> TimeframeFeatures:
    """Create TimeframeFeatures with specified ADX."""
    return TimeframeFeatures(
        timeframe=timeframe,
        ema_short=100.0,
        ema_long=100.0,
        ema_50=100.0,
        ema_200=100.0,
        rsi=50.0,
        macd=0.0,
        macd_signal=0.0,
        macd_histogram=0.0,
        adx=adx,
        volume=10000,
        volume_avg=10000,
        volume_ratio=1.0,
        high=101.0,
        low=99.0,
        close=100.0,
    )


def create_mtf_features(adx_15min: float = 25.0) -> MTFFeatures:
    """Create MTFFeatures with specified 15-min ADX."""
    return MTFFeatures(
        symbol='TEST',
        tf_1min=create_timeframe_features('1min'),
        tf_5min=create_timeframe_features('5min'),
        tf_15min=create_timeframe_features('15min', adx=adx_15min),
        tf_daily=create_timeframe_features('daily'),
        timestamp=datetime.now(timezone.utc),
    )


class TestTimeframeWeightProperties:
    """Property tests for timeframe weight calculation."""

    def test_property_7_default_weights_sum_to_one(self):
        """
        **Feature: multi-timeframe-analysis, Property 7: Timeframe Weight Calculation**
        
        With default settings, weights should sum to 100% with 15-min at 40%, 5-min at 35%, 1-min at 25%.
        
        **Validates: Requirements 5.1**
        """
        calculator = MTFConfidenceCalculator()
        features = create_mtf_features(adx_15min=20.0)  # Below threshold
        
        weights = calculator.get_effective_weights(features)
        
        # Check default weights
        assert abs(weights['15min'] - 0.40) < 0.01, f"15min should be 0.40, got {weights['15min']}"
        assert abs(weights['5min'] - 0.35) < 0.01, f"5min should be 0.35, got {weights['5min']}"
        assert abs(weights['1min'] - 0.25) < 0.01, f"1min should be 0.25, got {weights['1min']}"
        
        # Check sum
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01, f"Weights should sum to 1.0, got {total}"

    @given(
        adx=st.floats(min_value=26, max_value=100, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_property_7_strong_trend_increases_15min_weight(self, adx: float):
        """
        **Feature: multi-timeframe-analysis, Property 7: Timeframe Weight Calculation**
        
        When 15-min ADX > 25, the 15-min weight should increase to 50%.
        
        **Validates: Requirements 5.2**
        """
        calculator = MTFConfidenceCalculator()
        features = create_mtf_features(adx_15min=adx)
        
        weights = calculator.get_effective_weights(features)
        
        assert weights['15min'] == 0.50, (
            f"15min weight should be 0.50 when ADX={adx}, got {weights['15min']}"
        )

    @given(
        adx=st.floats(min_value=0, max_value=24.9, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_weak_trend_keeps_default_weights(self, adx: float):
        """
        Test that weak trend (ADX <= 25) keeps default weights.
        
        **Validates: Requirements 5.1, 5.2**
        """
        calculator = MTFConfidenceCalculator()
        features = create_mtf_features(adx_15min=adx)
        
        weights = calculator.get_effective_weights(features)
        
        assert weights['15min'] == 0.40, (
            f"15min weight should be 0.40 when ADX={adx}, got {weights['15min']}"
        )


class TestAlignmentBonus:
    """Tests for alignment bonus."""

    @given(
        base_confidence=st.floats(min_value=0, max_value=80, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_alignment_bonus_adds_20_points(self, base_confidence: float):
        """
        Test that full alignment adds 20 points.
        
        **Validates: Requirements 5.3**
        """
        calculator = MTFConfidenceCalculator()
        
        adjusted = calculator.apply_alignment_bonus(base_confidence, all_aligned=True)
        
        expected = min(100.0, base_confidence + 20)
        assert abs(adjusted - expected) < 0.01, (
            f"Should add 20 points: {base_confidence} + 20 = {expected}, got {adjusted}"
        )

    @given(
        base_confidence=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_no_bonus_when_not_aligned(self, base_confidence: float):
        """
        Test that no bonus is added when not aligned.
        
        **Validates: Requirements 5.3**
        """
        calculator = MTFConfidenceCalculator()
        
        adjusted = calculator.apply_alignment_bonus(base_confidence, all_aligned=False)
        
        assert adjusted == base_confidence, (
            f"Should not change: {base_confidence}, got {adjusted}"
        )

    def test_alignment_bonus_capped_at_100(self):
        """Test that confidence is capped at 100."""
        calculator = MTFConfidenceCalculator()
        
        adjusted = calculator.apply_alignment_bonus(90.0, all_aligned=True)
        
        assert adjusted == 100.0, f"Should be capped at 100, got {adjusted}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
