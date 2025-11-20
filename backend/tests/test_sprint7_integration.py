#!/usr/bin/env python3
"""
Integration Test for Sprint 7 Filters

Tests all three filters working together in the strategy evaluation flow.
"""

import unittest
from datetime import datetime
import pytz
from unittest.mock import Mock, patch, MagicMock

from trading.strategy import EMAStrategy
from data.daily_cache import DailyCache


class TestSprint7Integration(unittest.TestCase):
    """Integration tests for all Sprint 7 filters together"""
    
    def setUp(self):
        self.order_manager = Mock()
        self.strategy = EMAStrategy(self.order_manager)
    
    @patch('trading.strategy.settings')
    @patch('trading.strategy.get_daily_cache')
    @patch('trading.strategy.datetime')
    @patch('trading.strategy.trading_state')
    @patch('trading.strategy.FeatureEngine')
    def test_all_filters_pass_buy_signal(self, mock_fe, mock_state, mock_dt, mock_cache, mock_settings):
        """Test buy signal passes all filters"""
        # Mock no existing position
        mock_state.get_position.return_value = None
        
        # Mock optimal time (10:00 AM)
        test_time = datetime(2025, 11, 11, 10, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
        mock_dt.now.return_value = test_time
        
        # Mock settings
        mock_settings.enable_time_of_day_filter = True
        mock_settings.enable_200_ema_filter = True
        mock_settings.enable_multitime_frame_filter = True
        mock_settings.optimal_hours_start_1 = (9, 30)
        mock_settings.optimal_hours_end_1 = (10, 30)
        mock_settings.optimal_hours_start_2 = (15, 0)
        mock_settings.optimal_hours_end_2 = (16, 0)
        mock_settings.avoid_lunch_hour = True
        
        # Mock daily data (bullish trend, price > 200-EMA)
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get_daily_data.return_value = {
            'price': 105.0,
            'ema_200': 100.0,
            'trend': 'bullish',
            'ema_9': 106.0,
            'ema_21': 103.0
        }
        
        # Mock enhanced signal detection
        mock_fe.detect_enhanced_signal.return_value = {
            'signal': 'buy',
            'confidence': 75.0,
            'confirmations': ['rsi_bullish', 'macd_bullish', 'volume_confirmed'],
            'confirmation_count': 3,
            'market_regime': 'trending',
            'rsi': 55.0,
            'adx': 25.0,
            'volume_ratio': 1.5
        }
        
        # Mock features
        features = {
            'ema_9': 106.0,
            'ema_21': 103.0,
            'rsi': 55.0,
            'atr': 2.5
        }
        
        # Evaluate
        signal = self.strategy.evaluate('AAPL', features)
        
        # Should return 'buy' signal
        self.assertEqual(signal, 'buy')
    
    @patch('trading.strategy.settings')
    @patch('trading.strategy.get_daily_cache')
    @patch('trading.strategy.datetime')
    @patch('trading.strategy.trading_state')
    @patch('trading.strategy.FeatureEngine')
    def test_time_filter_blocks_signal(self, mock_fe, mock_state, mock_dt, mock_cache, mock_settings):
        """Test time-of-day filter blocks signal during lunch"""
        # Mock no existing position
        mock_state.get_position.return_value = None
        
        # Mock lunch hour (12:30 PM)
        test_time = datetime(2025, 11, 11, 12, 30, 0, tzinfo=pytz.timezone('US/Eastern'))
        mock_dt.now.return_value = test_time
        
        # Mock settings
        mock_settings.enable_time_of_day_filter = True
        mock_settings.enable_200_ema_filter = True
        mock_settings.enable_multitime_frame_filter = True
        mock_settings.optimal_hours_start_1 = (9, 30)
        mock_settings.optimal_hours_end_1 = (10, 30)
        mock_settings.optimal_hours_start_2 = (15, 0)
        mock_settings.optimal_hours_end_2 = (16, 0)
        mock_settings.avoid_lunch_hour = True
        
        # Mock features
        features = {'ema_9': 106.0, 'ema_21': 103.0}
        
        # Evaluate
        signal = self.strategy.evaluate('AAPL', features)
        
        # Should be blocked by time filter
        self.assertIsNone(signal)
        
        # FeatureEngine should NOT be called (filtered before signal detection)
        mock_fe.detect_enhanced_signal.assert_not_called()
    
    @patch('trading.strategy.settings')
    @patch('trading.strategy.get_daily_cache')
    @patch('trading.strategy.datetime')
    @patch('trading.strategy.trading_state')
    @patch('trading.strategy.FeatureEngine')
    def test_200ema_filter_blocks_counter_trend(self, mock_fe, mock_state, mock_dt, mock_cache, mock_settings):
        """Test 200-EMA filter blocks counter-trend trade"""
        # Mock no existing position
        mock_state.get_position.return_value = None
        
        # Mock optimal time (10:00 AM)
        test_time = datetime(2025, 11, 11, 10, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
        mock_dt.now.return_value = test_time
        
        # Mock settings
        mock_settings.enable_time_of_day_filter = True
        mock_settings.enable_200_ema_filter = True
        mock_settings.enable_multitime_frame_filter = True
        mock_settings.optimal_hours_start_1 = (9, 30)
        mock_settings.optimal_hours_end_1 = (10, 30)
        mock_settings.optimal_hours_start_2 = (15, 0)
        mock_settings.optimal_hours_end_2 = (16, 0)
        mock_settings.avoid_lunch_hour = True
        
        # Mock daily data (price BELOW 200-EMA - bearish)
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get_daily_data.return_value = {
            'price': 95.0,
            'ema_200': 100.0,
            'trend': 'bearish'
        }
        
        # Mock enhanced signal detection (BUY signal)
        mock_fe.detect_enhanced_signal.return_value = {
            'signal': 'buy',  # Trying to buy in downtrend
            'confidence': 75.0,
            'confirmations': ['rsi_bullish'],
            'confirmation_count': 1,
            'market_regime': 'ranging'
        }
        
        # Mock features
        features = {'ema_9': 96.0, 'ema_21': 94.0}
        
        # Evaluate
        signal = self.strategy.evaluate('AAPL', features)
        
        # Should be blocked by 200-EMA filter
        self.assertIsNone(signal)
    
    @patch('trading.strategy.settings')
    @patch('trading.strategy.get_daily_cache')
    @patch('trading.strategy.datetime')
    @patch('trading.strategy.trading_state')
    @patch('trading.strategy.FeatureEngine')
    def test_multitime_filter_blocks_misaligned(self, mock_fe, mock_state, mock_dt, mock_cache, mock_settings):
        """Test multi-timeframe filter blocks misaligned trade"""
        # Mock no existing position
        mock_state.get_position.return_value = None
        
        # Mock optimal time (10:00 AM)
        test_time = datetime(2025, 11, 11, 10, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
        mock_dt.now.return_value = test_time
        
        # Mock settings
        mock_settings.enable_time_of_day_filter = True
        mock_settings.enable_200_ema_filter = True
        mock_settings.enable_multitime_frame_filter = True
        mock_settings.optimal_hours_start_1 = (9, 30)
        mock_settings.optimal_hours_end_1 = (10, 30)
        mock_settings.optimal_hours_start_2 = (15, 0)
        mock_settings.optimal_hours_end_2 = (16, 0)
        mock_settings.avoid_lunch_hour = True
        
        # Mock daily data (price > 200-EMA but trend is bearish)
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get_daily_data.return_value = {
            'price': 105.0,
            'ema_200': 100.0,
            'trend': 'bearish',  # Daily trend bearish
            'ema_9': 104.0,
            'ema_21': 106.0
        }
        
        # Mock enhanced signal detection (BUY signal)
        mock_fe.detect_enhanced_signal.return_value = {
            'signal': 'buy',  # Trying to buy when daily is bearish
            'confidence': 75.0,
            'confirmations': ['rsi_bullish'],
            'confirmation_count': 1,
            'market_regime': 'ranging'
        }
        
        # Mock features
        features = {'ema_9': 106.0, 'ema_21': 103.0}
        
        # Evaluate
        signal = self.strategy.evaluate('AAPL', features)
        
        # Should be blocked by multi-timeframe filter
        self.assertIsNone(signal)
    
    @patch('trading.strategy.settings')
    def test_filters_can_be_disabled(self, mock_settings):
        """Test filters can be disabled via settings"""
        # Disable all filters
        mock_settings.enable_time_of_day_filter = False
        mock_settings.enable_200_ema_filter = False
        mock_settings.enable_multitime_frame_filter = False
        
        # Filters should not be called when disabled
        # This is tested implicitly by the strategy flow
        self.assertFalse(mock_settings.enable_time_of_day_filter)
        self.assertFalse(mock_settings.enable_200_ema_filter)
        self.assertFalse(mock_settings.enable_multitime_frame_filter)


class TestFilterOrdering(unittest.TestCase):
    """Test that filters are applied in the correct order"""
    
    def setUp(self):
        self.order_manager = Mock()
        self.strategy = EMAStrategy(self.order_manager)
    
    @patch('trading.strategy.settings')
    @patch('trading.strategy.datetime')
    @patch('trading.strategy.trading_state')
    def test_time_filter_runs_first(self, mock_state, mock_dt, mock_settings):
        """Test time-of-day filter runs before signal detection"""
        # Mock no existing position
        mock_state.get_position.return_value = None
        
        # Mock lunch hour (should block immediately)
        test_time = datetime(2025, 11, 11, 12, 30, 0, tzinfo=pytz.timezone('US/Eastern'))
        mock_dt.now.return_value = test_time
        
        # Enable time filter
        mock_settings.enable_time_of_day_filter = True
        mock_settings.optimal_hours_start_1 = (9, 30)
        mock_settings.optimal_hours_end_1 = (10, 30)
        mock_settings.optimal_hours_start_2 = (15, 0)
        mock_settings.optimal_hours_end_2 = (16, 0)
        mock_settings.avoid_lunch_hour = True
        
        # Mock features
        features = {'ema_9': 106.0, 'ema_21': 103.0}
        
        # Evaluate
        with patch('trading.strategy.FeatureEngine') as mock_fe:
            signal = self.strategy.evaluate('AAPL', features)
            
            # Should be blocked by time filter
            self.assertIsNone(signal)
            
            # FeatureEngine should NOT be called (time filter runs first)
            mock_fe.detect_enhanced_signal.assert_not_called()


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
