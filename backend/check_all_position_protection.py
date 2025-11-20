#!/usr/bin/env python3
"""
Check all positions for proper stop loss protection
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient

def check_all_positions():
    """Check all positions for active stop losses"""
    print("🛡️  Position Protection Check")
    print("=" * 70)
    
    alpaca = AlpacaClient()
    
    # Get all positions
    positions = alpaca.get_positions()
    
    if not positions:
        print("✅ No open positions")
        return
    
    print(f"📊 Found {len(positions)} open positions\n")
    
    # Get all orders
    all_orders = alpaca.get_orders(status='all')
    
    issues_found = []
    
    for pos in positions:
        symbol = pos.symbol
        qty = int(pos.qty)
        entry_price = float(pos.avg_entry_price)
        current_price = float(pos.current_price)
        unrealized_pl = float(pos.unrealized_pl)
        
        print(f"{'='*70}")
        print(f"📈 {symbol}")
        print(f"   Quantity: {qty}")
        print(f"   Entry: ${entry_price:.2f}")
        print(f"   Current: ${current_price:.2f}")
        print(f"   P/L: ${unrealized_pl:.2f} ({float(pos.unrealized_plpc)*100:.2f}%)")
        
        # Find orders for this symbol
        symbol_orders = [o for o in all_orders if o.symbol == symbol]
        
        # Check for stop loss
        has_active_stop = False
        has_held_stop = False
        has_take_profit = False
        has_trailing_stop = False
        
        for order in symbol_orders:
            if order.status.value in ['new', 'accepted', 'pending_new']:
                if order.type.value == 'stop':
                    has_active_stop = True
                    print(f"   ✅ Active Stop Loss: ${float(order.stop_price):.2f}")
                elif order.type.value == 'trailing_stop':
                    has_trailing_stop = True
                    print(f"   ✅ Active Trailing Stop: {float(order.trail_percent):.2f}%")
                elif order.type.value == 'limit' and order.side.value != pos.side.value:
                    has_take_profit = True
                    print(f"   ✅ Active Take Profit: ${float(order.limit_price):.2f}")
            
            elif order.status.value == 'held':
                if order.type.value in ['stop', 'trailing_stop']:
                    has_held_stop = True
                    print(f"   ❌ HELD Stop Loss: ${float(order.stop_price) if hasattr(order, 'stop_price') else 'N/A':.2f}")
                    issues_found.append({
                        'symbol': symbol,
                        'issue': 'HELD stop loss',
                        'order_id': order.id
                    })
        
        # Summary for this position
        if not has_active_stop and not has_trailing_stop:
            print(f"   🚨 NO ACTIVE STOP LOSS PROTECTION!")
            issues_found.append({
                'symbol': symbol,
                'issue': 'No active stop loss',
                'pl': unrealized_pl
            })
        
        if has_held_stop:
            print(f"   ⚠️  Stop loss is HELD (not active)")
        
        if not has_take_profit:
            print(f"   ⚠️  No take profit order")
        
        print()
    
    # Summary
    print(f"{'='*70}")
    print(f"📋 SUMMARY")
    print(f"{'='*70}")
    
    if not issues_found:
        print(f"✅ All positions have active stop loss protection")
    else:
        print(f"🚨 Found {len(issues_found)} issues:\n")
        for issue in issues_found:
            print(f"   • {issue['symbol']}: {issue['issue']}")
            if 'pl' in issue:
                print(f"     Current P/L: ${issue['pl']:.2f}")
        
        print(f"\n💡 Recommendations:")
        print(f"   1. Fix HELD orders immediately")
        print(f"   2. Add stop losses to unprotected positions")
        print(f"   3. Enable Smart Order Executor (USE_SMART_EXECUTOR=True)")
        print(f"   4. Monitor order status regularly")

if __name__ == "__main__":
    check_all_positions()
