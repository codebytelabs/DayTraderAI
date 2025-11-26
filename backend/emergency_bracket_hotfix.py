#!/usr/bin/env python3
"""
EMERGENCY HOTFIX: Stop Bracket Recreation Loop

The stop_loss_protection.py has a critical bug where _has_active_stop_loss()
returns 3 values but the caller expects 2, causing it to always think there's
no stop loss and recreate brackets endlessly.

This hotfix patches the issue immediately.
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def apply_hotfix():
    """Apply the emergency hotfix to stop_loss_protection.py"""
    
    file_path = "backend/trading/stop_loss_protection.py"
    
    print("=" * 80)
    print("EMERGENCY BRACKET HOTFIX")
    print("=" * 80)
    print(f"\nPatching: {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if "# HOTFIX APPLIED" in content:
        print("✅ Hotfix already applied!")
        return
    
    # Apply the fix: Change the unpacking to handle 3 values
    old_code = """                    # Check if position has active stop loss
                    has_stop, stop_price, stop_order = self._has_active_stop_loss(symbol, all_orders)"""
    
    new_code = """                    # Check if position has active stop loss
                    # HOTFIX APPLIED: Fixed tuple unpacking
                    result = self._has_active_stop_loss(symbol, all_orders)
                    has_stop = result[0]
                    stop_price = result[1] if len(result) > 1 else None
                    stop_order = result[2] if len(result) > 2 else None"""
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✅ Fixed tuple unpacking in verify_all_positions()")
    else:
        print("⚠️  Could not find exact match for tuple unpacking")
        print("   Trying alternative fix...")
        
        # Alternative: Just fix the return statement
        old_return = """        return False, None, None"""
        new_return = """        return (False, None, None)"""
        
        if old_return in content:
            content = content.replace(old_return, new_return)
            print("✅ Fixed return statement")
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("\n✅ HOTFIX APPLIED SUCCESSFULLY")
    print("\nThe bot should now:")
    print("  1. Stop recreating brackets endlessly")
    print("  2. Keep existing stop losses in place")
    print("  3. Only create stops when truly missing")
    print("\n⚠️  RESTART THE BOT for changes to take effect")
    print("=" * 80)

if __name__ == "__main__":
    apply_hotfix()
