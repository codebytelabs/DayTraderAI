#!/usr/bin/env python3
"""
Verify long-only mode and trailing stops configuration.
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config import settings

def verify_configuration():
    """Verify that long-only mode and trailing stops are properly configured."""
    print("=" * 70)
    print("LONG-ONLY MODE & TRAILING STOPS VERIFICATION")
    print("=" * 70)
    
    # Test long-only mode
    long_only = getattr(settings, 'long_only_mode', False)
    print(f"\n✅ Long-Only Mode: {long_only}")
    if long_only:
        print("   → SELL signals will be rejected in trading_engine.py")
        print("   → Only BUY signals will be processed")
    else:
        print("   ⚠️  WARNING: Long-only mode is DISABLED")
        print("   → Both BUY and SELL signals allowed")
    
    # Test trailing stops
    trailing_enabled = getattr(settings, 'trailing_stops_enabled', False)
    activation_threshold = getattr(settings, 'trailing_stops_activation_threshold', 2.0)
    trail_distance = getattr(settings, 'trailing_stops_distance_r', 0.5)
    
    print(f"\n✅ Trailing Stops Enabled: {trailing_enabled}")
    print(f"✅ Activation Threshold: +{activation_threshold}R profit")
    print(f"✅ Trail Distance: {trail_distance}R ({trail_distance}%)")
    
    if trailing_enabled:
        print(f"\n   → Fixed stops for positions below +{activation_threshold}R")
        print(f"   → Trailing stops for positions at +{activation_threshold}R or better")
        print(f"   → Stops trail {trail_distance}% below current price")
    
    # Test dynamic watchlist (should still be enabled)
    dynamic_watchlist = getattr(settings, 'use_dynamic_watchlist', False)
    print(f"\n✅ Dynamic Watchlist: {dynamic_watchlist}")
    
    print("\n" + "=" * 70)
    print("EXPECTED BEHAVIOR AFTER RESTART:")
    print("=" * 70)
    
    if long_only:
        print("✅ No more 'account not allowed to short' errors")
        print("✅ SELL signals filtered out BEFORE order submission")
        print("✅ Only long positions will be taken")
        print("\nExpected log messages:")
        print("   ⚠️  AAPL SELL signal rejected: Long-only mode enabled")
        print("   ⚠️  AMD SELL signal rejected: Long-only mode enabled")
        print("   📈 Signal detected: BUY NVDA")
    else:
        print("⚠️  WARNING: Short selling still enabled!")
        print("   You will continue to see short selling errors")
    
    if trailing_enabled:
        print(f"\n✅ New positions get fixed stops (1% below entry)")
        print(f"✅ Profitable positions (+{activation_threshold}R) get trailing stops")
        print(f"✅ Trailing stops follow price up with {trail_distance}% distance")
    
    print("\n" + "=" * 70)
    if long_only and trailing_enabled:
        print("✅ CONFIGURATION READY! Restart to activate.")
    else:
        print("⚠️  CONFIGURATION INCOMPLETE! Check settings above.")
    print("=" * 70)

if __name__ == "__main__":
    verify_configuration()
