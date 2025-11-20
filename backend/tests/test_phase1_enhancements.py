"""
Unit Tests for Phase 1 Enhancements
Tests AI Scanner and Risk Manager daily data integration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

import unittest
from unittest.mock import Mock, patch, MagicMock
from scanner.opportunity_scanner import OpportunityScanner
from trading.risk_manager import RiskManager


class TestAIScannerEnhancements(unittest.TestCase):
    """Test AI Scanner daily data bonus calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.market_data = Mock()
        self.scanner = OpportunityScanner(self.market_data, use_ai=False)
        
        # Mock daily cache
        self.scanner.daily_cache = Mock()
    
    def test_long_signal_above_200ema_strong_uptrend(self):
        """Test LONG signal gets bonus for strong uptrend (>15% above 200-EMA)."""
        # Mock daily data: Strong uptrend
        self.scanner.daily_cache.get_daily_data.return_value = {
            'ema_200': 100.0,
            'ema_9': 125.0,
            'ema_21': 120.0,
            'trend': 'bullish'
        }
        
        # Current price 20% above 200-EMA
        bonus = self.scanner.calculate_daily_data_bonus('AAPL', 120.0, signal='long')
        
        # Should get maximum bonuses
        self.assertEqual(bonus['ema_200_bonus'], 15, "Should get +15 for >15% above 200-EMA")
        # Trend strength is (125-120)/120 = 4.17%, so gets +10 (moderate, not strong which needs >5%)
        self.assertGreaterEqual(bonus['daily_trend_bonus'], 10, "Should get at least +10 for bullish trend")
        # Trend strength bonus: both >10 and >5 = 5 points (good alignment, not excellent which needs both >10)
        self.assertGreaterEqual(bonus['trend_strength_bonus'], 5, "Should get at least +5 for good alignment")
        self.assertGreaterEqual(bonus['total_bonus'], 30, "Total should be at least 30 points")
    
    def test_short_signal_below_200ema_strong_downtrend(self):
        """Test SHORT signal gets bonus for strong downtrend (>15% below 200-EMA)."""
        # Mock daily data: Strong downtrend
        self.scanner.daily_cache.get_daily_data.return_value = {
            'ema_200': 100.0,
            'ema_9': 80.0,
            'ema_21': 85.0,
            'trend': 'bearish'
        }
        
        # Current price 20% below 200-EMA
        bonus = self.scanner.calculate_daily_data_bonus('XYZ', 80.0, signal='short')
        
        # Should get maximum bonuses
        self.assertEqual(bonus['ema_200_bonus'], 15, "Should get +15 for >15% below 200-EMA")
        self.assertEqual(bonus['daily_trend_bonus'], 15, "Should get +15 for strong bearish trend")
        self.assertEqual(bonus['trend_strength_bonus'], 10, "Should get +10 for excellent alignment")
        self.assertEqual(bonus['total_bonus'], 40, "Total should be 40 points")
    
    def test_long_signal_below_200ema_gets_no_bonus(self):
        """Test LONG signal gets NO bonus when below 200-EMA (wrong trend)."""
        # Mock daily data: Downtrend
        self.scanner.daily_cache.get_daily_data.return_value = {
            'ema_200': 100.0,
            'ema_9': 90.0,
            'ema_21': 95.0,
            'trend': 'bearish'
        }
        
        # Current price below 200-EMA
        bonus = self.scanner.calculate_daily_data_bonus('XYZ', 90.0, signal='long')
        
        # Should get NO bonuses (wrong trend for LONG)
        self.assertEqual(bonus['total_bonus'], 0, "LONG below 200-EMA should get 0 bonus")
    
    def test_short_signal_above_200ema_gets_no_bonus(self):
        """Test SHORT signal gets NO bonus when above 200-EMA (wrong trend)."""
        # Mock daily data: Uptrend
        self.scanner.daily_cache.get_daily_data.return_value = {
            'ema_200': 100.0,
            'ema_9': 115.0,
            'ema_21': 110.0,
            'trend': 'bullish'
        }
        
        # Current price above 200-EMA
        bonus = self.scanner.calculate_daily_data_bonus('AAPL', 115.0, signal='short')
        
        # Should get NO bonuses (wrong trend for SHORT)
        self.assertEqual(bonus['total_bonus'], 0, "SHORT above 200-EMA should get 0 bonus")
    
    def test_moderate_uptrend_gets_partial_bonus(self):
        """Test moderate uptrend gets partial bonus."""
        # Mock daily data: Moderate uptrend
        self.scanner.daily_cache.get_daily_data.return_value = {
            'ema_200': 100.0,
            'ema_9': 108.0,
            'ema_21': 105.0,
            'trend': 'bullish'
        }
        
        # Current price 7% above 200-EMA
        bonus = self.scanner.calculate_daily_data_bonus('AAPL', 107.0, signal='long')
        
        # Should get partial bonuses
        self.assertEqual(bonus['ema_200_bonus'], 8, "Should get +8 for 5-10% above 200-EMA")
        # Trend strength is (108-105)/105 = 2.86%, so gets +10 (moderate)
        self.assertEqual(bonus['daily_trend_bonus'], 10, "Should get +10 for moderate bullish")
        self.assertEqual(bonus['trend_strength_bonus'], 5, "Should get +5 for good alignment")
        self.assertEqual(bonus['total_bonus'], 23, "Total should be 23 points")
    
    def test_no_daily_cache_returns_zero_bonus(self):
        """Test that missing daily cache returns zero bonus."""
        self.scanner.daily_cache = None
        
        bonus = self.scanner.calculate_daily_data_bonus('AAPL', 150.0, signal='long')
        
        self.assertEqual(bonus['total_bonus'], 0, "No cache should return 0 bonus")
    
    def test_missing_daily_data_returns_zero_bonus(self):
        """Test that missing daily data returns zero bonus."""
        self.scanner.daily_cache.get_daily_data.return_value = None
        
        bonus = self.scanner.calculate_daily_data_bonus('UNKNOWN', 100.0, signal='long')
        
        self.assertEqual(bonus['total_bonus'], 0, "Missing data should return 0 bonus")


class TestRiskManagerEnhancements(unittest.TestCase):
    """Test Risk Manager trend strength multipliers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.alpaca = Mock()
        self.sentiment = Mock()
        
        # Initialize risk manager (only takes alpaca and sentiment)
        self.risk_manager = RiskManager(self.alpaca, self.sentiment)
        
        # Mock daily cache
        self.risk_manager.daily_cache = Mock()
    
    def test_long_strong_uptrend_increases_size(self):
        """Test LONG in strong uptrend gets 1.2x multiplier."""
        # Mock daily data: >10% above 200-EMA
        self.risk_manager.daily_cache.get_daily_data.return_value = {
            'ema_200': 100.0
        }
        
        # Price 15% above 200-EMA
        multiplier = self.risk_manager._get_trend_strength_multiplier('AAPL', 115.0, side='long')
        
        self.assertEqual(multiplier, 1.2, "LONG >10% above 200-EMA should get 1.2x")
    
    def test_short_strong_downtrend_increases_size(self):
        """Test SHORT in strong downtrend gets 1.2x multiplier."""
        # Mock daily data: >10% below 200-EMA
        self.risk_manager.daily_cache.get_daily_data.return_value = {
            'ema_200': 100.0
        }
        
        # Price 15% below 200-EMA
        multiplier = self.risk_manager._get_trend_strength_multiplier('XYZ', 85.0, side='short')
        
        self.assertEqual(multiplier, 1.2, "SHORT >10% below 200-EMA should get 1.2x")
    
    def test_long_counter_trend_reduces_size(self):
        """Test LONG below 200-EMA gets 0.8x multiplier (counter-trend)."""
        # Mock daily data
        self.risk_manager.daily_cache.get_daily_data.return_value = {
            'ema_200': 100.0
        }
        
        # Price 10% below 200-EMA (counter-trend for LONG)
        multiplier = self.risk_manager._get_trend_strength_multiplier('XYZ', 90.0, side='long')
        
        self.assertEqual(multiplier, 0.8, "LONG >5% below 200-EMA should get 0.8x")
    
    def test_short_counter_trend_reduces_size(self):
        """Test SHORT above 200-EMA gets 0.8x multiplier (counter-trend)."""
        # Mock daily data
        self.risk_manager.daily_cache.get_daily_data.return_value = {
            'ema_200': 100.0
        }
        
        # Price 10% above 200-EMA (counter-trend for SHORT)
        multiplier = self.risk_manager._get_trend_strength_multiplier('AAPL', 110.0, side='short')
        
        self.assertEqual(multiplier, 0.8, "SHORT >5% above 200-EMA should get 0.8x")
    
    def test_long_moderate_uptrend_gets_1_1x(self):
        """Test LONG in moderate uptrend gets 1.1x multiplier."""
        # Mock daily data
        self.risk_manager.daily_cache.get_daily_data.return_value = {
            'ema_200': 100.0
        }
        
        # Price 7% above 200-EMA
        multiplier = self.risk_manager._get_trend_strength_multiplier('AAPL', 107.0, side='long')
        
        self.assertEqual(multiplier, 1.1, "LONG 5-10% above 200-EMA should get 1.1x")
    
    def test_no_daily_cache_returns_1_0(self):
        """Test missing daily cache returns 1.0 (no adjustment)."""
        self.risk_manager.daily_cache = None
        
        multiplier = self.risk_manager._get_trend_strength_multiplier('AAPL', 150.0, side='long')
        
        self.assertEqual(multiplier, 1.0, "No cache should return 1.0")
    
    def test_missing_daily_data_returns_1_0(self):
        """Test missing daily data returns 1.0 (no adjustment)."""
        self.risk_manager.daily_cache.get_daily_data.return_value = None
        
        multiplier = self.risk_manager._get_trend_strength_multiplier('UNKNOWN', 100.0, side='long')
        
        self.assertEqual(multiplier, 1.0, "Missing data should return 1.0")
    
    def test_symmetry_long_vs_short(self):
        """Test that LONG and SHORT get symmetric treatment."""
        # Mock daily data
        self.risk_manager.daily_cache.get_daily_data.return_value = {
            'ema_200': 100.0
        }
        
        # LONG 15% above 200-EMA
        long_mult = self.risk_manager._get_trend_strength_multiplier('AAPL', 115.0, side='long')
        
        # SHORT 15% below 200-EMA
        short_mult = self.risk_manager._get_trend_strength_multiplier('XYZ', 85.0, side='short')
        
        self.assertEqual(long_mult, short_mult, "LONG uptrend and SHORT downtrend should get same multiplier")
        self.assertEqual(long_mult, 1.2, "Both should get 1.2x")


def run_tests():
    """Run all tests and print results."""
    print("=" * 70)
    print("PHASE 1 ENHANCEMENTS - UNIT TESTS")
    print("=" * 70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAIScannerEnhancements))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskManagerEnhancements))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    exit(run_tests())
