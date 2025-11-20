#!/usr/bin/env python3
"""
Check ONDS position status and bracket orders
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient

def check_onds_position():
    """Check ONDS position and orders"""
    print("🔍 Checking ONDS Position Status")
    print("=" * 70)
    
    # Initialize clients
    alpaca = AlpacaClient()
    supabase = SupabaseClient()
    
    # Get all positions
    positions = alpaca.get_positions()
    
    # Find ONDS
    onds_position = None
    for pos in positions:
        if pos.symbol == "ONDS":
            onds_position = pos
            break
    
    if not onds_position:
        print("❌ No ONDS position found")
        return
    
    print(f"\n📊 ONDS Position Details:")
    print(f"   Symbol: {onds_position.symbol}")
    print(f"   Quantity: {onds_position.qty}")
    print(f"   Side: {onds_position.side}")
    print(f"   Entry Price: ${float(onds_position.avg_entry_price):.2f}")
    print(f"   Current Price: ${float(onds_position.current_price):.2f}")
    print(f"   Market Value: ${float(onds_position.market_value):.2f}")
    print(f"   Cost Basis: ${float(onds_position.cost_basis):.2f}")
    print(f"   Unrealized P/L: ${float(onds_position.unrealized_pl):.2f}")
    print(f"   Unrealized P/L %: {float(onds_position.unrealized_plpc)*100:.2f}%")
    
    # Calculate what the high was
    entry_price = float(onds_position.avg_entry_price)
    current_price = float(onds_position.current_price)
    unrealized_pl = float(onds_position.unrealized_pl)
    
    # If it was +$200 at some point
    if unrealized_pl < 0:
        print(f"\n⚠️  Position is now in LOSS: ${unrealized_pl:.2f}")
        print(f"   This suggests stop loss may not have triggered")
    
    # Get all orders for ONDS
    print(f"\n📋 Checking Orders for ONDS:")
    all_orders = alpaca.get_orders(status='all')
    # Filter for ONDS
    all_orders = [o for o in all_orders if o.symbol == 'ONDS']
    
    if not all_orders:
        print("   ❌ No orders found for ONDS")
    else:
        for order in all_orders:
            print(f"\n   Order ID: {order.id}")
            print(f"   Type: {order.type}")
            print(f"   Side: {order.side}")
            print(f"   Status: {order.status}")
            print(f"   Qty: {order.qty}")
            
            if hasattr(order, 'limit_price') and order.limit_price:
                print(f"   Limit Price: ${float(order.limit_price):.2f}")
            if hasattr(order, 'stop_price') and order.stop_price:
                print(f"   Stop Price: ${float(order.stop_price):.2f}")
            if hasattr(order, 'trail_percent') and order.trail_percent:
                print(f"   Trail Percent: {float(order.trail_percent):.2f}%")
            
            print(f"   Submitted: {order.submitted_at}")
            if order.filled_at:
                print(f"   Filled: {order.filled_at}")
            if order.canceled_at:
                print(f"   Canceled: {order.canceled_at}")
    
    # Check database for trade history
    print(f"\n📚 Checking Database for ONDS Trade History:")
    try:
        result = supabase.client.table("trades").select("*").eq("symbol", "ONDS").order("entry_time", desc=True).limit(5).execute()
        
        if result.data:
            for trade in result.data:
                print(f"\n   Trade ID: {trade.get('id')}")
                print(f"   Entry Time: {trade.get('entry_time')}")
                print(f"   Entry Price: ${trade.get('entry_price', 0):.2f}")
                print(f"   Stop Loss: ${trade.get('stop_loss', 0):.2f}")
                print(f"   Take Profit: ${trade.get('take_profit', 0):.2f}")
                print(f"   Status: {trade.get('status')}")
                if trade.get('exit_price'):
                    print(f"   Exit Price: ${trade.get('exit_price'):.2f}")
                if trade.get('exit_time'):
                    print(f"   Exit Time: {trade.get('exit_time')}")
        else:
            print("   No trade records found in database")
    except Exception as e:
        print(f"   Error checking database: {e}")
    
    # Analysis
    print(f"\n🔍 Analysis:")
    print(f"=" * 70)
    
    # Check if bracket orders exist
    has_stop_loss = False
    has_take_profit = False
    has_trailing_stop = False
    
    for order in all_orders:
        if order.status in ['new', 'accepted', 'pending_new']:
            if order.type == 'stop':
                has_stop_loss = True
                print(f"✅ Active Stop Loss found: ${float(order.stop_price):.2f}")
            elif order.type == 'limit' and order.side != onds_position.side:
                has_take_profit = True
                print(f"✅ Active Take Profit found: ${float(order.limit_price):.2f}")
            elif order.type == 'trailing_stop':
                has_trailing_stop = True
                print(f"✅ Active Trailing Stop found: {float(order.trail_percent):.2f}%")
    
    if not has_stop_loss and not has_trailing_stop:
        print(f"❌ NO ACTIVE STOP LOSS OR TRAILING STOP!")
        print(f"   This is why the position went from +$200 to loss")
        print(f"   Bracket orders may have failed or been canceled")
    
    if not has_take_profit:
        print(f"⚠️  No active take profit order")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    print(f"=" * 70)
    
    if not has_stop_loss and not has_trailing_stop:
        print(f"1. ⚠️  URGENT: Add stop loss immediately to protect position")
        print(f"2. Check why bracket orders weren't created or were canceled")
        print(f"3. Review order submission logs")
        print(f"4. Consider enabling Smart Order Executor (USE_SMART_EXECUTOR=True)")
    
    if unrealized_pl < -50:
        print(f"5. ⚠️  Position is significantly underwater (${unrealized_pl:.2f})")
        print(f"   Consider closing position to prevent further losses")

if __name__ == "__main__":
    check_onds_position()
