#!/usr/bin/env python3
"""
Fix trailing stops for existing positions that are in profit.
Updates stop losses to lock in gains.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest, ReplaceOrderRequest
from alpaca.trading.enums import QueryOrderStatus

# Load env
api_key = os.environ.get('ALPACA_API_KEY', 'PKKX2K9CFFAABD5M8I5R')
secret_key = os.environ.get('ALPACA_SECRET_KEY', 'cRMG3ccQfZ5lzexiJ0c8EFgsVdiIcCrxx7uNntay')

client = TradingClient(api_key, secret_key, paper=True)

def fix_trailing_stops():
    """Update stops to lock in profits for positions that are in profit"""
    
    positions = client.get_all_positions()
    orders = client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN))
    
    # Build order map by symbol
    stop_orders = {}
    for order in orders:
        order_type = str(order.order_type).upper()
        if 'STOP' in order_type and 'LIMIT' not in order_type:
            stop_orders[order.symbol] = order
    
    print("=" * 60)
    print("TRAILING STOP FIX - Locking in Profits")
    print("=" * 60)
    
    for pos in positions:
        symbol = pos.symbol
        entry = float(pos.avg_entry_price)
        current = float(pos.current_price)
        qty = int(float(pos.qty))
        pnl_pct = float(pos.unrealized_plpc) * 100
        
        # Calculate R-multiple (assuming 1.5% initial risk)
        initial_risk = entry * 0.015
        profit = current - entry
        r_multiple = profit / initial_risk if initial_risk > 0 else 0
        
        stop_order = stop_orders.get(symbol)
        current_stop = float(stop_order.stop_price) if stop_order else None
        
        print(f"\n{symbol}:")
        print(f"  Entry: ${entry:.2f} | Current: ${current:.2f} | P/L: {pnl_pct:.2f}%")
        print(f"  R-Multiple: {r_multiple:.2f}R")
        print(f"  Current Stop: ${current_stop:.2f}" if current_stop else "  Current Stop: NONE")
        
        # Calculate new trailing stop based on R-multiple (same as intelligent_stop_manager)
        if r_multiple >= 4.0:
            # At 4R+, trail at 2R profit
            new_stop = entry + (2.0 * initial_risk)
            trail_reason = f"4R+ reached, locking 2R profit (${2.0 * initial_risk:.2f})"
        elif r_multiple >= 3.0:
            # At 3R, trail at 1.5R profit
            new_stop = entry + (1.5 * initial_risk)
            trail_reason = f"3R+ reached, locking 1.5R profit (${1.5 * initial_risk:.2f})"
        elif r_multiple >= 2.0:
            # At 2R, trail at 1R profit
            new_stop = entry + (1.0 * initial_risk)
            trail_reason = f"2R+ reached, locking 1R profit (${1.0 * initial_risk:.2f})"
        elif r_multiple >= 1.5:
            # At 1.5R, trail at 0.5R profit
            new_stop = entry + (0.5 * initial_risk)
            trail_reason = f"1.5R reached, locking 0.5R profit (${0.5 * initial_risk:.2f})"
        elif r_multiple >= 1.0:
            # At 1R, move to breakeven
            new_stop = entry
            trail_reason = "1R reached, moving to breakeven"
        else:
            # Not enough profit to trail
            print(f"  ⏳ Not enough profit to trail (need 1R+)")
            continue
        
        # Round to 2 decimal places
        new_stop = round(new_stop, 2)
        
        # Only update if new stop is higher than current
        if current_stop and new_stop <= current_stop:
            print(f"  ✅ Stop already at ${current_stop:.2f} (no update needed)")
            continue
        
        print(f"  📈 {trail_reason}")
        print(f"  🎯 New Stop: ${new_stop:.2f} (was ${current_stop:.2f})" if current_stop else f"  🎯 New Stop: ${new_stop:.2f}")
        
        # Update the stop order
        if stop_order:
            try:
                replace_request = ReplaceOrderRequest(
                    qty=qty,
                    stop_price=new_stop
                )
                client.replace_order_by_id(stop_order.id, replace_request)
                print(f"  ✅ Stop updated to ${new_stop:.2f}")
            except Exception as e:
                print(f"  ❌ Failed to update stop: {e}")
        else:
            print(f"  ⚠️  No stop order found - position unprotected!")

if __name__ == "__main__":
    fix_trailing_stops()
