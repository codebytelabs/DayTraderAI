#!/usr/bin/env python3
"""
Check Live Bracket Order Status

Connects to Alpaca and shows current bracket order status for all positions.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.alpaca_client import AlpacaClient
from config import settings
from datetime import datetime
import pytz

def check_bracket_status():
    """Check current bracket order status"""
    print("=" * 80)
    print("🔍 LIVE BRACKET ORDER STATUS CHECK")
    print("=" * 80)
    print()
    
    # Initialize Alpaca client
    alpaca = AlpacaClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        base_url=settings.alpaca_base_url
    )
    
    # Get all positions
    print("📊 Current Positions:")
    print("-" * 80)
    
    try:
        positions = alpaca.get_positions()
        
        if not positions:
            print("❌ No open positions")
            return
        
        for pos in positions:
            symbol = pos.symbol
            qty = int(pos.qty)
            entry = float(pos.avg_entry_price)
            current = float(pos.current_price)
            pnl = float(pos.unrealized_pl)
            pnl_pct = float(pos.unrealized_plpc) * 100
            
            print(f"\n{'='*80}")
            print(f"Symbol: {symbol}")
            print(f"Quantity: {qty}")
            print(f"Entry: ${entry:.2f}")
            print(f"Current: ${current:.2f}")
            print(f"P/L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
            print(f"{'-'*80}")
            
            # Get all orders for this symbol
            all_orders = alpaca.get_orders(status='all')
            symbol_orders = [o for o in all_orders if o.symbol == symbol]
            
            if not symbol_orders:
                print(f"⚠️  NO ORDERS FOUND for {symbol}")
                print(f"❌ POSITION IS UNPROTECTED!")
                continue
            
            # Categorize orders
            active_stops = []
            active_limits = []
            cancelled_stops = []
            cancelled_limits = []
            filled_orders = []
            
            for order in symbol_orders:
                status = order.status.value
                order_type = order.type.value
                side = order.side.value
                
                # Check if it's a bracket leg
                is_bracket = (
                    hasattr(order, 'order_class') and order.order_class == 'bracket'
                ) or (
                    hasattr(order, 'legs') and order.legs
                )
                
                if status in ['new', 'accepted', 'pending_new']:
                    if order_type in ['stop', 'trailing_stop']:
                        stop_price = float(order.stop_price) if hasattr(order, 'stop_price') else 0
                        active_stops.append({
                            'id': order.id,
                            'type': order_type,
                            'price': stop_price,
                            'bracket': is_bracket
                        })
                    elif order_type == 'limit':
                        limit_price = float(order.limit_price) if hasattr(order, 'limit_price') else 0
                        active_limits.append({
                            'id': order.id,
                            'type': order_type,
                            'price': limit_price,
                            'bracket': is_bracket
                        })
                
                elif status == 'cancelled':
                    if order_type in ['stop', 'trailing_stop']:
                        cancelled_stops.append(order.id)
                    elif order_type == 'limit':
                        cancelled_limits.append(order.id)
                
                elif status == 'filled':
                    filled_orders.append(order.id)
            
            # Report findings
            print(f"\n📋 Order Status for {symbol}:")
            print()
            
            if active_stops:
                print(f"✅ ACTIVE STOP LOSSES: {len(active_stops)}")
                for stop in active_stops:
                    bracket_tag = " [BRACKET]" if stop['bracket'] else ""
                    distance = abs(current - stop['price'])
                    distance_pct = (distance / current) * 100
                    print(f"   • {stop['type']}: ${stop['price']:.2f} ({distance_pct:.2f}% away){bracket_tag}")
            else:
                print(f"❌ NO ACTIVE STOP LOSSES")
            
            print()
            
            if active_limits:
                print(f"✅ ACTIVE TAKE PROFITS: {len(active_limits)}")
                for limit in active_limits:
                    bracket_tag = " [BRACKET]" if limit['bracket'] else ""
                    distance = abs(limit['price'] - current)
                    distance_pct = (distance / current) * 100
                    print(f"   • {limit['type']}: ${limit['price']:.2f} ({distance_pct:.2f}% away){bracket_tag}")
            else:
                print(f"❌ NO ACTIVE TAKE PROFITS")
            
            print()
            
            if cancelled_stops:
                print(f"⚠️  CANCELLED STOPS: {len(cancelled_stops)}")
                print(f"   This means stops were cancelled after position entry!")
            
            if cancelled_limits:
                print(f"⚠️  CANCELLED LIMITS: {len(cancelled_limits)}")
                print(f"   This means take profits were cancelled after position entry!")
            
            # Overall assessment
            print()
            if active_stops and active_limits:
                print(f"✅ {symbol} IS PROTECTED with active brackets")
            elif active_stops:
                print(f"⚠️  {symbol} has stop loss but NO take profit")
            elif active_limits:
                print(f"⚠️  {symbol} has take profit but NO stop loss")
            else:
                print(f"🚨 {symbol} IS UNPROTECTED - NO ACTIVE BRACKETS!")
        
        print(f"\n{'='*80}")
        print()
        
        # Summary
        print("📊 SUMMARY:")
        print("-" * 80)
        total_positions = len(positions)
        protected = sum(1 for pos in positions if any(
            o.symbol == pos.symbol and 
            o.status.value in ['new', 'accepted', 'pending_new'] and
            o.type.value in ['stop', 'trailing_stop']
            for o in alpaca.get_orders(status='all')
        ))
        
        print(f"Total Positions: {total_positions}")
        print(f"Protected: {protected}")
        print(f"Unprotected: {total_positions - protected}")
        
        if protected == total_positions:
            print()
            print("✅ ALL POSITIONS ARE PROTECTED!")
        else:
            print()
            print("🚨 SOME POSITIONS ARE UNPROTECTED!")
            print("   This is a CRITICAL issue - positions without stops can lose unlimited money!")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_bracket_status()
