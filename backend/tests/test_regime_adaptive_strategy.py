import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.regime_manager import RegimeManager, MarketRegime
from trading.trailing_stops import TrailingStopManager
from trading.profit_taker import ProfitTaker
from utils.dynamic_position_sizer import DynamicPositionSizer

class TestRegimeAdaptiveStrategy(unittest.TestCase):
    def setUp(self):
        self.mock_supabase = MagicMock()
        self.mock_alpaca = MagicMock()
        
    def test_regime_manager_classification(self):
        """Test that RegimeManager correctly classifies market regimes based on F&G index"""
        manager = RegimeManager()
        
        # Test Extreme Fear (< 20)
        manager.scraper.get_fear_greed_index = MagicMock(return_value={'value': 15, 'timestamp': 'now'})
        regime = asyncio_run(manager.update_regime())
        self.assertEqual(regime, MarketRegime.EXTREME_FEAR)
        params = manager.get_params()
        self.assertEqual(params['profit_target_r'], 4.0)
        self.assertEqual(params['trailing_stop_r'], 1.5)
        
        # Reset cache
        manager._last_update = datetime.min
        
        # Test Fear (20-40)
        manager.scraper.get_fear_greed_index = MagicMock(return_value={'value': 30, 'timestamp': 'now'})
        regime = asyncio_run(manager.update_regime())
        self.assertEqual(regime, MarketRegime.FEAR)
        params = manager.get_params()
        self.assertEqual(params['profit_target_r'], 3.0)
        
        # Reset cache
        manager._last_update = datetime.min
        
        # Test Neutral (40-60)
        manager.scraper.get_fear_greed_index = MagicMock(return_value={'value': 50, 'timestamp': 'now'})
        regime = asyncio_run(manager.update_regime())
        self.assertEqual(regime, MarketRegime.NEUTRAL)
        params = manager.get_params()
        self.assertEqual(params['profit_target_r'], 2.0)
        
        # Reset cache
        manager._last_update = datetime.min
        
        # Test Greed (60-80)
        manager.scraper.get_fear_greed_index = MagicMock(return_value={'value': 70, 'timestamp': 'now'})
        regime = asyncio_run(manager.update_regime())
        self.assertEqual(regime, MarketRegime.GREED)
        params = manager.get_params()
        self.assertEqual(params['profit_target_r'], 2.5)
        
        # Reset cache
        manager._last_update = datetime.min
        
        # Test Extreme Greed (> 80)
        manager.scraper.get_fear_greed_index = MagicMock(return_value={'value': 90, 'timestamp': 'now'})
        regime = asyncio_run(manager.update_regime())
        self.assertEqual(regime, MarketRegime.EXTREME_GREED)
        params = manager.get_params()
        self.assertEqual(params['profit_target_r'], 3.0)
        self.assertEqual(params['trailing_stop_r'], 1.5)

    def test_trailing_stop_adaptation(self):
        """Test that TrailingStopManager adapts to regime parameters"""
        ts_manager = TrailingStopManager(self.mock_supabase)
        
        # Setup: Entry $100, Stop $98 (Risk = $2)
        entry = 100.0
        stop = 98.0
        current = 105.0
        side = 'long'
        r = entry - stop # $2
        
        # Case 1: Default (no regime params) -> uses config (0.5R default)
        # 0.5 * 2 = 1.0 distance
        new_stop = ts_manager.calculate_trailing_stop(
            'AAPL', entry, current, stop, side, atr=None, regime_params=None
        )
        expected_stop = current - (r * ts_manager.trailing_distance_r)
        self.assertAlmostEqual(new_stop, expected_stop)
        
        # Case 2: Extreme Fear (1.5R)
        regime_params = {'trailing_stop_r': 1.5}
        new_stop = ts_manager.calculate_trailing_stop(
            'AAPL', entry, current, stop, side, atr=None, regime_params=regime_params
        )
        # Distance = 2 * 1.5 = 3.0
        # Stop = 105 - 3.0 = 102.0
        self.assertEqual(new_stop, 102.0)
        
        # Case 3: Extreme Greed (1.5R)
        regime_params = {'trailing_stop_r': 1.5}
        new_stop = ts_manager.calculate_trailing_stop(
            'AAPL', entry, current, stop, side, atr=None, regime_params=regime_params
        )
        # Distance = 2 * 1.5 = 3.0
        # Stop = 105 - 3.0 = 102.0
        self.assertEqual(new_stop, 102.0)

    def test_profit_taker_adaptation(self):
        """Test that ProfitTaker adapts targets based on regime"""
        pt_manager = ProfitTaker(self.mock_supabase)
        
        # Setup: Entry $100, Stop $90 (Risk = $10)
        entry = 100.0
        stop = 90.0
        side = 'long'
        
        # Case 1: Neutral Regime (Target 2R)
        # Current price $115 (+1.5R) -> Should NOT take profit if target is 2R
        # Wait, ProfitTaker usually takes PARTIAL profit at 1R.
        # Let's check requirements.
        # Extreme Fear: Partial Profit at 1.5R
        # Neutral: Partial Profit at 1.0R
        
        current = 115.0 # +1.5R
        
        # Neutral Params (1.0R target)
        regime_params = {'partial_profit_1_r': 1.0}
        result = pt_manager.should_take_partial_profits(
            'AAPL', entry, current, stop, side, regime_params=regime_params
        )
        self.assertTrue(result['should_take'])
        self.assertEqual(result['target_r'], 1.0)
        
        # Extreme Fear Params (1.5R target)
        # At 1.5R exactly, it should trigger
        regime_params = {'partial_profit_1_r': 1.5}
        result = pt_manager.should_take_partial_profits(
            'AAPL', entry, current, stop, side, regime_params=regime_params
        )
        self.assertTrue(result['should_take'])
        self.assertEqual(result['target_r'], 1.5)
        
        # If price was only $110 (+1.0R)
        current_low = 110.0
        result = pt_manager.should_take_partial_profits(
            'AAPL', entry, current_low, stop, side, regime_params=regime_params
        )
        self.assertFalse(result['should_take']) # 1.0R < 1.5R target

    def test_position_sizing_reasoning(self):
        """Test that DynamicPositionSizer includes regime info in reasoning"""
        sizer = DynamicPositionSizer(self.mock_alpaca)
        
        # Mock account
        self.mock_alpaca.get_account.return_value = MagicMock(
            equity=100000, cash=100000, buying_power=200000, 
            daytrading_buying_power=400000, pattern_day_trader=True
        )
        
        regime_data = {'regime': 'EXTREME_FEAR', 'position_size_mult': 1.0}
        
        qty, reasoning = sizer.calculate_optimal_size(
            'AAPL', 150.0, 2.0, 80.0, 0.01, 0.10, regime_data=regime_data
        )
        
        self.assertIn("Regime: EXTREME_FEAR", reasoning)

# Helper for async tests
import asyncio
def asyncio_run(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

if __name__ == '__main__':
    unittest.main()
