#!/usr/bin/env python3
"""
Immediately clean up remnant positions (< 1% of equity).
Run this to free up capital for new full-size trades.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from trading.position_manager import PositionManager
from config import settings

def main():
    print("🧹 Remnant Position Cleanup")
    print("=" * 50)
    
    # Initialize clients
    alpaca = AlpacaClient()
    supabase = SupabaseClient()
    position_manager = PositionManager(alpaca, supabase)
    
    # Get account info
    account = alpaca.get_account()
    equity = float(account.equity)
    print(f"💰 Account Equity: ${equity:,.2f}")
    
    # Get current positions
    positions = alpaca.get_positions()
    print(f"📊 Current Positions: {len(positions)}")
    
    # Calculate remnant threshold
    remnant_pct = getattr(settings, 'remnant_position_pct', 0.01)
    remnant_threshold = equity * remnant_pct
    print(f"🎯 Remnant Threshold: ${remnant_threshold:,.2f} ({remnant_pct*100:.1f}% of equity)")
    print()
    
    # Identify remnant positions
    remnants = []
    keepers = []
    
    for pos in positions:
        symbol = pos.symbol
        qty = int(pos.qty)
        market_value = abs(float(pos.market_value))
        entry_price = float(pos.avg_entry_price)
        current_price = float(pos.current_price)
        pnl = float(pos.unrealized_pl)
        pnl_pct = float(pos.unrealized_plpc) * 100
        
        if market_value < remnant_threshold:
            remnants.append({
                'symbol': symbol,
                'qty': qty,
                'value': market_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
            print(f"🗑️  REMNANT: {symbol} | Qty: {qty} | Value: ${market_value:,.2f} | P/L: ${pnl:+.2f} ({pnl_pct:+.1f}%)")
        else:
            keepers.append({
                'symbol': symbol,
                'qty': qty,
                'value': market_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
            print(f"✅ KEEP: {symbol} | Qty: {qty} | Value: ${market_value:,.2f} | P/L: ${pnl:+.2f} ({pnl_pct:+.1f}%)")
    
    print()
    print(f"📊 Summary: {len(remnants)} remnants, {len(keepers)} keepers")
    
    if not remnants:
        print("✅ No remnant positions to clean up!")
        return
    
    # Ask for confirmation
    total_remnant_value = sum(r['value'] for r in remnants)
    total_remnant_pnl = sum(r['pnl'] for r in remnants)
    
    print()
    print(f"💵 Total Remnant Value: ${total_remnant_value:,.2f}")
    print(f"📈 Total Remnant P/L: ${total_remnant_pnl:+.2f}")
    print()
    
    confirm = input("🔄 Close all remnant positions? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Cancelled")
        return
    
    # Close remnant positions
    print()
    print("🔄 Closing remnant positions...")
    
    closed = position_manager.cleanup_tiny_positions(min_pct=remnant_pct)
    
    print()
    print(f"✅ Closed {closed} remnant positions")
    print(f"💰 Freed up ~${total_remnant_value:,.2f} for new trades")

if __name__ == "__main__":
    main()
