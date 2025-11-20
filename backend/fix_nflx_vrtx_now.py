#!/usr/bin/env python3
"""
Quick fix for NFLX and VRTX wash trade errors.
Run from backend directory: python fix_nflx_vrtx_now.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient
import time

def fix_symbol_orders(client, symbol):
    """Fix wash trade error for a symbol by canceling conflicting orders."""
    print(f"\n🔍 Checking {symbol} orders...")
    
    # Get all open orders and filter for this symbol
    all_orders = client.get_orders(status='open')
    orders = [o for o in all_orders if o.symbol == symbol]
    
    if not orders:
        print(f"✅ No open {symbol} orders found")
        return True
    
    print(f"📋 Found {len(orders)} open {symbol} orders:")
    for order in orders:
        price = order.stop_price or order.limit_price or 0
        print(f"  - {order.side} {order.qty} @ ${price:.2f} ({order.type})")
    
    # Cancel all orders
    print(f"🗑️  Canceling all {symbol} orders...")
    for order in orders:
        try:
            client.cancel_order(order.id)
            print(f"✅ Canceled order {order.id}")
        except Exception as e:
            print(f"❌ Failed to cancel {order.id}: {e}")
    
    # Wait for cancellations to process
    print("⏳ Waiting 2 seconds for cancellations...")
    time.sleep(2)
    
    # Get current position
    try:
        position = client.get_position(symbol)
        if not position:
            print(f"ℹ️  No {symbol} position found")
            return True
            
        qty = int(position.qty)
        entry_price = float(position.avg_entry_price)
        current_price = float(position.current_price)
        
        print(f"📊 {symbol} Position: {qty} shares @ ${entry_price:.2f} (current: ${current_price:.2f})")
        
        # Create proper bracket order
        stop_price = entry_price * 0.985  # 1.5% stop
        take_profit = entry_price * 1.03  # 3% target
        
        print(f"🎯 Creating bracket: Stop ${stop_price:.2f} | Target ${take_profit:.2f}")
        
        # Submit bracket order
        order = client.submit_order(
            symbol=symbol,
            qty=qty,
            side='sell',
            type='market',
            time_in_force='gtc',
            order_class='bracket',
            stop_loss={'stop_price': stop_price},
            take_profit={'limit_price': take_profit}
        )
        
        print(f"✅ Created bracket order for {symbol}: {order.id}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create {symbol} bracket: {e}")
        return False


def main():
    print("🚨 EMERGENCY FIX FOR NFLX & VRTX")
    print("=" * 60)
    
    client = AlpacaClient()
    
    # Fix NFLX
    nflx_ok = fix_symbol_orders(client, 'NFLX')
    
    # Fix VRTX
    vrtx_ok = fix_symbol_orders(client, 'VRTX')
    
    # Summary
    print("\n" + "=" * 60)
    if nflx_ok and vrtx_ok:
        print("✅ All fixes applied successfully!")
    else:
        print("⚠️  Some fixes failed - check errors above")
    print("=" * 60)


if __name__ == "__main__":
    main()
