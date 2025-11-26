#!/usr/bin/env python3
"""
Diagnose Bracket Order Chaos
Analyzes why brackets keep getting recreated
"""

import os
import sys
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient

def analyze_bracket_chaos():
    """Analyze bracket order issues"""
    
    print("=" * 80)
    print("BRACKET ORDER CHAOS DIAGNOSIS")
    print("=" * 80)
    
    alpaca = AlpacaClient()
    supabase = SupabaseClient()
    
    # Get current positions
    positions = alpaca.get_positions()
    print(f"\n📊 Current Positions: {len(positions)}")
    
    for pos in positions:
        symbol = pos.symbol
        qty = float(pos.qty)
        side = pos.side
        entry = float(pos.avg_entry_price)
        current = float(pos.current_price)
        pnl = float(pos.unrealized_pl)
        
        print(f"\n{symbol}:")
        print(f"  Side: {side} | Qty: {qty} | Entry: ${entry:.2f} | Current: ${current:.2f}")
        print(f"  P/L: ${pnl:.2f}")
        
        # Get all orders for this symbol
        all_open_orders = alpaca.get_orders(status='open')
        orders = [o for o in all_open_orders if o.symbol == symbol]
        print(f"  Open Orders: {len(orders)}")
        
        stop_orders = []
        limit_orders = []
        
        for order in orders:
            if order.type == 'stop':
                stop_orders.append(order)
                print(f"    🛑 STOP: {order.side} {order.qty} @ ${order.stop_price} (ID: {str(order.id)[:8]}...)")
            elif order.type == 'limit':
                limit_orders.append(order)
                print(f"    🎯 LIMIT: {order.side} {order.qty} @ ${order.limit_price} (ID: {str(order.id)[:8]}...)")
        
        # Check for issues
        if len(stop_orders) == 0:
            print(f"  ⚠️  NO STOP LOSS - Position unprotected!")
        elif len(stop_orders) > 1:
            print(f"  ⚠️  MULTIPLE STOP LOSSES - Conflict detected!")
        
        if len(limit_orders) > 1:
            print(f"  ⚠️  MULTIPLE TAKE PROFITS - Conflict detected!")
    
    # Check recent order activity
    print("\n" + "=" * 80)
    print("RECENT ORDER ACTIVITY (Last 30 minutes)")
    print("=" * 80)
    
    all_orders = alpaca.get_orders(status='all')[:100]
    
    # Filter to last 30 minutes
    cutoff = datetime.now() - timedelta(minutes=30)
    recent_orders = [o for o in all_orders if o.created_at.replace(tzinfo=None) > cutoff]
    
    # Group by symbol
    by_symbol = {}
    for order in recent_orders:
        if order.symbol not in by_symbol:
            by_symbol[order.symbol] = []
        by_symbol[order.symbol].append(order)
    
    for symbol, orders in sorted(by_symbol.items()):
        print(f"\n{symbol}: {len(orders)} orders in last 30 min")
        
        # Count by type and status
        canceled = len([o for o in orders if o.status == 'canceled'])
        filled = len([o for o in orders if o.status == 'filled'])
        new = len([o for o in orders if o.status == 'new'])
        
        print(f"  Canceled: {canceled} | Filled: {filled} | New: {new}")
        
        if canceled > 5:
            print(f"  🚨 EXCESSIVE CANCELLATIONS - Bracket recreation loop!")
    
    # Check today's trades
    print("\n" + "=" * 80)
    print("TODAY'S CLOSED TRADES")
    print("=" * 80)
    
    response = supabase.client.table('trades').select('*').gte(
        'exit_time', datetime.now().strftime('%Y-%m-%d')
    ).order('exit_time', desc=True).execute()
    
    if response.data:
        total_pnl = 0
        for trade in response.data:
            symbol = trade['symbol']
            pnl = trade['pnl']
            reason = trade.get('exit_reason', 'unknown')
            total_pnl += pnl
            
            emoji = "✅" if pnl > 0 else "❌"
            print(f"{emoji} {symbol}: ${pnl:.2f} ({reason})")
        
        print(f"\n💰 Total P/L Today: ${total_pnl:.2f}")
        
        # Count emergency stops
        emergency_stops = [t for t in response.data if t.get('exit_reason') == 'emergency_stop']
        if emergency_stops:
            print(f"⚠️  Emergency Stops: {len(emergency_stops)}")
            print("   This indicates bracket orders are being lost/canceled")
    
    print("\n" + "=" * 80)
    print("DIAGNOSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    analyze_bracket_chaos()
