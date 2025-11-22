import sys
import os
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from core.alpaca_client import AlpacaClient
from config import settings

def analyze_performance():
    print("📊 Generating Daily Performance Review...")
    print("=" * 50)
    
    client = AlpacaClient()
    
    # 1. Account Snapshot
    account = client.get_account()
    equity = float(account.equity)
    last_equity = float(account.last_equity)
    daily_pl = equity - last_equity
    daily_pl_pct = (daily_pl / last_equity) * 100
    
    print(f"💰 Account Equity: ${equity:,.2f}")
    print(f"📈 Daily P&L:      ${daily_pl:,.2f} ({daily_pl_pct:+.2f}%)")
    print(f"💵 Buying Power:   ${float(account.buying_power):,.2f}")
    print("-" * 50)
    
    # 2. Trade Analysis
    # Determine the last trading session (US ET)
    from datetime import time
    import pytz
    
    ny_tz = pytz.timezone('America/New_York')
    now_ny = datetime.now(ny_tz)
    
    # If today is Saturday (5) or Sunday (6), go back to Friday
    if now_ny.weekday() == 5: # Saturday
        target_date = (now_ny - timedelta(days=1)).date()
    elif now_ny.weekday() == 6: # Sunday
        target_date = (now_ny - timedelta(days=2)).date()
    else:
        # If weekday, check if market open. If before 9:30 AM, look at yesterday
        if now_ny.time() < time(9, 30):
             target_date = (now_ny - timedelta(days=1)).date()
        else:
             target_date = now_ny.date()
             
    # Override for specific request if needed (Nov 21st)
    # target_date = datetime(2025, 11, 21).date()
    
    print(f"📅 Analyzing Trading Session: {target_date} (US/Eastern)")
    
    orders = client.get_orders(status='closed')
    
    # Filter for target date's filled orders (converting to ET)
    todays_trades = []
    for order in orders:
        if order.filled_at:
            # Convert to NY time
            filled_at_ny = order.filled_at.astimezone(ny_tz)
            if filled_at_ny.date() == target_date:
                todays_trades.append(order)
            
    print(f"🔄 Trades Executed: {len(todays_trades)}")
    
    if not todays_trades:
        print("⚠️  No trades executed today.")
    else:
        # Group by symbol to calculate P&L per ticker (approximate based on orders)
        # Note: Precise P&L requires matching buy/sell pairs, which is complex.
        # We'll use the account P&L as the source of truth for money made.
        
        # Analyze order types
        buys = sum(1 for o in todays_trades if o.side == 'buy')
        sells = sum(1 for o in todays_trades if o.side == 'sell')
        print(f"   • Buys: {buys}")
        print(f"   • Sells: {sells}")
        
        symbols = set(o.symbol for o in todays_trades)
        print(f"   • Symbols Traded: {', '.join(symbols)}")

    print("-" * 50)

    # 3. Benchmark Comparison (SPY)
    print("🏆 Benchmark Comparison (SPY)")
    from alpaca.data.timeframe import TimeFrame
    try:
        spy_bars = client.get_bars_for_symbol('SPY', limit=2, timeframe=TimeFrame.Day)
        if spy_bars is not None and not spy_bars.empty:
            # Get latest daily bar
            latest_bar = spy_bars.iloc[-1]
            spy_open = latest_bar['open']
            spy_close = latest_bar['close']
            spy_change_pct = ((spy_close - spy_open) / spy_open) * 100
            
            print(f"🇺🇸 SPY Performance: {spy_change_pct:+.2f}%")
            
            # Compare
            alpha = daily_pl_pct - spy_change_pct
            if alpha > 0:
                print(f"🚀 BEATING THE MARKET by {alpha:+.2f}%")
            else:
                print(f"📉 Trailing the market by {alpha:+.2f}%")
        else:
            print("⚠️  Could not fetch SPY data")
            
    except Exception as e:
        print(f"⚠️  Benchmark error: {e}")

    print("=" * 50)
    
    # 4. Bot Health Check
    print("🤖 Bot Health Check")
    positions = client.get_positions()
    print(f"📦 Open Positions: {len(positions)}")
    
    # Calculate Unrealized P&L
    unrealized_pl = 0.0
    winning_positions = 0
    for pos in positions:
        pl = float(pos.unrealized_pl)
        unrealized_pl += pl
        if pl > 0:
            winning_positions += 1
            
    print(f"💎 Unrealized P&L: ${unrealized_pl:,.2f}")
    if len(positions) > 0:
        win_rate = (winning_positions / len(positions)) * 100
        print(f"   • Winning Positions: {winning_positions}/{len(positions)} ({win_rate:.1f}%)")
    
    # Check for stop losses
    orders_open = client.get_orders(status='open')
    stop_orders = [o for o in orders_open if o.type in ['stop', 'stop_limit', 'trailing_stop']]
    
    print(f"🛡️  Active Stop Losses: {len(stop_orders)}")
    
    if len(positions) > 0:
        coverage = (len(stop_orders) / len(positions)) * 100
        print(f"   • Protection Coverage: {coverage:.0f}%")
        if coverage < 100:
            print("   ⚠️  WARNING: Some positions may be unprotected!")
    
    print("=" * 50)
    
    # 5. Verdict
    if daily_pl > 0:
        print("✅ VERDICT: MONEY PRINTER GOING BRRR 💸")
    elif daily_pl == 0:
        print("😐 VERDICT: FLAT DAY")
    else:
        print("❌ VERDICT: DRAWDOWN - REVIEW STRATEGY")

if __name__ == "__main__":
    analyze_performance()
