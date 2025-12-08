"""
Property-Based Tests for MTF Volume Analyzer.

Uses Hypothesis to verify volume confirmation properties.

**Feature: multi-timeframe-analysis**
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.mtf.volume_analyzer import VolumeAnalyzer
from trading.mtf.models import TimeframeFeatures, MTFFeatures


settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=50)


def create_timeframe_features(
    timeframe: str, 
    volume_ratio: float = 1.0
) -> TimeframeFeatures:
    """Create TimeframeFeatures with specified volume ratio."""
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
        adx=25.0,
        volume=10000 * volume_ratio,
        volume_avg=10000,
        volume_ratio=volume_ratio,
        high=101.0,
        low=99.0,
        close=100.0,
    )


def create_mtf_features(
    vol_5min: float = 1.0, 
    vol_15min: float = 1.0
) -> MTFFeatures:
    """Create MTFFeatures with specified volume ratios."""
    return MTFFeatures(
        symbol='TEST',
        tf_1min=create_timeframe_features('1min'),
        tf_5min=create_timeframe_features('5min', volume_ratio=vol_5min),
        tf_15min=create_timeframe_features('15min', volume_ratio=vol_15min),
        tf_daily=create_timeframe_features('daily'),
        timestamp=datetime.now(timezone.utc),
    )


class TestVolumeConfirmationProperties:
    """Property tests for volume confirmation."""

    @given(
        vol_ratio=st.floats(min_value=1.51, max_value=10.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_9_volume_confirmation_above_threshold(self, vol_ratio: float):
        """
        **Feature: multi-timeframe-analysis, Property 9: Volume Confirmation Logic**
        
        Volume confirmation is added when 5-minute volume exceeds 1.5x the 20-period average.
        
        **Validates: Requirements 6.2**
        """
        analyzer = VolumeAnalyzer()
        features = create_mtf_features(vol_5min=vol_ratio)
        
        is_confirmed = analyzer.check_volume_confirmation(features)
        
        assert is_confirmed, (
            f"Volume should be confirmed when ratio={vol_ratio} > 1.5"
        )

    @given(
        vol_ratio=st.floats(min_value=0.0, max_value=1.49, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_9_no_confirmation_below_threshold(self, vol_ratio: float):
        """
        **Feature: multi-timeframe-analysis, Property 9: Volume Confirmation Logic**
        
        No volume confirmation when 5-minute volume is below 1.5x average.
        
        **Validates: Requirements 6.2**
        """
        analyzer = VolumeAnalyzer()
        features = create_mtf_features(vol_5min=vol_ratio)
        
        is_confirmed = analyzer.check_volume_confirmation(features)
        
        assert not is_confirmed, (
            f"Volume should not be confirmed when ratio={vol_ratio} <= 1.5"
        )

    @given(
        vol_ratio=st.floats(min_value=0.0, max_value=0.69, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_9_low_volume_penalty(self, vol_ratio: float):
        """
        **Feature: multi-timeframe-analysis, Property 9: Volume Confirmation Logic**
        
        MTF confidence is reduced by 10 points when 15-minute volume is below 0.7x average.
        
        **Validates: Requirements 6.3**
        """
        analyzer = VolumeAnalyzer()
        features = create_mtf_features(vol_15min=vol_ratio)
        
        penalty = analyzer.get_volume_penalty(features)
        
        assert penalty == -10, (
            f"Should have -10 penalty when 15min vol={vol_ratio} < 0.7, got {penalty}"
        )

    @given(
        vol_ratio=st.floats(min_value=0.71, max_value=10.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_no_penalty_above_threshold(self, vol_ratio: float):
        """
        Test that no penalty when 15-min volume is above 0.7x average.
        
        **Validates: Requirements 6.3**
        """
        analyzer = VolumeAnalyzer()
        features = create_mtf_features(vol_15min=vol_ratio)
        
        penalty = analyzer.get_volume_penalty(features)
        
        assert penalty == 0, (
            f"Should have no penalty when 15min vol={vol_ratio} >= 0.7, got {penalty}"
        )


class TestVolumeScoreCalculation:
    """Tests for volume score calculation."""

    def test_high_volume_gives_bonus(self):
        """Test that high volume on 5-min gives bonus."""
        analyzer = VolumeAnalyzer()
        features = create_mtf_features(vol_5min=2.0, vol_15min=1.5)
        
        score = analyzer.get_volume_score(features, 'buy')
        
        # Should get confirmation bonus (10) + alignment bonus (10) = 20
        assert score >= 10, f"High volume should give positive score, got {score}"

    def test_low_volume_gives_penalty(self):
        """Test that low volume on 15-min gives penalty."""
        analyzer = VolumeAnalyzer()
        features = create_mtf_features(vol_5min=0.5, vol_15min=0.5)
        
        score = analyzer.get_volume_score(features, 'buy')
        
        # Should get penalty (-10)
        assert score < 0, f"Low volume should give negative score, got {score}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
