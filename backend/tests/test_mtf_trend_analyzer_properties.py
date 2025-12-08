"""
Property-Based Tests for Multi-Timeframe Trend Analyzer.

Uses Hypothesis to verify trend classification and signal alignment properties.

**Feature: multi-timeframe-analysis**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.mtf.trend_analyzer import TrendAnalyzer
from trading.mtf.models import (
    TrendBias,
    TrendDirection,
    TimeframeFeatures,
    MTFFeatures,
)


# Configure Hypothesis for CI
settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=50)


def create_timeframe_features(
    timeframe: str,
    ema_50: float,
    ema_200: float,
    close: float = 100.0,
) -> TimeframeFeatures:
    """Create TimeframeFeatures with specified EMA values."""
    return TimeframeFeatures(
        timeframe=timeframe,
        ema_short=close * 0.99,
        ema_long=close * 1.01,
        ema_50=ema_50,
        ema_200=ema_200,
        rsi=50.0,
        macd=0.0,
        macd_signal=0.0,
        macd_histogram=0.0,
        adx=25.0,
        volume=10000,
        volume_avg=10000,
        volume_ratio=1.0,
        high=close * 1.01,
        low=close * 0.99,
        close=close,
    )


def create_mtf_features(
    symbol: str,
    ema_50_15min: float,
    ema_200_15min: float,
    ema_50_daily: float,
    ema_200_daily: float,
    close: float = 100.0,
) -> MTFFeatures:
    """Create MTFFeatures with specified EMA values for 15min and daily."""
    return MTFFeatures(
        symbol=symbol,
        tf_1min=create_timeframe_features('1min', close, close, close),
        tf_5min=create_timeframe_features('5min', close, close, close),
        tf_15min=create_timeframe_features('15min', ema_50_15min, ema_200_15min, close),
        tf_daily=create_timeframe_features('daily', ema_50_daily, ema_200_daily, close),
        timestamp=datetime.now(timezone.utc),
    )


class TestTrendClassificationProperties:
    """Property tests for trend classification."""

    @given(
        ema_50=st.floats(min_value=1, max_value=1000, allow_nan=False, allow_infinity=False),
        ema_200=st.floats(min_value=1, max_value=1000, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_property_1_trend_classification_consistency(
        self, ema_50: float, ema_200: float
    ):
        """
        **Feature: multi-timeframe-analysis, Property 1: Trend Classification Consistency**
        
        For any 15-minute price data with EMA(50) and EMA(200) values, the trend classification should be:
        - Bullish when EMA(50) > EMA(200) by more than 0.1%
        - Bearish when EMA(50) < EMA(200) by more than 0.1%
        - Neutral when EMAs are within 0.1% of each other
        
        **Validates: Requirements 2.2, 2.3, 2.4**
        """
        analyzer = TrendAnalyzer()
        
        # Create MTF features with the given EMA values
        features = create_mtf_features(
            symbol='TEST',
            ema_50_15min=ema_50,
            ema_200_15min=ema_200,
            ema_50_daily=100.0,  # Neutral daily
            ema_200_daily=100.0,
        )
        
        trend_bias = analyzer.get_trend_bias(features)
        
        # Calculate expected classification
        ema_diff_pct = ((ema_50 - ema_200) / ema_200) * 100
        threshold = 0.1
        
        if ema_diff_pct > threshold:
            expected_direction = TrendDirection.BULLISH
        elif ema_diff_pct < -threshold:
            expected_direction = TrendDirection.BEARISH
        else:
            expected_direction = TrendDirection.NEUTRAL
        
        assert trend_bias.direction == expected_direction, (
            f"EMA diff {ema_diff_pct:.4f}% should classify as {expected_direction.value}, "
            f"got {trend_bias.direction.value}"
        )

    @given(
        ema_50=st.floats(min_value=100, max_value=200, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_bullish_trend_when_ema50_above_ema200(self, ema_50: float):
        """
        Test that trend is bullish when EMA(50) > EMA(200) by more than 0.1%.
        
        **Validates: Requirements 2.2**
        """
        # Set EMA(200) such that EMA(50) is more than 0.1% above
        ema_200 = ema_50 / 1.002  # EMA(50) is 0.2% above EMA(200)
        
        analyzer = TrendAnalyzer()
        features = create_mtf_features(
            symbol='TEST',
            ema_50_15min=ema_50,
            ema_200_15min=ema_200,
            ema_50_daily=100.0,
            ema_200_daily=100.0,
        )
        
        trend_bias = analyzer.get_trend_bias(features)
        
        assert trend_bias.direction == TrendDirection.BULLISH, (
            f"Should be bullish when EMA(50)={ema_50} > EMA(200)={ema_200}"
        )

    @given(
        ema_200=st.floats(min_value=100, max_value=200, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_bearish_trend_when_ema50_below_ema200(self, ema_200: float):
        """
        Test that trend is bearish when EMA(50) < EMA(200) by more than 0.1%.
        
        **Validates: Requirements 2.3**
        """
        # Set EMA(50) such that it's more than 0.1% below EMA(200)
        ema_50 = ema_200 / 1.002  # EMA(50) is 0.2% below EMA(200)
        
        analyzer = TrendAnalyzer()
        features = create_mtf_features(
            symbol='TEST',
            ema_50_15min=ema_50,
            ema_200_15min=ema_200,
            ema_50_daily=100.0,
            ema_200_daily=100.0,
        )
        
        trend_bias = analyzer.get_trend_bias(features)
        
        assert trend_bias.direction == TrendDirection.BEARISH, (
            f"Should be bearish when EMA(50)={ema_50} < EMA(200)={ema_200}"
        )


class TestSignalTrendAlignmentProperties:
    """Property tests for signal-trend alignment."""

    @given(
        ema_200=st.floats(min_value=100, max_value=200, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_property_2_buy_signal_rejected_in_bearish_trend(self, ema_200: float):
        """
        **Feature: multi-timeframe-analysis, Property 2: Signal-Trend Alignment Rejection**
        
        For any 1-minute buy signal with a bearish 15-minute trend bias, 
        the signal should be rejected.
        
        **Validates: Requirements 2.5, 7.1**
        """
        # Create bearish trend (EMA(50) < EMA(200) by more than 0.1%)
        ema_50 = ema_200 / 1.002  # 0.2% below
        
        analyzer = TrendAnalyzer()
        features = create_mtf_features(
            symbol='TEST',
            ema_50_15min=ema_50,
            ema_200_15min=ema_200,
            ema_50_daily=100.0,
            ema_200_daily=100.0,
        )
        
        trend_bias = analyzer.get_trend_bias(features)
        
        # Verify trend is bearish
        assert trend_bias.direction == TrendDirection.BEARISH
        
        # Buy signal should be rejected
        is_aligned, rejection_reason = analyzer.check_trend_alignment('buy', trend_bias)
        
        assert not is_aligned, "Buy signal should be rejected in bearish trend"
        assert rejection_reason is not None, "Should have rejection reason"
        assert "bearish" in rejection_reason.lower(), "Rejection should mention bearish trend"

    @given(
        ema_50=st.floats(min_value=100, max_value=200, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_property_2_sell_signal_rejected_in_bullish_trend(self, ema_50: float):
        """
        **Feature: multi-timeframe-analysis, Property 2: Signal-Trend Alignment Rejection**
        
        For any 1-minute sell signal with a bullish 15-minute trend bias, 
        the signal should be rejected.
        
        **Validates: Requirements 2.5, 7.1**
        """
        # Create bullish trend (EMA(50) > EMA(200) by more than 0.1%)
        ema_200 = ema_50 / 1.002  # EMA(50) is 0.2% above
        
        analyzer = TrendAnalyzer()
        features = create_mtf_features(
            symbol='TEST',
            ema_50_15min=ema_50,
            ema_200_15min=ema_200,
            ema_50_daily=100.0,
            ema_200_daily=100.0,
        )
        
        trend_bias = analyzer.get_trend_bias(features)
        
        # Verify trend is bullish
        assert trend_bias.direction == TrendDirection.BULLISH
        
        # Sell signal should be rejected
        is_aligned, rejection_reason = analyzer.check_trend_alignment('sell', trend_bias)
        
        assert not is_aligned, "Sell signal should be rejected in bullish trend"
        assert rejection_reason is not None, "Should have rejection reason"
        assert "bullish" in rejection_reason.lower(), "Rejection should mention bullish trend"

    @given(
        ema_50=st.floats(min_value=100, max_value=200, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_buy_signal_accepted_in_bullish_trend(self, ema_50: float):
        """
        Test that buy signals are accepted in bullish trends.
        
        **Validates: Requirements 2.5**
        """
        # Create bullish trend
        ema_200 = ema_50 / 1.002
        
        analyzer = TrendAnalyzer()
        features = create_mtf_features(
            symbol='TEST',
            ema_50_15min=ema_50,
            ema_200_15min=ema_200,
            ema_50_daily=100.0,
            ema_200_daily=100.0,
        )
        
        trend_bias = analyzer.get_trend_bias(features)
        is_aligned, rejection_reason = analyzer.check_trend_alignment('buy', trend_bias)
        
        assert is_aligned, "Buy signal should be accepted in bullish trend"
        assert rejection_reason is None, "Should have no rejection reason"

    @given(
        ema_200=st.floats(min_value=100, max_value=200, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_sell_signal_accepted_in_bearish_trend(self, ema_200: float):
        """
        Test that sell signals are accepted in bearish trends.
        
        **Validates: Requirements 2.5**
        """
        # Create bearish trend
        ema_50 = ema_200 / 1.002
        
        analyzer = TrendAnalyzer()
        features = create_mtf_features(
            symbol='TEST',
            ema_50_15min=ema_50,
            ema_200_15min=ema_200,
            ema_50_daily=100.0,
            ema_200_daily=100.0,
        )
        
        trend_bias = analyzer.get_trend_bias(features)
        is_aligned, rejection_reason = analyzer.check_trend_alignment('sell', trend_bias)
        
        assert is_aligned, "Sell signal should be accepted in bearish trend"
        assert rejection_reason is None, "Should have no rejection reason"


class TestDailyAlignmentBonus:
    """Tests for daily trend alignment bonus."""

    def test_daily_alignment_bonus_when_aligned(self):
        """
        Test that 15-point bonus is given when daily trend aligns.
        
        **Validates: Requirements 2.6**
        """
        analyzer = TrendAnalyzer()
        
        # Both 15min and daily are bullish
        features = create_mtf_features(
            symbol='TEST',
            ema_50_15min=102.0,  # Bullish
            ema_200_15min=100.0,
            ema_50_daily=102.0,  # Also bullish
            ema_200_daily=100.0,
        )
        
        trend_bias = analyzer.get_trend_bias(features)
        bonus = analyzer.get_daily_alignment_bonus(trend_bias)
        
        assert trend_bias.daily_aligned, "Daily should be aligned"
        assert bonus == 15, f"Bonus should be 15, got {bonus}"

    def test_no_bonus_when_not_aligned(self):
        """
        Test that no bonus is given when daily trend doesn't align.
        
        **Validates: Requirements 2.6**
        """
        analyzer = TrendAnalyzer()
        
        # 15min bullish, daily bearish
        features = create_mtf_features(
            symbol='TEST',
            ema_50_15min=102.0,  # Bullish
            ema_200_15min=100.0,
            ema_50_daily=98.0,   # Bearish
            ema_200_daily=100.0,
        )
        
        trend_bias = analyzer.get_trend_bias(features)
        bonus = analyzer.get_daily_alignment_bonus(trend_bias)
        
        assert not trend_bias.daily_aligned, "Daily should not be aligned"
        assert bonus == 0, f"Bonus should be 0, got {bonus}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
