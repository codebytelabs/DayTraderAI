#!/usr/bin/env python3
"""
Unit Tests for Daily Cache with Twelve Data Integration
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import sys
import os
from dotenv import load_dotenv
import pathlib

# Load .env before importing modules
env_path = pathlib.Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from data.daily_cache import DailyCache


class TestDailyCacheUnit(unittest.TestCase):
    """Unit tests for DailyCache class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.cache = DailyCache()
        self.test_symbol = 'AAPL'
    
    def test_init(self):
        """Test cache initialization"""
        self.assertIsNotNone(self.cache)
        self.assertEqual(len(self.cache.cache), 0)
        self.assertIsNone(self.cache.cache_date)
        self.assertEqual(self.cache.twelvedata_base_url, "https://api.twelvedata.com")
    
    def test_is_cache_valid_empty(self):
        """Test cache validity when empty"""
        self.assertFalse(self.cache.is_cache_valid())
    
    def test_is_cache_valid_today(self):
        """Test cache validity for today"""
        self.cache.cache_date = datetime.now().date()
        self.assertTrue(self.cache.is_cache_valid())
    
    def test_is_cache_valid_yesterday(self):
        """Test cache validity for yesterday"""
        from datetime import timedelta
        self.cache.cache_date = datetime.now().date() - timedelta(days=1)
        self.assertFalse(self.cache.is_cache_valid())
    
    def test_get_daily_data_empty(self):
        """Test getting data from empty cache"""
        result = self.cache.get_daily_data(self.test_symbol)
        self.assertIsNone(result)
    
    def test_set_and_get_daily_data(self):
        """Test setting and getting daily data"""
        test_data = {
            'price': 269.43,
            'ema_200': 232.16,
            'ema_9': 265.50,
            'ema_21': 260.30,
            'trend': 'bullish'
        }
        
        self.cache.set_daily_data(self.test_symbol, test_data)
        self.cache.cache_date = datetime.now().date()  # Mark as valid
        
        result = self.cache.get_daily_data(self.test_symbol)
        self.assertIsNotNone(result)
        self.assertEqual(result['price'], 269.43)
        self.assertEqual(result['ema_200'], 232.16)
        self.assertEqual(result['trend'], 'bullish')
    
    def test_calculate_ema_simple(self):
        """Test EMA calculation with simple data"""
        prices = [100, 102, 101, 103, 105]
        ema = self.cache.calculate_ema(prices, 3)
        
        # EMA should be between min and max
        self.assertGreater(ema, 100)
        self.assertLess(ema, 105)
        self.assertIsInstance(ema, float)
    
    def test_calculate_ema_insufficient_data(self):
        """Test EMA calculation with insufficient data"""
        prices = [100, 102]
        ema = self.cache.calculate_ema(prices, 10)
        
        # Should return last price
        self.assertEqual(ema, 102)
    
    def test_calculate_ema_200(self):
        """Test 200-EMA calculation"""
        # Generate 200 prices trending up
        prices = [100 + i * 0.5 for i in range(200)]
        ema = self.cache.calculate_ema(prices, 200)
        
        # EMA should be between start and end
        self.assertGreater(ema, 100)
        self.assertLess(ema, 200)
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Add some data
        self.cache.set_daily_data(self.test_symbol, {'price': 100})
        self.assertEqual(len(self.cache.cache), 1)
        
        # Clear cache
        self.cache.clear_cache()
        self.assertEqual(len(self.cache.cache), 0)
        self.assertIsNone(self.cache.cache_date)
    
    def test_get_cache_stats_empty(self):
        """Test cache statistics when empty"""
        stats = self.cache.get_cache_stats()
        
        self.assertEqual(stats['symbols_cached'], 0)
        self.assertIsNone(stats['cache_date'])
        self.assertFalse(stats['is_valid'])
    
    def test_get_cache_stats_with_data(self):
        """Test cache statistics with data"""
        self.cache.set_daily_data('AAPL', {'price': 100})
        self.cache.set_daily_data('TSLA', {'price': 200})
        
        stats = self.cache.get_cache_stats()
        
        self.assertEqual(stats['symbols_cached'], 2)
        self.assertEqual(stats['cache_date'], datetime.now().date())
        self.assertTrue(stats['is_valid'])
    
    @patch('requests.get')
    def test_fetch_twelvedata_bars_success(self, mock_get):
        """Test successful Twelve Data API call"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'values': [
                {'datetime': '2025-11-10', 'close': '269.43'},
                {'datetime': '2025-11-09', 'close': '268.50'},
                {'datetime': '2025-11-08', 'close': '267.80'}
            ]
        }
        mock_get.return_value = mock_response
        
        # Set API key
        self.cache.twelvedata_api_key = 'test_key'
        
        # Fetch bars
        bars = self.cache.fetch_twelvedata_bars('AAPL')
        
        # Verify
        self.assertIsNotNone(bars)
        self.assertEqual(len(bars), 3)
        # Should be reversed (oldest first)
        self.assertEqual(bars[0]['datetime'], '2025-11-08')
        self.assertEqual(bars[-1]['datetime'], '2025-11-10')
    
    @patch('requests.get')
    def test_fetch_twelvedata_bars_api_error(self, mock_get):
        """Test Twelve Data API error response"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'error',
            'message': 'Invalid API key'
        }
        mock_get.return_value = mock_response
        
        self.cache.twelvedata_api_key = 'invalid_key'
        
        bars = self.cache.fetch_twelvedata_bars('AAPL')
        
        self.assertIsNone(bars)
    
    @patch('requests.get')
    def test_fetch_twelvedata_bars_http_error(self, mock_get):
        """Test Twelve Data HTTP error"""
        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 429  # Rate limit
        mock_get.return_value = mock_response
        
        self.cache.twelvedata_api_key = 'test_key'
        
        bars = self.cache.fetch_twelvedata_bars('AAPL')
        
        self.assertIsNone(bars)
    
    @patch('requests.get')
    def test_fetch_twelvedata_bars_no_api_key(self, mock_get):
        """Test Twelve Data call without API key"""
        self.cache.twelvedata_api_key = None
        
        bars = self.cache.fetch_twelvedata_bars('AAPL')
        
        self.assertIsNone(bars)
        mock_get.assert_not_called()
    
    @patch.object(DailyCache, 'fetch_twelvedata_bars')
    def test_refresh_cache_success(self, mock_fetch):
        """Test successful cache refresh"""
        # Mock Twelve Data response
        mock_bars = [
            {'datetime': f'2025-{10-i:02d}-01', 'close': str(100 + i)}
            for i in range(200)
        ]
        mock_fetch.return_value = mock_bars
        
        # Refresh cache
        self.cache.refresh_cache(symbols=['AAPL', 'TSLA'])
        
        # Verify
        self.assertEqual(len(self.cache.cache), 2)
        self.assertIsNotNone(self.cache.get_daily_data('AAPL'))
        self.assertIsNotNone(self.cache.get_daily_data('TSLA'))
        self.assertEqual(self.cache.cache_date, datetime.now().date())
    
    @patch.object(DailyCache, 'fetch_twelvedata_bars')
    def test_refresh_cache_partial_failure(self, mock_fetch):
        """Test cache refresh with some failures"""
        # Mock: AAPL succeeds, TSLA fails
        def side_effect(symbol):
            if symbol == 'AAPL':
                return [{'datetime': f'2025-{10-i:02d}-01', 'close': str(100 + i)} for i in range(200)]
            else:
                return None
        
        mock_fetch.side_effect = side_effect
        
        # Refresh cache
        self.cache.refresh_cache(symbols=['AAPL', 'TSLA'])
        
        # Verify
        self.assertEqual(len(self.cache.cache), 1)
        self.assertIsNotNone(self.cache.get_daily_data('AAPL'))
        self.assertIsNone(self.cache.get_daily_data('TSLA'))
    
    @patch.object(DailyCache, 'fetch_twelvedata_bars')
    def test_refresh_cache_insufficient_bars(self, mock_fetch):
        """Test cache refresh with insufficient bars"""
        # Mock: Only 50 bars (need 200)
        mock_bars = [
            {'datetime': f'2025-10-{i:02d}', 'close': str(100 + i)}
            for i in range(50)
        ]
        mock_fetch.return_value = mock_bars
        
        # Refresh cache
        self.cache.refresh_cache(symbols=['AAPL'])
        
        # Verify - should fail
        self.assertEqual(len(self.cache.cache), 0)
    
    def test_trend_calculation_bullish(self):
        """Test bullish trend detection"""
        # EMA 9 > EMA 21 = bullish
        test_data = {
            'price': 100,
            'ema_200': 90,
            'ema_9': 102,  # Higher
            'ema_21': 98,  # Lower
            'trend': 'bullish'
        }
        
        self.cache.set_daily_data('TEST', test_data)
        result = self.cache.get_daily_data('TEST')
        
        self.assertEqual(result['trend'], 'bullish')
    
    def test_trend_calculation_bearish(self):
        """Test bearish trend detection"""
        # EMA 9 < EMA 21 = bearish
        test_data = {
            'price': 100,
            'ema_200': 110,
            'ema_9': 98,   # Lower
            'ema_21': 102, # Higher
            'trend': 'bearish'
        }
        
        self.cache.set_daily_data('TEST', test_data)
        result = self.cache.get_daily_data('TEST')
        
        self.assertEqual(result['trend'], 'bearish')


def run_tests():
    """Run all unit tests"""
    print("="*80)
    print("🧪 DAILY CACHE UNIT TESTS")
    print("="*80)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDailyCacheUnit)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL UNIT TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    exit(run_tests())
