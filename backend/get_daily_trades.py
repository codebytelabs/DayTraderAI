#!/usr/bin/env python3
"""
Get Today's Trading Activity from Alpaca API
Pull all orders and positions for comprehensive daily summary
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from core.alpaca_client import AlpacaClient


def main():
    print("=" * 80)
    print("DAILY TRADING SUMMARY - November 6, 2025")
    print("=" * 80)
    print()
    
    try:
        # Initialize Alpaca client
        alpaca = AlpacaClient()
        print("✓ Connected to Alpaca (Paper Trading)")
        print()
        
        # Get account info
        account = alpaca.get_account()
        print("📊 ACCOUNT STATUS")
        print("-" * 80)
        print(f"Equity: ${float(account.equity):,.2f}")
        print(f"Cash: ${float(account.cash):,.2f}")
        print(f"Buying Power: ${float(account.buying_power):,.2f}")
        print(f"Day Trading Buying Power: ${float(account.daytrading_buying_power):,.2f}")
        print(f"Portfolio Value: ${float(account.portfolio_value):,.2f}")
        print(f"Last Equity: ${float(account.last_equity):,.2f}")
        
        # Calculate daily P/L
        daily_pl = float(account.equity) - float(account.last_equity)
        daily_pl_pct = (daily_pl / float(account.last_equity)) * 100 if float(account.last_equity) > 0 else 0
        
        print(f"\n💰 Daily P/L: ${daily_pl:+,.2f} ({daily_pl_pct:+.2f}%)")
        print()
        
        # Get all orders from today
        print("📋 TODAY'S ORDERS")
        print("-" * 80)
        
        # Get orders from last 24 hours
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus
        
        after_date = datetime.now() - timedelta(days=1)
        
        request = GetOrdersRequest(
            status=QueryOrderStatus.ALL,
            after=after_date,
            limit=500
        )
        orders = alpaca.trading_client.get_orders(filter=request)
        
        if not orders:
            print("No orders today")
        else:
            print(f"Total orders: {len(orders)}\n")
            
            # Group by status
            filled_orders = [o for o in orders if o.status == 'filled']
            pending_orders = [o for o in orders if o.status in ['new', 'accepted', 'pending_new']]
            cancelled_orders = [o for o in orders if o.status == 'canceled']
            rejected_orders = [o for o in orders if o.status == 'rejected']
            
            print(f"✅ Filled: {len(filled_orders)}")
            print(f"⏳ Pending: {len(pending_orders)}")
            print(f"❌ Cancelled: {len(cancelled_orders)}")
            print(f"🚫 Rejected: {len(rejected_orders)}")
            print()
            
            # Show filled orders
            if filled_orders:
                print("✅ FILLED ORDERS:")
                print("-" * 80)
                for order in filled_orders:
                    filled_at = order.filled_at.strftime("%H:%M:%S") if order.filled_at else "N/A"
                    filled_price = float(order.filled_avg_price) if order.filled_avg_price else 0
                    filled_qty = float(order.filled_qty) if order.filled_qty else 0
                    value = filled_price * filled_qty
                    
                    print(f"{filled_at} | {order.side.upper():4} {filled_qty:>6.0f} {order.symbol:6} @ ${filled_price:>8.2f} | ${value:>10,.2f}")
                    if hasattr(order, 'order_class') and order.order_class == 'bracket':
                        print(f"         └─ Bracket order (TP/SL attached)")
                print()
            
            # Show pending orders
            if pending_orders:
                print("⏳ PENDING ORDERS:")
                print("-" * 80)
                for order in pending_orders:
                    submitted_at = order.submitted_at.strftime("%H:%M:%S") if order.submitted_at else "N/A"
                    qty = float(order.qty)
                    limit_price = float(order.limit_price) if order.limit_price else 0
                    
                    print(f"{submitted_at} | {order.side.upper():4} {qty:>6.0f} {order.symbol:6} @ ${limit_price:>8.2f} | {order.status}")
                print()
            
            # Show cancelled orders
            if cancelled_orders:
                print("❌ CANCELLED ORDERS:")
                print("-" * 80)
                for order in cancelled_orders:
                    submitted_at = order.submitted_at.strftime("%H:%M:%S") if order.submitted_at else "N/A"
                    qty = float(order.qty)
                    
                    print(f"{submitted_at} | {order.side.upper():4} {qty:>6.0f} {order.symbol:6} | Cancelled")
                print()
        
        # Get current positions
        print("📈 CURRENT POSITIONS")
        print("-" * 80)
        
        positions = alpaca.get_positions()
        
        if not positions:
            print("No open positions")
        else:
            print(f"Total positions: {len(positions)}\n")
            
            total_market_value = 0
            total_unrealized_pl = 0
            
            for pos in positions:
                qty = int(pos.qty)
                side = "LONG" if qty > 0 else "SHORT"
                entry = float(pos.avg_entry_price)
                current = float(pos.current_price)
                market_value = float(pos.market_value)
                unrealized_pl = float(pos.unrealized_pl)
                unrealized_pl_pct = float(pos.unrealized_plpc) * 100
                
                total_market_value += abs(market_value)
                total_unrealized_pl += unrealized_pl
                
                pl_symbol = "+" if unrealized_pl >= 0 else ""
                
                print(f"{pos.symbol:6} | {side:5} {abs(qty):>4} @ ${entry:>8.2f} | "
                      f"Now: ${current:>8.2f} | "
                      f"P/L: {pl_symbol}${unrealized_pl:>8.2f} ({pl_symbol}{unrealized_pl_pct:>6.2f}%)")
            
            print()
            print(f"Total Market Value: ${total_market_value:,.2f}")
            print(f"Total Unrealized P/L: ${total_unrealized_pl:+,.2f}")
        
        print()
        
        # Get closed positions (trades closed today)
        print("💵 CLOSED POSITIONS (Today)")
        print("-" * 80)
        
        # Get activities from today
        try:
            from alpaca.trading.requests import GetAccountActivitiesRequest
            from alpaca.trading.enums import ActivityType
            
            request = GetAccountActivitiesRequest(
                activity_types=[ActivityType.FILL],
                date=datetime.now().date()
            )
            activities = alpaca.trading_client.get_account_activities(request)
        except Exception as e:
            print(f"Could not fetch activities: {e}")
            activities = []
        
        if not activities:
            print("No closed positions today")
        else:
            # Group fills by symbol to identify closed positions
            fills_by_symbol = {}
            for activity in activities:
                symbol = activity.symbol
                if symbol not in fills_by_symbol:
                    fills_by_symbol[symbol] = []
                fills_by_symbol[symbol].append(activity)
            
            closed_count = 0
            total_realized_pl = 0
            
            for symbol, fills in fills_by_symbol.items():
                # Check if position was closed (buy and sell)
                buys = [f for f in fills if f.side == 'buy']
                sells = [f for f in fills if f.side == 'sell']
                
                if buys and sells:
                    closed_count += 1
                    # Calculate P/L (simplified)
                    buy_value = sum(float(f.price) * float(f.qty) for f in buys)
                    sell_value = sum(float(f.price) * float(f.qty) for f in sells)
                    realized_pl = sell_value - buy_value
                    total_realized_pl += realized_pl
                    
                    print(f"{symbol:6} | Closed | P/L: ${realized_pl:+,.2f}")
            
            if closed_count == 0:
                print("No positions closed today (only entries/exits)")
            else:
                print()
                print(f"Total Closed: {closed_count}")
                print(f"Total Realized P/L: ${total_realized_pl:+,.2f}")
        
        print()
        print("=" * 80)
        print("END OF DAILY SUMMARY")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
