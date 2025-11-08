#!/usr/bin/env python3
"""
Analyze today's trading performance vs market indices
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pytz
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from core.alpaca_client import AlpacaClient
from alpaca.trading.enums import QueryOrderStatus
import pandas as pd

# Initialize Alpaca client
alpaca_client = AlpacaClient()

def get_market_date():
    """Get today's date in market timezone (ET)"""
    et_tz = pytz.timezone('America/New_York')
    now_et = datetime.now(et_tz)
    return now_et.date()

def fetch_account_data():
    """Fetch current account status"""
    account = alpaca_client.trading_client.get_account()
    return {
        'equity': float(account.equity),
        'cash': float(account.cash),
        'buying_power': float(account.buying_power),
        'portfolio_value': float(account.portfolio_value),
        'last_equity': float(account.last_equity),
        'day_pnl': float(account.equity) - float(account.last_equity),
        'day_pnl_pct': ((float(account.equity) - float(account.last_equity)) / float(account.last_equity)) * 100 if float(account.last_equity) > 0 else 0
    }

def fetch_positions():
    """Fetch current positions"""
    positions = alpaca_client.trading_client.get_all_positions()
    position_data = []
    
    for pos in positions:
        position_data.append({
            'symbol': pos.symbol,
            'qty': float(pos.qty),
            'avg_entry': float(pos.avg_entry_price),
            'current_price': float(pos.current_price),
            'market_value': float(pos.market_value),
            'unrealized_pl': float(pos.unrealized_pl),
            'unrealized_plpc': float(pos.unrealized_plpc) * 100,
            'side': pos.side
        })
    
    return pd.DataFrame(position_data) if position_data else pd.DataFrame()

def fetch_todays_orders():
    """Fetch today's orders"""
    market_date = get_market_date()
    
    # Get orders from today using the correct API
    from alpaca.trading.requests import GetOrdersRequest
    request = GetOrdersRequest(
        status=QueryOrderStatus.ALL,
        limit=500,
        nested=True
    )
    orders = alpaca_client.trading_client.get_orders(filter=request)
    
    todays_orders = []
    for order in orders:
        order_date = order.created_at.date()
        if order_date == market_date:
            todays_orders.append({
                'symbol': order.symbol,
                'side': order.side.value,
                'qty': float(order.qty) if order.qty else 0,
                'type': order.type.value,
                'status': order.status.value,
                'filled_qty': float(order.filled_qty) if order.filled_qty else 0,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else 0,
                'created_at': order.created_at,
                'filled_at': order.filled_at if hasattr(order, 'filled_at') else None,
                'order_class': order.order_class.value if order.order_class else 'simple'
            })
    
    return pd.DataFrame(todays_orders) if todays_orders else pd.DataFrame()

def fetch_todays_trades():
    """Fetch today's closed trades"""
    market_date = get_market_date()
    start_date = datetime.combine(market_date, datetime.min.time())
    
    # Get activities (trades)
    try:
        activities = alpaca_client.trading_client.get_activities(
            activity_types='FILL',
            date=market_date
        )
        
        trades = []
        for activity in activities:
            trades.append({
                'symbol': activity.symbol,
                'side': activity.side.value,
                'qty': float(activity.qty),
                'price': float(activity.price),
                'amount': float(activity.qty) * float(activity.price),
                'timestamp': activity.transaction_time
            })
        
        return pd.DataFrame(trades) if trades else pd.DataFrame()
    except Exception as e:
        print(f"Error fetching trades: {e}")
        return pd.DataFrame()

def fetch_market_indices():
    """Fetch market index performance for today"""
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    
    market_date = get_market_date()
    start = datetime.combine(market_date, datetime.min.time())
    end = datetime.now()
    
    indices = {}
    symbols = ['SPY', 'QQQ', 'DIA', 'IWM']  # S&P 500, Nasdaq, Dow, Russell 2000
    
    for symbol in symbols:
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start,
                end=end
            )
            bars_response = alpaca_client.data_client.get_stock_bars(request)
            bars = bars_response[symbol]
            
            if bars and len(bars) > 0:
                bar = bars[-1]  # Get the latest bar
                day_change = ((bar.close - bar.open) / bar.open) * 100
                indices[symbol] = {
                    'open': bar.open,
                    'close': bar.close,
                    'high': bar.high,
                    'low': bar.low,
                    'change_pct': day_change
                }
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
    
    return indices

def generate_report():
    """Generate comprehensive trading report"""
    print("=" * 80)
    print(f"📊 TRADING PERFORMANCE REPORT - {get_market_date()}")
    print("=" * 80)
    print()
    
    # Account Summary
    print("💰 ACCOUNT SUMMARY")
    print("-" * 80)
    account = fetch_account_data()
    print(f"Portfolio Value:  ${account['equity']:,.2f}")
    print(f"Cash Available:   ${account['cash']:,.2f}")
    print(f"Buying Power:     ${account['buying_power']:,.2f}")
    print(f"Day P&L:          ${account['day_pnl']:,.2f} ({account['day_pnl_pct']:+.2f}%)")
    print()
    
    # Current Positions
    print("📈 CURRENT POSITIONS")
    print("-" * 80)
    positions = fetch_positions()
    if not positions.empty:
        positions_sorted = positions.sort_values('unrealized_pl', ascending=False)
        total_unrealized = positions['unrealized_pl'].sum()
        
        for _, pos in positions_sorted.iterrows():
            pnl_symbol = "🟢" if pos['unrealized_pl'] >= 0 else "🔴"
            print(f"{pnl_symbol} {pos['symbol']:6s} | {pos['qty']:>6.0f} shares @ ${pos['avg_entry']:>8.2f} | "
                  f"Current: ${pos['current_price']:>8.2f} | "
                  f"P&L: ${pos['unrealized_pl']:>+8.2f} ({pos['unrealized_plpc']:>+6.2f}%)")
        
        print(f"\nTotal Unrealized P&L: ${total_unrealized:+,.2f}")
        print(f"Number of Positions: {len(positions)}")
    else:
        print("No open positions")
    print()
    
    # Today's Orders
    print("📋 TODAY'S ORDERS")
    print("-" * 80)
    orders = fetch_todays_orders()
    if not orders.empty:
        filled_orders = orders[orders['status'] == 'filled']
        pending_orders = orders[orders['status'].isin(['new', 'pending_new', 'accepted'])]
        
        if not filled_orders.empty:
            print("\n✅ FILLED ORDERS:")
            for _, order in filled_orders.iterrows():
                side_symbol = "🟢" if order['side'] == 'buy' else "🔴"
                print(f"{side_symbol} {order['side'].upper():4s} {order['filled_qty']:>6.0f} {order['symbol']:6s} @ ${order['filled_avg_price']:>8.2f} | "
                      f"Class: {order['order_class']:8s} | {order['created_at'].strftime('%H:%M:%S')}")
        
        if not pending_orders.empty:
            print("\n⏳ PENDING ORDERS:")
            for _, order in pending_orders.iterrows():
                print(f"   {order['side'].upper():4s} {order['qty']:>6.0f} {order['symbol']:6s} | "
                      f"Status: {order['status']:12s} | {order['created_at'].strftime('%H:%M:%S')}")
        
        print(f"\nTotal Orders Today: {len(orders)} (Filled: {len(filled_orders)}, Pending: {len(pending_orders)})")
    else:
        print("No orders today")
    print()
    
    # Today's Trades
    print("💵 TODAY'S TRADE ACTIVITY")
    print("-" * 80)
    trades = fetch_todays_trades()
    if not trades.empty:
        buys = trades[trades['side'] == 'buy']
        sells = trades[trades['side'] == 'sell']
        
        print(f"Total Trades: {len(trades)}")
        print(f"  Buys:  {len(buys)} trades, ${buys['amount'].sum():,.2f} total")
        print(f"  Sells: {len(sells)} trades, ${sells['amount'].sum():,.2f} total")
        print(f"\nNet Activity: ${(sells['amount'].sum() - buys['amount'].sum()):+,.2f}")
    else:
        print("No trades executed today")
    print()
    
    # Market Comparison
    print("📊 MARKET INDICES COMPARISON")
    print("-" * 80)
    indices = fetch_market_indices()
    
    if indices:
        print(f"{'Index':<10s} {'Change %':>10s}")
        print("-" * 25)
        for symbol, data in indices.items():
            change_symbol = "🟢" if data['change_pct'] >= 0 else "🔴"
            index_name = {
                'SPY': 'S&P 500',
                'QQQ': 'Nasdaq',
                'DIA': 'Dow Jones',
                'IWM': 'Russell 2K'
            }.get(symbol, symbol)
            print(f"{change_symbol} {index_name:<10s} {data['change_pct']:>+9.2f}%")
        
        print()
        print("📈 PERFORMANCE VS MARKET")
        print("-" * 80)
        your_performance = account['day_pnl_pct']
        spy_performance = indices.get('SPY', {}).get('change_pct', 0)
        qqq_performance = indices.get('QQQ', {}).get('change_pct', 0)
        
        print(f"Your Portfolio:  {your_performance:>+8.2f}%")
        print(f"S&P 500 (SPY):   {spy_performance:>+8.2f}%")
        print(f"Nasdaq (QQQ):    {qqq_performance:>+8.2f}%")
        print()
        
        vs_spy = your_performance - spy_performance
        vs_qqq = your_performance - qqq_performance
        
        spy_symbol = "🎯" if vs_spy > 0 else "📉"
        qqq_symbol = "🎯" if vs_qqq > 0 else "📉"
        
        print(f"{spy_symbol} vs S&P 500:  {vs_spy:>+8.2f}% {'(Outperforming)' if vs_spy > 0 else '(Underperforming)'}")
        print(f"{qqq_symbol} vs Nasdaq:   {vs_qqq:>+8.2f}% {'(Outperforming)' if vs_qqq > 0 else '(Underperforming)'}")
    else:
        print("Unable to fetch market data")
    
    print()
    print("=" * 80)
    
    return {
        'account': account,
        'positions': positions,
        'orders': orders,
        'trades': trades,
        'indices': indices
    }

if __name__ == '__main__':
    try:
        data = generate_report()
        
        # Save to file
        output_file = f"TRADING_REPORT_{get_market_date()}.txt"
        with open(output_file, 'w') as f:
            # Redirect stdout to file
            import sys
            old_stdout = sys.stdout
            sys.stdout = f
            generate_report()
            sys.stdout = old_stdout
        
        print(f"\n✅ Report saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
