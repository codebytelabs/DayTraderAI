#!/usr/bin/env python3
"""Recreate proper bracket orders for all positions"""

import sys
sys.path.insert(0, '/Users/vishnuvardhanmedara/DayTraderAI/backend')

from core.alpaca_client import AlpacaClient
from alpaca.trading.requests import GetOrdersRequest, StopOrderRequest, LimitOrderRequest
from alpaca.trading.enums import QueryOrderStatus, OrderSide, TimeInForce
import time

alpaca_client = AlpacaClient()

def recreate_brackets():
    print("=" * 80)
    print("🔄 RECREATING PROPER BRACKET ORDERS")
    print("=" * 80)
    
    # Get positions
    positions = alpaca_client.get_positions()
    print(f"\n📊 Open Positions: {len(positions)}")
    
    for pos in positions:
        symbol = pos.symbol
        qty = abs(float(pos.qty))
        side = pos.side
        entry = float(pos.avg_entry_price)
        current = float(pos.current_price)
        
        print(f"\n{'='*80}")
        print(f"🔄 {symbol} - {side.upper()} {qty} shares @ ${entry:.2f}")
        print(f"   Current: ${current:.2f}")
        print(f"{'='*80}")
        
        # Step 1: Cancel ALL existing orders for this symbol
        request = GetOrdersRequest(
            status=QueryOrderStatus.OPEN,
            symbols=[symbol]
        )
        orders = alpaca_client.trading_client.get_orders(filter=request)
        
        if orders:
            print(f"\n   🗑️  Canceling {len(orders)} existing orders...")
            for order in orders:
                try:
                    alpaca_client.trading_client.cancel_order_by_id(order.id)
                    print(f"      ✓ Canceled {order.id}")
                except Exception as e:
                    print(f"      ✗ Failed to cancel {order.id}: {e}")
            
            # Wait for cancellations to process
            print(f"   ⏳ Waiting for cancellations to process...")
            time.sleep(3)
        
        # Step 2: Calculate correct prices based on position side
        if side == 'buy':
            # LONG: profit above, stop below
            take_profit_price = round(entry * 1.025, 2)  # 2.5% above
            stop_loss_price = round(entry * 0.985, 2)    # 1.5% below
            exit_side = OrderSide.SELL
        else:
            # SHORT: profit below, stop above
            take_profit_price = round(entry * 0.975, 2)  # 2.5% below
            stop_loss_price = round(entry * 1.015, 2)    # 1.5% above
            exit_side = OrderSide.BUY
        
        print(f"\n   📊 Creating bracket orders:")
        print(f"      Exit Side: {exit_side}")
        print(f"      Take-Profit: ${take_profit_price:.2f}")
        print(f"      Stop-Loss: ${stop_loss_price:.2f}")
        
        # Step 3: Create stop-loss first (more important)
        try:
            stop_request = StopOrderRequest(
                symbol=symbol,
                qty=qty,
                side=exit_side,
                time_in_force=TimeInForce.GTC,
                stop_price=stop_loss_price
            )
            
            stop_order = alpaca_client.trading_client.submit_order(stop_request)
            print(f"      ✅ Stop-Loss created: {stop_order.id}")
            
            # Wait between orders
            time.sleep(1)
            
        except Exception as e:
            print(f"      ❌ Stop-Loss failed: {e}")
            continue
        
        # Step 4: Create take-profit
        try:
            tp_request = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=exit_side,
                time_in_force=TimeInForce.GTC,
                limit_price=take_profit_price
            )
            
            tp_order = alpaca_client.trading_client.submit_order(tp_request)
            print(f"      ✅ Take-Profit created: {tp_order.id}")
            
        except Exception as e:
            print(f"      ❌ Take-Profit failed: {e}")
            # If TP fails, we still have stop-loss which is more important
    
    print(f"\n{'='*80}")
    print("✅ Bracket recreation complete")
    print("=" * 80)

if __name__ == "__main__":
    recreate_brackets()
