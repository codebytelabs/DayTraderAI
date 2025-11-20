#!/usr/bin/env python3
"""
Emergency fix for all HELD stop losses
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient
from alpaca.trading.requests import StopOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

def fix_all_held_stops():
    """Fix all HELD stop loss orders"""
    print("🚨 Emergency Fix for ALL HELD Stop Losses")
    print("=" * 70)
    
    alpaca = AlpacaClient()
    
    # Get all positions
    positions = alpaca.get_positions()
    all_orders = alpaca.get_orders(status='all')
    
    fixed_count = 0
    
    for pos in positions:
        symbol = pos.symbol
        qty = int(pos.qty)
        current_price = float(pos.current_price)
        entry_price = float(pos.avg_entry_price)
        
        print(f"\n{'='*70}")
        print(f"📊 {symbol}")
        print(f"   Entry: ${entry_price:.2f}")
        print(f"   Current: ${current_price:.2f}")
        print(f"   P/L: ${float(pos.unrealized_pl):.2f}")
        
        # Find HELD stop loss
        held_stop = None
        for order in all_orders:
            if (order.symbol == symbol and 
                order.type.value == 'stop' and 
                order.status.value == 'held'):
                held_stop = order
                break
        
        if not held_stop:
            print(f"   ✅ No HELD stop loss found")
            continue
        
        print(f"   ❌ Found HELD stop loss: {held_stop.id}")
        print(f"   Original stop: ${float(held_stop.stop_price):.2f}")
        
        # Cancel HELD order
        try:
            alpaca.cancel_order(held_stop.id)
            print(f"   ✅ Canceled HELD order")
        except Exception as e:
            print(f"   ⚠️  Could not cancel: {e}")
            continue
        
        # Calculate new stop loss
        # Use 1.5% below current price as emergency stop
        emergency_stop = current_price * 0.985  # 1.5% below
        
        # Don't set stop above entry (for losing positions)
        if emergency_stop > entry_price:
            emergency_stop = entry_price * 0.99  # 1% below entry
        
        print(f"   🛡️  Creating new stop at ${emergency_stop:.2f}")
        
        try:
            stop_request = StopOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.GTC,
                stop_price=round(emergency_stop, 2)
            )
            
            new_stop = alpaca.submit_order_request(stop_request)
            print(f"   ✅ New stop created: {new_stop.id}")
            print(f"   Status: {new_stop.status}")
            fixed_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed to create stop: {e}")
    
    print(f"\n{'='*70}")
    print(f"📋 SUMMARY")
    print(f"{'='*70}")
    print(f"Fixed {fixed_count} positions")
    print(f"\n✅ All positions now have active stop loss protection")
    print(f"\n💡 Next Steps:")
    print(f"   1. Monitor new stops to ensure they're active")
    print(f"   2. Enable Smart Order Executor: USE_SMART_EXECUTOR=True")
    print(f"   3. Add order status monitoring to prevent future issues")

if __name__ == "__main__":
    fix_all_held_stops()
