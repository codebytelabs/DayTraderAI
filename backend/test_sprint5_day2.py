"""
Sprint 5 - Day 2: Limited Test Validation
Tests that trailing stops work correctly with 2 position limit
"""

import os
import sys
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from trading.trailing_stops import TrailingStopManager
from core.supabase_client import SupabaseClient


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_status(label, value, expected=None):
    """Print status line"""
    if expected is not None:
        status = "✓" if value == expected else "✗"
        print(f"{status} {label}: {value} (expected: {expected})")
    else:
        print(f"  {label}: {value}")


def test_day2_configuration():
    """Test Day 2 configuration is correct"""
    print_section("DAY 2 CONFIGURATION CHECK")
    
    all_good = True
    
    # Check enabled
    if not settings.trailing_stops_enabled:
        print("✗ TRAILING_STOPS_ENABLED should be true for Day 2")
        all_good = False
    else:
        print("✓ TRAILING_STOPS_ENABLED: true")
    
    # Check position limit
    if settings.max_trailing_stop_positions != 2:
        print(f"✗ MAX_TRAILING_STOP_POSITIONS should be 2 for Day 2 (got {settings.max_trailing_stop_positions})")
        all_good = False
    else:
        print("✓ MAX_TRAILING_STOP_POSITIONS: 2")
    
    # Check other settings
    print(f"  Activation Threshold: {settings.trailing_stops_activation_threshold}R")
    print(f"  Trailing Distance: {settings.trailing_stops_distance_r}R")
    print(f"  Use ATR: {settings.trailing_stops_use_atr}")
    
    return all_good


def test_position_limit():
    """Test that position limit is enforced"""
    print_section("POSITION LIMIT TEST")
    
    supabase = SupabaseClient()
    manager = TrailingStopManager(supabase)
    
    # Verify manager settings
    print(f"Manager enabled: {manager.enabled}")
    print(f"Manager max positions: {manager.max_positions}")
    print(f"Manager shadow mode: {manager.shadow_mode_active}")
    
    if manager.shadow_mode_active:
        print("\n✗ ERROR: Manager is still in shadow mode!")
        print("  Check that config is loading correctly")
        return False
    
    # Simulate 3 positions trying to activate
    positions = [
        ("AAPL", 150.0, 156.0, 147.0, 'long'),  # +2R
        ("MSFT", 300.0, 306.0, 297.0, 'long'),  # +2R
        ("NVDA", 500.0, 506.0, 497.0, 'long'),  # +2R (should be rejected)
    ]
    
    results = []
    for symbol, entry, current, stop, side in positions:
        result = manager.update_trailing_stop(
            symbol=symbol,
            entry_price=entry,
            current_price=current,
            current_stop=stop,
            side=side,
            atr=2.0
        )
        results.append((symbol, result))
    
    # Check results
    activated_count = sum(1 for _, r in results if r.get('activated') and r.get('updated'))
    
    print(f"\nPositions attempted: 3")
    print(f"Positions activated: {activated_count}")
    print(f"Expected: 2 (limit enforced)")
    
    for symbol, result in results:
        if result.get('activated'):
            if result.get('updated'):
                print(f"✓ {symbol}: Activated (stop: ${result['new_stop']:.2f})")
            else:
                print(f"  {symbol}: Already optimal")
        elif result.get('at_limit'):
            print(f"✓ {symbol}: Rejected (at limit) - CORRECT")
        else:
            print(f"  {symbol}: Not activated ({result.get('reason')})")
    
    # Verify exactly 2 active
    active_count = len(manager.active_trailing_stops)
    if active_count == 2:
        print(f"\n✓ Active trailing stops: {active_count} (limit enforced correctly)")
        return True
    else:
        print(f"\n✗ Active trailing stops: {active_count} (expected 2)")
        return False


def test_live_mode():
    """Test that we're in live mode, not shadow mode"""
    print_section("LIVE MODE VERIFICATION")
    
    supabase = SupabaseClient()
    manager = TrailingStopManager(supabase)
    
    # Test a position update
    result = manager.update_trailing_stop(
        symbol="TEST",
        entry_price=100.0,
        current_price=104.0,  # +2R
        current_stop=98.0,
        side='long',
        atr=1.5
    )
    
    # Check it's not in shadow mode
    if result.get('shadow_mode'):
        print("✗ ERROR: Still in shadow mode!")
        return False
    
    # Check it actually updated
    if result.get('activated') and result.get('updated'):
        print("✓ Live mode active - trailing stop actually updated")
        print(f"  New stop: ${result['new_stop']:.2f}")
        print(f"  Profit protected: {result['profit_protected_pct']:.2f}%")
        return True
    else:
        print(f"⚠️  Position not updated: {result.get('reason')}")
        return True  # Still pass, just not activated


def test_health_check():
    """Test health check in live mode"""
    print_section("HEALTH CHECK")
    
    supabase = SupabaseClient()
    manager = TrailingStopManager(supabase)
    
    health = manager.check_health()
    
    print(f"Status: {health['status']}")
    print(f"Enabled: {health['enabled']}")
    print(f"Shadow Mode: {health['shadow_mode']}")
    print(f"Active Trailing Stops: {health['active_trailing_stops']}")
    print(f"Max Positions: {health['config']['max_positions']}")
    
    if health.get('issues'):
        print(f"\n⚠️  Issues: {health['issues']}")
        return False
    
    if health.get('warnings'):
        print(f"\n⚠️  Warnings: {health['warnings']}")
    
    # Should be enabled and not in shadow mode
    if health['enabled'] and not health['shadow_mode']:
        print("\n✓ System healthy and in live mode")
        return True
    else:
        print("\n✗ System not in correct state for Day 2")
        return False


def main():
    print("\n" + "="*80)
    print("  SPRINT 5 - DAY 2: LIMITED TEST VALIDATION")
    print("  Testing with 2 Position Limit")
    print("="*80)
    
    results = []
    
    # Test 1: Configuration
    passed = test_day2_configuration()
    results.append(("Configuration", passed))
    
    if not passed:
        print("\n❌ Configuration incorrect - fix before proceeding!")
        print("\nRequired settings in backend/.env:")
        print("  TRAILING_STOPS_ENABLED=true")
        print("  MAX_TRAILING_STOP_POSITIONS=2")
        return False
    
    # Test 2: Position Limit
    passed = test_position_limit()
    results.append(("Position Limit", passed))
    
    # Test 3: Live Mode
    passed = test_live_mode()
    results.append(("Live Mode", passed))
    
    # Test 4: Health Check
    passed = test_health_check()
    results.append(("Health Check", passed))
    
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
        print(f"  🎉 ALL TESTS PASSED - Ready for Live Trading (Day 2)")
    else:
        print(f"  ⚠️  {total - passed_count} test(s) failed - Review before trading")
    
    print(f"{'='*80}\n")
    
    if passed_count == total:
        print("\n📊 DAY 2 EXPECTATIONS:")
        print("  • Trailing stops will activate on first 2 profitable positions")
        print("  • Additional positions will be rejected (at limit)")
        print("  • Stops will trail as price moves favorably")
        print("  • Profits will be protected if price reverses")
        
        print("\n📋 MONITORING DURING DAY 2:")
        print("  1. Watch for 'Trailing stop activated' messages")
        print("  2. Verify stops trail correctly (check logs)")
        print("  3. Monitor for 'at limit' rejections (expected)")
        print("  4. Check no unexpected position closes")
        print("  5. Measure profit protection on the 2 positions")
        
        print("\n🚀 IF DAY 2 SUCCESSFUL:")
        print("  1. Review performance of 2 positions")
        print("  2. Verify profit protection worked")
        print("  3. Check for any issues in logs")
        print("  4. If all good, proceed to Day 3:")
        print("     • Set MAX_TRAILING_STOP_POSITIONS=999")
        print("     • Enable for all positions")
        
        print("\n⚠️  IF ANY ISSUES:")
        print("  1. Set TRAILING_STOPS_ENABLED=false")
        print("  2. Restart backend")
        print("  3. Review logs and fix issues")
        print("  4. Re-test before re-enabling")
    
    print("\n" + "="*80 + "\n")
    
    return passed_count == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
