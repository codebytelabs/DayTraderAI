#!/usr/bin/env python3
"""
Audit Alpaca order history to understand why take profits resulted in losses
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus

load_dotenv()

# Initialize Alpaca client
api_key = os.getenv("ALPACA_API_KEY")
api_secret = os.getenv("ALPACA_SECRET_KEY")
client = TradingClient(api_key, api_secret, paper=True)

print("=" * 80)
print("🔍 ALPACA ORDER HISTORY AUDIT")
print("=" * 80)

# Get orders from last 24 hours
symbols = ["JPM", "PLTR", "SOFI", "WFC"]

for symbol in symbols:
    print(f"\n{'=' * 80}")
    print(f"📊 {symbol} - Order History")
    print("=" * 80)
    
    # Get all orders for this symbol
    request = GetOrdersRequest(
        status=QueryOrderStatus.ALL,
        symbols=[symbol],
        limit=50
    )
    
    orders = client.get_orders(filter=request)
    
    if not orders:
        print(f"❌ No orders found for {symbol}")
        continue
    
    # Group orders by client_order_id (bracket orders share same base ID)
    bracket_groups = {}
    
    for order in orders:
        # Extract base order ID (remove _tp or _sl suffix)
        base_id = order.client_order_id
        if base_id:
            if '_tp' in base_id:
                base_id = base_id.replace('_tp', '')
            elif '_sl' in base_id:
                base_id = base_id.replace('_sl', '')
        
        if base_id not in bracket_groups:
            bracket_groups[base_id] = []
        bracket_groups[base_id].append(order)
    
    # Analyze each bracket group
    for base_id, group_orders in bracket_groups.items():
        print(f"\n📦 Bracket Group: {base_id[:20]}...")
        print("-" * 80)
        
        entry_order = None
        tp_order = None
        sl_order = None
        
        for order in group_orders:
            order_type = "ENTRY"
            if order.client_order_id and '_tp' in order.client_order_id:
                order_type = "TAKE_PROFIT"
                tp_order = order
            elif order.client_order_id and '_sl' in order.client_order_id:
                order_type = "STOP_LOSS"
                sl_order = order
            elif order.side == OrderSide.BUY:
                entry_order = order
            
            print(f"\n  {order_type}:")
            print(f"    Order ID: {order.id}")
            print(f"    Side: {order.side}")
            print(f"    Qty: {order.qty}")
            print(f"    Status: {order.status}")
            print(f"    Type: {order.type}")
            
            if order.limit_price:
                print(f"    Limit Price: ${float(order.limit_price):.2f}")
            if order.stop_price:
                print(f"    Stop Price: ${float(order.stop_price):.2f}")
            if order.filled_avg_price:
                print(f"    Filled Avg Price: ${float(order.filled_avg_price):.2f}")
            if order.filled_qty:
                print(f"    Filled Qty: {float(order.filled_qty)}")
            
            print(f"    Created: {order.created_at}")
            if order.filled_at:
                print(f"    Filled: {order.filled_at}")
        
        # Calculate P/L if we have entry and exit
        if entry_order and entry_order.filled_avg_price:
            entry_price = float(entry_order.filled_avg_price)
            entry_qty = float(entry_order.filled_qty or order.qty)
            
            print(f"\n  💰 P/L ANALYSIS:")
            print(f"    Entry: {entry_qty} shares @ ${entry_price:.2f} = ${entry_price * entry_qty:.2f}")
            
            # Find exit order (either TP or SL that was filled)
            exit_order = None
            exit_type = None
            
            for order in group_orders:
                if order.side == OrderSide.SELL and order.filled_avg_price and order.id != entry_order.id:
                    exit_order = order
                    if '_tp' in (order.client_order_id or ''):
                        exit_type = "TAKE_PROFIT"
                    elif '_sl' in (order.client_order_id or ''):
                        exit_type = "STOP_LOSS"
                    else:
                        exit_type = "MANUAL_EXIT"
                    break
            
            if exit_order and exit_order.filled_avg_price:
                exit_price = float(exit_order.filled_avg_price)
                exit_qty = float(exit_order.filled_qty or exit_order.qty)
                
                pnl = (exit_price - entry_price) * exit_qty
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                
                print(f"    Exit ({exit_type}): {exit_qty} shares @ ${exit_price:.2f} = ${exit_price * exit_qty:.2f}")
                print(f"    P/L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
                
                # Check if TP/SL prices make sense
                if tp_order and tp_order.limit_price:
                    tp_price = float(tp_order.limit_price)
                    expected_tp_pnl = (tp_price - entry_price) * entry_qty
                    print(f"\n    🎯 Take Profit Analysis:")
                    print(f"       TP Price: ${tp_price:.2f}")
                    print(f"       Expected TP P/L: ${expected_tp_pnl:.2f}")
                    
                    if expected_tp_pnl < 0:
                        print(f"       ⚠️  WARNING: TP price is BELOW entry! This will cause losses!")
                
                if sl_order and sl_order.stop_price:
                    sl_price = float(sl_order.stop_price)
                    expected_sl_pnl = (sl_price - entry_price) * entry_qty
                    print(f"\n    🛡️  Stop Loss Analysis:")
                    print(f"       SL Price: ${sl_price:.2f}")
                    print(f"       Expected SL P/L: ${expected_sl_pnl:.2f}")

print("\n" + "=" * 80)
print("✅ Audit Complete")
print("=" * 80)
