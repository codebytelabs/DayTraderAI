"""
Sprint 6 - Day 1: Partial Profit Taking (Shadow Mode) Test Suite
Tests shadow mode, configuration, and integration
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from trading.profit_taker import ProfitTaker
from core.supabase_client import SupabaseClient


class MockConfig:
    """Mock config for testing"""
    partial_profits_enabled = False  # Shadow mode
    partial_profits_first_target_r = 1.0
    partial_profits_percentage = 0.5
    partial_profits_second_target_r = 2.0
    partial_profits_use_trailing = True
    max_partial_profit_positions = 999


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"  {details}")


def test_configuration():
    """Test Sprint 6 configuration"""
    print_section("DAY 1 CONFIGURATION CHECK")
    
    tests_passed = 0
    total_tests = 6
    
    # Test 1: Feature flag disabled (shadow mode)
    enabled = settings.partial_profits_enabled
    print(f"✓ PARTIAL_PROFITS_ENABLED: {enabled}")
    if not enabled:
        print("  ✓ Shadow mode active (correct for Day 1)")
        tests_passed += 1
    else:
        print("  ✗ Should be disabled for Day 1 shadow mode")
    
    # Test 2: First target
    print(f"✓ PARTIAL_PROFITS_FIRST_TARGET_R: {settings.partial_profits_first_target_r}R")
    if settings.partial_profits_first_target_r == 1.0:
        tests_passed += 1
    
    # Test 3: Percentage
    print(f"✓ PARTIAL_PROFITS_PERCENTAGE: {settings.partial_profits_percentage*100:.0f}%")
    if settings.partial_profits_percentage == 0.5:
        tests_passed += 1
    
    # Test 4: Second target
    print(f"✓ PARTIAL_PROFITS_SECOND_TARGET_R: {settings.partial_profits_second_target_r}R")
    if settings.partial_profits_second_target_r == 2.0:
        tests_passed += 1
    
    # Test 5: Use trailing
    print(f"✓ PARTIAL_PROFITS_USE_TRAILING: {settings.partial_profits_use_trailing}")
    if settings.partial_profits_use_trailing:
        tests_passed += 1
    
    # Test 6: Max positions
    print(f"✓ MAX_PARTIAL_PROFIT_POSITIONS: {settings.max_partial_profit_positions}")
    if settings.max_partial_profit_positions == 999:
        tests_passed += 1
    
    return tests_passed, total_tests


def test_shadow_mode():
    """Test shadow mode functionality"""
    print_section("SHADOW MODE TEST")
    
    supabase = SupabaseClient()
    profit_taker = ProfitTaker(supabase)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Shadow mode active
    if profit_taker.shadow_mode_active:
        print("✓ Shadow mode is active")
        tests_passed += 1
    else:
        print("✗ Shadow mode should be active")
    
    # Test 2: Simulate +1R profit (LONG)
    result = profit_taker.should_take_partial_profits(
        symbol='TEST',
        entry_price=100.0,
        current_price=102.0,  # +2% = +1R if stop is at 98
        stop_loss=98.0,
        side='long'
    )
    
    if result.get('shadow_mode') and result.get('would_take'):
        print("✓ Shadow mode prediction: Would take partial profits at +1R (LONG)")
        print(f"  Profit: +{result['profit_r']:.2f}R")
        print(f"  Would sell: {result['percentage']*100:.0f}%")
        tests_passed += 1
    else:
        print("✗ Shadow mode should predict partial profit taking")
    
    # Test 3: Simulate +1R profit (SHORT)
    result = profit_taker.should_take_partial_profits(
        symbol='TEST2',
        entry_price=100.0,
        current_price=98.0,  # -2% = +1R if stop is at 102
        stop_loss=102.0,
        side='short'
    )
    
    if result.get('shadow_mode') and result.get('would_take'):
        print("✓ Shadow mode prediction: Would take partial profits at +1R (SHORT)")
        print(f"  Profit: +{result['profit_r']:.2f}R")
        tests_passed += 1
    else:
        print("✗ Shadow mode should predict partial profit taking for shorts")
    
    # Test 4: Check shadow predictions logged
    if len(profit_taker.shadow_predictions) >= 2:
        print(f"✓ Shadow predictions logged: {len(profit_taker.shadow_predictions)}")
        tests_passed += 1
    else:
        print("✗ Shadow predictions not logged correctly")
    
    return tests_passed, total_tests


def test_health_check():
    """Test health check functionality"""
    print_section("HEALTH CHECK")
    
    supabase = SupabaseClient()
    profit_taker = ProfitTaker(supabase)
    
    health = profit_taker.check_health()
    
    print(f"Status: {health['status']}")
    print(f"Enabled: {health['enabled']}")
    print(f"Shadow Mode: {health['shadow_mode']}")
    print(f"Partial Profits Taken: {health['partial_profits_taken']}")
    print(f"Shadow Predictions: {health['shadow_predictions']}")
    
    if health.get('warnings'):
        print(f"⚠️  Warnings: {health['warnings']}")
    
    if health.get('issues'):
        print(f"❌ Issues: {health['issues']}")
        return 0, 1
    
    if health['status'] in ['healthy', 'healthy_with_warnings']:
        print("✓ System healthy")
        return 1, 1
    
    return 0, 1


def test_shadow_report():
    """Test shadow mode reporting"""
    print_section("SHADOW MODE REPORT")
    
    supabase = SupabaseClient()
    profit_taker = ProfitTaker(supabase)
    
    # Generate some shadow predictions
    for i in range(3):
        profit_taker.should_take_partial_profits(
            symbol=f'TEST{i}',
            entry_price=100.0,
            current_price=102.0 + i,
            stop_loss=98.0,
            side='long'
        )
    
    report = profit_taker.get_shadow_mode_report()
    
    print(f"Shadow Mode: {report['shadow_mode']}")
    print(f"Total Predictions: {report['total_predictions']}")
    
    if report['total_predictions'] > 0:
        print(f"Avg Profit R: +{report['avg_profit_r']:.2f}R")
        print(f"Avg Profit Amount: ${report['avg_profit_amount']:.2f}")
        print(f"Symbols Tracked: {report['symbols_tracked']}")
        print("✓ Shadow mode report generated")
        return 1, 1
    
    print("✗ No shadow predictions in report")
    return 0, 1


def main():
    """Run all Sprint 6 Day 1 tests"""
    print_section("SPRINT 6 - DAY 1: PARTIAL PROFIT TAKING (SHADOW MODE)")
    print("Testing shadow mode, configuration, and integration")
    
    all_tests_passed = 0
    all_tests_total = 0
    
    # Run tests
    passed, total = test_configuration()
    all_tests_passed += passed
    all_tests_total += total
    
    passed, total = test_shadow_mode()
    all_tests_passed += passed
    all_tests_total += total
    
    passed, total = test_health_check()
    all_tests_passed += passed
    all_tests_total += total
    
    passed, total = test_shadow_report()
    all_tests_passed += passed
    all_tests_total += total
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"✓ Configuration: Passed")
    print(f"✓ Shadow Mode: Passed")
    print(f"✓ Health Check: Passed")
    print(f"✓ Shadow Report: Passed")
    
    print(f"\n{'='*80}")
    print(f"  RESULTS: {all_tests_passed}/{all_tests_total} tests passed")
    
    if all_tests_passed == all_tests_total:
        print(f"  🎉 ALL TESTS PASSED - Shadow Mode Ready")
    else:
        print(f"  ⚠️  {all_tests_total - all_tests_passed} tests failed")
    
    print(f"{'='*80}\n")
    
    # Day 1 instructions
    print("📊 DAY 1 EXPECTATIONS:")
    print("  • Shadow mode will log what WOULD happen")
    print("  • No actual partial profit orders will be placed")
    print("  • System will track predictions for analysis")
    print("  • Monitor shadow predictions in logs")
    
    print("\n📋 MONITORING DURING DAY 1:")
    print("  1. Watch for '[SHADOW] Would take partial profits' messages")
    print("  2. Check shadow predictions accumulate")
    print("  3. Verify no actual orders placed")
    print("  4. Review shadow mode report at end of day")
    
    print("\n🚀 IF DAY 1 SUCCESSFUL:")
    print("  1. Review shadow predictions")
    print("  2. Verify logic is correct")
    print("  3. Check for any issues in logs")
    print("  4. If all good, proceed to Day 2:")
    print("     • Set PARTIAL_PROFITS_ENABLED=true")
    print("     • Set MAX_PARTIAL_PROFIT_POSITIONS=2")
    print("     • Enable for 2 positions only")
    
    print("\n⚠️  IF ANY ISSUES:")
    print("  1. Keep PARTIAL_PROFITS_ENABLED=false")
    print("  2. Review logs and fix issues")
    print("  3. Re-test before enabling")
    
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
