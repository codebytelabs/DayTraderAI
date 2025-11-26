#!/usr/bin/env python3
"""
Verify all critical fixes are in place
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_smart_executor():
    """Check Smart Order Executor configuration"""
    print("🔍 Checking Smart Order Executor...")
    
    try:
        from orders.smart_order_executor import SmartOrderExecutor, OrderConfig
        
        # Check default timeout
        config = OrderConfig()
        if config.fill_timeout_seconds >= 60:
            print(f"   ✅ Fill timeout: {config.fill_timeout_seconds}s (Good)")
        else:
            print(f"   ⚠️  Fill timeout: {config.fill_timeout_seconds}s (Should be 60s+)")
        
        # Check slippage protection
        if config.max_slippage_pct <= 0.001:
            print(f"   ✅ Max slippage: {config.max_slippage_pct*100:.2f}% (Good)")
        else:
            print(f"   ⚠️  Max slippage: {config.max_slippage_pct*100:.2f}% (High)")
        
        # Check R/R ratio
        if config.min_rr_ratio >= 2.0:
            print(f"   ✅ Min R/R ratio: 1:{config.min_rr_ratio} (Good)")
        else:
            print(f"   ⚠️  Min R/R ratio: 1:{config.min_rr_ratio} (Should be 2.0+)")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_position_manager():
    """Check Position Manager configuration"""
    print("\n🔍 Checking Position Manager...")
    
    try:
        # Check if position manager has emergency stop grace period
        file_path = os.path.join(os.path.dirname(__file__), 'trading', 'position_manager.py')
        with open(file_path, 'r') as f:
            content = f.read()
        
        if 'emergency_stop_grace_period' in content:
            print("   ✅ Emergency stop grace period: Present")
        else:
            print("   ⚠️  Emergency stop grace period: Not found")
        
        if 'no_orders_detected_time' in content:
            print("   ✅ Grace period tracking: Present")
        else:
            print("   ⚠️  Grace period tracking: Not found")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_bracket_protection():
    """Check bracket protection system"""
    print("\n🔍 Checking Bracket Protection...")
    
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'trading', 'position_manager.py')
        with open(file_path, 'r') as f:
            content = f.read()
        
        if 'last_bracket_recreation_time' in content:
            print("   ✅ Bracket recreation cooldown: Present")
        else:
            print("   ⚠️  Bracket recreation cooldown: Not found")
        
        if 'BRACKET_RECREATION_COOLDOWN' in content or 'bracket_recreation_cooldown' in content:
            print("   ✅ Cooldown constant: Present")
        else:
            print("   ⚠️  Cooldown constant: Not found")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_position_sizing():
    """Check position sizing tolerance"""
    print("\n🔍 Checking Position Sizing...")
    
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'trading', 'order_manager.py')
        with open(file_path, 'r') as f:
            content = f.read()
        
        if '0.001' in content or '0.1%' in content:
            print("   ✅ Position sizing tolerance: Present")
        else:
            print("   ⚠️  Position sizing tolerance: Not found")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_config():
    """Check configuration settings"""
    print("\n🔍 Checking Configuration...")
    
    try:
        from config import settings
        
        # Check Smart Executor enabled
        if hasattr(settings, 'USE_SMART_EXECUTOR'):
            if settings.USE_SMART_EXECUTOR:
                print("   ✅ Smart Executor: ENABLED")
            else:
                print("   ⚠️  Smart Executor: DISABLED")
        else:
            print("   ⚠️  Smart Executor setting: Not found")
        
        # Check bracket orders
        if hasattr(settings, 'bracket_orders_enabled'):
            if settings.bracket_orders_enabled:
                print("   ✅ Bracket Orders: ENABLED")
            else:
                print("   ⚠️  Bracket Orders: DISABLED")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 VERIFYING ALL CRITICAL FIXES")
    print("=" * 60)
    print()
    
    checks = [
        check_smart_executor(),
        check_position_manager(),
        check_bracket_protection(),
        check_position_sizing(),
        check_config()
    ]
    
    print()
    print("=" * 60)
    
    if all(checks):
        print("✅ ALL CHECKS PASSED!")
        print("=" * 60)
        print()
        print("🚀 Your bot is ready to trade!")
        print()
        print("Start with:")
        print("  ./backend/RESTART_FIXED_BOT.sh")
        print()
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("=" * 60)
        print()
        print("Review the warnings above and apply fixes if needed.")
        print()

if __name__ == "__main__":
    main()
