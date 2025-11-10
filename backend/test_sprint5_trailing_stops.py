"""
Sprint 5: Trailing Stops - Comprehensive Test Suite
Tests shadow mode, configuration, and integration
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Set working directory to backend
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import SupabaseClient
from trading.trailing_stops import TrailingStopManager
from config import settings


class MockConfig:
    """Mock config for testing"""
    trailing_stops_enabled = False  # Shadow mode
    trailing_stops_activation_threshold = 2.0
    trailing_stops_distance_r = 0.5
    trailing_stops_min_distance_pct = 0.005
    trailing_stops_use_atr = True
    trailing_stops_atr_multiplier = 1.5
    max_trailing_stop_positions = 999


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status} | {test_name}")
    if details:
        print(f"       {details}")


async def test_configuration():
    """Test 1: Configuration Loading"""
    print_section("TEST 1: Configuration Loading")
    
    try:
        # Test with real settings
        supabase = SupabaseClient()
        manager = TrailingStopManager(supabase)
        
        # Check configuration loaded
        assert manager.enabled == settings.trailing_stops_enabled
        assert manager.activation_threshold == settings.trailing_stops_activation_threshold
        assert manager.trailing_distance_r == settings.trailing_stops_distance_r
        
        print_result(
            "Configuration Loading",
            True,
            f"Enabled: {manager.enabled}, Threshold: {manager.activation_threshold}R"
        )
        
        # Test shadow mode detection
        assert manager.shadow_mode_active == (not manager.enabled)
        print_result(
            "Shadow Mode Detection",
            True,
            f"Shadow mode: {manager.shadow_mode_active}"
        )
        
        return True, manager
        
    except Exception as e:
        print_result("Configuration Loading", False, str(e))
        return False, None


async def test_activation_logic(manager: TrailingStopManager):
    """Test 2: Activation Logic"""
    print_section("TEST 2: Activation Logic")
    
    test_cases = [
        # (entry, current, stop, side, should_activate, description)
        (100.0, 104.0, 98.0, 'long', True, "+2R profit (long)"),
        (100.0, 102.0, 98.0, 'long', False, "+1R profit (long) - not enough"),
        (100.0, 96.0, 102.0, 'short', True, "+2R profit (short)"),
        (100.0, 98.0, 102.0, 'short', False, "+1R profit (short) - not enough"),
        (100.0, 100.0, 98.0, 'long', False, "No profit (long)"),
    ]
    
    all_passed = True
    for entry, current, stop, side, expected, desc in test_cases:
        result = manager.should_activate_trailing_stop(
            "TEST", entry, current, stop, side
        )
        passed = result == expected
        all_passed = all_passed and passed
        print_result(desc, passed, f"Expected: {expected}, Got: {result}")
    
    return all_passed


async def test_trailing_calculation(manager: TrailingStopManager):
    """Test 3: Trailing Stop Calculation"""
    print_section("TEST 3: Trailing Stop Calculation")
    
    # Test long position
    entry = 100.0
    current = 104.0  # +4% profit
    stop = 98.0  # -2% stop (R = 2.0)
    side = 'long'
    
    # Without ATR (R-based)
    new_stop = manager.calculate_trailing_stop(
        "TEST", entry, current, stop, side, atr=None
    )
    
    # Should trail by 0.5R = 0.5 * 2.0 = 1.0
    # New stop = 104.0 - 1.0 = 103.0
    expected_stop = 103.0
    passed = abs(new_stop - expected_stop) < 0.01
    print_result(
        "R-based Trailing (Long)",
        passed,
        f"Expected: ${expected_stop:.2f}, Got: ${new_stop:.2f}"
    )
    
    # With ATR
    atr = 1.5
    new_stop_atr = manager.calculate_trailing_stop(
        "TEST", entry, current, stop, side, atr=atr
    )
    
    # Should trail by 1.5 * ATR = 1.5 * 1.5 = 2.25
    # New stop = 104.0 - 2.25 = 101.75
    expected_stop_atr = 101.75
    passed_atr = abs(new_stop_atr - expected_stop_atr) < 0.01
    print_result(
        "ATR-based Trailing (Long)",
        passed_atr,
        f"Expected: ${expected_stop_atr:.2f}, Got: ${new_stop_atr:.2f}"
    )
    
    # Test short position
    entry_short = 100.0
    current_short = 96.0  # +4% profit (short)
    stop_short = 102.0  # +2% stop (R = 2.0)
    side_short = 'short'
    
    new_stop_short = manager.calculate_trailing_stop(
        "TEST", entry_short, current_short, stop_short, side_short, atr=None
    )
    
    # Should trail by 0.5R = 1.0
    # New stop = 96.0 + 1.0 = 97.0
    expected_stop_short = 97.0
    passed_short = abs(new_stop_short - expected_stop_short) < 0.01
    print_result(
        "R-based Trailing (Short)",
        passed_short,
        f"Expected: ${expected_stop_short:.2f}, Got: ${new_stop_short:.2f}"
    )
    
    return passed and passed_atr and passed_short


async def test_shadow_mode(manager: TrailingStopManager):
    """Test 4: Shadow Mode Logging"""
    print_section("TEST 4: Shadow Mode Logging")
    
    if not manager.shadow_mode_active:
        print_result("Shadow Mode", False, "Shadow mode not active - check .env")
        return False
    
    # Simulate position update in shadow mode
    # Need +2R profit to activate
    # Entry: 150, Stop: 147, R = 3.0
    # Need current >= 150 + (2 * 3.0) = 156.0
    result = manager.update_trailing_stop(
        symbol="AAPL",
        entry_price=150.0,
        current_price=156.0,  # +4% profit = +2R
        current_stop=147.0,  # R = 3.0
        side='long',
        atr=2.0
    )
    
    # Check shadow mode flags
    is_shadow = result.get('shadow_mode') == True
    has_prediction = result.get('would_update') == True or result.get('activated') == True
    not_updated = result.get('updated') == False  # Not actually updated
    
    passed = is_shadow and not_updated
    
    print_result(
        "Shadow Mode Logging",
        passed,
        f"Logged prediction: {result.get('new_stop'):.2f} (shadow: {is_shadow}, updated: {result.get('updated')})"
    )
    
    if not passed:
        print(f"       Full result: {result}")
        return False
    
    # Check shadow predictions were recorded
    report = manager.get_shadow_mode_report()
    assert report['total_predictions'] > 0
    
    print_result(
        "Shadow Predictions Tracking",
        True,
        f"Total predictions: {report['total_predictions']}"
    )
    
    return True


async def test_health_check(manager: TrailingStopManager):
    """Test 5: Health Check"""
    print_section("TEST 5: Health Check")
    
    health = manager.check_health()
    
    print(f"Status: {health['status']}")
    print(f"Enabled: {health['enabled']}")
    print(f"Shadow Mode: {health['shadow_mode']}")
    print(f"Active Trailing Stops: {health['active_trailing_stops']}")
    print(f"Shadow Predictions: {health['shadow_predictions']}")
    
    if health.get('issues'):
        print(f"\n⚠️  Issues: {health['issues']}")
    
    if health.get('warnings'):
        print(f"\n⚠️  Warnings: {health['warnings']}")
    
    passed = health['status'] in ['healthy', 'healthy_with_warnings']
    print_result("Health Check", passed)
    
    return passed


async def test_integration():
    """Test 6: Integration with Position Manager"""
    print_section("TEST 6: Integration Test")
    
    try:
        from core.alpaca_client import AlpacaClient
        from trading.position_manager import PositionManager
        
        alpaca = AlpacaClient()
        supabase = SupabaseClient()
        
        # Create position manager (should auto-initialize trailing stops)
        pos_manager = PositionManager(alpaca, supabase)
        
        assert pos_manager.trailing_stop_manager is not None
        print_result(
            "Position Manager Integration",
            True,
            "Trailing Stop Manager auto-initialized"
        )
        
        # Check health
        health = pos_manager.trailing_stop_manager.check_health()
        print_result(
            "Integrated Health Check",
            health['status'] in ['healthy', 'healthy_with_warnings'],
            f"Status: {health['status']}"
        )
        
        return True
        
    except Exception as e:
        print_result("Integration Test", False, str(e))
        return False


async def run_all_tests():
    """Run all Sprint 5 tests"""
    print("\n" + "="*80)
    print("  SPRINT 5: TRAILING STOPS - COMPREHENSIVE TEST SUITE")
    print("  Shadow Mode Testing (Day 1)")
    print("="*80)
    
    results = []
    
    # Test 1: Configuration
    passed, manager = await test_configuration()
    results.append(("Configuration", passed))
    
    if not manager:
        print("\n❌ Cannot continue - configuration failed")
        return
    
    # Test 2: Activation Logic
    passed = await test_activation_logic(manager)
    results.append(("Activation Logic", passed))
    
    # Test 3: Trailing Calculation
    passed = await test_trailing_calculation(manager)
    results.append(("Trailing Calculation", passed))
    
    # Test 4: Shadow Mode
    passed = await test_shadow_mode(manager)
    results.append(("Shadow Mode", passed))
    
    # Test 5: Health Check
    passed = await test_health_check(manager)
    results.append(("Health Check", passed))
    
    # Test 6: Integration
    passed = await test_integration()
    results.append(("Integration", passed))
    
    # Summary
    print_section("TEST SUMMARY")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    for test_name, passed in results:
        status = "✓" if passed else "✗"
        print(f"{status} {test_name}")
    
    print(f"\n{'='*80}")
    print(f"  RESULTS: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print(f"  🎉 ALL TESTS PASSED - Ready for Day 2 (Limited Test)")
    else:
        print(f"  ⚠️  {total - passed_count} test(s) failed - Review before proceeding")
    
    print(f"{'='*80}\n")
    
    # Next steps
    print("\n📋 NEXT STEPS:")
    print("1. Review shadow mode logs during trading day")
    print("2. Verify trailing stop calculations are correct")
    print("3. If all looks good, proceed to Day 2 (Limited Test)")
    print("4. Set TRAILING_STOPS_ENABLED=true and MAX_TRAILING_STOP_POSITIONS=2")
    print()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
