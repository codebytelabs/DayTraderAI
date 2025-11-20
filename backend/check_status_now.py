#!/usr/bin/env python3
"""Quick status check"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient

client = AlpacaClient()

print("\n📊 CURRENT POSITIONS:")
print("=" * 70)

positions = client.get_positions()
total_pnl = 0

for pos in positions:
    pnl = float(pos.unrealized_pl)
    pnl_pct = float(pos.unrealized_plpc) * 100
    total_pnl += pnl
    
    color = "+" if pnl > 0 else ""
    print(f"{pos.symbol:6} | {pos.qty:3} shares | {color}${pnl:7.2f} ({color}{pnl_pct:6.2f}%)")

print("=" * 70)
print(f"Total P/L: ${total_pnl:+.2f}\n")

print("📋 OPEN ORDERS:")
print("=" * 70)

orders = client.get_orders(status='open')
print(f"Total: {len(orders)} orders\n")

# Group by symbol
by_symbol = {}
for order in orders:
    if order.symbol not in by_symbol:
        by_symbol[order.symbol] = []
    by_symbol[order.symbol].append(order)

for symbol in sorted(by_symbol.keys()):
    orders_list = by_symbol[symbol]
    print(f"{symbol}:")
    for order in orders_list:
        price = order.stop_price or order.limit_price or 0
        if price:
            price = float(price)
            print(f"  {order.side:4} {order.qty:3} @ ${price:7.2f} ({order.type})")
        else:
            print(f"  {order.side:4} {order.qty:3} @ MARKET ({order.type})")

print("=" * 70)
