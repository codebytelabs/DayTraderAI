#!/usr/bin/env python3
"""
Emergency fix for ONDS stop loss
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient

def fix_onds_stop_loss():
    """Fix ONDS stop loss"""
    print("🚨 Emergency ONDS Stop Loss Fix")
    print("=" * 70)
    
    alpaca = AlpacaClient()
    
    # Get ONDS position
    positions = alpaca.get_positions()
    onds_pos = None
    for pos in positions:
        if pos.symbol == "ONDS":
            onds_pos = pos
            break
    
    if not onds_pos:
        print("❌ No ONDS position found")
        return
    
    current_price = float(onds_pos.current_price)
    entry_price = float(onds_pos.avg_entry_price)
    qty = int(onds_pos.qty)
    
    print(f"📊 Current Status:")
    print(f"   Entry: ${entry_price:.2f}")
    print(f"   Current: ${current_price:.2f}")
    print(f"   P/L: ${float(onds_pos.unrealized_pl):.2f}")
    
    # Cancel the HELD stop loss
    print(f"\n🔄 Canceling HELD stop loss order...")
    all_orders = alpaca.get_orders(status='all')
    for order in all_orders:
        if order.symbol == 'ONDS' and order.type.value == 'stop' and order.status.value == 'held':
            try:
                alpaca.cancel_order(order.id)
                print(f"   ✅ Canceled HELD stop loss: {order.id}")
            except Exception as e:
                print(f"   ⚠️  Could not cancel: {e}")
    
    # Create new stop loss at breakeven or small loss
    # Use 1% below current price as emergency stop
    emergency_stop = current_price * 0.99  # 1% below current
    
    print(f"\n🛡️  Creating new emergency stop loss...")
    print(f"   Stop Price: ${emergency_stop:.2f} (1% below current)")
    
    try:
        from alpaca.trading.requests import StopOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce
        
        stop_request = StopOrderRequest(
            symbol="ONDS",
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            stop_price=round(emergency_stop, 2)
        )
        
        stop_order = alpaca.submit_order_request(stop_request)
        print(f"   ✅ New stop loss created: {stop_order.id}")
        print(f"   Status: {stop_order.status}")
        
    except Exception as e:
        print(f"   ❌ Failed to create stop loss: {e}")
        print(f"\n⚠️  MANUAL ACTION REQUIRED:")
        print(f"   1. Go to Alpaca dashboard")
        print(f"   2. Manually add stop loss for ONDS at ${emergency_stop:.2f}")
        print(f"   3. Or close position immediately to prevent further losses")
    
    print(f"\n📋 Summary:")
    print(f"=" * 70)
    print(f"Issue: Stop loss was in HELD status (not active)")
    print(f"Action: Canceled HELD order and created new active stop")
    print(f"New Stop: ${emergency_stop:.2f}")
    print(f"Protection: Will exit if price drops 1% more")

if __name__ == "__main__":
    fix_onds_stop_loss()
