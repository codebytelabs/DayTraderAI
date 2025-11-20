#!/usr/bin/env python3
"""
Check order history for BA, COIN, PYPL to see what happened to take-profit orders
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus

api_key = os.getenv("ALPACA_API_KEY")
api_secret = os.getenv("ALPACA_SECRET_KEY")

if not api_key or not api_secret:
    print("❌ Error: API keys not set")
    sys.exit(1)

client = TradingClient(api_key, api_secret, paper=True)

symbols = ["BA", "COIN", "PYPL"]

print("=" * 80)
print("📜 ORDER HISTORY FOR CURRENT POSITIONS")
print("=" * 80)

for symbol in symbols:
    print(f"\n{'='*80}")
    print(f"🔍 {symbol} - Order History")
    print(f"{'='*80}")
    
    # Get all orders for this symbol (last 7 days)
    request = GetOrdersRequest(
        status=QueryOrderStatus.ALL,
        symbols=[symbol],
        limit=50
    )
    
    orders = client.get_orders(filter=request)
    
    if not orders:
        print(f"  No orders found for {symbol}")
        continue
    
    # Group by status
    by_status = {}
    for order in orders:
        status = order.status.value
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(order)
    
    for status, status_orders in sorted(by_status.items()):
        print(f"\n  {status.upper()}: {len(status_orders)} orders")
        for order in status_orders[:10]:  # Show last 10
            order_type = order.type.value
            side = order.side.value
            qty = order.qty
            
            price_info = ""
            if order.stop_price:
                price_info = f"stop @ ${float(order.stop_price):.2f}"
            elif order.limit_price:
                price_info = f"limit @ ${float(order.limit_price):.2f}"
            
            created = order.created_at.strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"    • {created} | {side} {qty} {order_type} {price_info}")
            
            if order.canceled_at:
                print(f"      ❌ CANCELLED at {order.canceled_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if order.filled_at:
                print(f"      ✅ FILLED at {order.filled_at.strftime('%Y-%m-%d %H:%M:%S')}")

print("\n" + "=" * 80)
print("🎯 ANALYSIS")
print("=" * 80)
print("Look for:")
print("  1. Take-profit orders that were CANCELLED (should not happen)")
print("  2. Take-profit orders that were FILLED (position should be closed)")
print("  3. Missing take-profit orders (were never created)")
print("=" * 80)
