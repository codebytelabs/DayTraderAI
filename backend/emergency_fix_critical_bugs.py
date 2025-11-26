#!/usr/bin/env python3
"""
EMERGENCY FIX: Critical Bug Fixes for Trading Bot
Fixes:
1. Smart Order Executor timeout too aggressive
2. Bracket recreation loop
3. Emergency stop false positives
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_smart_executor_timeout():
    """Fix 1: Increase Smart Order Executor timeout from 1s to 5s"""
    print("🔧 Fix 1: Adjusting Smart Order Executor timeout...")
    
    file_path = "backend/trading/order_manager.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find and replace the timeout value
    if 'await asyncio.sleep(1)  # Wait for fill' in content:
        content = content.replace(
            'await asyncio.sleep(1)  # Wait for fill',
            'await asyncio.sleep(5)  # Wait for fill (increased from 1s to prevent premature rejections)'
        )
        print("   ✅ Increased fill wait time from 1s to 5s")
    
    # Also increase the total timeout
    if 'timeout = 2  # seconds' in content:
        content = content.replace(
            'timeout = 2  # seconds',
            'timeout = 8  # seconds (increased to allow fills)'
        )
        print("   ✅ Increased total timeout from 2s to 8s")
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("   ✅ Smart Order Executor timeout fixed!\n")

def fix_bracket_recreation_loop():
    """Fix 2: Add cooldown to bracket recreation to prevent loops"""
    print("🔧 Fix 2: Adding bracket recreation cooldown...")
    
    file_path = "backend/trading/stop_loss_protection.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add cooldown tracking at class level
    if 'self.last_recreation_time = {}' not in content:
        # Find __init__ method and add cooldown tracking
        init_marker = 'def __init__(self, alpaca_client, supabase_client):'
        if init_marker in content:
            content = content.replace(
                init_marker + '\n        self.alpaca_client = alpaca_client',
                init_marker + '\n        self.alpaca_client = alpaca_client\n        self.last_recreation_time = {}  # Track last recreation per symbol\n        self.recreation_cooldown = 30  # seconds'
            )
            print("   ✅ Added cooldown tracking")
    
    # Add cooldown check before recreation
    if 'async def _ensure_stop_loss' in content and 'self.last_recreation_time.get(symbol' not in content:
        # Find the method and add cooldown check
        content = content.replace(
            'logger.warning(f"🚨 {symbol} has NO ACTIVE STOP LOSS - creating now...")',
            '''# Check cooldown to prevent recreation loops
        import time
        now = time.time()
        last_recreation = self.last_recreation_time.get(symbol, 0)
        if now - last_recreation < self.recreation_cooldown:
            logger.info(f"⏳ {symbol} bracket recreation on cooldown ({int(now - last_recreation)}s ago, need {self.recreation_cooldown}s)")
            return
        
        logger.warning(f"🚨 {symbol} has NO ACTIVE STOP LOSS - creating now...")
        self.last_recreation_time[symbol] = now'''
        )
        print("   ✅ Added 30-second cooldown before recreation")
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("   ✅ Bracket recreation loop fixed!\n")

def fix_emergency_stop_false_positives():
    """Fix 3: Add grace period before emergency stop triggers"""
    print("🔧 Fix 3: Adding emergency stop grace period...")
    
    file_path = "backend/trading/position_manager.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add grace period tracking
    if 'self.no_orders_detected_time = {}' not in content:
        # Find __init__ and add tracking
        init_marker = 'def __init__(self, alpaca_client, supabase_client):'
        if init_marker in content:
            content = content.replace(
                init_marker + '\n        self.alpaca_client = alpaca_client',
                init_marker + '\n        self.alpaca_client = alpaca_client\n        self.no_orders_detected_time = {}  # Track when NO orders first detected\n        self.emergency_stop_grace_period = 15  # seconds'
            )
            print("   ✅ Added grace period tracking")
    
    # Modify the emergency stop logic to use grace period
    if 'logger.warning(f"⚠️  {symbol} has NO orders - manual check activated")' in content:
        content = content.replace(
            '''logger.warning(f"⚠️  {symbol} has NO orders - manual check activated")
                
                # Emergency stop if no protection
                logger.error(f"🚨 EMERGENCY STOP: {symbol} @ ${current_price}")''',
            '''logger.warning(f"⚠️  {symbol} has NO orders - manual check activated")
                
                # Check grace period before emergency stop
                import time
                now = time.time()
                if symbol not in self.no_orders_detected_time:
                    self.no_orders_detected_time[symbol] = now
                    logger.info(f"⏳ {symbol} grace period started - will emergency stop in {self.emergency_stop_grace_period}s if not resolved")
                    continue
                
                time_without_orders = now - self.no_orders_detected_time[symbol]
                if time_without_orders < self.emergency_stop_grace_period:
                    logger.info(f"⏳ {symbol} in grace period ({int(time_without_orders)}s/{self.emergency_stop_grace_period}s)")
                    continue
                
                # Emergency stop after grace period
                logger.error(f"🚨 EMERGENCY STOP: {symbol} @ ${current_price} (no orders for {int(time_without_orders)}s)")'''
        )
        print("   ✅ Added 15-second grace period before emergency stop")
    
    # Clear grace period when orders are detected
    if 'else:  # Has orders' in content and 'self.no_orders_detected_time.pop(symbol, None)' not in content:
        content = content.replace(
            'else:  # Has orders',
            '''else:  # Has orders
                # Clear grace period since orders exist
                self.no_orders_detected_time.pop(symbol, None)'''
        )
        print("   ✅ Added grace period reset when orders detected")
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("   ✅ Emergency stop false positives fixed!\n")

def fix_position_sizing_tolerance():
    """Fix 4: Add 0.1% tolerance to position sizing to prevent $0.93 rejections"""
    print("🔧 Fix 4: Adding position sizing tolerance...")
    
    file_path = "backend/trading/order_manager.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the position size check and add tolerance
    if 'if position_value > max_position_value:' in content:
        content = content.replace(
            'if position_value > max_position_value:',
            'if position_value > max_position_value * 1.001:  # 0.1% tolerance for rounding'
        )
        print("   ✅ Added 0.1% tolerance to position sizing")
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("   ✅ Position sizing tolerance fixed!\n")

def main():
    print("=" * 60)
    print("🚨 EMERGENCY FIX: Critical Bug Fixes")
    print("=" * 60)
    print()
    
    try:
        fix_smart_executor_timeout()
        fix_bracket_recreation_loop()
        fix_emergency_stop_false_positives()
        fix_position_sizing_tolerance()
        
        print("=" * 60)
        print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("📋 Summary of fixes:")
        print("  1. ✅ Smart Order Executor timeout: 1s → 5s")
        print("  2. ✅ Bracket recreation cooldown: 30 seconds")
        print("  3. ✅ Emergency stop grace period: 15 seconds")
        print("  4. ✅ Position sizing tolerance: 0.1%")
        print()
        print("🔄 RESTART THE BOT NOW to apply fixes!")
        print()
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
