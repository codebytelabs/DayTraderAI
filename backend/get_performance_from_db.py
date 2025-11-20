#!/usr/bin/env python3
"""
Get performance data from Supabase database.
"""
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from supabase import create_client
from alpaca.trading.client import TradingClient

load_dotenv()

# Initialize clients
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

trading_client = TradingClient(
    os.getenv('ALPACA_API_KEY'),
    os.getenv('ALPACA_SECRET_KEY'),
    paper=True
)

def get_daily_metrics():
    """Get daily metrics from database"""
    try:
        # Get metrics from Oct 27 onwards
        response = supabase.table('metrics').select('*').gte(
            'timestamp', '2024-10-27'
        ).order('timestamp', desc=False).execute()
        
        return response.data
    except Exception as e:
        print(f"Error getting metrics: {e}")
        return []

def get_trades_history():
    """Get trade history from database"""
    try:
        response = supabase.table('trades').select('*').gte(
            'entry_time', '2024-10-27'
        ).order('entry_time', desc=False).execute()
        
        return response.data
    except Exception as e:
        print(f"Error getting trades: {e}")
        return []

def generate_report():
    """Generate performance report from database"""
    
    print("\n" + "="*100)
    print("📊 PORTFOLIO PERFORMANCE REPORT - DETAILED ANALYSIS")
    print("="*100)
    print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S ET')}")
    print(f"Period: October 27, 2024 - Present")
    print("="*100)
    
    # Get current account
    account = trading_client.get_account()
    current_equity = float(account.equity)
    
    print(f"\n💰 CURRENT STATUS (as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"   Portfolio Value: ${current_equity:,.2f}")
    print(f"   Cash: ${float(account.cash):,.2f}")
    print(f"   Positions Value: ${current_equity - float(account.cash):,.2f}")
    
    # Get metrics from database
    metrics = get_daily_metrics()
    
    if metrics:
        print(f"\n📊 DAILY PERFORMANCE BREAKDOWN:")
        print(f"   Total Data Points: {len(metrics)}")
        print()
        print(f"{'Date':<12} {'Time':<8} {'Equity':<15} {'Daily Change':<15} {'% Change':<12} {'Positions':<10}")
        print("-" * 100)
        
        # Group by date
        daily_data = {}
        for metric in metrics:
            timestamp = datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00'))
            date_key = timestamp.strftime('%Y-%m-%d')
            
            if date_key not in daily_data:
                daily_data[date_key] = []
            daily_data[date_key].append(metric)
        
        # Calculate daily summaries
        prev_close = None
        daily_summary = []
        
        for date_key in sorted(daily_data.keys()):
            day_metrics = daily_data[date_key]
            
            # Get opening and closing values
            opening = day_metrics[0]['equity']
            closing = day_metrics[-1]['equity']
            positions = day_metrics[-1]['open_positions']
            
            # Calculate change
            if prev_close:
                change = closing - prev_close
                change_pct = (change / prev_close) * 100
            else:
                change = 0
                change_pct = 0
            
            daily_summary.append({
                'date': date_key,
                'opening': opening,
                'closing': closing,
                'change': change,
                'change_pct': change_pct,
                'positions': positions
            })
            
            # Print summary
            print(f"{date_key:<12} {'Close':<8} ${closing:>12,.2f} ${change:>12,.2f} {change_pct:>10.2f}% {positions:>10}")
            
            prev_close = closing
        
        # Overall statistics
        if daily_summary:
            first_day = daily_summary[0]
            last_day = daily_summary[-1]
            
            total_return = last_day['closing'] - first_day['opening']
            total_return_pct = (total_return / first_day['opening']) * 100
            
            # Calculate win/loss days
            win_days = sum(1 for day in daily_summary if day['change'] > 0)
            loss_days = sum(1 for day in daily_summary if day['change'] < 0)
            flat_days = sum(1 for day in daily_summary if day['change'] == 0)
            
            print("\n" + "="*100)
            print("📈 OVERALL STATISTICS:")
            print(f"   Starting Value (Oct 27): ${first_day['opening']:,.2f}")
            print(f"   Current Value: ${last_day['closing']:,.2f}")
            print(f"   Total Return: ${total_return:,.2f} ({total_return_pct:+.2f}%)")
            print(f"   Trading Days: {len(daily_summary)}")
            print(f"   Win Days: {win_days} ({win_days/len(daily_summary)*100:.1f}%)")
            print(f"   Loss Days: {loss_days} ({loss_days/len(daily_summary)*100:.1f}%)")
            print(f"   Flat Days: {flat_days}")
            
            # Best and worst days
            best_day = max(daily_summary, key=lambda x: x['change'])
            worst_day = min(daily_summary, key=lambda x: x['change'])
            
            print(f"\n   Best Day: {best_day['date']} (+${best_day['change']:,.2f}, +{best_day['change_pct']:.2f}%)")
            print(f"   Worst Day: {worst_day['date']} (${worst_day['change']:,.2f}, {worst_day['change_pct']:.2f}%)")
            
            # Average daily return
            avg_daily_return = sum(day['change'] for day in daily_summary) / len(daily_summary)
            avg_daily_return_pct = sum(day['change_pct'] for day in daily_summary) / len(daily_summary)
            
            print(f"   Average Daily Return: ${avg_daily_return:,.2f} ({avg_daily_return_pct:+.2f}%)")
    
    # Get trades
    trades = get_trades_history()
    
    if trades:
        print(f"\n📋 TRADING ACTIVITY:")
        print(f"   Total Trades: {len(trades)}")
        
        # Calculate win rate
        closed_trades = [t for t in trades if t.get('exit_time')]
        if closed_trades:
            winning_trades = [t for t in closed_trades if t.get('pnl', 0) > 0]
            losing_trades = [t for t in closed_trades if t.get('pnl', 0) < 0]
            
            total_pnl = sum(t.get('pnl', 0) for t in closed_trades)
            win_rate = len(winning_trades) / len(closed_trades) * 100
            
            print(f"   Closed Trades: {len(closed_trades)}")
            print(f"   Winning Trades: {len(winning_trades)} ({win_rate:.1f}%)")
            print(f"   Losing Trades: {len(losing_trades)}")
            print(f"   Total P&L from Trades: ${total_pnl:,.2f}")
            
            if winning_trades:
                avg_win = sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades)
                print(f"   Average Win: ${avg_win:,.2f}")
            
            if losing_trades:
                avg_loss = sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades)
                print(f"   Average Loss: ${avg_loss:,.2f}")
    
    print("\n" + "="*100)
    print("📝 NOTES:")
    print("   - Data sourced from Supabase database")
    print("   - Daily changes calculated from closing values")
    print("   - Current value from live Alpaca account")
    print("="*100)

if __name__ == "__main__":
    generate_report()
