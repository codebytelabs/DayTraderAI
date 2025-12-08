"""
Property-Based Tests for MTF Signal Filter.

Uses Hypothesis to verify confidence-based and ADX-based position sizing.

**Feature: multi-timeframe-analysis**
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.mtf.signal_filter import MTFSignalFilter
from trading.mtf.models import TimeframeFeatures, MTFFeatures, MTFConfig, SRLevels


settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=50)


def create_timeframe_features(
    timeframe: str,
    adx: float = 25.0,
    ema_50: float = 100.0,
    ema_200: float = 100.0,
    rsi: float = 50.0,
    macd_histogram: float = 0.0,
) -> TimeframeFeatures:
    """Create TimeframeFeatures with specified values."""
    return TimeframeFeatures(
        timeframe=timeframe,
        ema_short=100.0,
        ema_long=100.0,
        ema_50=ema_50,
        ema_200=ema_200,
        rsi=rsi,
        macd=0.0,
        macd_signal=0.0,
        macd_histogram=macd_histogram,
        adx=adx,
        volume=10000,
        volume_avg=10000,
        volume_ratio=1.0,
        high=101.0,
        low=99.0,
        close=100.0,
    )


def create_mtf_features_with_adx(
    adx_1min: float = 25.0,
    adx_5min: float = 25.0,
    adx_15min: float = 25.0,
) -> MTFFeatures:
    """Create MTFFeatures with specified ADX values."""
    return MTFFeatures(
        symbol='TEST',
        tf_1min=create_timeframe_features('1min', adx=adx_1min),
        tf_5min=create_timeframe_features('5min', adx=adx_5min),
        tf_15min=create_timeframe_features('15min', adx=adx_15min),
        tf_daily=create_timeframe_features('daily'),
        timestamp=datetime.now(timezone.utc),
    )


class TestConfidenceBasedSizingProperties:
    """Property tests for confidence-based position sizing."""

    @given(
        confidence=st.floats(min_value=0, max_value=59.9, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_8_reject_below_60(self, confidence: float):
        """
        **Feature: multi-timeframe-analysis, Property 8: Confidence-Based Position Sizing**
        
        Below 60: Signal rejected (0.0x position size).
        
        **Validates: Requirements 5.4**
        """
        signal_filter = MTFSignalFilter()
        
        should_reject, reason = signal_filter.should_reject(confidence, trend_aligned=True)
        
        assert should_reject, f"Should reject when confidence={confidence} < 60"
        assert reason is not None, "Should have rejection reason"

    @given(
        confidence=st.floats(min_value=60, max_value=69.9, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_8_reduced_size_60_to_70(self, confidence: float):
        """
        **Feature: multi-timeframe-analysis, Property 8: Confidence-Based Position Sizing**
        
        60-70: Position size = 0.7x normal.
        
        **Validates: Requirements 5.6**
        """
        signal_filter = MTFSignalFilter()
        features = create_mtf_features_with_adx()
        sr_levels = SRLevels(
            nearest_support=95.0,
            nearest_resistance=105.0,
            daily_high=102.0,
            daily_low=98.0,
            daily_close=100.0,
        )
        
        multiplier = signal_filter._calculate_position_multiplier(
            confidence, features, 'buy', sr_levels
        )
        
        # Base multiplier should be 0.7 (may be adjusted by ADX)
        assert multiplier <= 0.7, (
            f"Multiplier should be <= 0.7 for confidence={confidence}, got {multiplier}"
        )

    @given(
        confidence=st.floats(min_value=70, max_value=79.9, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_8_normal_size_70_to_80(self, confidence: float):
        """
        **Feature: multi-timeframe-analysis, Property 8: Confidence-Based Position Sizing**
        
        70-80: Position size = 1.0x normal.
        
        **Validates: Requirements 5.5**
        """
        signal_filter = MTFSignalFilter()
        features = create_mtf_features_with_adx(adx_1min=30, adx_5min=30, adx_15min=30)
        sr_levels = SRLevels(
            nearest_support=95.0,
            nearest_resistance=105.0,
            daily_high=102.0,
            daily_low=98.0,
            daily_close=100.0,
        )
        
        multiplier = signal_filter._calculate_position_multiplier(
            confidence, features, 'buy', sr_levels
        )
        
        assert multiplier == 1.0, (
            f"Multiplier should be 1.0 for confidence={confidence}, got {multiplier}"
        )

    @given(
        confidence=st.floats(min_value=80.1, max_value=100, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_8_increased_size_above_80(self, confidence: float):
        """
        **Feature: multi-timeframe-analysis, Property 8: Confidence-Based Position Sizing**
        
        Above 80: Position size = up to 1.5x normal.
        
        **Validates: Requirements 5.5**
        """
        signal_filter = MTFSignalFilter()
        features = create_mtf_features_with_adx(adx_1min=30, adx_5min=30, adx_15min=30)
        sr_levels = SRLevels(
            nearest_support=95.0,
            nearest_resistance=105.0,
            daily_high=102.0,
            daily_low=98.0,
            daily_close=100.0,
        )
        
        multiplier = signal_filter._calculate_position_multiplier(
            confidence, features, 'buy', sr_levels
        )
        
        assert multiplier == 1.5, (
            f"Multiplier should be 1.5 for confidence={confidence}, got {multiplier}"
        )


class TestADXBasedSizingProperties:
    """Property tests for ADX-based position sizing."""

    @given(
        adx=st.floats(min_value=0, max_value=19.9, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_10_ranging_market_reduction(self, adx: float):
        """
        **Feature: multi-timeframe-analysis, Property 10: ADX-Based Position Sizing**
        
        If more than one timeframe has ADX < 20 (ranging), reduce position size by 40%.
        
        **Validates: Requirements 7.3**
        """
        signal_filter = MTFSignalFilter()
        
        # Create features with 2 ranging timeframes
        features = create_mtf_features_with_adx(
            adx_1min=adx,
            adx_5min=adx,
            adx_15min=30.0,  # One trending
        )
        
        multiplier = signal_filter._get_adx_multiplier(features)
        
        assert multiplier == 0.6, (
            f"Should reduce by 40% (0.6x) when 2 TFs have ADX={adx} < 20, got {multiplier}"
        )

    @given(
        adx=st.floats(min_value=26, max_value=100, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_10_trending_market_full_size(self, adx: float):
        """
        **Feature: multi-timeframe-analysis, Property 10: ADX-Based Position Sizing**
        
        If all timeframes have ADX > 25 (trending), allow full position sizing.
        
        **Validates: Requirements 7.4**
        """
        signal_filter = MTFSignalFilter()
        
        # Create features with all trending timeframes
        features = create_mtf_features_with_adx(
            adx_1min=adx,
            adx_5min=adx,
            adx_15min=adx,
        )
        
        multiplier = signal_filter._get_adx_multiplier(features)
        
        assert multiplier == 1.0, (
            f"Should allow full size (1.0x) when all TFs have ADX={adx} > 25, got {multiplier}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
