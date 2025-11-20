#!/usr/bin/env python3
"""
Sprint 7 Implementation Validation

Validates that all Sprint 7 filters are properly implemented and configured.
"""

import sys
from datetime import datetime
import pytz

def validate_imports():
    """Validate all required imports work"""
    print("=" * 80)
    print("SPRINT 7 IMPLEMENTATION VALIDATION")
    print("=" * 80)
    print()
    
    print("1. Validating imports...")
    try:
        from trading.strategy import EMAStrategy
        from data.daily_cache import DailyCache, get_daily_cache
        from config import settings
        print("   ✓ All imports successful")
        return True
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False


def validate_strategy_methods():
    """Validate strategy has all three filter methods"""
    print("\n2. Validating strategy filter methods...")
    try:
        from trading.strategy import EMAStrategy
        from unittest.mock import Mock
        
        order_manager = Mock()
        strategy = EMAStrategy(order_manager)
        
        # Check for filter methods
        methods = [
            '_is_optimal_trading_time',
            '_check_daily_trend',
            '_check_timeframe_alignment'
        ]
        
        for method in methods:
            if not hasattr(strategy, method):
                print(f"   ✗ Missing method: {method}")
                return False
            print(f"   ✓ Method exists: {method}")
        
        return True
    except Exception as e:
        print(f"   ✗ Validation failed: {e}")
        return False


def validate_config_settings():
    """Validate config has all Sprint 7 settings"""
    print("\n3. Validating configuration settings...")
    try:
        from config import settings
        
        required_settings = [
            'enable_time_of_day_filter',
            'enable_200_ema_filter',
            'enable_multitime_frame_filter',
            'optimal_hours_start_1',
            'optimal_hours_end_1',
            'optimal_hours_start_2',
            'optimal_hours_end_2',
            'avoid_lunch_hour',
            'daily_trend_ema_period',
            'cache_refresh_time'
        ]
        
        for setting in required_settings:
            if not hasattr(settings, setting):
                print(f"   ✗ Missing setting: {setting}")
                return False
            value = getattr(settings, setting)
            print(f"   ✓ {setting}: {value}")
        
        return True
    except Exception as e:
        print(f"   ✗ Validation failed: {e}")
        return False


def validate_daily_cache():
    """Validate daily cache functionality"""
    print("\n4. Validating daily cache...")
    try:
        from data.daily_cache import DailyCache, get_daily_cache
        
        # Test singleton
        cache1 = get_daily_cache()
        cache2 = get_daily_cache()
        
        if cache1 is not cache2:
            print("   ✗ Daily cache singleton not working")
            return False
        print("   ✓ Singleton pattern working")
        
        # Test cache operations
        test_data = {
            'price': 100.0,
            'ema_200': 95.0,
            'trend': 'bullish'
        }
        
        cache1.set_daily_data('TEST', test_data)
        retrieved = cache1.get_daily_data('TEST')
        
        if retrieved != test_data:
            print("   ✗ Cache set/get not working")
            return False
        print("   ✓ Cache set/get working")
        
        # Test cache stats
        stats = cache1.get_cache_stats()
        if stats['symbols_cached'] != 1:
            print("   ✗ Cache stats not working")
            return False
        print("   ✓ Cache stats working")
        
        # Clear cache
        cache1.clear_cache()
        
        return True
    except Exception as e:
        print(f"   ✗ Validation failed: {e}")
        return False


def validate_filter_logic():
    """Validate filter logic with test cases"""
    print("\n5. Validating filter logic...")
    try:
        from trading.strategy import EMAStrategy
        from unittest.mock import Mock, patch
        
        order_manager = Mock()
        strategy = EMAStrategy(order_manager)
        
        # Test time-of-day filter
        print("   Testing time-of-day filter...")
        with patch('trading.strategy.settings') as mock_settings:
            with patch('trading.strategy.datetime') as mock_dt:
                mock_settings.optimal_hours_start_1 = (9, 30)
                mock_settings.optimal_hours_end_1 = (10, 30)
                mock_settings.optimal_hours_start_2 = (15, 0)
                mock_settings.optimal_hours_end_2 = (16, 0)
                mock_settings.avoid_lunch_hour = True
                
                # Test optimal time
                test_time = datetime(2025, 11, 11, 10, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
                mock_dt.now.return_value = test_time
                
                allowed, reason = strategy._is_optimal_trading_time()
                if not allowed:
                    print(f"   ✗ Time filter failed: {reason}")
                    return False
                print("   ✓ Time-of-day filter working")
        
        # Test 200-EMA filter
        print("   Testing 200-EMA filter...")
        with patch('trading.strategy.get_daily_cache') as mock_cache:
            mock_cache_instance = Mock()
            mock_cache.return_value = mock_cache_instance
            mock_cache_instance.get_daily_data.return_value = {
                'price': 105.0,
                'ema_200': 100.0
            }
            
            allowed, reason = strategy._check_daily_trend('TEST', 'buy')
            if not allowed:
                print(f"   ✗ 200-EMA filter failed: {reason}")
                return False
            print("   ✓ 200-EMA filter working")
        
        # Test multi-timeframe filter
        print("   Testing multi-timeframe filter...")
        with patch('trading.strategy.get_daily_cache') as mock_cache:
            mock_cache_instance = Mock()
            mock_cache.return_value = mock_cache_instance
            mock_cache_instance.get_daily_data.return_value = {
                'trend': 'bullish'
            }
            
            allowed, reason = strategy._check_timeframe_alignment('TEST', 'buy')
            if not allowed:
                print(f"   ✗ Multi-timeframe filter failed: {reason}")
                return False
            print("   ✓ Multi-timeframe filter working")
        
        return True
    except Exception as e:
        print(f"   ✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_integration():
    """Validate filters are integrated into strategy.evaluate()"""
    print("\n6. Validating integration into strategy.evaluate()...")
    try:
        from trading.strategy import EMAStrategy
        from unittest.mock import Mock
        import inspect
        
        order_manager = Mock()
        strategy = EMAStrategy(order_manager)
        
        # Get source code of evaluate method
        source = inspect.getsource(strategy.evaluate)
        
        # Check for filter calls
        required_calls = [
            '_is_optimal_trading_time',
            '_check_daily_trend',
            '_check_timeframe_alignment'
        ]
        
        for call in required_calls:
            if call not in source:
                print(f"   ✗ Filter not integrated: {call}")
                return False
            print(f"   ✓ Filter integrated: {call}")
        
        # Check for feature flags
        required_flags = [
            'enable_time_of_day_filter',
            'enable_200_ema_filter',
            'enable_multitime_frame_filter'
        ]
        
        for flag in required_flags:
            if flag not in source:
                print(f"   ✗ Feature flag not used: {flag}")
                return False
            print(f"   ✓ Feature flag used: {flag}")
        
        return True
    except Exception as e:
        print(f"   ✗ Validation failed: {e}")
        return False


def main():
    """Run all validations"""
    results = []
    
    results.append(("Imports", validate_imports()))
    results.append(("Strategy Methods", validate_strategy_methods()))
    results.append(("Config Settings", validate_config_settings()))
    results.append(("Daily Cache", validate_daily_cache()))
    results.append(("Filter Logic", validate_filter_logic()))
    results.append(("Integration", validate_integration()))
    
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:.<50} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 80)
    
    if all_passed:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("\nSprint 7 filters are properly implemented and ready to use.")
        print("\nNext steps:")
        print("1. Restart backend: pm2 restart backend")
        print("2. Monitor logs for filter activity")
        print("3. Check that filters are working in production")
        return 0
    else:
        print("\n❌ SOME VALIDATIONS FAILED")
        print("\nPlease fix the issues above before deploying.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
