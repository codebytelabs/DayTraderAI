#!/usr/bin/env python3
"""
Property-Based Tests for WaveEntryEngine

Tests correctness properties for wave entry timing:
- Fresh crossover classification
- Extended crossover penalty
- ADX filter
"""

import pytest
from hypothesis import given, strategies as st, settings


class TestWaveEntryEngineProperties:
    """Property-based tests for WaveEntryEngine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from trading.wave_entry import WaveEntryEngine, CrossoverType
        self.engine = WaveEntryEngine()
        self.CrossoverType = CrossoverType
    
    @given(
        ema_diff=st.floats(min_value=0.05, max_value=0.3, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_fresh_crossover_classification(self, ema_diff):
        """
        **Feature: momentum-wave-rider, Property 9: Fresh Crossover Classification**
        **Validates: Requirements 5.1**
        
        For any EMA difference between 0.05% and 0.3%, 
        the crossover should be classified as "fresh".
        """
        crossover_type = self.engine.classify_crossover(ema_diff)
        
        assert crossover_type == self.CrossoverType.FRESH, (
            f"EMA diff {ema_diff}% should be FRESH, got {crossover_type}"
        )
        
        # Also test negative (short direction)
        crossover_type_neg = self.engine.classify_crossover(-ema_diff)
        assert crossover_type_neg == self.CrossoverType.FRESH, (
            f"EMA diff -{ema_diff}% should be FRESH, got {crossover_type_neg}"
        )
    
    @given(
        ema_diff=st.floats(min_value=1.01, max_value=5.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_extended_crossover_penalty(self, ema_diff):
        """
        **Feature: momentum-wave-rider, Property 10: Extended Crossover Penalty**
        **Validates: Requirements 5.2**
        
        For any EMA difference > 1%, the confidence should be reduced by 15 points.
        """
        crossover_type = self.engine.classify_crossover(ema_diff)
        
        assert crossover_type == self.CrossoverType.EXTENDED, (
            f"EMA diff {ema_diff}% should be EXTENDED, got {crossover_type}"
        )
        
        # Check that analysis applies the penalty
        features = {
            'ema_diff': ema_diff,
            'vwap_distance': 1.0,  # Not near VWAP
            'adx': 25.0,
            'multi_tf_aligned': False
        }
        
        analysis = self.engine.analyze_entry(features)
        
        # Extended penalty should be applied (-15)
        assert analysis.confidence_adjustment <= -15, (
            f"Extended crossover should have -15 penalty, got {analysis.confidence_adjustment}"
        )
    
    @given(
        adx=st.floats(min_value=0.0, max_value=19.9, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    def test_adx_filter(self, adx):
        """
        **Feature: momentum-wave-rider, Property 11: ADX Filter**
        **Validates: Requirements 5.4**
        
        For any ADX below 20, the trade should be skipped.
        """
        features = {
            'ema_diff': 0.1,  # Fresh crossover
            'vwap_distance': 0.0,  # Near VWAP
            'adx': adx,
            'multi_tf_aligned': True
        }
        
        analysis = self.engine.analyze_entry(features)
        
        assert not analysis.should_enter, (
            f"Should not enter with ADX {adx}"
        )
        assert "adx" in analysis.reason.lower() or "choppy" in analysis.reason.lower()

    @given(
        vwap_distance=st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    def test_vwap_bonus(self, vwap_distance):
        """
        Test that VWAP proximity gives +5 bonus.
        """
        features = {
            'ema_diff': 0.1,
            'vwap_distance': vwap_distance,
            'adx': 25.0,
            'multi_tf_aligned': False
        }
        
        analysis = self.engine.analyze_entry(features)
        
        assert analysis.vwap_bonus == 5, (
            f"VWAP distance {vwap_distance}% should give +5 bonus, got {analysis.vwap_bonus}"
        )
    
    def test_developing_crossover(self):
        """Test developing crossover classification (0.3-1.0%)."""
        # Test at 0.5% (middle of developing range)
        crossover_type = self.engine.classify_crossover(0.5)
        assert crossover_type == self.CrossoverType.DEVELOPING
        
        # Test at 0.9% (near upper bound)
        crossover_type = self.engine.classify_crossover(0.9)
        assert crossover_type == self.CrossoverType.DEVELOPING
    
    def test_entry_quality_ideal(self):
        """Test ideal entry quality conditions."""
        features = {
            'ema_diff': 0.1,  # Fresh
            'vwap_distance': 0.0,  # Near VWAP
            'adx': 30.0,
            'multi_tf_aligned': True
        }
        
        analysis = self.engine.analyze_entry(features)
        
        from trading.wave_entry import EntryQuality
        assert analysis.entry_quality == EntryQuality.IDEAL
        assert analysis.should_enter
        assert analysis.vwap_bonus == 5
        assert analysis.timeframe_bonus == 10
    
    def test_extended_should_not_enter(self):
        """Test that extended crossovers should not enter."""
        features = {
            'ema_diff': 2.0,  # Extended
            'vwap_distance': 0.0,
            'adx': 30.0,
            'multi_tf_aligned': True
        }
        
        analysis = self.engine.analyze_entry(features)
        
        assert not analysis.should_enter
        assert "extended" in analysis.reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
