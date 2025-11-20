#!/usr/bin/env python3
"""
Add missing take-profit orders for existing positions
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

api_key = os.getenv("ALPACA_API_KEY")
api_secret = os.getenv("ALPACA_SECRET_KEY")

if not api_key or not api_secret:
    print("❌ Error: API keys not set")
    sys.exit(1)

client = TradingClient(api_key, api_secret, paper=True)

print("=" * 80)
print("🎯 ADDING MISSING TAKE-PROFIT ORDERS")
print("=" * 80)

# Get positions
positions = client.get_all_positions()

for pos in positions:
    symbol = pos.symbol
    qty = int(pos.qty)
    entry = float(pos.avg_entry_price)
    current = float(pos.current_price)
    
    print(f"\n📊 {symbol}:")
    print(f"  Entry: ${entry:.2f}")
    print(f"  Current: ${current:.2f}")
    print(f"  Qty: {qty} shares")
    
    # Calculate take-profit at 2.5% above entry (2.5:1 R/R with 1.5% stop)
    take_profit_price = entry * 1.025
    
    print(f"  Take-Profit Target: ${take_profit_price:.2f} (+2.5%)")
    
    # Check if take-profit already exists
    orders = client.get_orders(status='open')
    has_take_profit = False
    
    for order in orders:
        if (order.symbol == symbol and 
            order.type.value == 'limit' and 
            order.side.value == 'sell'):
            has_take_profit = True
            print(f"  ✓ Already has take-profit order")
            break
    
    if has_take_profit:
        continue
    
    # Create take-profit order
    try:
        take_profit_request = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            limit_price=round(take_profit_price, 2)
        )
        
        order = client.submit_order(take_profit_request)
        print(f"  ✅ Created take-profit order: {order.id}")
        print(f"     Sell {qty} @ ${take_profit_price:.2f}")
        
    except Exception as e:
        print(f"  ❌ Failed to create take-profit: {e}")

print("\n" + "=" * 80)
print("✅ DONE - Check positions now")
print("=" * 80)
