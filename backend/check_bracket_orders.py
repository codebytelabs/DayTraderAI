#!/usr/bin/env python3
"""
Check bracket order status and diagnose why stop losses aren't being set.
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.alpaca_client import AlpacaClient
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


def check_bracket_orders():
    """Check all orders and positions to diagnose bracket order issues."""
    
    alpaca = AlpacaClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        base_url=settings.alpaca_base_url
    )
    
    print("\n" + "="*80)
    print("BRACKET ORDER DIAGNOSTIC")
    print("="*80)
    
    # Get all positions
    positions = alpaca.get_positions()
    print(f"\n📊 POSITIONS ({len(positions)}):")
    print("-" * 80)
    
    for pos in positions:
        print(f"\n{pos.symbol}:")
        print(f"  Qty: {pos.qty}")
        print(f"  Entry: ${float(pos.avg_entry_price):.2f}")
        print(f"  Current: ${float(pos.current_price):.2f}")
        print(f"  P/L: ${float(pos.unrealized_pl):.2f} ({float(pos.unrealized_plpc)*100:.2f}%)")
    
    # Get all orders
    all_orders = alpaca.get_orders(status='all', limit=100)
    print(f"\n📋 ALL ORDERS ({len(all_orders)}):")
    print("-" * 80)
    
    # Group orders by symbol
    orders_by_symbol = {}
    for order in all_orders:
        symbol = order.symbol
        if symbol not in orders_by_symbol:
            orders_by_symbol[symbol] = []
        orders_by_symbol[symbol].append(order)
    
    # Analyze each symbol
    for symbol in sorted(orders_by_symbol.keys()):
        orders = orders_by_symbol[symbol]
        print(f"\n{symbol} ({len(orders)} orders):")
        
        # Find bracket orders
        bracket_parents = [o for o in orders if hasattr(o, 'order_class') and o.order_class == 'bracket']
        
        for parent in bracket_parents:
            print(f"\n  🎯 BRACKET ORDER: {parent.id}")
            print(f"     Status: {parent.status}")
            print(f"     Side: {parent.side}")
            print(f"     Qty: {parent.qty}")
            print(f"     Filled: {parent.filled_qty}/{parent.qty}")
            print(f"     Created: {parent.created_at}")
            
            # Check for legs
            if hasattr(parent, 'legs') and parent.legs:
                print(f"     Legs: {len(parent.legs)}")
                for i, leg in enumerate(parent.legs, 1):
                    print(f"\n     LEG {i}: {leg.id}")
                    print(f"       Type: {leg.type}")
                    print(f"       Status: {leg.status}")
                    if hasattr(leg, 'stop_price') and leg.stop_price:
                        print(f"       Stop Price: ${float(leg.stop_price):.2f}")
                    if hasattr(leg, 'limit_price') and leg.limit_price:
                        print(f"       Limit Price: ${float(leg.limit_price):.2f}")
            else:
                print(f"     ⚠️  NO LEGS FOUND!")
        
        # Find standalone stop/limit orders
        standalone = [o for o in orders if not (hasattr(o, 'order_class') and o.order_class == 'bracket')]
        if standalone:
            print(f"\n  📌 STANDALONE ORDERS ({len(standalone)}):")
            for order in standalone:
                print(f"     {order.type} | {order.status} | {order.side} {order.qty}")
                if order.type == 'stop' and hasattr(order, 'stop_price'):
                    print(f"       Stop: ${float(order.stop_price):.2f}")
                if order.type == 'limit' and hasattr(order, 'limit_price'):
                    print(f"       Limit: ${float(order.limit_price):.2f}")
    
    # Check for positions without protection
    print("\n" + "="*80)
    print("PROTECTION STATUS")
    print("="*80)
    
    for pos in positions:
        symbol = pos.symbol
        
        # Check for active stop loss
        has_stop = False
        for order in all_orders:
            if (order.symbol == symbol and 
                order.type in ['stop', 'trailing_stop'] and 
                order.status in ['new', 'accepted', 'pending_new']):
                has_stop = True
                break
        
        status = "✅ PROTECTED" if has_stop else "🚨 NO STOP LOSS"
        print(f"\n{symbol}: {status}")
        print(f"  P/L: ${float(pos.unrealized_pl):.2f}")
    
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    unprotected = [pos.symbol for pos in positions if not any(
        o.symbol == pos.symbol and 
        o.type in ['stop', 'trailing_stop'] and 
        o.status in ['new', 'accepted', 'pending_new']
        for o in all_orders
    )]
    
    if unprotected:
        print(f"\n⚠️  {len(unprotected)} positions without stop loss protection:")
        for symbol in unprotected:
            print(f"   - {symbol}")
        print("\nPossible causes:")
        print("  1. Bracket order legs not created by Alpaca")
        print("  2. Bracket order legs in HELD status")
        print("  3. Stop loss orders were canceled")
        print("\nSolutions:")
        print("  1. Restart the trading engine to trigger auto-fix")
        print("  2. Manually create stop loss orders")
        print("  3. Close positions if at risk")
    else:
        print("\n✅ All positions have stop loss protection!")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    check_bracket_orders()
