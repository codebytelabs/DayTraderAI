#!/usr/bin/env python3
"""
Generate comprehensive performance report from Oct 27 to current date.
Compares portfolio performance with SPY benchmark.
"""
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

load_dotenv()

# Initialize clients
trading_client = TradingClient(
    os.getenv('ALPACA_API_KEY'),
    os.getenv('ALPACA_SECRET_KEY'),
    paper=True
)

data_client = StockHistoricalDataClient(
    os.getenv('ALPACA_API_KEY'),
    os.getenv('ALPACA_SECRET_KEY')
)

def get_account_history():
    """Get portfolio value history"""
    try:
        # Get portfolio history - use date_start and date_end
        end_date = datetime.now(pytz.timezone('US/Eastern'))
        start_date = datetime(2024, 10, 27, tzinfo=pytz.timezone('US/Eastern'))
        
        portfolio_history = trading_client.get_portfolio_history(
            date_start=start_date.date(),
            date_end=end_date.date(),
            timeframe='1D'
        )
        
        return portfolio_history
    except Exception as e:
        print(f"Error getting portfolio history: {e}")
        return None

def get_spy_history():
    """Get SPY price history for comparison"""
    try:
        end_date = datetime.now(pytz.timezone('US/Eastern'))
        start_date = datetime(2024, 10, 27, tzinfo=pytz.timezone('US/Eastern'))
        
        request_params = StockBarsRequest(
            symbol_or_symbols=['SPY'],
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date
        )
        
        bars = data_client.get_stock_bars(request_params)
        return bars['SPY']
    except Exception as e:
        print(f"Error getting SPY history: {e}")
        return None

def generate_report():
    """Generate comprehensive performance report"""
    
    print("\n" + "="*80)
    print("📊 PORTFOLIO PERFORMANCE REPORT")
    print("="*80)
    print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S ET')}")
    print(f"Period: October 27, 2024 - Present")
    print("="*80)
    
    # Get current account info
    account = trading_client.get_account()
    current_equity = float(account.equity)
    current_cash = float(account.cash)
    
    print(f"\n📈 CURRENT ACCOUNT STATUS:")
    print(f"   Portfolio Value: ${current_equity:,.2f}")
    print(f"   Cash: ${current_cash:,.2f}")
    print(f"   Buying Power: ${float(account.buying_power):,.2f}")
    
    # Get portfolio history
    portfolio_history = get_account_history()
    
    if portfolio_history:
        print(f"\n📊 PORTFOLIO HISTORY:")
        print(f"   Data Points: {len(portfolio_history.equity)}")
        
        # Calculate daily changes
        equity_values = portfolio_history.equity
        timestamps = portfolio_history.timestamp
        
        if len(equity_values) > 0:
            starting_value = equity_values[0]
            current_value = equity_values[-1]
            total_return = current_value - starting_value
            total_return_pct = (total_return / starting_value) * 100
            
            print(f"\n💰 OVERALL PERFORMANCE:")
            print(f"   Starting Value: ${starting_value:,.2f}")
            print(f"   Current Value: ${current_value:,.2f}")
            print(f"   Total Return: ${total_return:,.2f} ({total_return_pct:+.2f}%)")
            
            # Daily breakdown
            print(f"\n📅 DAILY BREAKDOWN:")
            print(f"{'Date':<12} {'Value':<15} {'Change $':<15} {'Change %':<12} {'SPY %':<12}")
            print("-" * 80)
            
            for i in range(len(equity_values)):
                date = datetime.fromtimestamp(timestamps[i], tz=pytz.timezone('US/Eastern'))
                value = equity_values[i]
                
                if i > 0:
                    prev_value = equity_values[i-1]
                    change_dollar = value - prev_value
                    change_pct = (change_dollar / prev_value) * 100
                    print(f"{date.strftime('%Y-%m-%d'):<12} ${value:>12,.2f} ${change_dollar:>12,.2f} {change_pct:>10.2f}% {'N/A':<12}")
                else:
                    print(f"{date.strftime('%Y-%m-%d'):<12} ${value:>12,.2f} {'--':<15} {'--':<12} {'--':<12}")
    
    # Get SPY comparison
    spy_bars = get_spy_history()
    if spy_bars:
        print(f"\n📊 SPY BENCHMARK COMPARISON:")
        spy_list = list(spy_bars)
        if len(spy_list) > 0:
            spy_start = spy_list[0].close
            spy_end = spy_list[-1].close
            spy_return = ((spy_end - spy_start) / spy_start) * 100
            
            print(f"   SPY Starting: ${spy_start:.2f}")
            print(f"   SPY Current: ${spy_end:.2f}")
            print(f"   SPY Return: {spy_return:+.2f}%")
            
            if portfolio_history and len(equity_values) > 0:
                alpha = total_return_pct - spy_return
                print(f"\n🎯 ALPHA (vs SPY): {alpha:+.2f}%")
                if alpha > 0:
                    print(f"   ✅ Outperforming market by {alpha:.2f}%")
                else:
                    print(f"   ⚠️  Underperforming market by {abs(alpha):.2f}%")
    
    # Get recent trades
    print(f"\n📋 RECENT ACTIVITY:")
    try:
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus
        
        request = GetOrdersRequest(
            status=QueryOrderStatus.CLOSED,
            limit=10
        )
        orders = trading_client.get_orders(filter=request)
        
        if orders:
            print(f"   Last 10 Orders:")
            for order in orders:
                print(f"   {order.filled_at.strftime('%Y-%m-%d %H:%M') if order.filled_at else 'N/A'} | "
                      f"{order.side.value.upper():<4} {order.filled_qty if order.filled_qty else 0:>6} "
                      f"{order.symbol:<6} @ ${float(order.filled_avg_price) if order.filled_avg_price else 0:>8.2f}")
        else:
            print("   No recent orders")
    except Exception as e:
        print(f"   Error getting orders: {e}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    generate_report()
