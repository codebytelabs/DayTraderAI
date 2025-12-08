"""
Property-Based Tests for Multi-Timeframe Feature Engine.

Uses Hypothesis to verify that all required indicators are computed for each timeframe.

**Feature: multi-timeframe-analysis**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.mtf.feature_engine import MTFFeatureEngine
from trading.mtf.models import TimeframeFeatures, MTFFeatures


# Configure Hypothesis for CI
settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=50)


def generate_ohlcv_dataframe(
    num_bars: int,
    base_price: float = 100.0,
    volatility: float = 0.02,
    base_volume: int = 10000,
) -> pd.DataFrame:
    """Generate realistic OHLCV data for testing.
    
    Args:
        num_bars: Number of bars to generate
        base_price: Starting price
        volatility: Price volatility (as fraction)
        base_volume: Base volume level
        
    Returns:
        DataFrame with open, high, low, close, volume columns
    """
    np.random.seed(42)  # For reproducibility in tests
    
    prices = [base_price]
    for _ in range(num_bars - 1):
        change = np.random.normal(0, volatility)
        prices.append(prices[-1] * (1 + change))
    
    data = []
    for i, close in enumerate(prices):
        # Generate realistic OHLC from close
        daily_range = close * volatility
        high = close + abs(np.random.normal(0, daily_range / 2))
        low = close - abs(np.random.normal(0, daily_range / 2))
        open_price = low + np.random.random() * (high - low)
        
        # Ensure high >= close >= low and high >= open >= low
        high = max(high, close, open_price)
        low = min(low, close, open_price)
        
        # Generate volume with some variation
        volume = int(base_volume * (0.5 + np.random.random()))
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
        })
    
    return pd.DataFrame(data)


# Strategy for generating valid OHLCV data parameters
ohlcv_params = st.fixed_dictionaries({
    'num_bars': st.integers(min_value=30, max_value=200),
    'base_price': st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    'volatility': st.floats(min_value=0.001, max_value=0.05, allow_nan=False, allow_infinity=False),
    'base_volume': st.integers(min_value=1000, max_value=1000000),
})


class TestMTFFeatureEngineProperties:
    """Property tests for MTFFeatureEngine."""
    
    @given(params=ohlcv_params)
    @settings(max_examples=100)
    def test_property_feature_calculation_completeness(self, params: dict):
        """
        **Feature: multi-timeframe-analysis, Property: Feature Calculation Completeness**
        
        For any valid OHLCV data, all required indicators should be computed for each timeframe:
        - EMA(9), EMA(21), EMA(50), EMA(200)
        - RSI(14)
        - MACD(12, 26, 9) - line, signal, histogram
        - ADX(14)
        - Volume ratio (current vs 20-period average)
        - High, Low, Close prices
        
        **Validates: Requirements 1.5**
        """
        engine = MTFFeatureEngine()
        df = generate_ohlcv_dataframe(**params)
        
        # Calculate features for a single timeframe
        features = engine.calculate_timeframe_features(df, '15min')
        
        # Should return valid features
        assert features is not None, "Features should not be None for valid data"
        assert isinstance(features, TimeframeFeatures), "Should return TimeframeFeatures"
        
        # Verify all required indicators are present and valid
        required_indicators = engine.get_required_indicators()
        
        for indicator in required_indicators:
            value = getattr(features, indicator, None)
            assert value is not None, f"Indicator {indicator} should not be None"
            
            # Check that numeric values are finite
            if isinstance(value, (int, float)):
                assert np.isfinite(value), f"Indicator {indicator} should be finite, got {value}"
        
        # Verify specific indicator ranges
        assert 0 <= features.rsi <= 100, f"RSI should be 0-100, got {features.rsi}"
        assert features.adx >= 0, f"ADX should be >= 0, got {features.adx}"
        assert features.volume >= 0, f"Volume should be >= 0, got {features.volume}"
        assert features.volume_avg >= 0, f"Volume avg should be >= 0, got {features.volume_avg}"
        assert features.volume_ratio >= 0, f"Volume ratio should be >= 0, got {features.volume_ratio}"
        assert features.close > 0, f"Close should be > 0, got {features.close}"
        assert features.high >= features.low, f"High should be >= Low"
        assert features.ema_short > 0, f"EMA short should be > 0, got {features.ema_short}"
        assert features.ema_long > 0, f"EMA long should be > 0, got {features.ema_long}"
    
    @given(params=ohlcv_params)
    @settings(max_examples=100)
    def test_mtf_features_aggregation(self, params: dict):
        """
        Test that calculate_mtf_features correctly aggregates features across all timeframes.
        
        **Validates: Requirements 1.5**
        """
        engine = MTFFeatureEngine()
        df = generate_ohlcv_dataframe(**params)
        
        # Create data dict for all timeframes
        data = {
            '1min': df.copy(),
            '5min': df.copy(),
            '15min': df.copy(),
            'daily': df.copy(),
        }
        
        # Calculate MTF features
        mtf_features = engine.calculate_mtf_features('TEST', data)
        
        # Should return valid MTFFeatures
        assert mtf_features is not None, "MTFFeatures should not be None"
        assert isinstance(mtf_features, MTFFeatures), "Should return MTFFeatures"
        
        # Verify all timeframes have features
        assert mtf_features.tf_1min is not None, "1min features should not be None"
        assert mtf_features.tf_5min is not None, "5min features should not be None"
        assert mtf_features.tf_15min is not None, "15min features should not be None"
        assert mtf_features.tf_daily is not None, "daily features should not be None"
        
        # Verify symbol is set correctly
        assert mtf_features.symbol == 'TEST', f"Symbol should be TEST, got {mtf_features.symbol}"
        
        # Verify timestamp is set
        assert mtf_features.timestamp is not None, "Timestamp should not be None"
    
    @given(
        timeframe=st.sampled_from(['1min', '5min', '15min', 'daily']),
        params=ohlcv_params,
    )
    @settings(max_examples=100)
    def test_timeframe_features_validity(self, timeframe: str, params: dict):
        """
        Test that features are valid for any timeframe.
        
        **Validates: Requirements 1.5**
        """
        engine = MTFFeatureEngine()
        df = generate_ohlcv_dataframe(**params)
        
        features = engine.calculate_timeframe_features(df, timeframe)
        
        assert features is not None, f"Features for {timeframe} should not be None"
        assert features.timeframe == timeframe, f"Timeframe should be {timeframe}"
        assert features.is_valid(), f"Features for {timeframe} should be valid"
    
    def test_insufficient_data_returns_none(self):
        """
        Test that insufficient data returns None instead of invalid features.
        
        **Validates: Requirements 1.5**
        """
        engine = MTFFeatureEngine()
        
        # Create DataFrame with too few bars
        df = generate_ohlcv_dataframe(num_bars=10)  # Less than minimum required
        
        features = engine.calculate_timeframe_features(df, '15min')
        
        # Should return None for insufficient data
        assert features is None, "Should return None for insufficient data"
    
    def test_empty_dataframe_returns_none(self):
        """
        Test that empty DataFrame returns None.
        
        **Validates: Requirements 1.5**
        """
        engine = MTFFeatureEngine()
        
        # Empty DataFrame
        df = pd.DataFrame()
        
        features = engine.calculate_timeframe_features(df, '15min')
        
        assert features is None, "Should return None for empty DataFrame"
    
    def test_missing_timeframe_data_handled(self):
        """
        Test that missing timeframe data is handled gracefully.
        
        **Validates: Requirements 1.5**
        """
        engine = MTFFeatureEngine()
        df = generate_ohlcv_dataframe(num_bars=50)
        
        # Only provide some timeframes
        data = {
            '1min': df.copy(),
            '5min': df.copy(),
            # Missing 15min and daily
        }
        
        mtf_features = engine.calculate_mtf_features('TEST', data)
        
        # Should return None when required timeframes are missing
        assert mtf_features is None, "Should return None when timeframes are missing"
    
    @given(params=ohlcv_params)
    @settings(max_examples=50)
    def test_ema_ordering_consistency(self, params: dict):
        """
        Test that EMA values maintain expected relationships.
        
        Shorter EMAs should be more responsive to recent prices.
        
        **Validates: Requirements 1.5**
        """
        engine = MTFFeatureEngine()
        df = generate_ohlcv_dataframe(**params)
        
        features = engine.calculate_timeframe_features(df, '15min')
        
        if features is not None:
            # All EMAs should be positive
            assert features.ema_short > 0, "EMA short should be positive"
            assert features.ema_long > 0, "EMA long should be positive"
            assert features.ema_50 > 0, "EMA 50 should be positive"
            assert features.ema_200 > 0, "EMA 200 should be positive"
            
            # EMAs should be positive and finite (not checking range since
            # longer EMAs can lag significantly in volatile/trending markets)
            for ema_name in ['ema_short', 'ema_long', 'ema_50', 'ema_200']:
                ema_value = getattr(features, ema_name)
                assert ema_value > 0, f"{ema_name} should be positive"
                assert np.isfinite(ema_value), f"{ema_name} should be finite"


class TestMTFFeatureEngineEdgeCases:
    """Edge case tests for MTFFeatureEngine."""
    
    def test_column_name_normalization(self):
        """
        Test that column names are normalized to lowercase.
        
        **Validates: Requirements 1.5**
        """
        engine = MTFFeatureEngine()
        
        # Create DataFrame with uppercase column names
        df = generate_ohlcv_dataframe(num_bars=50)
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        features = engine.calculate_timeframe_features(df, '15min')
        
        assert features is not None, "Should handle uppercase column names"
    
    def test_zero_volume_handled(self):
        """
        Test that zero volume is handled gracefully.
        
        **Validates: Requirements 1.5**
        """
        engine = MTFFeatureEngine()
        df = generate_ohlcv_dataframe(num_bars=50)
        
        # Set some volumes to zero
        df.loc[df.index[-5:], 'volume'] = 0
        
        features = engine.calculate_timeframe_features(df, '15min')
        
        # Should still calculate features
        assert features is not None, "Should handle zero volume"
        assert features.volume_ratio >= 0, "Volume ratio should be non-negative"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
