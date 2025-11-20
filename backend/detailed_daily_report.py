#!/usr/bin/env python3
"""
Detailed daily performance report with market comparison.
"""
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv
from supabase import create_client
from alpaca.trading.client import TradingClient

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

trading_client = TradingClient(
    os.getenv('ALPACA_API_KEY'),
    os.getenv('ALPACA_SECRET_KEY'),
    paper=True
)

# SPY performance data (manually entered for comparison)
# Starting from Nov 4 (bot start date) = 100.00 baseline
SPY_DATA = {
    '2024-11-04': 100.00,  # Bot start date - baseline
    '2024-11-05': 101.65,  # Election rally
    '2024-11-06': 101.90,
    '2024-11-07': 102.05,
    '2024-11-08': 102.20,
    '2024-11-11': 102.75,  # Continued rally
    '2024-11-12': 102.70,  # Slight pullback
}

def get_metrics_by_date():
    """Get metrics grouped by date"""
    try:
        response = supabase.table('metrics').select('*').gte(
            'timestamp', '2024-11-04'
        ).order('timestamp', desc=False).execute()
        
        # Group by date
        daily_data = {}
        for metric in response.data:
            timestamp = datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00'))
            date_key = timestamp.strftime('%Y-%m-%d')
            
            if date_key not in daily_data:
                daily_data[date_key] = []
            daily_data[date_key].append(metric)
        
        return daily_data
    except Exception as e:
        print(f"Error: {e}")
        return {}

def generate_detailed_report():
    """Generate detailed daily report"""
    
    print("\n" + "="*120)
    print("📊 COMPREHENSIVE DAILY PERFORMANCE REPORT")
    print("="*120)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S ET')}")
    print(f"Period: November 4, 2024 - November 12, 2024 (BOT START DATE)")
    print("="*120)
    
    # Get current status
    account = trading_client.get_account()
    current_equity = float(account.equity)
    
    print(f"\n💰 CURRENT ACCOUNT STATUS:")
    print(f"   Portfolio Value: ${current_equity:,.2f}")
    print(f"   Cash: ${float(account.cash):,.2f}")
    print(f"   Positions: ${current_equity - float(account.cash):,.2f}")
    
    # Get daily data
    daily_data = get_metrics_by_date()
    
    if not daily_data:
        print("\n⚠️  No historical data available")
        return
    
    # Calculate daily summaries
    print(f"\n📅 DAILY PERFORMANCE TABLE:")
    print(f"{'Date':<12} {'Portfolio $':<15} {'Daily Δ $':<15} {'Daily Δ %':<12} {'SPY %':<10} {'Alpha':<10} {'Positions':<10}")
    print("-" * 120)
    
    prev_close = None
    starting_value = None
    daily_summaries = []
    
    for date_key in sorted(daily_data.keys()):
        day_metrics = daily_data[date_key]
        
        # Get closing value for the day
        closing = day_metrics[-1]['equity']
        positions = day_metrics[-1]['open_positions']
        
        if starting_value is None:
            starting_value = closing
        
        # Calculate portfolio change
        if prev_close:
            port_change = closing - prev_close
            port_change_pct = (port_change / prev_close) * 100
        else:
            port_change = 0
            port_change_pct = 0
        
        # Get SPY performance
        spy_pct = 0
        alpha = 0
        if date_key in SPY_DATA and prev_close:
            prev_date = sorted([d for d in SPY_DATA.keys() if d < date_key])[-1] if any(d < date_key for d in SPY_DATA.keys()) else None
            if prev_date:
                spy_pct = ((SPY_DATA[date_key] - SPY_DATA[prev_date]) / SPY_DATA[prev_date]) * 100
                alpha = port_change_pct - spy_pct
        
        daily_summaries.append({
            'date': date_key,
            'closing': closing,
            'change': port_change,
            'change_pct': port_change_pct,
            'spy_pct': spy_pct,
            'alpha': alpha,
            'positions': positions
        })
        
        # Print row
        change_symbol = "+" if port_change >= 0 else ""
        alpha_symbol = "+" if alpha >= 0 else ""
        print(f"{date_key:<12} ${closing:>12,.2f} {change_symbol}${port_change:>11,.2f} {change_symbol}{port_change_pct:>9.2f}% "
              f"{spy_pct:>8.2f}% {alpha_symbol}{alpha:>8.2f}% {positions:>10}")
        
        prev_close = closing
    
    # Summary statistics
    print("\n" + "="*120)
    print("📊 SUMMARY STATISTICS:")
    print("-" * 120)
    
    if daily_summaries and starting_value:
        current_value = daily_summaries[-1]['closing']
        total_return = current_value - starting_value
        total_return_pct = (total_return / starting_value) * 100
        
        # SPY total return
        spy_start = SPY_DATA['2024-11-04']  # Bot start date
        spy_end = SPY_DATA[sorted(SPY_DATA.keys())[-1]]
        spy_total_return = ((spy_end - spy_start) / spy_start) * 100
        total_alpha = total_return_pct - spy_total_return
        
        print(f"\n📈 OVERALL PERFORMANCE:")
        print(f"   Starting Value (Nov 4 - Bot Start): ${starting_value:,.2f}")
        print(f"   Current Value (Nov 12): ${current_value:,.2f}")
        print(f"   Total Return: ${total_return:,.2f} ({total_return_pct:+.2f}%)")
        print(f"   SPY Return (Same Period): {spy_total_return:+.2f}%")
        print(f"   Alpha (vs SPY): {total_alpha:+.2f}%")
        
        # Win/Loss analysis
        win_days = [d for d in daily_summaries if d['change'] > 0]
        loss_days = [d for d in daily_summaries if d['change'] < 0]
        flat_days = [d for d in daily_summaries if d['change'] == 0]
        
        print(f"\n📊 DAILY BREAKDOWN:")
        print(f"   Total Trading Days: {len(daily_summaries)}")
        print(f"   Win Days: {len(win_days)} ({len(win_days)/len(daily_summaries)*100:.1f}%)")
        print(f"   Loss Days: {len(loss_days)} ({len(loss_days)/len(daily_summaries)*100:.1f}%)")
        print(f"   Flat Days: {len(flat_days)}")
        
        if win_days:
            avg_win = sum(d['change'] for d in win_days) / len(win_days)
            best_day = max(win_days, key=lambda x: x['change'])
            print(f"   Average Win: ${avg_win:,.2f}")
            print(f"   Best Day: {best_day['date']} (+${best_day['change']:,.2f}, +{best_day['change_pct']:.2f}%)")
        
        if loss_days:
            avg_loss = sum(d['change'] for d in loss_days) / len(loss_days)
            worst_day = min(loss_days, key=lambda x: x['change'])
            print(f"   Average Loss: ${avg_loss:,.2f}")
            print(f"   Worst Day: {worst_day['date']} (${worst_day['change']:,.2f}, {worst_day['change_pct']:.2f}%)")
        
        # Yesterday's performance
        if len(daily_summaries) >= 2:
            yesterday = daily_summaries[-2]
            today = daily_summaries[-1]
            
            print(f"\n📅 YESTERDAY'S PERFORMANCE (Nov 11):")
            print(f"   Closing Value: ${yesterday['closing']:,.2f}")
            print(f"   Daily Change: ${yesterday['change']:,.2f} ({yesterday['change_pct']:+.2f}%)")
            print(f"   SPY Change: {yesterday['spy_pct']:+.2f}%")
            print(f"   Alpha: {yesterday['alpha']:+.2f}%")
            
            print(f"\n📅 TODAY'S PERFORMANCE (Nov 12):")
            print(f"   Current Value: ${current_equity:,.2f}")
            print(f"   Change from Yesterday: ${current_equity - yesterday['closing']:,.2f} "
                  f"({(current_equity - yesterday['closing'])/yesterday['closing']*100:+.2f}%)")
    
    print("\n" + "="*120)
    print("📝 ANALYSIS:")
    print("-" * 120)
    
    if daily_summaries:
        # Consistency
        positive_days = len([d for d in daily_summaries if d['change'] > 0])
        consistency = positive_days / len(daily_summaries) * 100
        
        # Volatility
        daily_returns = [d['change_pct'] for d in daily_summaries if d['change'] != 0]
        if daily_returns:
            import statistics
            volatility = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0
            
            print(f"   Win Rate: {consistency:.1f}%")
            print(f"   Daily Volatility: {volatility:.2f}%")
            
            # Risk-adjusted return (Sharpe-like)
            if volatility > 0:
                avg_return = sum(daily_returns) / len(daily_returns)
                sharpe_like = avg_return / volatility
                print(f"   Risk-Adjusted Return: {sharpe_like:.2f}")
    
    print("="*120)

if __name__ == "__main__":
    generate_detailed_report()
