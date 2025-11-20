#!/usr/bin/env python3
"""
Unit Tests for Sprint 7 Filters

Tests the new win rate optimization filters:
1. Time-of-day filter
2. 200-EMA daily trend filter
3. Multi-timeframe alignment filter
"""

import unittest
from datetime import datetime
import pytz
from unittest.mock import Mock, patch, MagicMock

# Import the strategy class
from trading.strategy import EMAStrategy
from data.daily_cache import DailyCache


class TestTimeOfDayFilter(unittest.TestCase):
    """Test time-of-day filter"""
    
    def setUp(self):
        self.order_manager = Mock()
        self.strategy = EMAStrategy(self.order_manager)
    
    @patch('trading.strategy.settings')
    @patch('trading.strategy.datetime')
    def test_first_hour_allowed(self, mock_dt, mock_settings):
        """Test first hour (9:30-10:30 AM) is allowed"""
        # Mock settings
        mock_settings.optimal_hours_start_1 = (9, 30)
        mock_settings.optimal_hours_end_1 = (10, 30)
        mock_settings.optimal_hours_start_2 = (15, 0)
        mock_settings.optimal_hours_end_2 = (16, 0)
        mock_settings.avoid_lunch_hour = True
        
        # 10:00 AM ET
        test_time = datetime(2025, 11, 11, 10, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
        mock_dt.now.return_value = test_time
        
        allowed, reason = self.strategy._is_optimal_trading_time()
        self.assertTrue(allowed)
        self.assertEqual(reason, "")
    
    @patch('trading.strategy.settings')
    @patch('trading.strategy.datetime')
    def test_last_hour_allowed(self, mock_dt, mock_settings):
        """Test last hour (3:00-4:00 PM) is allowed"""
        # Mock settings
        mock_settings.optimal_hours_start_1 = (9, 30)
        mock_settings.optimal_hours_end_1 = (10, 30)
        mock_settings.optimal_hours_start_2 = (15, 0)
        mock_settings.optimal_hours_end_2 = (16, 0)
        mock_settings.avoid_lunch_hour = True
        
        # 3:30 PM ET
        test_time = datetime(2025, 11, 11, 15, 30, 0, tzinfo=pytz.timezone('US/Eastern'))
        mock_dt.now.return_value = test_time
        
        allowed, reason = self.strategy._is_optimal_trading_time()
        self.assertTrue(allowed)
        self.assertEqual(reason, "")
    
    @patch('trading.strategy.settings')
    @patch('trading.strategy.datetime')
    def test_lunch_hour_blocked(self, mock_dt, mock_settings):
        """Test lunch hour (11:30 AM-2:00 PM) is blocked"""
        # Mock settings
        mock_settings.optimal_hours_start_1 = (9, 30)
        mock_settings.optimal_hours_end_1 = (10, 30)
        mock_settings.optimal_hours_start_2 = (15, 0)
        mock_settings.optimal_hours_end_2 = (16, 0)
        mock_settings.avoid_lunch_hour = True
        
        # 12:30 PM ET
        test_time = datetime(2025, 11, 11, 12, 30, 0, tzinfo=pytz.timezone('US/Eastern'))
        mock_dt.now.return_value = test_time
        
        allowed, reason = self.strategy._is_optimal_trading_time()
        self.assertFalse(allowed)
        self.assertIn("Lunch hour", reason)
    
    @patch('trading.strategy.settings')
    @patch('trading.strategy.datetime')
    def test_outside_hours_blocked(self, mock_dt, mock_settings):
        """Test outside optimal hours is blocked"""
        # Mock settings
        mock_settings.optimal_hours_start_1 = (9, 30)
        mock_settings.optimal_hours_end_1 = (10, 30)
        mock_settings.optimal_hours_start_2 = (15, 0)
        mock_settings.optimal_hours_end_2 = (16, 0)
        mock_settings.avoid_lunch_hour = True
        
        # 11:00 AM ET (between first and last hour)
        test_time = datetime(2025, 11, 11, 11, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
        mock_dt.now.return_value = test_time
        
        allowed, reason = self.strategy._is_optimal_trading_time()
        self.assertFalse(allowed)
        self.assertIn("Outside optimal", reason)


class TestDailyTrendFilter(unittest.TestCase):
    """Test 200-EMA daily trend filter"""
    
    def setUp(self):
        self.order_manager = Mock()
        self.strategy = EMAStrategy(self.order_manager)
    
    @patch('trading.strategy.get_daily_cache')
    def test_long_with_trend_allowed(self, mock_cache):
        """Test long signal with bullish trend is allowed"""
        # Mock daily data: price above 200-EMA
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get_daily_data.return_value = {
            'price': 105.0,
            'ema_200': 100.0,
            'trend': 'bullish'
        }
        
        allowed, reason = self.strategy._check_daily_trend('AAPL', 'buy')
        self.assertTrue(allowed)
        self.assertEqual(reason, "")
    
    @patch('trading.strategy.get_daily_cache')
    def test_long_against_trend_blocked(self, mock_cache):
        """Test long signal against trend is blocked"""
        # Mock daily data: price below 200-EMA
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get_daily_data.return_value = {
            'price': 95.0,
            'ema_200': 100.0,
            'trend': 'bearish'
        }
        
        allowed, reason = self.strategy._check_daily_trend('AAPL', 'buy')
        self.assertFalse(allowed)
        self.assertIn("Counter-trend long", reason)
    
    @patch('trading.strategy.get_daily_cache')
    def test_short_with_trend_allowed(self, mock_cache):
        """Test short signal with bearish trend is allowed"""
        # Mock daily data: price below 200-EMA
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get_daily_data.return_value = {
            'price': 95.0,
            'ema_200': 100.0,
            'trend': 'bearish'
        }
        
        allowed, reason = self.strategy._check_daily_trend('AAPL', 'sell')
        self.assertTrue(allowed)
        self.assertEqual(reason, "")
    
    @patch('trading.strategy.get_daily_cache')
    def test_short_against_trend_blocked(self, mock_cache):
        """Test short signal against trend is blocked"""
        # Mock daily data: price above 200-EMA
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get_daily_data.return_value = {
            'price': 105.0,
            'ema_200': 100.0,
            'trend': 'bullish'
        }
        
        allowed, reason = self.strategy._check_daily_trend('AAPL', 'sell')
        self.assertFalse(allowed)
        self.assertIn("Counter-trend short", reason)
    
    @patch('trading.strategy.get_daily_cache')
    def test_no_data_allowed(self, mock_cache):
        """Test missing daily data allows trade (graceful fallback)"""
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get_daily_data.return_value = None
        
        allowed, reason = self.strategy._check_daily_trend('AAPL', 'buy')
        self.assertTrue(allowed)
        self.assertEqual(reason, "")


class TestMultiTimeframeFilter(unittest.TestCase):
    """Test multi-timeframe alignment filter"""
    
    def setUp(self):
        self.order_manager = Mock()
        self.strategy = EMAStrategy(self.order_manager)
    
    @patch('trading.strategy.get_daily_cache')
    def test_long_with_bullish_daily_allowed(self, mock_cache):
        """Test long signal with bullish daily trend is allowed"""
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get_daily_data.return_value = {
            'trend': 'bullish',
            'ema_9': 105.0,
            'ema_21': 100.0
        }
        
        allowed, reason = self.strategy._check_timeframe_alignment('AAPL', 'buy')
        self.assertTrue(allowed)
        self.assertEqual(reason, "")
    
    @patch('trading.strategy.get_daily_cache')
    def test_long_with_bearish_daily_blocked(self, mock_cache):
        """Test long signal with bearish daily trend is blocked"""
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get_daily_data.return_value = {
            'trend': 'bearish',
            'ema_9': 95.0,
            'ema_21': 100.0
        }
        
        allowed, reason = self.strategy._check_timeframe_alignment('AAPL', 'buy')
        self.assertFalse(allowed)
        self.assertIn("Daily trend bearish", reason)
    
    @patch('trading.strategy.get_daily_cache')
    def test_short_with_bearish_daily_allowed(self, mock_cache):
        """Test short signal with bearish daily trend is allowed"""
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get_daily_data.return_value = {
            'trend': 'bearish',
            'ema_9': 95.0,
            'ema_21': 100.0
        }
        
        allowed, reason = self.strategy._check_timeframe_alignment('AAPL', 'sell')
        self.assertTrue(allowed)
        self.assertEqual(reason, "")
    
    @patch('trading.strategy.get_daily_cache')
    def test_short_with_bullish_daily_blocked(self, mock_cache):
        """Test short signal with bullish daily trend is blocked"""
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get_daily_data.return_value = {
            'trend': 'bullish',
            'ema_9': 105.0,
            'ema_21': 100.0
        }
        
        allowed, reason = self.strategy._check_timeframe_alignment('AAPL', 'sell')
        self.assertFalse(allowed)
        self.assertIn("Daily trend bullish", reason)


class TestDailyCache(unittest.TestCase):
    """Test daily cache functionality"""
    
    def setUp(self):
        self.cache = DailyCache()
    
    def test_cache_initialization(self):
        """Test cache initializes correctly"""
        self.assertEqual(len(self.cache.cache), 0)
        self.assertIsNone(self.cache.cache_date)
        self.assertFalse(self.cache.is_cache_valid())
    
    def test_set_and_get_data(self):
        """Test setting and getting cache data"""
        test_data = {
            'price': 100.0,
            'ema_200': 95.0,
            'ema_9': 102.0,
            'ema_21': 98.0,
            'trend': 'bullish'
        }
        
        self.cache.set_daily_data('AAPL', test_data)
        
        retrieved = self.cache.get_daily_data('AAPL')
        self.assertEqual(retrieved, test_data)
    
    def test_cache_stats(self):
        """Test cache statistics"""
        # Empty cache
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['symbols_cached'], 0)
        
        # Add data
        self.cache.set_daily_data('AAPL', {'price': 100.0})
        
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['symbols_cached'], 1)
    
    def test_clear_cache(self):
        """Test cache clearing"""
        self.cache.set_daily_data('AAPL', {'price': 100.0})
        self.assertEqual(len(self.cache.cache), 1)
        
        self.cache.clear_cache()
        self.assertEqual(len(self.cache.cache), 0)
        self.assertIsNone(self.cache.cache_date)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
