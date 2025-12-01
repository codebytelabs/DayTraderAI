#!/usr/bin/env python3
"""
Property-Based Tests for MomentumScanner

**Feature: momentum-wave-rider, Property 1: Volume Filter Correctness**
**Validates: Requirements 1.3**

These tests use property-based testing to verify correctness properties
that should hold for all valid inputs, not just specific examples.
"""

import pytest
from hypothesis import given, strategies as st, settings
from typing import List, Dict
from unittest.mock import Mock


class TestMomentumScannerProperties:
    """
    Property-based tests for MomentumScanner.
    
    These tests verify that certain properties hold for all valid inputs,
    ensuring the scanner behaves correctly across a wide range of scenarios.
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        from scanner.momentum_scanner import MomentumScanner
        
        # Mock clients
        self.mock_alpaca = Mock()
        self.mock_market_data = Mock()
        
        # Create scanner instance
        self.scanner = MomentumScanner(self.mock_alpaca, self.mock_market_data)
    
    @given(
        candidates=st.lists(
            st.fixed_dictionaries({
                'symbol': st.text(min_size=1, max_size=5, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
                'price': st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
                'change_pct': st.floats(min_value=-50.0, max_value=50.0, allow_nan=False, allow_infinity=False),
                'volume': st.integers(min_value=1000, max_value=10000000),
                'bars': st.lists(
                    st.fixed_dictionaries({
                        'volume': st.integers(min_value=1000, max_value=5000000),
                        'close': st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
                        'open': st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
                        'high': st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
                        'low': st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
                    }),
                    min_size=21,  # Ensure we have enough bars for volume calculation
                    max_size=100
                )
            }),
            min_size=0,
            max_size=50
        ),
        min_ratio=st.floats(min_value=1.0, max_value=5.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=5000)
    def test_volume_filter_correctness(self, candidates: List[Dict], min_ratio: float):
        """
        **Feature: momentum-wave-rider, Property 1: Volume Filter Correctness**
        **Validates: Requirements 1.3**
        
        For any set of candidates returned by filter_by_volume_surge(),
        all candidates should have volume_ratio >= min_ratio.
        """
        # Apply the volume filter
        filtered_candidates = self.scanner.filter_by_volume_surge(candidates, min_ratio)
        
        # PROPERTY: All filtered candidates must have volume_ratio >= min_ratio
        for candidate in filtered_candidates:
            volume_ratio = candidate.get('volume_ratio', 0.0)
            assert volume_ratio >= min_ratio, (
                f"Volume filter failed: {candidate['symbol']} has ratio {volume_ratio:.2f} "
                f"but minimum required is {min_ratio:.2f}"
            )
        
        # PROPERTY: Filtered list should be a subset of original list
        filtered_symbols = {c['symbol'] for c in filtered_candidates}
        original_symbols = {c['symbol'] for c in candidates}
        assert filtered_symbols.issubset(original_symbols), (
            "Filtered candidates contain symbols not in original list"
        )

    @given(
        bars=st.lists(
            st.fixed_dictionaries({
                'volume': st.integers(min_value=1000, max_value=5000000),
                'close': st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
                'open': st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
                'high': st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
                'low': st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
            }),
            min_size=21,
            max_size=100
        )
    )
    @settings(max_examples=50)
    def test_volume_ratio_calculation_properties(self, bars: List[Dict]):
        """
        Property: Volume Ratio Calculation Properties
        
        Tests that volume ratio calculation behaves correctly:
        1. Always returns a positive number
        2. Is finite (not inf or nan)
        """
        candidate = {
            'symbol': 'TEST',
            'bars': bars
        }
        
        # Calculate volume ratio
        volume_ratio = self.scanner._calculate_volume_ratio(candidate)
        
        # PROPERTY: Volume ratio should always be positive
        assert volume_ratio > 0, f"Volume ratio should be positive, got {volume_ratio}"
        
        # PROPERTY: Volume ratio should be finite
        assert volume_ratio != float('inf'), f"Volume ratio should be finite, got {volume_ratio}"
        assert volume_ratio == volume_ratio, f"Volume ratio should not be NaN"
    
    def test_volume_filter_edge_cases(self):
        """
        Test edge cases for volume filter that might not be covered by property tests.
        """
        # Test empty candidates list
        result = self.scanner.filter_by_volume_surge([], 1.5)
        assert result == [], "Empty input should return empty output"
        
        # Test candidate with insufficient bars
        candidate_insufficient_bars = {
            'symbol': 'TEST',
            'bars': [{'volume': 1000, 'close': 100.0, 'open': 99.0, 'high': 101.0, 'low': 98.0}]
        }
        result = self.scanner.filter_by_volume_surge([candidate_insufficient_bars], 1.5)
        assert isinstance(result, list), "Should handle insufficient bars gracefully"
        
        # Test candidate with high volume surge (should pass)
        high_volume_bars = [
            {'volume': 1000, 'close': 100.0, 'open': 99.0, 'high': 101.0, 'low': 98.0}
            for _ in range(20)
        ]
        # Add a high volume bar at the end
        high_volume_bars.append({'volume': 5000, 'close': 100.0, 'open': 99.0, 'high': 101.0, 'low': 98.0})
        
        candidate_high_volume = {
            'symbol': 'HIGH',
            'bars': high_volume_bars
        }
        result = self.scanner.filter_by_volume_surge([candidate_high_volume], 1.5)
        assert len(result) == 1, "High volume candidate should pass filter"
        assert result[0]['volume_ratio'] >= 1.5, "Volume ratio should be >= 1.5"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
