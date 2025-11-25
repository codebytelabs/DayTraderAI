#!/usr/bin/env python3
"""
Cleanup Tiny Positions Script
Closes positions that are too small to be meaningful for the portfolio.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from trading.position_manager import PositionManager
from config import settings

def main():
    print("\n" + "="*70)
    print("🧹 TINY POSITION CLEANUP")
    print("="*70)
    
    # Initialize clients
    alpaca = AlpacaClient()
    supabase = SupabaseClient()
    position_manager = PositionManager(alpaca, supabase)
    
    # Get account info
    account = alpaca.get_account()
    equity = float(account.equity)
    print(f"\n📊 Account Equity: ${equity:,.2f}")
    
    # Calculate minimum position value (0.7% of equity, min $1000)
    min_value = max(1000, equity * 0.007)
    print(f"📏 Minimum Position Value: ${min_value:,.2f}")
    
    # Get current positions
    positions = alpaca.get_positions()
    print(f"\n📋 Current Positions: {len(positions)}")
    
    # Identify tiny positions
    tiny_positions = []
    for pos in positions:
        market_value = abs(float(pos.market_value))
        if market_value < min_value:
            tiny_positions.append({
                'symbol': pos.symbol,
                'qty': pos.qty,
                'market_value': market_value,
                'pnl': float(pos.unrealized_pl),
                'pnl_pct': float(pos.unrealized_plpc) * 100
            })
    
    if not tiny_positions:
        print("\n✅ No tiny positions found!")
        return
    
    print(f"\n⚠️  Found {len(tiny_positions)} tiny positions:")
    print("-" * 70)
    print(f"{'Symbol':<10} {'Qty':<8} {'Value':<12} {'P/L':<12} {'P/L %':<10}")
    print("-" * 70)
    
    total_value = 0
    total_pnl = 0
    for pos in tiny_positions:
        print(f"{pos['symbol']:<10} {pos['qty']:<8} ${pos['market_value']:<10,.2f} ${pos['pnl']:<10,.2f} {pos['pnl_pct']:<8,.2f}%")
        total_value += pos['market_value']
        total_pnl += pos['pnl']
    
    print("-" * 70)
    print(f"{'TOTAL':<10} {'':<8} ${total_value:<10,.2f} ${total_pnl:<10,.2f}")
    
    # Ask for confirmation
    print(f"\n⚠️  This will close {len(tiny_positions)} positions worth ${total_value:,.2f}")
    print(f"   This will free up {len(tiny_positions)} position slots (max 25)")
    
    confirm = input("\nProceed with cleanup? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Cleanup cancelled")
        return
    
    # Execute cleanup
    print("\n🔄 Closing tiny positions...")
    closed = position_manager.cleanup_tiny_positions(min_value)
    
    print(f"\n✅ Cleanup complete! Closed {closed} positions")
    print(f"   Freed up {closed} position slots for better opportunities")

if __name__ == "__main__":
    main()
