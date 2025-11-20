#!/usr/bin/env python3
"""
Analyze the 4 positions that closed at "take profit" but resulted in losses
"""
import os
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
print("🔍 ANALYZING RECENT LOSSES - JPM, PLTR, SOFI, WFC")
print("=" * 80)

# These are the 4 positions that closed today
positions = {
    "JPM": {"expected_pnl": -22.44},
    "PLTR": {"expected_pnl": -56.88},
    "SOFI": {"expected_pnl": -82.33},
    "WFC": {"expected_pnl": -14.49}
}

for symbol, data in positions.items():
    print(f"\n{'=' * 80}")
    print(f"📊 {symbol} - DETAILED ANALYSIS")
    print("=" * 80)
    
    # Get recent orders
    request = GetOrdersRequest(
        status=QueryOrderStatus.ALL,
        symbols=[symbol],
        limit=10
    )
    
    orders = client.get_orders(filter=request)
    
    # Find the most recent filled BUY and SELL
    buy_order = None
    sell_order = None
    
    for order in orders:
        if order.filled_avg_price:
            if order.side == OrderSide.BUY and not buy_order:
                buy_order = order
            elif order.side == OrderSide.SELL and not sell_order:
                sell_order = order
        
        if buy_order and sell_order:
            break
    
    if not buy_order or not sell_order:
        print(f"❌ Could not find complete trade for {symbol}")
        continue
    
    entry_price = float(buy_order.filled_avg_price)
    entry_qty = float(buy_order.filled_qty)
    exit_price = float(sell_order.filled_avg_price)
    exit_qty = float(sell_order.filled_qty)
    
    actual_pnl = (exit_price - entry_price) * exit_qty
    actual_pnl_pct = ((exit_price - entry_price) / entry_price) * 100
    
    print(f"\n📈 ENTRY:")
    print(f"   Order ID: {buy_order.id}")
    print(f"   Time: {buy_order.filled_at}")
    print(f"   Price: ${entry_price:.2f}")
    print(f"   Quantity: {entry_qty}")
    print(f"   Total: ${entry_price * entry_qty:.2f}")
    
    print(f"\n📉 EXIT:")
    print(f"   Order ID: {sell_order.id}")
    print(f"   Time: {sell_order.filled_at}")
    print(f"   Price: ${exit_price:.2f}")
    print(f"   Quantity: {exit_qty}")
    print(f"   Total: ${exit_price * exit_qty:.2f}")
    
    print(f"\n💰 P/L:")
    print(f"   Actual: ${actual_pnl:.2f} ({actual_pnl_pct:+.2f}%)")
    print(f"   Expected (from logs): ${data['expected_pnl']:.2f}")
    print(f"   Match: {'✅' if abs(actual_pnl - data['expected_pnl']) < 1 else '❌'}")
    
    # Now find the bracket orders to see what TP/SL were set
    print(f"\n🎯 BRACKET ANALYSIS:")
    
    # Find all orders from the same bracket group
    bracket_orders = []
    for order in orders:
        if order.created_at == buy_order.created_at:
            bracket_orders.append(order)
    
    tp_order = None
    sl_order = None
    
    for order in bracket_orders:
        if order.side == OrderSide.SELL and order.id != sell_order.id:
            if order.limit_price and not order.stop_price:
                tp_order = order
            elif order.stop_price:
                sl_order = order
    
    if tp_order and tp_order.limit_price:
        tp_price = float(tp_order.limit_price)
        expected_tp_pnl = (tp_price - entry_price) * entry_qty
        expected_tp_pct = ((tp_price - entry_price) / entry_price) * 100
        
        print(f"   Take Profit Order:")
        print(f"      Price: ${tp_price:.2f}")
        print(f"      Expected P/L: ${expected_tp_pnl:.2f} ({expected_tp_pct:+.2f}%)")
        print(f"      Status: {tp_order.status}")
        
        if expected_tp_pnl < 0:
            print(f"      ⚠️  CRITICAL: TP PRICE IS BELOW ENTRY! THIS IS THE BUG!")
        elif tp_price < entry_price:
            print(f"      ⚠️  CRITICAL: TP PRICE (${tp_price:.2f}) < ENTRY (${entry_price:.2f})")
    
    if sl_order and sl_order.stop_price:
        sl_price = float(sl_order.stop_price)
        expected_sl_pnl = (sl_price - entry_price) * entry_qty
        expected_sl_pct = ((sl_price - entry_price) / entry_price) * 100
        
        print(f"   Stop Loss Order:")
        print(f"      Price: ${sl_price:.2f}")
        print(f"      Expected P/L: ${expected_sl_pnl:.2f} ({expected_sl_pct:+.2f}%)")
        print(f"      Status: {sl_order.status}")
    
    # Determine what actually triggered
    print(f"\n🔍 WHAT TRIGGERED:")
    if tp_order and tp_order.status.name == "FILLED":
        print(f"   ✅ Take Profit was FILLED")
        print(f"   Exit Price: ${exit_price:.2f}")
        print(f"   TP Price: ${tp_price:.2f}")
        print(f"   Difference: ${exit_price - tp_price:.2f}")
    elif sl_order and sl_order.status.name == "FILLED":
        print(f"   ✅ Stop Loss was FILLED")
    else:
        print(f"   ⚠️  Manual exit or protection manager")
        print(f"   Sell order type: {sell_order.type}")
        print(f"   Sell order client_order_id: {sell_order.client_order_id}")

print("\n" + "=" * 80)
print("📋 SUMMARY")
print("=" * 80)
print("\n🔍 ROOT CAUSE ANALYSIS:")
print("   Need to check bracket_orders.py to see how TP/SL are calculated")
print("   Specifically: Are TP prices being set BELOW entry for long positions?")
print("\n✅ Next Steps:")
print("   1. Review bracket_orders.py calculation logic")
print("   2. Check if TP/SL are inverted")
print("   3. Verify slippage handling")
print("   4. Test with corrected logic")
