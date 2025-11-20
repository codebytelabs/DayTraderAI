#!/usr/bin/env python3
"""Quick check of current bracket orders"""

import sys
sys.path.insert(0, '/Users/vishnuvardhanmedara/DayTraderAI/backend')

from core.alpaca_client import AlpacaClient

alpaca_client = AlpacaClient()

def check_brackets():
    print("=" * 80)
    print("🔍 CHECKING BRACKET ORDERS FOR OPEN POSITIONS")
    print("=" * 80)
    
    # Get positions
    positions = alpaca_client.get_positions()
    print(f"\n📊 Open Positions: {len(positions)}")
    
    for pos in positions:
        symbol = pos.symbol
        qty = float(pos.qty)
        side = pos.side
        entry = float(pos.avg_entry_price)
        current = float(pos.current_price)
        pnl = float(pos.unrealized_pl)
        pnl_pct = float(pos.unrealized_plpc) * 100
        
        print(f"\n{'='*80}")
        print(f"📈 {symbol} - {side.upper()} {abs(qty)} shares")
        print(f"   Entry: ${entry:.2f} | Current: ${current:.2f}")
        print(f"   P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        print(f"{'='*80}")
        
        # Get all orders for this symbol
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus
        
        request = GetOrdersRequest(
            status=QueryOrderStatus.OPEN,
            symbols=[symbol]
        )
        orders = alpaca_client.trading_client.get_orders(filter=request)
        
        stop_loss = None
        take_profit = None
        
        for order in orders:
            order_type = order.type
            order_side = order.side
            order_qty = float(order.qty)
            
            if order_type == 'stop':
                stop_loss = order
                print(f"   🛑 STOP-LOSS: {order_side} {order_qty} @ ${float(order.stop_price):.2f}")
                print(f"      Status: {order.status}")
                print(f"      Order ID: {order.id}")
                
            elif order_type == 'limit':
                take_profit = order
                print(f"   🎯 TAKE-PROFIT: {order_side} {order_qty} @ ${float(order.limit_price):.2f}")
                print(f"      Status: {order.status}")
                print(f"      Order ID: {order.id}")
        
        # Validate brackets
        print(f"\n   ✅ Bracket Status:")
        if stop_loss and take_profit:
            print(f"      ✓ Both stop-loss and take-profit present")
            
            # Check quantities match
            if abs(float(stop_loss.qty)) == abs(qty) and abs(float(take_profit.qty)) == abs(qty):
                print(f"      ✓ Quantities match position size ({abs(qty)} shares)")
            else:
                print(f"      ⚠️  Quantity mismatch!")
                print(f"         Position: {abs(qty)}, Stop: {abs(float(stop_loss.qty))}, TP: {abs(float(take_profit.qty))}")
            
            # Check sides are correct
            expected_exit_side = 'buy' if side == 'short' else 'sell'
            if stop_loss.side == expected_exit_side and take_profit.side == expected_exit_side:
                print(f"      ✓ Order sides correct ({expected_exit_side})")
            else:
                print(f"      ⚠️  Order side mismatch!")
                print(f"         Expected: {expected_exit_side}, Stop: {stop_loss.side}, TP: {take_profit.side}")
                
        elif stop_loss and not take_profit:
            print(f"      ⚠️  MISSING TAKE-PROFIT!")
        elif take_profit and not stop_loss:
            print(f"      ⚠️  MISSING STOP-LOSS!")
        else:
            print(f"      ❌ NO BRACKETS FOUND!")
    
    print(f"\n{'='*80}")
    print("✅ Bracket check complete")
    print("=" * 80)

if __name__ == "__main__":
    check_brackets()
