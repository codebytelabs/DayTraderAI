#!/usr/bin/env python3
"""
Weekly and daily performance analysis to show improvement trend
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus
from dotenv import load_dotenv

load_dotenv()

def get_orders_by_week(trading_client, start_date):
    """Get all orders and group by week"""
    try:
        request = GetOrdersRequest(
            status=QueryOrderStatus.ALL,
            after=start_date,
            limit=500
        )
        orders = trading_client.get_orders(filter=request)
        return orders
    except Exception as e:
        print(f"Error getting orders: {e}")
        return []

def analyze_by_period(orders, start_date):
    """Analyze trades by week and by day"""
    
    # Group trades by symbol first
    trades = {}
    for order in orders:
        if order.status == 'filled' and order.filled_at:
            symbol = order.symbol
            if symbol not in trades:
                trades[symbol] = {'buys': [], 'sells': []}
            
            if order.side == OrderSide.BUY:
                trades[symbol]['buys'].append({
                    'qty': float(order.filled_qty),
                    'price': float(order.filled_avg_price),
                    'time': order.filled_at
                })
            else:
                trades[symbol]['sells'].append({
                    'qty': float(order.filled_qty),
                    'price': float(order.filled_avg_price),
                    'time': order.filled_at
                })
    
    # Calculate P&L for each completed trade (matched buy/sell)
    completed_trades = []
    
    for symbol, data in trades.items():
        buys = sorted(data['buys'], key=lambda x: x['time'])
        sells = sorted(data['sells'], key=lambda x: x['time'])
        
        # Match sells to buys (FIFO)
        for sell in sells:
            if buys:
                buy = buys[0]
                qty = min(sell['qty'], buy['qty'])
                
                pnl = (sell['price'] - buy['price']) * qty
                pnl_pct = ((sell['price'] - buy['price']) / buy['price']) * 100
                
                completed_trades.append({
                    'symbol': symbol,
                    'date': sell['time'].date(),
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'is_win': pnl > 0
                })
                
                # Update quantities
                buy['qty'] -= qty
                sell['qty'] -= qty
                
                if buy['qty'] <= 0:
                    buys.pop(0)
    
    # Group by week
    weekly_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0, 'trades': []})
    daily_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0, 'trades': []})
    
    for trade in completed_trades:
        trade_date = trade['date']
        
        # Calculate week number
        week_start = trade_date - timedelta(days=trade_date.weekday())
        week_key = week_start.strftime('%Y-%m-%d')
        
        # Daily stats
        day_key = trade_date.strftime('%Y-%m-%d')
        daily_stats[day_key]['trades'].append(trade)
        daily_stats[day_key]['pnl'] += trade['pnl']
        if trade['is_win']:
            daily_stats[day_key]['wins'] += 1
        else:
            daily_stats[day_key]['losses'] += 1
        
        # Weekly stats
        weekly_stats[week_key]['trades'].append(trade)
        weekly_stats[week_key]['pnl'] += trade['pnl']
        if trade['is_win']:
            weekly_stats[week_key]['wins'] += 1
        else:
            weekly_stats[week_key]['losses'] += 1
    
    return weekly_stats, daily_stats, completed_trades

def print_report(weekly_stats, daily_stats):
    """Print beautiful weekly and daily report"""
    
    print("\n" + "="*80)
    print("📊 WEEKLY PERFORMANCE TREND ANALYSIS")
    print("="*80)
    
    sorted_weeks = sorted(weekly_stats.keys())
    
    for i, week in enumerate(sorted_weeks, 1):
        stats = weekly_stats[week]
        total = stats['wins'] + stats['losses']
        win_rate = (stats['wins'] / total * 100) if total > 0 else 0
        
        week_end = datetime.strptime(week, '%Y-%m-%d') + timedelta(days=6)
        
        print(f"\n┌{'─'*78}┐")
        print(f"│ 📅 Week {i}: {week} to {week_end.strftime('%Y-%m-%d')}{' '*30}│")
        print(f"├{'─'*78}┤")
        print(f"│  Total Trades:    {total:2d}                                                      │")
        print(f"│  Wins:            {stats['wins']:2d} ({win_rate:5.1f}%)                                           │")
        print(f"│  Losses:          {stats['losses']:2d} ({(100-win_rate):5.1f}%)                                           │")
        print(f"│  Net P&L:         ${stats['pnl']:+8.2f}                                              │")
        
        # Show trend
        if i > 1:
            prev_week = sorted_weeks[i-2]
            prev_stats = weekly_stats[prev_week]
            prev_total = prev_stats['wins'] + prev_stats['losses']
            prev_win_rate = (prev_stats['wins'] / prev_total * 100) if prev_total > 0 else 0
            
            win_rate_change = win_rate - prev_win_rate
            pnl_change = stats['pnl'] - prev_stats['pnl']
            
            trend = "📈" if win_rate_change > 0 else "📉" if win_rate_change < 0 else "➡️"
            print(f"│  {trend} Win Rate Change: {win_rate_change:+5.1f}%                                              │")
            print(f"│  {'💰' if pnl_change > 0 else '💸'} P&L Change:      ${pnl_change:+8.2f}                                              │")
        
        print(f"└{'─'*78}┘")
    
    # Last 7 days detailed
    print("\n" + "="*80)
    print("📅 LAST 7 DAYS - DAILY BREAKDOWN")
    print("="*80)
    
    sorted_days = sorted(daily_stats.keys())
    last_7_days = sorted_days[-7:] if len(sorted_days) >= 7 else sorted_days
    
    for day in last_7_days:
        stats = daily_stats[day]
        total = stats['wins'] + stats['losses']
        win_rate = (stats['wins'] / total * 100) if total > 0 else 0
        
        day_name = datetime.strptime(day, '%Y-%m-%d').strftime('%A')
        
        print(f"\n  {day} ({day_name})")
        print(f"  {'─'*50}")
        print(f"  Trades: {total} | Wins: {stats['wins']} ({win_rate:.1f}%) | Losses: {stats['losses']} | P&L: ${stats['pnl']:+.2f}")
        
        if stats['trades']:
            print(f"  Symbols: {', '.join([t['symbol'] for t in stats['trades']])}")
    
    # Calculate improvement metrics
    print("\n" + "="*80)
    print("📈 IMPROVEMENT ANALYSIS")
    print("="*80)
    
    if len(sorted_weeks) >= 2:
        # Compare first week vs last week
        first_week = weekly_stats[sorted_weeks[0]]
        last_week = weekly_stats[sorted_weeks[-1]]
        
        first_total = first_week['wins'] + first_week['losses']
        last_total = last_week['wins'] + last_week['losses']
        
        first_wr = (first_week['wins'] / first_total * 100) if first_total > 0 else 0
        last_wr = (last_week['wins'] / last_total * 100) if last_total > 0 else 0
        
        print(f"\n  First Week (Week 1):")
        print(f"    Win Rate: {first_wr:.1f}% | P&L: ${first_week['pnl']:+.2f}")
        
        print(f"\n  Latest Week (Week {len(sorted_weeks)}):")
        print(f"    Win Rate: {last_wr:.1f}% | P&L: ${last_week['pnl']:+.2f}")
        
        print(f"\n  📊 Improvement:")
        print(f"    Win Rate: {last_wr - first_wr:+.1f}% {'✅ IMPROVED' if last_wr > first_wr else '⚠️ DECLINED'}")
        print(f"    P&L: ${last_week['pnl'] - first_week['pnl']:+.2f} {'✅ IMPROVED' if last_week['pnl'] > first_week['pnl'] else '⚠️ DECLINED'}")
    
    # Last 7 days vs previous 7 days
    if len(sorted_days) >= 14:
        last_7 = sorted_days[-7:]
        prev_7 = sorted_days[-14:-7]
        
        last_7_wins = sum(daily_stats[d]['wins'] for d in last_7)
        last_7_total = sum(daily_stats[d]['wins'] + daily_stats[d]['losses'] for d in last_7)
        last_7_wr = (last_7_wins / last_7_total * 100) if last_7_total > 0 else 0
        last_7_pnl = sum(daily_stats[d]['pnl'] for d in last_7)
        
        prev_7_wins = sum(daily_stats[d]['wins'] for d in prev_7)
        prev_7_total = sum(daily_stats[d]['wins'] + daily_stats[d]['losses'] for d in prev_7)
        prev_7_wr = (prev_7_wins / prev_7_total * 100) if prev_7_total > 0 else 0
        prev_7_pnl = sum(daily_stats[d]['pnl'] for d in prev_7)
        
        print(f"\n  Last 7 Days vs Previous 7 Days:")
        print(f"    Previous 7: {prev_7_wr:.1f}% win rate | ${prev_7_pnl:+.2f} P&L")
        print(f"    Last 7:     {last_7_wr:.1f}% win rate | ${last_7_pnl:+.2f} P&L")
        print(f"    Change:     {last_7_wr - prev_7_wr:+.1f}% {'✅ IMPROVED' if last_7_wr > prev_7_wr else '⚠️ DECLINED'}")
    
    print("\n" + "="*80)

def main():
    """Main execution"""
    print("🤖 Analyzing Weekly Performance Trend...\n")
    
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY')
    trading_client = TradingClient(api_key, api_secret, paper=True)
    
    start_date = datetime(2025, 11, 4)
    
    print(f"📅 Analyzing from: {start_date.strftime('%Y-%m-%d')}")
    print("📈 Fetching order history...")
    
    orders = get_orders_by_week(trading_client, start_date)
    print(f"   Found {len(orders)} orders")
    
    print("\n🔍 Analyzing performance trends...")
    weekly_stats, daily_stats, completed_trades = analyze_by_period(orders, start_date)
    
    print_report(weekly_stats, daily_stats)
    
    print("\n💾 Analysis complete!")

if __name__ == "__main__":
    main()
