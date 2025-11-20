#!/usr/bin/env python3
"""
Emergency fix for missing stop losses.
Creates standalone stop loss orders for all unprotected positions.
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.alpaca_client import AlpacaClient
from config import settings
from alpaca.trading.requests import StopOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

def create_emergency_stops():
    """Create emergency stop loss orders for all unprotected positions."""
    
    alpaca = AlpacaClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        base_url=settings.alpaca_base_url
    )
    
    print("\n" + "="*80)
    print("EMERGENCY STOP LOSS FIX")
    print("="*80)
    
    # Get all positions
    positions = alpaca.get_positions()
    print(f"\n📊 Found {len(positions)} positions")
    
    # Get all orders
    all_orders = alpaca.get_orders(status='all', limit=100)
    
    # Check each position for active stop loss
    for pos in positions:
        symbol = pos.symbol
        qty = float(pos.qty)
        entry_price = float(pos.avg_entry_price)
        current_price = float(pos.current_price)
        unrealized_pl = float(pos.unrealized_pl)
        
        print(f"\n{symbol}:")
        print(f"  Qty: {qty}")
        print(f"  Entry: ${entry_price:.2f}")
        print(f"  Current: ${current_price:.2f}")
        print(f"  P/L: ${unrealized_pl:.2f}")
        
        # Check for active stop loss
        has_active_stop = False
        for order in all_orders:
            if (order.symbol == symbol and 
                order.type in ['stop', 'trailing_stop'] and 
                order.status in ['new', 'accepted', 'pending_new']):
                has_active_stop = True
                print(f"  ✅ Has active stop loss at ${float(order.stop_price):.2f}")
                break
        
        if not has_active_stop:
            print(f"  🚨 NO ACTIVE STOP LOSS!")
            
            # Calculate emergency stop (1.5% below current price, but not above entry for losing positions)
            emergency_stop = current_price * 0.985
            
            # Don't set stop above entry for losing positions
            if emergency_stop > entry_price:
                emergency_stop = entry_price * 0.99
            
            print(f"  💡 Creating emergency stop at ${emergency_stop:.2f}")
            
            try:
                stop_request = StopOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.SELL,  # Assuming long positions
                    time_in_force=TimeInForce.GTC,
                    stop_price=round(emergency_stop, 2)
                )
                
                new_stop = alpaca.submit_order_request(stop_request)
                print(f"  ✅ Emergency stop created: Order ID {new_stop.id}")
                
            except Exception as e:
                print(f"  ❌ Failed to create stop: {e}")
    
    print("\n" + "="*80)
    print("EMERGENCY FIX COMPLETE")
    print("="*80)
    print("\nAll positions should now have stop loss protection.")
    print("Monitor the Alpaca dashboard to verify stops are active.\n")


if __name__ == "__main__":
    create_emergency_stops()
