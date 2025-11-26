#!/usr/bin/env python3
"""
Simple daily trend analysis showing improvement over time
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

def main():
    """Main execution"""
    print("🤖 Daily Performance Trend Analysis\n")
    
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY')
    trading_client = TradingClient(api_key, api_secret, paper=True)
    
    start_date = datetime(2025, 11, 4)
    
    # Get all orders
    request = GetOrdersRequest(
        status=QueryOrderStatus.ALL,
        after=start_date,
        limit=500
    )
    orders = trading_client.get_orders(filter=request)
    
    # Group by date
    daily_orders = defaultdict(list)
    for order in orders:
        if order.status == 'filled' and order.filled_at:
            date_key = order.filled_at.date()
            daily_orders[date_key].append(order)
    
    # Analyze each day
    print("="*80)
    print("📅 DAILY TRADING ACTIVITY (Nov 4 - Today)")
    print("="*80)
    
    sorted_dates = sorted(daily_orders.keys())
    
    for date in sorted_dates:
        day_orders = daily_orders[date]
        buys = sum(1 for o in day_orders if o.side == OrderSide.BUY)
        sells = sum(1 for o in day_orders if o.side == OrderSide.SELL)
        
        day_name = date.strftime('%A')
        print(f"\n{date} ({day_name})")
        print(f"  Orders: {len(day_orders)} | Buys: {buys} | Sells: {sells}")
        
        # Show some symbols
        symbols = list(set(o.symbol for o in day_orders[:10]))
        print(f"  Symbols: {', '.join(symbols[:8])}")
    
    # Calculate win rate by period
    print("\n" + "="*80)
    print("📊 WIN RATE TREND ANALYSIS")
    print("="*80)
    
    # Match buys to sells for P&L
    trades_by_symbol = defaultdict(lambda: {'buys': [], 'sells': []})
    
    for order in orders:
        if order.status == 'filled' and order.filled_at:
            symbol = order.symbol
            if order.side == OrderSide.BUY:
                trades_by_symbol[symbol]['buys'].append({
                    'qty': float(order.filled_qty),
                    'price': float(order.filled_avg_price),
                    'date': order.filled_at.date()
                })
            else:
                trades_by_symbol[symbol]['sells'].append({
                    'qty': float(order.filled_qty),
                    'price': float(order.filled_avg_price),
                    'date': order.filled_at.date()
                })
    
    # Calculate completed trades
    completed_trades = []
    for symbol, data in trades_by_symbol.items():
        for sell in data['sells']:
            if data['buys']:
                buy = data['buys'][0]
                pnl = (sell['price'] - buy['price']) * sell['qty']
                completed_trades.append({
                    'symbol': symbol,
                    'date': sell['date'],
                    'pnl': pnl,
                    'is_win': pnl > 0
                })
    
    # Group by week
    if completed_trades:
        # Sort by date
        completed_trades.sort(key=lambda x: x['date'])
        
        # Split into periods
        total_days = (sorted_dates[-1] - sorted_dates[0]).days + 1
        
        if total_days >= 14:
            # First week vs last week
            mid_date = sorted_dates[0] + timedelta(days=7)
            
            first_week = [t for t in completed_trades if t['date'] < mid_date]
            last_week = [t for t in completed_trades if t['date'] >= mid_date]
            
            if first_week:
                fw_wins = sum(1 for t in first_week if t['is_win'])
                fw_total = len(first_week)
                fw_wr = (fw_wins / fw_total * 100) if fw_total > 0 else 0
                fw_pnl = sum(t['pnl'] for t in first_week)
                
                print(f"\n📅 First Week (Nov 4-10):")
                print(f"  Trades: {fw_total} | Wins: {fw_wins} | Win Rate: {fw_wr:.1f}%")
                print(f"  Net P&L: ${fw_pnl:+.2f}")
            
            if last_week:
                lw_wins = sum(1 for t in last_week if t['is_win'])
                lw_total = len(last_week)
                lw_wr = (lw_wins / lw_total * 100) if lw_total > 0 else 0
                lw_pnl = sum(t['pnl'] for t in last_week)
                
                print(f"\n📅 Recent Week (Nov 11+):")
                print(f"  Trades: {lw_total} | Wins: {lw_wins} | Win Rate: {lw_wr:.1f}%")
                print(f"  Net P&L: ${lw_pnl:+.2f}")
                
                if first_week:
                    print(f"\n📈 IMPROVEMENT:")
                    print(f"  Win Rate: {lw_wr - fw_wr:+.1f}% {'✅ BETTER' if lw_wr > fw_wr else '⚠️ WORSE'}")
                    print(f"  P&L: ${lw_pnl - fw_pnl:+.2f} {'✅ BETTER' if lw_pnl > fw_pnl else '⚠️ WORSE'}")
        
        # Overall stats
        total_wins = sum(1 for t in completed_trades if t['is_win'])
        total_trades = len(completed_trades)
        overall_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0
        overall_pnl = sum(t['pnl'] for t in completed_trades)
        
        print(f"\n📊 OVERALL (Nov 4 - Today):")
        print(f"  Total Trades: {total_trades}")
        print(f"  Wins: {total_wins} ({overall_wr:.1f}%)")
        print(f"  Losses: {total_trades - total_wins} ({100-overall_wr:.1f}%)")
        print(f"  Net P&L: ${overall_pnl:+.2f}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
