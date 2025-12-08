"""
Property-Based Tests for Multi-Timeframe Momentum Analyzer.

Uses Hypothesis to verify RSI and MACD alignment properties.

**Feature: multi-timeframe-analysis**
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.mtf.momentum_analyzer import MomentumAnalyzer
from trading.mtf.models import TimeframeFeatures, MTFFeatures


settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=50)


def create_timeframe_features(
    timeframe: str,
    rsi: float = 50.0,
    macd_histogram: float = 0.0,
    close: float = 100.0,
) -> TimeframeFeatures:
    """Create TimeframeFeatures with specified RSI and MACD values."""
    return TimeframeFeatures(
        timeframe=timeframe,
        ema_short=close * 0.99,
        ema_long=close * 1.01,
        ema_50=close,
        ema_200=close,
        rsi=rsi,
        macd=0.0,
        macd_signal=0.0,
        macd_histogram=macd_histogram,
        adx=25.0,
        volume=10000,
        volume_avg=10000,
        volume_ratio=1.0,
        high=close * 1.01,
        low=close * 0.99,
        close=close,
    )


def create_mtf_features_with_momentum(
    rsi_1min: float,
    rsi_5min: float,
    rsi_15min: float,
    macd_5min: float,
    macd_15min: float,
) -> MTFFeatures:
    """Create MTFFeatures with specified RSI and MACD values."""
    return MTFFeatures(
        symbol='TEST',
        tf_1min=create_timeframe_features('1min', rsi=rsi_1min),
        tf_5min=create_timeframe_features('5min', rsi=rsi_5min, macd_histogram=macd_5min),
        tf_15min=create_timeframe_features('15min', rsi=rsi_15min, macd_histogram=macd_15min),
        tf_daily=create_timeframe_features('daily'),
        timestamp=datetime.now(timezone.utc),
    )


class TestRSIConfirmationProperties:
    """Property tests for RSI confirmation rule."""

    @given(
        rsi_1min=st.floats(min_value=51, max_value=100, allow_nan=False),
        rsi_5min=st.floats(min_value=51, max_value=100, allow_nan=False),
        rsi_15min=st.floats(min_value=0, max_value=100, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_3_rsi_buy_confirmation_2_of_3(
        self, rsi_1min: float, rsi_5min: float, rsi_15min: float
    ):
        """
        **Feature: multi-timeframe-analysis, Property 3: RSI Confirmation Rule**
        
        For any buy signal, RSI must be above 50 on at least 2 of 3 timeframes.
        
        **Validates: Requirements 3.1**
        """
        analyzer = MomentumAnalyzer()
        
        # At least 2 RSI values are > 50 (rsi_1min and rsi_5min)
        features = create_mtf_features_with_momentum(
            rsi_1min=rsi_1min,
            rsi_5min=rsi_5min,
            rsi_15min=rsi_15min,
            macd_5min=0.0,
            macd_15min=0.0,
        )
        
        is_aligned, count = analyzer.check_rsi_alignment(features, 'buy')
        
        # Should be aligned since at least 2 are > 50
        assert count >= 2, f"Should have at least 2 aligned, got {count}"
        assert is_aligned, "Should be aligned with 2+ RSI > 50"

    @given(
        rsi_1min=st.floats(min_value=0, max_value=49, allow_nan=False),
        rsi_5min=st.floats(min_value=0, max_value=49, allow_nan=False),
        rsi_15min=st.floats(min_value=0, max_value=100, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_3_rsi_sell_confirmation_2_of_3(
        self, rsi_1min: float, rsi_5min: float, rsi_15min: float
    ):
        """
        **Feature: multi-timeframe-analysis, Property 3: RSI Confirmation Rule**
        
        For any sell signal, RSI must be below 50 on at least 2 of 3 timeframes.
        
        **Validates: Requirements 3.2**
        """
        analyzer = MomentumAnalyzer()
        
        # At least 2 RSI values are < 50 (rsi_1min and rsi_5min)
        features = create_mtf_features_with_momentum(
            rsi_1min=rsi_1min,
            rsi_5min=rsi_5min,
            rsi_15min=rsi_15min,
            macd_5min=0.0,
            macd_15min=0.0,
        )
        
        is_aligned, count = analyzer.check_rsi_alignment(features, 'sell')
        
        # Should be aligned since at least 2 are < 50
        assert count >= 2, f"Should have at least 2 aligned, got {count}"
        assert is_aligned, "Should be aligned with 2+ RSI < 50"

    def test_rsi_buy_not_aligned_when_only_1_above_50(self):
        """Test that buy is not aligned when only 1 RSI > 50."""
        analyzer = MomentumAnalyzer()
        
        features = create_mtf_features_with_momentum(
            rsi_1min=60.0,  # > 50
            rsi_5min=40.0,  # < 50
            rsi_15min=40.0,  # < 50
            macd_5min=0.0,
            macd_15min=0.0,
        )
        
        is_aligned, count = analyzer.check_rsi_alignment(features, 'buy')
        
        assert count == 1, f"Should have 1 aligned, got {count}"
        assert not is_aligned, "Should not be aligned with only 1 RSI > 50"


class TestMACDConfirmationProperties:
    """Property tests for MACD confirmation."""

    @given(
        macd_5min=st.floats(min_value=0.001, max_value=10, allow_nan=False),
        macd_15min=st.floats(min_value=0.001, max_value=10, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_4_macd_bullish_confirmation(
        self, macd_5min: float, macd_15min: float
    ):
        """
        **Feature: multi-timeframe-analysis, Property 4: MACD Momentum Confirmation**
        
        Bullish momentum confirmation requires positive MACD histogram on both 5-min and 15-min.
        
        **Validates: Requirements 3.3**
        """
        analyzer = MomentumAnalyzer()
        
        features = create_mtf_features_with_momentum(
            rsi_1min=50.0,
            rsi_5min=50.0,
            rsi_15min=50.0,
            macd_5min=macd_5min,
            macd_15min=macd_15min,
        )
        
        is_aligned = analyzer.check_macd_alignment(features, 'buy')
        
        assert is_aligned, (
            f"Should be aligned with positive MACD on both timeframes "
            f"(5min={macd_5min}, 15min={macd_15min})"
        )

    @given(
        macd_5min=st.floats(min_value=-10, max_value=-0.001, allow_nan=False),
        macd_15min=st.floats(min_value=-10, max_value=-0.001, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_4_macd_bearish_confirmation(
        self, macd_5min: float, macd_15min: float
    ):
        """
        **Feature: multi-timeframe-analysis, Property 4: MACD Momentum Confirmation**
        
        Bearish momentum confirmation requires negative MACD histogram on both 5-min and 15-min.
        
        **Validates: Requirements 3.4**
        """
        analyzer = MomentumAnalyzer()
        
        features = create_mtf_features_with_momentum(
            rsi_1min=50.0,
            rsi_5min=50.0,
            rsi_15min=50.0,
            macd_5min=macd_5min,
            macd_15min=macd_15min,
        )
        
        is_aligned = analyzer.check_macd_alignment(features, 'sell')
        
        assert is_aligned, (
            f"Should be aligned with negative MACD on both timeframes "
            f"(5min={macd_5min}, 15min={macd_15min})"
        )

    def test_macd_not_aligned_when_mixed(self):
        """Test that MACD is not aligned when signs are mixed."""
        analyzer = MomentumAnalyzer()
        
        features = create_mtf_features_with_momentum(
            rsi_1min=50.0,
            rsi_5min=50.0,
            rsi_15min=50.0,
            macd_5min=0.5,   # Positive
            macd_15min=-0.5,  # Negative
        )
        
        assert not analyzer.check_macd_alignment(features, 'buy')
        assert not analyzer.check_macd_alignment(features, 'sell')


class TestMomentumAlignmentConfidenceProperties:
    """Property tests for momentum alignment confidence adjustment."""

    @given(
        rsi=st.floats(min_value=51, max_value=100, allow_nan=False),
        macd=st.floats(min_value=0.001, max_value=10, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_5_full_alignment_bonus(self, rsi: float, macd: float):
        """
        **Feature: multi-timeframe-analysis, Property 5: Momentum Alignment Confidence Adjustment**
        
        If all three timeframes show aligned momentum, add 25 points.
        
        **Validates: Requirements 3.6**
        """
        analyzer = MomentumAnalyzer()
        
        # All RSI > 50 and all MACD positive for buy
        features = create_mtf_features_with_momentum(
            rsi_1min=rsi,
            rsi_5min=rsi,
            rsi_15min=rsi,
            macd_5min=macd,
            macd_15min=macd,
        )
        
        score = analyzer.get_momentum_score(features, 'buy')
        
        assert score == 25, f"Full alignment should give +25, got {score}"

    @given(
        rsi=st.floats(min_value=0, max_value=49, allow_nan=False),
        macd=st.floats(min_value=-10, max_value=-0.001, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_property_5_conflict_penalty(self, rsi: float, macd: float):
        """
        **Feature: multi-timeframe-analysis, Property 5: Momentum Alignment Confidence Adjustment**
        
        If momentum indicators conflict across timeframes, subtract 20 points.
        
        **Validates: Requirements 3.5**
        """
        analyzer = MomentumAnalyzer()
        
        # RSI < 50 and MACD negative (bearish) but signal is buy (conflict)
        features = create_mtf_features_with_momentum(
            rsi_1min=rsi,
            rsi_5min=rsi,
            rsi_15min=rsi,
            macd_5min=macd,
            macd_15min=macd,
        )
        
        score = analyzer.get_momentum_score(features, 'buy')
        
        assert score == -20, f"Conflict should give -20, got {score}"

    def test_no_adjustment_for_partial_alignment(self):
        """Test that partial alignment gives no bonus or penalty."""
        analyzer = MomentumAnalyzer()
        
        # 2 of 3 RSI aligned, MACD not aligned
        features = create_mtf_features_with_momentum(
            rsi_1min=60.0,
            rsi_5min=60.0,
            rsi_15min=40.0,  # Not aligned
            macd_5min=0.5,
            macd_15min=-0.5,  # Not aligned
        )
        
        score = analyzer.get_momentum_score(features, 'buy')
        
        assert score == 0, f"Partial alignment should give 0, got {score}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
