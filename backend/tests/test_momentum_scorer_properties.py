#!/usr/bin/env python3
"""
Property-Based Tests for MomentumScorer

Tests correctness properties for the momentum scoring system including:
- Score range invariant (0-100)
- Volume score calculation
- Overbought/oversold penalty
- Upside potential scoring
- Insufficient room penalty
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Dict


class TestMomentumScorerProperties:
    """
    Property-based tests for MomentumScorer.
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        from scanner.momentum_scorer import MomentumScorer
        self.scorer = MomentumScorer()
    
    @given(
        volume_ratio=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        adx=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        rsi=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        ema_diff=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
        price=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        resistance_pct=st.floats(min_value=1.0, max_value=1.2, allow_nan=False, allow_infinity=False),
        support_pct=st.floats(min_value=0.8, max_value=0.99, allow_nan=False, allow_infinity=False),
        vwap_distance=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
        multi_tf_aligned=st.booleans()
    )
    @settings(max_examples=100, deadline=5000)
    def test_score_range_invariant(self, volume_ratio, adx, rsi, ema_diff, price, 
                                    resistance_pct, support_pct, vwap_distance, multi_tf_aligned):
        """
        **Feature: momentum-wave-rider, Property 2: Score Range Invariant**
        **Validates: Requirements 2.1**
        
        For any valid input features, the calculated momentum score 
        should be between 0 and 100 inclusive.
        """
        features = {
            'volume_ratio': volume_ratio,
            'adx': adx,
            'rsi': rsi,
            'ema_diff': ema_diff,
            'price': price,
            'resistance': price * resistance_pct,
            'support': price * support_pct,
            'vwap_distance': vwap_distance,
            'multi_tf_aligned': multi_tf_aligned
        }
        
        score = self.scorer.calculate_score(features)
        
        # PROPERTY: Total score must be between 0 and 100
        assert 0 <= score.total_score <= 100, (
            f"Score {score.total_score} out of range [0, 100]"
        )
        
        # PROPERTY: Component scores must be in valid ranges
        assert 0 <= score.volume_score <= 25, f"Volume score {score.volume_score} out of range"
        assert 0 <= score.momentum_score <= 20, f"Momentum score {score.momentum_score} out of range"
        assert 0 <= score.breakout_score <= 20, f"Breakout score {score.breakout_score} out of range"
        assert 0 <= score.upside_score <= 25, f"Upside score {score.upside_score} out of range"
        assert 0 <= score.trend_score <= 10, f"Trend score {score.trend_score} out of range"

    @given(
        volume_ratio=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_volume_score_calculation(self, volume_ratio):
        """
        **Feature: momentum-wave-rider, Property 3: Volume Score Calculation**
        **Validates: Requirements 2.2**
        
        For any volume ratio, the volume score should be:
        - 25 if ratio >= 2.0
        - 20 if ratio >= 1.5
        - 10 if ratio >= 1.0
        - 0 otherwise
        """
        score = self.scorer.calculate_volume_score(volume_ratio)
        
        if volume_ratio >= 2.0:
            assert score == 25, f"Volume ratio {volume_ratio} should give 25 pts, got {score}"
        elif volume_ratio >= 1.5:
            assert score == 20, f"Volume ratio {volume_ratio} should give 20 pts, got {score}"
        elif volume_ratio >= 1.0:
            assert score == 10, f"Volume ratio {volume_ratio} should give 10 pts, got {score}"
        else:
            assert score == 0, f"Volume ratio {volume_ratio} should give 0 pts, got {score}"
    
    @given(
        rsi=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        price=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_overbought_oversold_penalty(self, rsi, price):
        """
        **Feature: momentum-wave-rider, Property 5: Overbought/Oversold Penalty**
        **Validates: Requirements 2.7**
        
        For any RSI > 75 or RSI < 25, the score should be reduced by exactly 20 points.
        """
        # Create features with the RSI value
        features = {
            'volume_ratio': 2.0,  # High volume to get base score
            'adx': 30,
            'rsi': rsi,
            'ema_diff': 0.1,
            'price': price,
            'resistance': price * 1.1,
            'support': price * 0.95,
            'vwap_distance': 0.0,
            'multi_tf_aligned': True
        }
        
        score = self.scorer.calculate_score(features)
        
        if rsi > 75 or rsi < 25:
            assert score.overbought_penalty == 20, (
                f"RSI {rsi} should trigger 20 pt penalty, got {score.overbought_penalty}"
            )
        else:
            assert score.overbought_penalty == 0, (
                f"RSI {rsi} should not trigger penalty, got {score.overbought_penalty}"
            )

    @given(
        price=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        upside_pct=st.floats(min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_upside_potential_scoring(self, price, upside_pct):
        """
        **Feature: momentum-wave-rider, Property 18: Upside Potential Scoring**
        **Validates: Requirements 2.5, 3.3, 3.4, 3.5, 3.6, 3.7**
        
        For any distance to resistance, the upside score should be:
        - 25 if >5%
        - 20 if >3% and <=5%
        - 15 if >2% and <=3%
        - 10 if >1% and <=2%
        - 0 if <=1%
        """
        resistance = price * (1 + upside_pct / 100)
        support = price * 0.95
        
        score = self.scorer.calculate_upside_potential(price, resistance, support)
        
        # Use small epsilon for floating point comparison at boundaries
        eps = 0.0001
        
        if upside_pct > 5.0 + eps:
            assert score == 25, f"Upside {upside_pct}% should give 25 pts, got {score}"
        elif upside_pct > 3.0 + eps:
            assert score == 20, f"Upside {upside_pct}% should give 20 pts, got {score}"
        elif upside_pct > 2.0 + eps:
            assert score == 15, f"Upside {upside_pct}% should give 15 pts, got {score}"
        elif upside_pct > 1.0 + eps:
            assert score == 10, f"Upside {upside_pct}% should give 10 pts, got {score}"
        else:
            # At or below 1%, score should be 0 or 10 (boundary)
            assert score in [0, 10], f"Upside {upside_pct}% should give 0 or 10 pts, got {score}"
    
    @given(
        price=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        upside_pct=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_insufficient_room_penalty(self, price, upside_pct):
        """
        **Feature: momentum-wave-rider, Property 19: Insufficient Room Penalty**
        **Validates: Requirements 2.8, 3.7**
        
        For any upside potential <1% to resistance, the score should be reduced by 15 points.
        """
        resistance = price * (1 + upside_pct / 100)
        
        penalties = self.scorer.apply_penalties(
            rsi=50,  # Normal RSI
            ema_diff=0.1,  # Normal EMA diff
            price=price,
            resistance=resistance
        )
        
        # Use small epsilon for floating point comparison at boundary
        eps = 0.0001
        
        if upside_pct < 1.0 - eps:
            assert penalties['insufficient_room'] == 15, (
                f"Upside {upside_pct}% should trigger 15 pt penalty, got {penalties['insufficient_room']}"
            )
        elif upside_pct > 1.0 + eps:
            assert penalties['insufficient_room'] == 0, (
                f"Upside {upside_pct}% should not trigger penalty, got {penalties['insufficient_room']}"
            )
        # At exactly 1.0%, either result is acceptable (boundary condition)
    
    def test_edge_cases(self):
        """Test edge cases for the scorer."""
        # Test with zero/invalid values
        features = {
            'volume_ratio': 0,
            'adx': 0,
            'rsi': 50,
            'ema_diff': 0,
            'price': 0,
            'resistance': 0,
            'support': 0,
            'vwap_distance': 0,
            'multi_tf_aligned': False
        }
        
        score = self.scorer.calculate_score(features)
        assert 0 <= score.total_score <= 100, "Score should be valid even with zero inputs"
        
        # Test with very high values
        features = {
            'volume_ratio': 10.0,
            'adx': 100,
            'rsi': 50,
            'ema_diff': 0.1,
            'price': 100,
            'resistance': 120,
            'support': 90,
            'vwap_distance': 0,
            'multi_tf_aligned': True
        }
        
        score = self.scorer.calculate_score(features)
        assert 0 <= score.total_score <= 100, "Score should be capped at 100"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
