#!/usr/bin/env python3
"""
Quick check of current positions and bracket orders
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, OrderStatus, QueryOrderStatus

# Initialize Alpaca
api_key = os.getenv("ALPACA_API_KEY")
api_secret = os.getenv("ALPACA_SECRET_KEY")

if not api_key or not api_secret:
    print("❌ Error: ALPACA_API_KEY and ALPACA_SECRET_KEY must be set")
    sys.exit(1)

client = TradingClient(api_key, api_secret, paper=True)

print("=" * 80)
print("🔍 CURRENT POSITIONS & BRACKET ORDERS")
print("=" * 80)

# Get positions
positions = client.get_all_positions()
print(f"\n📊 OPEN POSITIONS: {len(positions)}")
print("-" * 80)

for pos in positions:
    print(f"\n  Symbol: {pos.symbol}")
    print(f"  Qty: {pos.qty} shares")
    print(f"  Entry: ${float(pos.avg_entry_price):.2f}")
    print(f"  Current: ${float(pos.current_price):.2f}")
    print(f"  P&L: ${float(pos.unrealized_pl):.2f} ({float(pos.unrealized_plpc)*100:.2f}%)")

# Get open orders
request = GetOrdersRequest(status=QueryOrderStatus.OPEN)
orders = client.get_orders(filter=request)

print(f"\n\n📋 PENDING ORDERS: {len(orders)}")
print("-" * 80)

# Group by symbol
by_symbol = {}
for order in orders:
    symbol = order.symbol
    if symbol not in by_symbol:
        by_symbol[symbol] = []
    by_symbol[symbol].append(order)

for symbol, symbol_orders in by_symbol.items():
    print(f"\n  {symbol}: {len(symbol_orders)} orders")
    for order in symbol_orders:
        order_type = order.type.value
        side = order.side.value
        
        if order.stop_price:
            print(f"    • STOP-LOSS: {side} {order.qty} @ ${float(order.stop_price):.2f}")
        elif order.limit_price:
            print(f"    • TAKE-PROFIT: {side} {order.qty} @ ${float(order.limit_price):.2f}")
        else:
            print(f"    • {order_type.upper()}: {side} {order.qty}")

print("\n" + "=" * 80)
print("✅ EXPECTED STRUCTURE:")
print("=" * 80)
print("For each position, you should see:")
print("  1. One OPEN POSITION (the stock holding)")
print("  2. One STOP-LOSS order (pending)")
print("  3. One TAKE-PROFIT order (pending)")
print("\nTotal: 3 positions = 3 holdings + 6 pending orders = 9 items")
print("=" * 80)
