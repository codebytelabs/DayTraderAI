"""
Property-Based Tests for Multi-Timeframe Analysis Configuration.

Uses Hypothesis to verify correctness properties from the design document.
Each test is annotated with the property number and requirements it validates.

**Feature: multi-timeframe-analysis**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.mtf.models import MTFConfig, TrendBias, TrendDirection


# Configure Hypothesis for CI
settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=50)


class MockSettings:
    """Mock settings object for testing configuration loading."""
    
    def __init__(
        self,
        enable_mtf: bool = True,
        strict_mode: bool = False,
        min_confidence: float = 60.0,
        weights: str = "",
    ):
        self.ENABLE_MTF_ANALYSIS = enable_mtf
        self.MTF_STRICT_MODE = strict_mode
        self.MTF_MIN_CONFIDENCE = min_confidence
        self.MTF_WEIGHTS = weights


class TestMTFConfigProperties:
    """Property tests for MTFConfig."""
    
    @given(
        enabled=st.booleans()
    )
    @settings(max_examples=100)
    def test_property_11_configuration_override(self, enabled: bool):
        """
        **Feature: multi-timeframe-analysis, Property 11: Configuration Override**
        
        For any custom configuration with ENABLE_MTF_ANALYSIS=False, 
        the system should bypass all multi-timeframe checks and use single-timeframe logic only.
        
        **Validates: Requirements 9.1**
        """
        config = MTFConfig(enabled=enabled)
        
        # When enabled=False, should_bypass() returns True
        # When enabled=True, should_bypass() returns False
        expected_bypass = not enabled
        
        assert config.should_bypass() == expected_bypass, (
            f"Config with enabled={enabled} should have should_bypass()={expected_bypass}, "
            f"got {config.should_bypass()}"
        )

    
    @given(
        weight_15min=st.floats(min_value=0.1, max_value=0.6, allow_nan=False, allow_infinity=False),
        weight_5min=st.floats(min_value=0.1, max_value=0.6, allow_nan=False, allow_infinity=False),
        weight_1min=st.floats(min_value=0.1, max_value=0.6, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_property_12_custom_weight_application(
        self, weight_15min: float, weight_5min: float, weight_1min: float
    ):
        """
        **Feature: multi-timeframe-analysis, Property 12: Custom Weight Application**
        
        For any custom timeframe weights specified in configuration, 
        those weights should be used instead of defaults in confidence calculation.
        
        **Validates: Requirements 9.2**
        """
        # Normalize weights to sum to 1.0
        total = weight_15min + weight_5min + weight_1min
        normalized_15min = weight_15min / total
        normalized_5min = weight_5min / total
        normalized_1min = weight_1min / total
        
        custom_weights = {
            '15min': normalized_15min,
            '5min': normalized_5min,
            '1min': normalized_1min,
        }
        
        config = MTFConfig(enabled=True, weights=custom_weights)
        
        # Custom weights should be used
        effective_weights = config.get_weights()
        
        assert abs(effective_weights['15min'] - normalized_15min) < 0.001, (
            f"15min weight should be {normalized_15min}, got {effective_weights['15min']}"
        )
        assert abs(effective_weights['5min'] - normalized_5min) < 0.001, (
            f"5min weight should be {normalized_5min}, got {effective_weights['5min']}"
        )
        assert abs(effective_weights['1min'] - normalized_1min) < 0.001, (
            f"1min weight should be {normalized_1min}, got {effective_weights['1min']}"
        )
        
        # Weights should sum to approximately 1.0
        assert config.validate_weights(), (
            f"Weights should sum to 1.0, got {sum(effective_weights.values())}"
        )
    
    @given(
        enabled=st.booleans(),
        strict_mode=st.booleans(),
        min_confidence=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_config_from_settings_preserves_values(
        self, enabled: bool, strict_mode: bool, min_confidence: float
    ):
        """
        Test that MTFConfig.from_settings() correctly loads all configuration values.
        
        **Validates: Requirements 9.1, 9.3, 9.4**
        """
        mock_settings = MockSettings(
            enable_mtf=enabled,
            strict_mode=strict_mode,
            min_confidence=min_confidence,
        )
        
        config = MTFConfig.from_settings(mock_settings)
        
        assert config.enabled == enabled, (
            f"enabled should be {enabled}, got {config.enabled}"
        )
        assert config.strict_mode == strict_mode, (
            f"strict_mode should be {strict_mode}, got {config.strict_mode}"
        )
        assert config.min_confidence == min_confidence, (
            f"min_confidence should be {min_confidence}, got {config.min_confidence}"
        )
    
    def test_default_weights_sum_to_one(self):
        """
        Test that default weights sum to 1.0.
        
        **Validates: Requirements 5.1**
        """
        config = MTFConfig()
        weights = config.get_weights()
        
        assert abs(sum(weights.values()) - 1.0) < 0.001, (
            f"Default weights should sum to 1.0, got {sum(weights.values())}"
        )
        
        # Verify default weight values per Requirements 5.1
        assert weights['15min'] == 0.40, f"15min weight should be 0.40, got {weights['15min']}"
        assert weights['5min'] == 0.35, f"5min weight should be 0.35, got {weights['5min']}"
        assert weights['1min'] == 0.25, f"1min weight should be 0.25, got {weights['1min']}"
    
    def test_empty_weights_uses_defaults(self):
        """
        Test that empty custom weights fall back to defaults.
        
        **Validates: Requirements 9.2**
        """
        config = MTFConfig(enabled=True, weights={})
        weights = config.get_weights()
        
        # Should use default weights
        assert weights['15min'] == 0.40
        assert weights['5min'] == 0.35
        assert weights['1min'] == 0.25


class TestTrendBiasProperties:
    """Property tests for TrendBias classification."""
    
    @given(
        ema_50=st.floats(min_value=1, max_value=1000, allow_nan=False, allow_infinity=False),
        ema_200=st.floats(min_value=1, max_value=1000, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_trend_classification_consistency(self, ema_50: float, ema_200: float):
        """
        **Feature: multi-timeframe-analysis, Property 1: Trend Classification Consistency**
        
        For any 15-minute price data with EMA(50) and EMA(200) values, the trend classification should be:
        - Bullish when EMA(50) > EMA(200) by more than 0.1%
        - Bearish when EMA(50) < EMA(200) by more than 0.1%
        - Neutral when EMAs are within 0.1% of each other
        
        **Validates: Requirements 2.2, 2.3, 2.4**
        """
        trend_bias = TrendBias.from_ema_values(ema_50, ema_200)
        
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
