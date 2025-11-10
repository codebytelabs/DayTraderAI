"""
Sprint 6 - Day 1: Shadow Mode Monitor
Real-time monitoring of partial profit shadow mode predictions
"""

import os
import sys
import time
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from trading.profit_taker import ProfitTaker
from core.supabase_client import SupabaseClient


def print_header():
    """Print monitor header"""
    print("\n" + "="*80)
    print("  SPRINT 6 - DAY 1: PARTIAL PROFIT SHADOW MODE MONITOR")
    print("  Real-time tracking of shadow predictions")
    print("="*80 + "\n")


def print_status(profit_taker: ProfitTaker):
    """Print current status"""
    health = profit_taker.check_health()
    report = profit_taker.get_shadow_mode_report()
    
    print(f"\n{'='*80}")
    print(f"  STATUS UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    print(f"\n📊 SYSTEM STATUS:")
    print(f"  Enabled: {health['enabled']}")
    print(f"  Shadow Mode: {health['shadow_mode']}")
    print(f"  Status: {health['status']}")
    
    print(f"\n🔮 SHADOW PREDICTIONS:")
    print(f"  Total Predictions: {report.get('total_predictions', 0)}")
    
    if report.get('total_predictions', 0) > 0:
        print(f"  Avg Profit R: +{report['avg_profit_r']:.2f}R")
        print(f"  Avg Profit Amount: ${report['avg_profit_amount']:.2f}")
        print(f"  Symbols Tracked: {report['symbols_tracked']}")
        
        if report.get('most_active_symbols'):
            print(f"\n  Most Active Symbols:")
            for symbol, count in report['most_active_symbols'][:3]:
                print(f"    • {symbol}: {count} predictions")
        
        if report.get('latest_predictions'):
            print(f"\n  Latest Predictions:")
            for pred in report['latest_predictions'][-3:]:
                print(f"    • {pred['symbol']}: +{pred['profit_r']:.2f}R @ {pred['timestamp']}")
    else:
        print("  No predictions yet (waiting for +1R positions)")
    
    if health.get('warnings'):
        print(f"\n⚠️  WARNINGS:")
        for warning in health['warnings']:
            print(f"  • {warning}")
    
    if health.get('issues'):
        print(f"\n❌ ISSUES:")
        for issue in health['issues']:
            print(f"  • {issue}")
    
    print(f"\n{'='*80}\n")


def monitor_loop():
    """Main monitoring loop"""
    print_header()
    
    print("Initializing...")
    supabase = SupabaseClient()
    profit_taker = ProfitTaker(supabase)
    
    print("✓ Profit Taker initialized")
    print("✓ Shadow mode active")
    print("\nMonitoring shadow predictions (Ctrl+C to stop)...\n")
    
    last_prediction_count = 0
    
    try:
        while True:
            # Get current report
            report = profit_taker.get_shadow_mode_report()
            current_count = report.get('total_predictions', 0)
            
            # Check for new predictions
            if current_count > last_prediction_count:
                new_predictions = current_count - last_prediction_count
                print(f"\n🔔 NEW SHADOW PREDICTIONS: {new_predictions}")
                
                # Show latest predictions
                if report.get('latest_predictions'):
                    for pred in report['latest_predictions'][-new_predictions:]:
                        print(f"  • {pred['symbol']}: +{pred['profit_r']:.2f}R")
                        print(f"    Would sell {pred['percentage']*100:.0f}% @ ${pred.get('profit_amount', 0):.2f}")
                
                last_prediction_count = current_count
            
            # Print status every 5 minutes
            if int(time.time()) % 300 == 0:
                print_status(profit_taker)
            
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        print_status(profit_taker)
        
        print("\n📋 FINAL SUMMARY:")
        print(f"  Total shadow predictions: {last_prediction_count}")
        print("  Review logs for detailed analysis")
        print("\n✓ Monitor shutdown complete\n")


if __name__ == "__main__":
    monitor_loop()
