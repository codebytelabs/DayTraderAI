#!/usr/bin/env python3
"""Fix incorrect bracket orders for short positions"""

import sys
sys.path.insert(0, '/Users/vishnuvardhanmedara/DayTraderAI/backend')

from core.alpaca_client import AlpacaClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus, OrderSide

alpaca_client = AlpacaClient()

def fix_brackets():
    print("=" * 80)
    print("🔧 FIXING BRACKET ORDERS FOR SHORT POSITIONS")
    print("=" * 80)
    
    # Get positions
    positions = alpaca_client.get_positions()
    print(f"\n📊 Open Positions: {len(positions)}")
    
    for pos in positions:
        symbol = pos.symbol
        qty = float(pos.qty)
        side = pos.side
        
        if side != 'short':
            print(f"\n⏭️  Skipping {symbol} - not a short position")
            continue
        
        print(f"\n{'='*80}")
        print(f"🔧 Fixing {symbol} - SHORT {abs(qty)} shares")
        print(f"{'='*80}")
        
        # Get all orders for this symbol
        request = GetOrdersRequest(
            status=QueryOrderStatus.OPEN,
            symbols=[symbol]
        )
        orders = alpaca_client.trading_client.get_orders(filter=request)
        
        wrong_orders = []
        correct_orders = []
        
        for order in orders:
            order_side = order.side
            order_type = order.type
            
            # For SHORT positions, exit orders should be BUY
            if order_side == OrderSide.SELL:
                wrong_orders.append(order)
                print(f"   ❌ WRONG: {order_type.upper()} {order_side} @ ${float(order.stop_price if order_type == 'stop' else order.limit_price):.2f} - ID: {order.id}")
            elif order_side == OrderSide.BUY:
                correct_orders.append(order)
                print(f"   ✅ CORRECT: {order_type.upper()} {order_side} @ ${float(order.stop_price if order_type == 'stop' else order.limit_price):.2f} - ID: {order.id}")
        
        # Cancel wrong orders
        if wrong_orders:
            print(f"\n   🗑️  Canceling {len(wrong_orders)} incorrect orders...")
            for order in wrong_orders:
                try:
                    alpaca_client.trading_client.cancel_order_by_id(order.id)
                    print(f"      ✓ Canceled {order.id}")
                except Exception as e:
                    print(f"      ✗ Failed to cancel {order.id}: {e}")
        
        # Verify correct orders remain
        if len(correct_orders) >= 2:
            print(f"\n   ✅ {symbol} has {len(correct_orders)} correct bracket orders remaining")
        else:
            print(f"\n   ⚠️  {symbol} only has {len(correct_orders)} correct orders - may need manual recreation")
    
    print(f"\n{'='*80}")
    print("✅ Bracket fix complete")
    print("=" * 80)

if __name__ == "__main__":
    fix_brackets()
