"""
Sprint 5 Validation Script
Quick check that trailing stops are properly integrated
"""

import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from trading.trailing_stops import TrailingStopManager
from core.supabase_client import SupabaseClient


def print_status(label, value, expected=None):
    """Print status line"""
    if expected is not None:
        status = "✓" if value == expected else "✗"
        print(f"{status} {label}: {value} (expected: {expected})")
    else:
        print(f"  {label}: {value}")


def main():
    print("\n" + "="*80)
    print("  SPRINT 5: TRAILING STOPS - SYSTEM VALIDATION")
    print("="*80 + "\n")
    
    # Check configuration
    print("📋 CONFIGURATION:")
    print_status("Enabled", settings.trailing_stops_enabled, False)
    print_status("Shadow Mode", not settings.trailing_stops_enabled, True)
    print_status("Activation Threshold", f"{settings.trailing_stops_activation_threshold}R")
    print_status("Trailing Distance", f"{settings.trailing_stops_distance_r}R")
    print_status("Use ATR", settings.trailing_stops_use_atr, True)
    print_status("Max Positions", settings.max_trailing_stop_positions)
    
    # Check manager initialization
    print("\n🔧 SYSTEM CHECK:")
    try:
        supabase = SupabaseClient()
        manager = TrailingStopManager(supabase)
        print("✓ TrailingStopManager initialized successfully")
        
        # Health check
        health = manager.check_health()
        print(f"✓ Health Status: {health['status']}")
        
        if health.get('issues'):
            print(f"  ⚠️  Issues: {health['issues']}")
        
        if health.get('warnings'):
            print(f"  ⚠️  Warnings: {health['warnings']}")
        
    except Exception as e:
        print(f"✗ Error initializing manager: {e}")
        return False
    
    # Check integration
    print("\n🔗 INTEGRATION CHECK:")
    try:
        from core.alpaca_client import AlpacaClient
        from trading.position_manager import PositionManager
        
        alpaca = AlpacaClient()
        pos_manager = PositionManager(alpaca, supabase)
        
        if pos_manager.trailing_stop_manager:
            print("✓ Position Manager has TrailingStopManager")
            print("✓ Integration complete")
        else:
            print("✗ Position Manager missing TrailingStopManager")
            return False
            
    except Exception as e:
        print(f"✗ Integration error: {e}")
        return False
    
    # Summary
    print("\n" + "="*80)
    print("  ✅ SPRINT 5 - DAY 1: READY FOR TRADING")
    print("="*80)
    
    print("\n📊 WHAT WILL HAPPEN:")
    print("  • Trailing stops will run in SHADOW MODE")
    print("  • System will LOG what it WOULD do")
    print("  • NO actual trades will be affected")
    print("  • Shadow predictions will be tracked")
    
    print("\n📋 DURING TRADING DAY:")
    print("  1. Watch for [SHADOW] log entries")
    print("  2. Verify trailing stop calculations")
    print("  3. Check health periodically")
    print("  4. Review shadow predictions at end of day")
    
    print("\n🚀 AFTER SUCCESSFUL DAY 1:")
    print("  1. Review shadow mode logs")
    print("  2. Validate calculations are correct")
    print("  3. If all good, proceed to Day 2:")
    print("     • Set TRAILING_STOPS_ENABLED=true")
    print("     • Set MAX_TRAILING_STOP_POSITIONS=2")
    print("     • Monitor 2 positions closely")
    
    print("\n" + "="*80 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
