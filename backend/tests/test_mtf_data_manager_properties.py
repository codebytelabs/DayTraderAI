"""
Property-Based Tests for Multi-Timeframe Data Manager.

Uses Hypothesis to verify correctness properties from the design document.
Tests the caching and fallback behavior of MTFDataManager.

**Feature: multi-timeframe-analysis**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.mtf.data_manager import MTFDataManager, CacheEntry


# Configure Hypothesis for CI
settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=50)


def create_mock_bars(num_bars: int = 50) -> pd.DataFrame:
    """Create mock OHLCV bar data for testing."""
    dates = pd.date_range(
        end=datetime.now(timezone.utc),
        periods=num_bars,
        freq='1min'
    )
    
    base_price = 100.0
    data = {
        'open': np.random.uniform(base_price * 0.99, base_price * 1.01, num_bars),
        'high': np.random.uniform(base_price * 1.00, base_price * 1.02, num_bars),
        'low': np.random.uniform(base_price * 0.98, base_price * 1.00, num_bars),
        'close': np.random.uniform(base_price * 0.99, base_price * 1.01, num_bars),
        'volume': np.random.randint(1000, 100000, num_bars),
    }
    
    df = pd.DataFrame(data, index=dates)
    return df


class MockAlpacaClient:
    """Mock Alpaca client for testing."""
    
    def __init__(self, should_fail: bool = False, return_empty: bool = False):
        self.should_fail = should_fail
        self.return_empty = return_empty
        self.call_count = 0
    
    def get_bars_for_symbol(self, symbol, timeframe, start=None, limit=None):
        self.call_count += 1
        
        if self.should_fail:
            raise Exception("Simulated API failure")
        
        if self.return_empty:
            return pd.DataFrame()
        
        return create_mock_bars(limit or 50)


class TestMTFDataManagerCacheProperties:
    """Property tests for MTFDataManager caching behavior."""
    
    @given(
        symbol=st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=5),
        timeframe=st.sampled_from(['1min', '5min', '15min', 'daily']),
    )
    @settings(max_examples=100)
    def test_property_cache_fallback_on_failure(self, symbol: str, timeframe: str):
        """
        **Feature: multi-timeframe-analysis, Property: Data Cache Fallback**
        
        For any symbol and timeframe, when a fetch fails, the system should
        return cached data if available.
        
        **Validates: Requirements 1.3, 1.4**
        """
        # Create manager with working client first
        working_client = MockAlpacaClient(should_fail=False)
        manager = MTFDataManager(alpaca_client=working_client)
        
        # Pre-populate cache with successful fetch
        initial_data = manager._fetch_timeframe_data(symbol, timeframe)
        assume(initial_data is not None)  # Skip if initial fetch fails
        
        # Now simulate failure
        failing_client = MockAlpacaClient(should_fail=True)
        manager.alpaca_client = failing_client
        
        # Fetch should return cached data on failure
        result = manager._fetch_timeframe_data(symbol, timeframe, use_cache_on_failure=True)
        
        assert result is not None, (
            f"Should return cached data for {symbol} {timeframe} when fetch fails"
        )
        assert len(result) > 0, (
            f"Cached data should not be empty for {symbol} {timeframe}"
        )

    
    @given(
        symbol=st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=5),
        timeframe=st.sampled_from(['1min', '5min', '15min', 'daily']),
    )
    @settings(max_examples=100)
    def test_cache_stores_data_after_successful_fetch(self, symbol: str, timeframe: str):
        """
        Test that successful fetches are stored in cache.
        
        **Validates: Requirements 1.3**
        """
        client = MockAlpacaClient(should_fail=False)
        manager = MTFDataManager(alpaca_client=client)
        
        # Fetch data
        data = manager._fetch_timeframe_data(symbol, timeframe)
        assume(data is not None)
        
        # Check cache
        cached = manager._get_cached_data(symbol, timeframe)
        
        assert cached is not None, (
            f"Data should be cached after successful fetch for {symbol} {timeframe}"
        )
        assert len(cached) == len(data), (
            f"Cached data length should match fetched data length"
        )
    
    @given(
        symbol=st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=5),
    )
    @settings(max_examples=50)
    def test_fetch_all_timeframes_returns_all_four(self, symbol: str):
        """
        Test that fetch_all_timeframes returns data for all four timeframes.
        
        **Validates: Requirements 1.1**
        """
        client = MockAlpacaClient(should_fail=False)
        manager = MTFDataManager(alpaca_client=client)
        
        result = manager.fetch_all_timeframes(symbol, force_refresh=True)
        
        expected_timeframes = {'1min', '5min', '15min', 'daily'}
        actual_timeframes = set(result.keys())
        
        assert actual_timeframes == expected_timeframes, (
            f"Should return all four timeframes, got {actual_timeframes}"
        )
        
        for tf, data in result.items():
            assert data is not None, f"Data for {tf} should not be None"
            assert len(data) > 0, f"Data for {tf} should not be empty"
    
    def test_refresh_intervals_are_correct(self):
        """
        Test that refresh intervals match requirements.
        
        **Validates: Requirements 1.2**
        """
        client = MockAlpacaClient()
        manager = MTFDataManager(alpaca_client=client)
        
        # Verify refresh intervals per Requirement 1.2
        assert manager.REFRESH_INTERVALS['1min'] == 60, "1-min should refresh every 60 seconds"
        assert manager.REFRESH_INTERVALS['5min'] == 300, "5-min should refresh every 5 minutes"
        assert manager.REFRESH_INTERVALS['15min'] == 900, "15-min should refresh every 15 minutes"
        assert manager.REFRESH_INTERVALS['daily'] == 86400, "Daily should refresh once per day"
    
    @given(
        elapsed_seconds=st.integers(min_value=0, max_value=100000),
    )
    @settings(max_examples=100)
    def test_needs_refresh_logic(self, elapsed_seconds: int):
        """
        Test that _needs_refresh correctly determines when refresh is needed.
        
        **Validates: Requirements 1.2**
        """
        client = MockAlpacaClient()
        manager = MTFDataManager(alpaca_client=client)
        
        # Set last refresh time
        past_time = datetime.now(timezone.utc) - timedelta(seconds=elapsed_seconds)
        manager.last_refresh['5min'] = past_time
        
        needs_refresh = manager._needs_refresh('5min')
        expected = elapsed_seconds >= manager.REFRESH_INTERVALS['5min']
        
        assert needs_refresh == expected, (
            f"After {elapsed_seconds}s, needs_refresh should be {expected}, got {needs_refresh}"
        )
    
    def test_empty_response_uses_cache(self):
        """
        Test that empty API response falls back to cache.
        
        **Validates: Requirements 1.4**
        """
        # First, populate cache with working client
        working_client = MockAlpacaClient(should_fail=False)
        manager = MTFDataManager(alpaca_client=working_client)
        
        symbol = "AAPL"
        timeframe = "5min"
        
        # Populate cache
        initial_data = manager._fetch_timeframe_data(symbol, timeframe)
        assert initial_data is not None
        
        # Now use client that returns empty data
        empty_client = MockAlpacaClient(return_empty=True)
        manager.alpaca_client = empty_client
        
        # Should fall back to cached data
        result = manager._fetch_timeframe_data(symbol, timeframe, use_cache_on_failure=True)
        
        assert result is not None, "Should return cached data when API returns empty"
        assert len(result) > 0, "Cached data should not be empty"
    
    def test_clear_cache_removes_data(self):
        """
        Test that clear_cache properly removes cached data.
        """
        client = MockAlpacaClient()
        manager = MTFDataManager(alpaca_client=client)
        
        # Populate cache
        manager._fetch_timeframe_data("AAPL", "5min")
        manager._fetch_timeframe_data("AAPL", "15min")
        manager._fetch_timeframe_data("MSFT", "5min")
        
        # Clear specific symbol/timeframe
        manager.clear_cache(symbol="AAPL", timeframe="5min")
        assert manager._get_cached_data("AAPL", "5min") is None
        assert manager._get_cached_data("AAPL", "15min") is not None
        
        # Clear all for symbol
        manager.clear_cache(symbol="AAPL")
        assert manager._get_cached_data("AAPL", "15min") is None
        assert manager._get_cached_data("MSFT", "5min") is not None
        
        # Clear all
        manager.clear_cache()
        assert manager._get_cached_data("MSFT", "5min") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
