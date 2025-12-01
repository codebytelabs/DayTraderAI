#!/usr/bin/env python3
"""
Property-Based Tests for ConfidenceBasedSizer

Tests correctness properties for confidence-based position sizing:
- Position size tiers match confidence levels
- Low confidence trades are skipped
- Volume bonus is capped at 15%
"""

import pytest
from hypothesis import given, strategies as st, settings, assume


class TestConfidenceBasedSizerProperties:
    """Property-based tests for ConfidenceBasedSizer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from utils.confidence_sizer import ConfidenceBasedSizer
        self.sizer = ConfidenceBasedSizer()
    
    @given(
        confidence=st.floats(min_value=60.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        equity=st.floats(min_value=1000.0, max_value=1000000.0, allow_nan=False, allow_infinity=False),
        price=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        volume_confirmed=st.booleans()
    )
    @settings(max_examples=100, deadline=5000)
    def test_position_size_tiers(self, confidence, equity, price, volume_confirmed):
        """
        **Feature: momentum-wave-rider, Property 6: Position Size Tiers**
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        
        For any confidence score, the position size percentage should match the tier:
        - 90+: 15% max
        - 80-89: 12% max
        - 70-79: 10% max
        - 60-69: 8% max
        """
        result = self.sizer.calculate_position_size(
            confidence=confidence,
            equity=equity,
            price=price,
            volume_confirmed=volume_confirmed,
            adx=25.0  # Valid ADX
        )
        
        # Should not skip (confidence >= 60, ADX >= 20)
        assert not result.skip_trade, f"Should not skip with confidence {confidence}"
        
        # Check tier assignment
        if confidence >= 90:
            assert result.confidence_tier == "ultra_high"
            base_max = 0.15
        elif confidence >= 80:
            assert result.confidence_tier == "high"
            base_max = 0.12
        elif confidence >= 70:
            assert result.confidence_tier == "medium"
            base_max = 0.10
        else:  # 60-69
            assert result.confidence_tier == "low"
            base_max = 0.08
        
        # With volume bonus, max is base + 2%, capped at 15%
        expected_max = min(base_max + (0.02 if volume_confirmed else 0), 0.15)
        
        # Position percentage should not exceed expected max
        # (may be slightly less due to whole share rounding)
        assert result.percent_of_equity <= expected_max + 0.01, (
            f"Position {result.percent_of_equity*100:.1f}% exceeds max {expected_max*100:.1f}%"
        )
    
    @given(
        confidence=st.floats(min_value=0.0, max_value=59.9, allow_nan=False, allow_infinity=False),
        equity=st.floats(min_value=1000.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
        price=st.floats(min_value=1.0, max_value=500.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_low_confidence_skip(self, confidence, equity, price):
        """
        **Feature: momentum-wave-rider, Property 7: Low Confidence Skip**
        **Validates: Requirements 4.5**
        
        For any confidence score below 60, the system should skip the trade.
        """
        result = self.sizer.calculate_position_size(
            confidence=confidence,
            equity=equity,
            price=price,
            volume_confirmed=True,
            adx=25.0
        )
        
        assert result.skip_trade, f"Should skip with confidence {confidence}"
        assert result.shares == 0, "Shares should be 0 when skipping"
        assert "confidence" in result.skip_reason.lower(), "Skip reason should mention confidence"

    @given(
        confidence=st.floats(min_value=60.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        equity=st.floats(min_value=10000.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
        price=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_volume_bonus_cap(self, confidence, equity, price):
        """
        **Feature: momentum-wave-rider, Property 8: Volume Bonus Cap**
        **Validates: Requirements 4.6**
        
        For any position with volume bonus, the total position size 
        should not exceed 15% of equity.
        """
        # Calculate with volume bonus
        result_with_bonus = self.sizer.calculate_position_size(
            confidence=confidence,
            equity=equity,
            price=price,
            volume_confirmed=True,
            adx=25.0
        )
        
        # Calculate without volume bonus
        result_without_bonus = self.sizer.calculate_position_size(
            confidence=confidence,
            equity=equity,
            price=price,
            volume_confirmed=False,
            adx=25.0
        )
        
        # PROPERTY: Position should never exceed 15%
        assert result_with_bonus.percent_of_equity <= 0.15 + 0.01, (
            f"Position with bonus {result_with_bonus.percent_of_equity*100:.1f}% exceeds 15%"
        )
        
        # PROPERTY: Volume bonus should be applied when confirmed
        if confidence < 90:  # Below 90, there's room for bonus
            # With bonus should be >= without bonus (or equal if capped)
            assert result_with_bonus.percent_of_equity >= result_without_bonus.percent_of_equity - 0.01
    
    @given(
        adx=st.floats(min_value=0.0, max_value=19.9, allow_nan=False, allow_infinity=False),
        confidence=st.floats(min_value=60.0, max_value=100.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    def test_low_adx_skip(self, adx, confidence):
        """
        Test that low ADX (choppy market) causes trade to be skipped.
        
        **Validates: Requirements 5.4 (ADX filter)**
        """
        result = self.sizer.calculate_position_size(
            confidence=confidence,
            equity=50000.0,
            price=100.0,
            volume_confirmed=True,
            adx=adx
        )
        
        assert result.skip_trade, f"Should skip with ADX {adx}"
        assert "adx" in result.skip_reason.lower() or "choppy" in result.skip_reason.lower()
    
    def test_edge_cases(self):
        """Test edge cases for position sizing."""
        # Test with zero equity
        result = self.sizer.calculate_position_size(
            confidence=90,
            equity=0,
            price=100,
            volume_confirmed=True,
            adx=25
        )
        assert result.shares == 0, "Should have 0 shares with 0 equity"
        
        # Test with very high price (can't afford 1 share)
        result = self.sizer.calculate_position_size(
            confidence=90,
            equity=1000,
            price=2000,  # Price > equity
            volume_confirmed=True,
            adx=25
        )
        assert result.shares == 0, "Should have 0 shares when price > position size"
        
        # Test boundary at exactly 60 confidence
        result = self.sizer.calculate_position_size(
            confidence=60,
            equity=50000,
            price=100,
            volume_confirmed=False,
            adx=25
        )
        assert not result.skip_trade, "Should not skip at exactly 60 confidence"
        assert result.confidence_tier == "low"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
