#!/usr/bin/env python3
"""
Diagnose why take-profit orders are being cancelled
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from alpaca.trading.client import TradingClient

api_key = os.getenv("ALPACA_API_KEY")
api_secret = os.getenv("ALPACA_SECRET_KEY")

if not api_key or not api_secret:
    print("❌ Error: API keys not set")
    sys.exit(1)

client = TradingClient(api_key, api_secret, paper=True)

print("=" * 80)
print("🔍 BRACKET ORDER DIAGNOSIS")
print("=" * 80)

# Get all orders
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus

request = GetOrdersRequest(status=QueryOrderStatus.ALL, limit=100)
all_orders = client.get_orders(filter=request)

# Focus on BA, COIN, PYPL
symbols = ["BA", "COIN", "PYPL"]

for symbol in symbols:
    print(f"\n{'='*80}")
    print(f"📊 {symbol} - Order Analysis")
    print(f"{'='*80}")
    
    symbol_orders = [o for o in all_orders if o.symbol == symbol]
    
    # Find the most recent entry
    filled_entries = [o for o in symbol_orders if o.status.value == 'filled' and o.side.value == 'buy']
    if not filled_entries:
        print(f"  No filled entries found")
        continue
    
    latest_entry = max(filled_entries, key=lambda x: x.filled_at)
    print(f"\n  Latest Entry:")
    print(f"    Order ID: {latest_entry.id}")
    print(f"    Filled At: {latest_entry.filled_at}")
    print(f"    Order Class: {getattr(latest_entry, 'order_class', 'N/A')}")
    print(f"    Has Legs: {hasattr(latest_entry, 'legs') and latest_entry.legs is not None}")
    
    if hasattr(latest_entry, 'legs') and latest_entry.legs:
        print(f"    Leg IDs: {[leg.id for leg in latest_entry.legs]}")
    
    # Find orders created around the same time
    entry_time = latest_entry.filled_at
    related_orders = [
        o for o in symbol_orders 
        if abs((o.created_at - entry_time).total_seconds()) < 120  # Within 2 minutes
    ]
    
    print(f"\n  Related Orders (within 2 min of entry):")
    for order in sorted(related_orders, key=lambda x: x.created_at):
        status = order.status.value
        order_type = order.type.value
        side = order.side.value
        
        price_info = ""
        if order.stop_price:
            price_info = f"@ ${float(order.stop_price):.2f}"
        elif order.limit_price:
            price_info = f"@ ${float(order.limit_price):.2f}"
        
        order_class = getattr(order, 'order_class', 'N/A')
        parent_id = getattr(order, 'parent_order_id', 'N/A')
        
        print(f"    • {order.created_at.strftime('%H:%M:%S')} | {status:8} | {order_type:12} | {side:4} {price_info}")
        print(f"      ID: {order.id}")
        print(f"      Class: {order_class} | Parent: {parent_id}")
        
        if order.canceled_at:
            print(f"      ❌ CANCELLED at {order.canceled_at.strftime('%H:%M:%S')}")

print("\n" + "=" * 80)
print("🎯 KEY QUESTIONS:")
print("=" * 80)
print("1. Does the entry order have order_class='bracket'?")
print("2. Does the entry order have 'legs' attribute with stop/limit IDs?")
print("3. Do the stop/limit orders have parent_order_id pointing to entry?")
print("4. Are the cancelled orders marked as bracket legs?")
print("=" * 80)
