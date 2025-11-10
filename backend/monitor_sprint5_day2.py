"""
Sprint 5 - Day 2: Real-time Monitoring Script
Monitor trailing stops during live trading
"""

import os
import sys
import time
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from trading.position_manager import PositionManager


def print_header():
    """Print monitoring header"""
    os.system('clear' if os.name == 'posix' else 'cls')
    print("="*80)
    print("  SPRINT 5 - DAY 2: TRAILING STOPS MONITOR")
    print("  Limited Test (2 Positions)")
    print("="*80)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")


def monitor_trailing_stops():
    """Monitor trailing stops in real-time"""
    
    # Initialize clients
    alpaca = AlpacaClient()
    supabase = SupabaseClient()
    pos_manager = PositionManager(alpaca, supabase)
    
    trailing_manager = pos_manager.trailing_stop_manager
    
    print_header()
    
    # Configuration
    print("📋 CONFIGURATION:")
    print(f"  Enabled: {trailing_manager.enabled}")
    print(f"  Max Positions: {trailing_manager.max_positions}")
    print(f"  Activation: +{trailing_manager.activation_threshold}R")
    print(f"  Distance: {trailing_manager.trailing_distance_r}R")
    print(f"  Use ATR: {trailing_manager.use_atr}")
    
    # Health check
    print("\n🏥 HEALTH CHECK:")
    health = trailing_manager.check_health()
    print(f"  Status: {health['status']}")
    print(f"  Active Trailing Stops: {health['active_trailing_stops']}/{health['config']['max_positions']}")
    
    if health.get('issues'):
        print(f"  ⚠️  Issues: {health['issues']}")
    
    if health.get('warnings'):
        print(f"  ⚠️  Warnings: {health['warnings']}")
    
    # Active trailing stops
    print("\n📊 ACTIVE TRAILING STOPS:")
    active_stops = trailing_manager.get_active_trailing_stops()
    
    if not active_stops:
        print("  No active trailing stops yet")
        print("  (Waiting for positions to reach +2R profit)")
    else:
        for symbol, data in active_stops.items():
            print(f"\n  {symbol}:")
            print(f"    Activated: {data.get('activated_at', 'N/A')}")
            print(f"    Initial Stop: ${data.get('initial_stop', 0):.2f}")
            print(f"    Current Stop: ${data.get('current_stop', 0):.2f}")
            print(f"    Updates: {data.get('updates', 0)}")
            if 'last_update' in data:
                print(f"    Last Update: {data['last_update']}")
    
    # Current positions
    print("\n💼 CURRENT POSITIONS:")
    from core.state import trading_state
    positions = trading_state.get_all_positions()
    
    if not positions:
        print("  No open positions")
    else:
        for pos in positions:
            # Calculate R
            if pos.side == 'buy':
                r = pos.avg_entry_price - pos.stop_loss
                profit_r = (pos.current_price - pos.avg_entry_price) / r if r > 0 else 0
            else:
                r = pos.stop_loss - pos.avg_entry_price
                profit_r = (pos.avg_entry_price - pos.current_price) / r if r > 0 else 0
            
            # Check if has trailing stop
            has_trailing = pos.symbol in active_stops
            trailing_indicator = "🎯" if has_trailing else "  "
            
            print(f"\n  {trailing_indicator} {pos.symbol}:")
            print(f"    Entry: ${pos.avg_entry_price:.2f}")
            print(f"    Current: ${pos.current_price:.2f}")
            print(f"    Stop: ${pos.stop_loss:.2f}")
            print(f"    P/L: ${pos.unrealized_pl:.2f} ({pos.unrealized_pl_pct:.2f}%)")
            print(f"    Profit: {profit_r:+.2f}R")
            
            if has_trailing:
                print(f"    ✓ Trailing stop ACTIVE")
            elif profit_r >= trailing_manager.activation_threshold:
                print(f"    ⏳ Ready for trailing stop (at +{profit_r:.2f}R)")
            else:
                needed = trailing_manager.activation_threshold - profit_r
                print(f"    ⏸️  Need +{needed:.2f}R more for trailing stop")
    
    # Statistics
    print("\n📈 STATISTICS:")
    print(f"  Total Positions: {len(positions)}")
    print(f"  With Trailing Stops: {len(active_stops)}/{trailing_manager.max_positions}")
    print(f"  Available Slots: {max(0, trailing_manager.max_positions - len(active_stops))}")
    
    # Instructions
    print("\n" + "="*80)
    print("  Press Ctrl+C to exit")
    print("  Refreshing every 10 seconds...")
    print("="*80)


def main():
    """Main monitoring loop"""
    try:
        while True:
            try:
                monitor_trailing_stops()
                time.sleep(10)  # Refresh every 10 seconds
            except KeyboardInterrupt:
                print("\n\n👋 Monitoring stopped")
                break
            except Exception as e:
                print(f"\n⚠️  Error: {e}")
                print("Retrying in 10 seconds...")
                time.sleep(10)
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped")


if __name__ == "__main__":
    print("\n🚀 Starting Sprint 5 - Day 2 Monitor...")
    print("   This will monitor trailing stops in real-time")
    print("   Press Ctrl+C to stop\n")
    time.sleep(2)
    main()
