#!/usr/bin/env python3
"""
Deep dive analysis: Why 70% win rate but only 0.04% return?
This is the critical question - high win rate but low returns
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

def analyze_position_sizing_impact(orders):
    """Analyze if position sizing is the issue"""
    
    trades_by_symbol = defaultdict(lambda: {'buys': [], 'sells': []})
    
    for order in orders:
        if order.status == 'filled' and order.filled_at:
            symbol = order.symbol
            if order.side == OrderSide.BUY:
                trades_by_symbol[symbol]['buys'].append({
                    'qty': float(order.filled_qty),
                    'price': float(order.filled_avg_price),
                    'value': float(order.filled_qty) * float(order.filled_avg_price),
                    'date': order.filled_at.date()
                })
            else:
                trades_by_symbol[symbol]['sells'].append({
                    'qty': float(order.filled_qty),
                    'price': float(order.filled_avg_price),
                    'value': float(order.filled_qty) * float(order.filled_avg_price),
                    'date': order.filled_at.date()
                })
    
    # Calculate trade details
    trade_details = []
    
    for symbol, data in trades_by_symbol.items():
        for sell in data['sells']:
            if data['buys']:
                buy = data['buys'][0]
                
                pnl = (sell['price'] - buy['price']) * sell['qty']
                pnl_pct = ((sell['price'] - buy['price']) / buy['price']) * 100
                position_size = buy['value']
                
                trade_details.append({
                    'symbol': symbol,
                    'date': sell['date'],
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'position_size': position_size,
                    'is_win': pnl > 0
                })
    
    return trade_details

def main():
    """Main analysis"""
    print("="*80)
    print("🔍 STRATEGY DEEP DIVE: Win Rate vs Returns Paradox")
    print("="*80)
    print("\n❓ THE QUESTION:")
    print("   Why 70% win rate but only 0.04% return when market did 0.9%?")
    print("="*80)
    
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY')
    trading_client = TradingClient(api_key, api_secret, paper=True)
    
    # Get last 2 days of orders
    two_days_ago = datetime.now() - timedelta(days=2)
    
    request = GetOrdersRequest(
        status=QueryOrderStatus.ALL,
        after=two_days_ago,
        limit=500
    )
    orders = trading_client.get_orders(filter=request)
    
    print(f"\n📊 Analyzing last 2 days ({len(orders)} orders)...")
    
    # Analyze trades
    trade_details = analyze_position_sizing_impact(orders)
    
    if not trade_details:
        print("\n⚠️  No completed trades found in last 2 days")
        return
    
    # Calculate stats
    wins = [t for t in trade_details if t['is_win']]
    losses = [t for t in trade_details if not t['is_win']]
    
    total_trades = len(trade_details)
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
    
    # Position sizing analysis
    avg_win_size = sum(t['position_size'] for t in wins) / len(wins) if wins else 0
    avg_loss_size = sum(t['position_size'] for t in losses) / len(losses) if losses else 0
    
    avg_win_pnl = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
    avg_loss_pnl = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
    
    avg_win_pct = sum(t['pnl_pct'] for t in wins) / len(wins) if wins else 0
    avg_loss_pct = sum(t['pnl_pct'] for t in losses) / len(losses) if losses else 0
    
    total_pnl = sum(t['pnl'] for t in trade_details)
    
    print("\n" + "="*80)
    print("📈 LAST 2 DAYS PERFORMANCE")
    print("="*80)
    
    print(f"\n  Total Trades: {total_trades}")
    print(f"  Wins: {len(wins)} ({win_rate:.1f}%)")
    print(f"  Losses: {len(losses)} ({100-win_rate:.1f}%)")
    print(f"  Net P&L: ${total_pnl:+,.2f}")
    
    print("\n" + "="*80)
    print("🔍 ROOT CAUSE ANALYSIS")
    print("="*80)
    
    print(f"\n1️⃣  POSITION SIZING:")
    print(f"   Average Win Position:  ${avg_win_size:,.2f}")
    print(f"   Average Loss Position: ${avg_loss_size:,.2f}")
    
    if avg_win_size < avg_loss_size:
        print(f"   ⚠️  ISSUE: Wins are SMALLER than losses!")
        print(f"   📊 Ratio: {avg_win_size/avg_loss_size:.2f}x (should be >1.0)")
    
    print(f"\n2️⃣  PROFIT/LOSS MAGNITUDE:")
    print(f"   Average Win:  ${avg_win_pnl:+,.2f} ({avg_win_pct:+.2f}%)")
    print(f"   Average Loss: ${avg_loss_pnl:+,.2f} ({avg_loss_pct:+.2f}%)")
    print(f"   Win/Loss Ratio: {abs(avg_win_pnl/avg_loss_pnl) if avg_loss_pnl != 0 else 0:.2f}x")
    
    if abs(avg_win_pnl) < abs(avg_loss_pnl):
        print(f"   ⚠️  ISSUE: Average win (${avg_win_pnl:.2f}) < Average loss (${avg_loss_pnl:.2f})")
    
    print(f"\n3️⃣  EXPECTANCY ANALYSIS:")
    expectancy = (win_rate/100 * avg_win_pnl) + ((100-win_rate)/100 * avg_loss_pnl)
    print(f"   Expectancy per trade: ${expectancy:+,.2f}")
    
    if expectancy < 10:
        print(f"   ⚠️  ISSUE: Low expectancy! Need ${10-expectancy:.2f} more per trade")
    
    print(f"\n4️⃣  DETAILED TRADE BREAKDOWN:")
    print(f"   {'Symbol':<8} {'Date':<12} {'Size':<12} {'P&L':<12} {'%':<8} {'Result'}")
    print(f"   {'-'*70}")
    
    for trade in sorted(trade_details, key=lambda x: x['date'], reverse=True)[:20]:
        result = "✅ WIN" if trade['is_win'] else "❌ LOSS"
        print(f"   {trade['symbol']:<8} {str(trade['date']):<12} ${trade['position_size']:>10,.0f} ${trade['pnl']:>10,.2f} {trade['pnl_pct']:>6.2f}% {result}")
    
    print("\n" + "="*80)
    print("💡 DIAGNOSIS")
    print("="*80)
    
    issues = []
    
    # Check position sizing
    if avg_win_size < avg_loss_size * 0.8:
        issues.append({
            'severity': 'HIGH',
            'issue': 'Position Sizing Imbalance',
            'detail': f'Wins are {avg_win_size/avg_loss_size:.1%} the size of losses',
            'impact': 'Even with 70% win rate, small wins can\'t offset large losses',
            'fix': 'Increase position size on high-confidence trades'
        })
    
    # Check win/loss magnitude
    if abs(avg_win_pnl) < abs(avg_loss_pnl) * 0.8:
        issues.append({
            'severity': 'HIGH',
            'issue': 'Win/Loss Magnitude Problem',
            'detail': f'Average win ${avg_win_pnl:.2f} vs average loss ${avg_loss_pnl:.2f}',
            'impact': 'Wins are too small relative to losses',
            'fix': 'Let winners run longer, cut losers faster'
        })
    
    # Check if taking profits too early
    if avg_win_pct < 1.0 and abs(avg_loss_pct) > 1.0:
        issues.append({
            'severity': 'MEDIUM',
            'issue': 'Taking Profits Too Early',
            'detail': f'Avg win {avg_win_pct:.2f}% vs avg loss {avg_loss_pct:.2f}%',
            'impact': 'Not letting winners run enough',
            'fix': 'Widen profit targets, use trailing stops'
        })
    
    # Check expectancy
    if expectancy < 5:
        issues.append({
            'severity': 'HIGH',
            'issue': 'Low Expectancy',
            'detail': f'Only ${expectancy:.2f} per trade',
            'impact': 'Strategy barely profitable despite high win rate',
            'fix': 'Need bigger wins or smaller losses'
        })
    
    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. [{issue['severity']}] {issue['issue']}")
            print(f"   📊 Detail: {issue['detail']}")
            print(f"   💥 Impact: {issue['impact']}")
            print(f"   🔧 Fix: {issue['fix']}")
    else:
        print("\n✅ No major issues detected!")
    
    print("\n" + "="*80)
    print("🎯 RECOMMENDATIONS")
    print("="*80)
    
    print("\n1. IMMEDIATE FIXES:")
    print("   • Increase position size on high-confidence signals (>70%)")
    print("   • Widen profit targets from 2R to 3R minimum")
    print("   • Use trailing stops to let winners run")
    
    print("\n2. STRATEGY ADJUSTMENTS:")
    print("   • Don't take partial profits until +5R minimum")
    print("   • Tighten initial stops to reduce loss size")
    print("   • Scale into winners (add to winning positions)")
    
    print("\n3. RISK MANAGEMENT:")
    print("   • Risk 1.5% on high-confidence trades (currently 1%)")
    print("   • Risk 0.5% on medium-confidence trades")
    print("   • Skip low-confidence trades entirely")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
