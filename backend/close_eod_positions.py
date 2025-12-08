#!/usr/bin/env python3
"""
Emergency EOD Position Closer
Run this script to close all open positions after market hours.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


def close_all_positions():
    """Close all open positions immediately."""
    try:
        alpaca = AlpacaClient()
        positions = alpaca.get_positions()
        
        if not positions:
            print("✅ No open positions to close")
            return
        
        print(f"\n🔴 Found {len(positions)} open positions to close:\n")
        
        total_pnl = 0.0
        
        for pos in positions:
            symbol = pos.symbol
            qty = float(pos.qty)
            entry = float(pos.avg_entry_price)
            current = float(pos.current_price)
            pnl = float(pos.unrealized_pl)
            pnl_pct = float(pos.unrealized_plpc) * 100
            
            total_pnl += pnl
            
            status = "🟢" if pnl >= 0 else "🔴"
            print(f"{status} {symbol}: {qty} shares @ ${current:.2f} | P/L: ${pnl:+.2f} ({pnl_pct:+.1f}%)")
        
        print(f"\n{'='*50}")
        print(f"Total Unrealized P/L: ${total_pnl:+.2f}")
        print(f"{'='*50}\n")
        
        # Confirm before closing
        confirm = input("Close all positions? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("❌ Cancelled - no positions closed")
            return
        
        print("\n🔄 Closing positions...\n")
        
        closed = 0
        failed = 0
        
        for pos in positions:
            symbol = pos.symbol
            try:
                # Cancel any existing orders first
                orders = alpaca.get_orders(symbol=symbol, status='open')
                for order in orders:
                    try:
                        alpaca.cancel_order(order.id)
                        print(f"   Cancelled order {order.id} for {symbol}")
                    except Exception as e:
                        print(f"   ⚠️  Could not cancel order: {e}")
                
                # Close the position
                alpaca.close_position(symbol)
                print(f"✅ Closed {symbol}")
                closed += 1
                
            except Exception as e:
                print(f"❌ Failed to close {symbol}: {e}")
                failed += 1
        
        print(f"\n{'='*50}")
        print(f"📊 Summary: {closed} closed, {failed} failed")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    close_all_positions()
