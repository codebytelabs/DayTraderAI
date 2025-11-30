"""
Property-Based Tests for Momentum-Confirmed Regime System.

Uses Hypothesis to verify correctness properties from the design document.
Each test is annotated with the property number and requirements it validates.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.momentum_strength import MomentumStrengthCalculator, MomentumStrengthResult


# Configure Hypothesis for CI
settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=50)


class TestMomentumStrengthProperties:
    """Property tests for MomentumStrengthCalculator"""
    
    @given(
        adx=st.floats(min_value=-100, max_value=200, allow_nan=False, allow_infinity=False),
        volume_ratio=st.floats(min_value=-10, max_value=20, allow_nan=False, allow_infinity=False),
        trend_strength=st.floats(min_value=-5, max_value=5, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_property_1_momentum_strength_always_bounded(
        self, adx: float, volume_ratio: float, trend_strength: float
    ):
        """
        **Feature: momentum-confirmed-regime, Property 1: Momentum strength is always bounded**
        
        For any combination of ADX, volume ratio, and trend strength values,
        the calculated momentum strength score SHALL always be between 0.0 and 1.0 inclusive.
        
        **Validates: Requirements 1.1**
        """
        calculator = MomentumStrengthCalculator()
        result = calculator.calculate_strength_from_values(adx, volume_ratio, trend_strength)
        
        assert 0.0 <= result.score <= 1.0, (
            f"Momentum score {result.score} out of bounds [0, 1] "
            f"for inputs: ADX={adx}, volume={volume_ratio}, trend={trend_strength}"
        )
    
    @given(
        adx=st.floats(min_value=-100, max_value=200, allow_nan=False, allow_infinity=False),
        volume_ratio=st.floats(min_value=-10, max_value=20, allow_nan=False, allow_infinity=False),
        trend_strength=st.floats(min_value=-5, max_value=5, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_property_8_invalid_inputs_sanitized(
        self, adx: float, volume_ratio: float, trend_strength: float
    ):
        """
        **Feature: momentum-confirmed-regime, Property 8: Invalid indicator values are sanitized**
        
        For any ADX value outside [0, 100], volume ratio outside [0, 10], 
        or trend strength outside [0, 1], the system SHALL sanitize to default values.
        
        **Validates: Requirements 8.2, 8.3, 8.4**
        """
        calculator = MomentumStrengthCalculator()
        sanitized_adx, sanitized_volume, sanitized_trend = calculator.validate_inputs(
            adx, volume_ratio, trend_strength
        )
        
        # ADX should be in valid range or default
        assert 0.0 <= sanitized_adx <= 100.0, (
            f"Sanitized ADX {sanitized_adx} out of valid range [0, 100]"
        )
        
        # Volume ratio should be in valid range or default
        assert 0.0 <= sanitized_volume <= 10.0, (
            f"Sanitized volume ratio {sanitized_volume} out of valid range [0, 10]"
        )
        
        # Trend strength should be clamped to [0, 1]
        assert 0.0 <= sanitized_trend <= 1.0, (
            f"Sanitized trend strength {sanitized_trend} out of valid range [0, 1]"
        )
        
        # Verify specific sanitization rules
        if adx < 0.0 or adx > 100.0:
            assert sanitized_adx == calculator.ADX_DEFAULT, (
                f"Invalid ADX {adx} should be replaced with default {calculator.ADX_DEFAULT}"
            )
        
        if volume_ratio < 0.0 or volume_ratio > 10.0:
            assert sanitized_volume == calculator.VOLUME_DEFAULT, (
                f"Invalid volume {volume_ratio} should be replaced with default {calculator.VOLUME_DEFAULT}"
            )
    
    @given(
        adx=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
        volume_ratio=st.floats(min_value=0, max_value=10, allow_nan=False, allow_infinity=False),
        trend_strength=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_adx_confirmation_threshold(
        self, adx: float, volume_ratio: float, trend_strength: float
    ):
        """
        **Feature: momentum-confirmed-regime, Property 1.3: ADX confirmation threshold**
        
        WHEN ADX exceeds 25, THE Trading Bot SHALL classify momentum as "confirmed".
        
        **Validates: Requirements 1.3**
        """
        calculator = MomentumStrengthCalculator()
        result = calculator.calculate_strength_from_values(adx, volume_ratio, trend_strength)
        
        expected_confirmed = adx >= calculator.ADX_THRESHOLD
        assert result.adx_confirmed == expected_confirmed, (
            f"ADX {adx} should be confirmed={expected_confirmed} (threshold={calculator.ADX_THRESHOLD})"
        )
    
    @given(
        adx=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
        volume_ratio=st.floats(min_value=0, max_value=10, allow_nan=False, allow_infinity=False),
        trend_strength=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_volume_confirmation_threshold(
        self, adx: float, volume_ratio: float, trend_strength: float
    ):
        """
        **Feature: momentum-confirmed-regime, Property 1.4: Volume confirmation threshold**
        
        WHEN volume ratio exceeds 1.5x average, THE Trading Bot SHALL classify volume as "confirmed".
        
        **Validates: Requirements 1.4**
        """
        calculator = MomentumStrengthCalculator()
        result = calculator.calculate_strength_from_values(adx, volume_ratio, trend_strength)
        
        expected_confirmed = volume_ratio >= calculator.VOLUME_THRESHOLD
        assert result.volume_confirmed == expected_confirmed, (
            f"Volume {volume_ratio} should be confirmed={expected_confirmed} (threshold={calculator.VOLUME_THRESHOLD})"
        )
    
    @given(
        adx=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
        volume_ratio=st.floats(min_value=0, max_value=10, allow_nan=False, allow_infinity=False),
        trend_strength=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_trend_confirmation_threshold(
        self, adx: float, volume_ratio: float, trend_strength: float
    ):
        """
        **Feature: momentum-confirmed-regime, Property 1.5: Trend confirmation threshold**
        
        WHEN trend strength score exceeds 0.7, THE Trading Bot SHALL classify trend as "confirmed".
        
        **Validates: Requirements 1.5**
        """
        calculator = MomentumStrengthCalculator()
        result = calculator.calculate_strength_from_values(adx, volume_ratio, trend_strength)
        
        expected_confirmed = trend_strength >= calculator.TREND_THRESHOLD
        assert result.trend_confirmed == expected_confirmed, (
            f"Trend {trend_strength} should be confirmed={expected_confirmed} (threshold={calculator.TREND_THRESHOLD})"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


from trading.vix_provider import VIXDataProvider


class TestVIXProviderProperties:
    """Property tests for VIXDataProvider"""
    
    @given(
        vix=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_property_4_vix_cap_follows_tiered_rules(self, vix: float):
        """
        **Feature: momentum-confirmed-regime, Property 4: VIX cap follows tiered rules**
        
        For any VIX level, the position size cap SHALL be:
        - 1.2x when VIX < 15
        - 1.0x when VIX is 15-25
        - 0.9x when VIX is 25-35
        - 0.7x when VIX > 35
        
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        """
        provider = VIXDataProvider()
        cap = provider._calculate_vix_cap(vix)
        
        if vix < 15.0:
            expected_cap = 1.2
        elif vix < 25.0:
            expected_cap = 1.0
        elif vix < 35.0:
            expected_cap = 0.9
        else:
            expected_cap = 0.7
        
        assert cap == expected_cap, (
            f"VIX {vix} should have cap {expected_cap}, got {cap}"
        )
    
    @given(
        vix=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_vix_cap_always_in_valid_range(self, vix: float):
        """
        VIX cap should always be between 0.7 and 1.2.
        """
        provider = VIXDataProvider()
        cap = provider._calculate_vix_cap(vix)
        
        assert 0.7 <= cap <= 1.2, (
            f"VIX cap {cap} out of valid range [0.7, 1.2] for VIX={vix}"
        )


from trading.momentum_confirmed_regime import MomentumConfirmedRegimeManager, MarketRegime


class TestMomentumConfirmedRegimeProperties:
    """Property tests for MomentumConfirmedRegimeManager"""
    
    @given(
        momentum=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_property_2_extreme_greed_multiplier_tiered_rules(self, momentum: float):
        """
        **Feature: momentum-confirmed-regime, Property 2: Extreme greed position multiplier follows tiered rules**
        
        For any extreme greed regime and momentum strength value, the position multiplier SHALL be:
        - 1.2x when momentum > 0.8
        - 0.9x when momentum is 0.5-0.8
        - 0.7x when momentum < 0.5
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        """
        manager = MomentumConfirmedRegimeManager()
        mult = manager.get_momentum_multiplier(MarketRegime.EXTREME_GREED, momentum)
        
        if momentum > 0.8:
            expected = 1.2
        elif momentum >= 0.5:
            expected = 0.9
        else:
            expected = 0.7
        
        assert mult == expected, (
            f"Extreme greed with momentum {momentum} should have multiplier {expected}, got {mult}"
        )
    
    @given(
        momentum=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_property_3_extreme_fear_multiplier_tiered_rules(self, momentum: float):
        """
        **Feature: momentum-confirmed-regime, Property 3: Extreme fear position multiplier follows tiered rules**
        
        For any extreme fear regime and momentum strength value, the position multiplier SHALL be:
        - 1.0x when momentum > 0.7
        - 0.8x when momentum <= 0.7
        
        **Validates: Requirements 3.1, 3.2**
        """
        manager = MomentumConfirmedRegimeManager()
        mult = manager.get_momentum_multiplier(MarketRegime.EXTREME_FEAR, momentum)
        
        if momentum > 0.7:
            expected = 1.0
        else:
            expected = 0.8
        
        assert mult == expected, (
            f"Extreme fear with momentum {momentum} should have multiplier {expected}, got {mult}"
        )
    
    @given(
        momentum=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
        vix=st.floats(min_value=5, max_value=80, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_property_5_combined_multiplier_bounded(self, momentum: float, vix: float):
        """
        **Feature: momentum-confirmed-regime, Property 5: Combined multiplier is always bounded**
        
        For any combination of regime multiplier, momentum multiplier, and VIX cap,
        the final combined multiplier SHALL always be between 0.5x and 1.5x inclusive.
        
        **Validates: Requirements 5.2, 5.3**
        """
        manager = MomentumConfirmedRegimeManager()
        
        # Test with all regimes
        for regime in MarketRegime:
            result = manager.get_effective_multiplier(momentum, vix=vix, regime=regime)
            
            assert 0.5 <= result.multiplier <= 1.5, (
                f"Combined multiplier {result.multiplier} out of bounds [0.5, 1.5] "
                f"for regime={regime.value}, momentum={momentum}, vix={vix}"
            )
    
    @given(
        momentum=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
        vix=st.floats(min_value=5, max_value=80, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_property_6_combined_multiplier_calculation(self, momentum: float, vix: float):
        """
        **Feature: momentum-confirmed-regime, Property 6: Combined multiplier is product of components**
        
        For any regime multiplier, momentum multiplier, and VIX cap, the combined multiplier
        (before bounding) SHALL equal the appropriate product based on regime type.
        
        **Validates: Requirements 5.1**
        """
        manager = MomentumConfirmedRegimeManager()
        
        # Test extreme greed (uses momentum_mult)
        result = manager.get_effective_multiplier(
            momentum, vix=vix, regime=MarketRegime.EXTREME_GREED
        )
        
        momentum_mult = manager.get_momentum_multiplier(MarketRegime.EXTREME_GREED, momentum)
        vix_cap = manager.vix_provider._calculate_vix_cap(vix)
        expected_raw = momentum_mult * min(1.0, vix_cap)
        
        # Allow small floating point tolerance
        assert abs(result.raw_multiplier - expected_raw) < 0.001, (
            f"Raw multiplier {result.raw_multiplier} != expected {expected_raw} "
            f"(momentum_mult={momentum_mult}, vix_cap={vix_cap})"
        )


class TestRTargetAndStopProperties:
    """Property tests for R-target and trailing stop adjustments"""
    
    @given(
        momentum=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_property_7_r_target_adjustment_rules(self, momentum: float):
        """
        **Feature: momentum-confirmed-regime, Property 7: R-target adjustment follows momentum rules**
        
        For any regime and momentum strength:
        - Strong momentum (>0.8) increases base R-target by 0.5R
        - Weak momentum (<0.5) decreases base R-target by 0.5R
        - Extreme fear caps R-target at 2.0R regardless of momentum
        
        **Validates: Requirements 6.1, 6.2, 6.5**
        """
        manager = MomentumConfirmedRegimeManager()
        
        # Test extreme fear cap
        params = manager.get_momentum_adjusted_params(momentum, regime=MarketRegime.EXTREME_FEAR)
        assert params.profit_target_r <= 2.0, (
            f"Extreme fear R-target {params.profit_target_r} exceeds cap of 2.0R"
        )
        
        # Test neutral regime adjustments
        params_neutral = manager.get_momentum_adjusted_params(momentum, regime=MarketRegime.NEUTRAL)
        base_r = params_neutral.base_profit_target_r
        
        if momentum > 0.8:
            # Strong momentum should boost R-target
            expected_min = base_r + 0.5 - 0.01  # Allow small tolerance
            assert params_neutral.profit_target_r >= expected_min, (
                f"Strong momentum ({momentum}) should boost R-target to at least {expected_min}"
            )
        elif momentum < 0.5:
            # Weak momentum should reduce R-target (but not below 1.0)
            expected_max = max(1.0, base_r - 0.5 + 0.01)
            assert params_neutral.profit_target_r <= expected_max + 0.01, (
                f"Weak momentum ({momentum}) should reduce R-target to at most {expected_max}"
            )
    
    @given(
        momentum=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_property_9_extreme_fear_wide_trailing_stop(self, momentum: float):
        """
        **Feature: momentum-confirmed-regime, Property 9: Extreme fear always uses wide trailing stop**
        
        For any extreme fear regime, regardless of momentum strength, 
        the trailing stop SHALL be 1.0R.
        
        **Validates: Requirements 3.3**
        """
        manager = MomentumConfirmedRegimeManager()
        params = manager.get_momentum_adjusted_params(momentum, regime=MarketRegime.EXTREME_FEAR)
        
        assert params.trailing_stop_r == 1.0, (
            f"Extreme fear trailing stop should be 1.0R, got {params.trailing_stop_r}"
        )
    
    @given(
        momentum=st.floats(min_value=0.81, max_value=1, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_property_10_extreme_greed_strong_momentum_tight_stop(self, momentum: float):
        """
        **Feature: momentum-confirmed-regime, Property 10: Extreme greed with strong momentum uses tight trailing stop**
        
        For any extreme greed regime with momentum > 0.8, 
        the trailing stop SHALL be 0.5R.
        
        **Validates: Requirements 2.4**
        """
        manager = MomentumConfirmedRegimeManager()
        params = manager.get_momentum_adjusted_params(momentum, regime=MarketRegime.EXTREME_GREED)
        
        assert params.trailing_stop_r == 0.5, (
            f"Extreme greed with strong momentum ({momentum}) should have 0.5R trailing stop, got {params.trailing_stop_r}"
        )
    
    @given(
        momentum=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_r_target_always_at_least_1r(self, momentum: float):
        """
        R-target should never go below 1.0R regardless of adjustments.
        """
        manager = MomentumConfirmedRegimeManager()
        
        for regime in MarketRegime:
            params = manager.get_momentum_adjusted_params(momentum, regime=regime)
            assert params.profit_target_r >= 1.0, (
                f"R-target {params.profit_target_r} below minimum 1.0R "
                f"for regime={regime.value}, momentum={momentum}"
            )
