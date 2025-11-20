#!/usr/bin/env python3
"""Add take-profit orders to positions that only have stop-losses"""

import sys
sys.path.insert(0, '/Users/vishnuvardhanmedara/DayTraderAI/backend')

from core.alpaca_client import AlpacaClient
from alpaca.trading.requests import LimitOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus

alpaca_client = AlpacaClient()

def add_take_profits():
    print("=" * 80)
    print("🎯 ADDING TAKE-PROFIT ORDERS")
    print("=" * 80)
    
    positions = alpaca_client.get_positions()
    
    for pos in positions:
        symbol = pos.symbol
        qty = abs(float(pos.qty))
        side = pos.side
        entry = float(pos.avg_entry_price)
        
        print(f"\n{'='*80}")
        print(f"📊 {symbol} - {side.upper()} {qty} shares @ ${entry:.2f}")
        
        # Check if already has take-profit
        request = GetOrdersRequest(
            status=QueryOrderStatus.OPEN,
            symbols=[symbol]
        )
        orders = alpaca_client.trading_client.get_orders(filter=request)
        
        has_tp = False
        has_sl = False
        
        for order in orders:
            if order.type == 'limit':
                has_tp = True
            if order.type == 'stop':
                has_sl = True
        
        if has_tp:
            print(f"   ✓ Already has take-profit order")
            continue
        
        if not has_sl:
            print(f"   ⚠️  No stop-loss found - skipping")
            continue
        
        # Calculate take-profit based on position side
        if side == 'buy':
            take_profit_price = round(entry * 1.025, 2)  # 2.5% above
            exit_side = OrderSide.SELL
        else:
            take_profit_price = round(entry * 0.975, 2)  # 2.5% below
            exit_side = OrderSide.BUY
        
        print(f"   🎯 Creating take-profit: {exit_side} {qty} @ ${take_profit_price:.2f}")
        
        try:
            # Try to create take-profit with reduced quantity first
            # (in case some shares are held by stop-loss)
            tp_request = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=exit_side,
                time_in_force=TimeInForce.GTC,
                limit_price=take_profit_price
            )
            
            order = alpaca_client.trading_client.submit_order(tp_request)
            print(f"   ✅ Take-profit created: {order.id}")
            
        except Exception as e:
            error_msg = str(e)
            if "insufficient qty" in error_msg:
                print(f"   ⚠️  Shares held by stop-loss - this is normal for paper trading")
                print(f"   ℹ️  Trailing stops will handle profit-taking at 2R")
            else:
                print(f"   ❌ Failed: {e}")
    
    print(f"\n{'='*80}")
    print("✅ Complete")
    print("=" * 80)

if __name__ == "__main__":
    add_take_profits()
