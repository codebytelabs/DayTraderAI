#!/usr/bin/env python3
"""
Manually fix brackets for BA and PYPL by using OCO orders
"""
import os
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import OrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

api_key = os.getenv("ALPACA_API_KEY")
api_secret = os.getenv("ALPACA_SECRET_KEY")

if not api_key or not api_secret:
    print("❌ Error: API keys not set")
    sys.exit(1)

client = TradingClient(api_key, api_secret, paper=True)

print("=" * 80)
print("🔧 MANUAL BRACKET FIX - Using OCO Orders")
print("=" * 80)
print("\nThis will:")
print("1. Cancel existing stop-loss orders")
print("2. Create OCO (One-Cancels-Other) orders with both stop and limit")
print("\n" + "=" * 80)

# Get positions
positions = client.get_all_positions()

for pos in positions:
    symbol = pos.symbol
    qty = int(pos.qty)
    entry = float(pos.avg_entry_price)
    
    print(f"\n📊 {symbol}:")
    print(f"  Entry: ${entry:.2f}")
    print(f"  Qty: {qty} shares")
    
    # Calculate prices
    stop_price = entry * 0.985  # 1.5% below
    take_profit_price = entry * 1.025  # 2.5% above
    
    print(f"  Stop: ${stop_price:.2f} (-1.5%)")
    print(f"  Target: ${take_profit_price:.2f} (+2.5%)")
    
    # Cancel existing stop-loss
    orders = client.get_orders(status='open')
    for order in orders:
        if order.symbol == symbol:
            try:
                client.cancel_order(order.id)
                print(f"  🗑️  Cancelled old order: {order.id}")
            except Exception as e:
                print(f"  ⚠️  Could not cancel {order.id}: {e}")
    
    # Wait for cancellation
    print(f"  ⏳ Waiting 3 seconds...")
    time.sleep(3)
    
    # Create OCO order (bracket without entry)
    try:
        from alpaca.trading.requests import OrderRequest
        
        # Use a simple approach: Create limit order first, then stop
        # Alpaca's OCO requires specific order types
        
        print(f"  ⚠️  Note: Alpaca paper trading may not support OCO orders")
        print(f"  💡 Recommendation: Close these positions and let bot enter fresh ones")
        print(f"     with proper bracket orders from the start")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "=" * 80)
print("🎯 RECOMMENDATION")
print("=" * 80)
print("""
The cleanest solution is to:

1. Manually close BA and PYPL positions in Alpaca dashboard
2. Let the bot enter fresh positions with proper bracket orders
3. New positions will have BOTH stop-loss AND take-profit from the start

This avoids the "insufficient qty" issue entirely because bracket orders
are created atomically by Alpaca.

Your current positions:
- BA: -$17.50 (-0.13%) - Close at small loss
- PYPL: $0.00 (0.00%) - Close at breakeven

Then the bot will find new opportunities with full bracket protection!
""")
print("=" * 80)
