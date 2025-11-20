"""
Comprehensive account check and test trade execution
"""
import sys
from datetime import datetime, timedelta
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from trading.risk_manager import RiskManager
from trading.order_manager import OrderManager
from utils.logger import setup_logger

logger = setup_logger(__name__)

def format_currency(value):
    """Format currency with color"""
    return f"${float(value):,.2f}"

def format_percent(value):
    """Format percentage with color"""
    val = float(value)
    return f"{val:+.2f}%"

def check_account_status(alpaca):
    """Check current account status"""
    print("\n" + "="*80)
    print("📊 ACCOUNT STATUS")
    print("="*80)
    
    account = alpaca.get_account()
    
    print(f"\n💰 BALANCE:")
    print(f"  Portfolio Value:     {format_currency(account.portfolio_value)}")
    print(f"  Equity:              {format_currency(account.equity)}")
    print(f"  Cash:                {format_currency(account.cash)}")
    print(f"  Buying Power:        {format_currency(account.buying_power)}")
    print(f"  Day Trading BP:      {format_currency(account.daytrading_buying_power)}")
    
    print(f"\n📈 ACCOUNT INFO:")
    print(f"  Pattern Day Trader:  {account.pattern_day_trader}")
    print(f"  Account Blocked:     {account.account_blocked}")
    print(f"  Trading Blocked:     {account.trading_blocked}")
    print(f"  Transfers Blocked:   {account.transfers_blocked}")
    
    print(f"\n📊 TRADING STATS:")
    print(f"  Day Trade Count:     {account.daytrade_count}")
    print(f"  Last Equity:         {format_currency(account.last_equity)}")
    
    return account

def check_positions(alpaca):
    """Check current positions"""
    print("\n" + "="*80)
    print("📍 CURRENT POSITIONS")
    print("="*80)
    
    positions = alpaca.get_positions()
    
    if not positions:
        print("\n  No open positions")
        return []
    
    print(f"\n  Total Positions: {len(positions)}")
    print()
    
    for pos in positions:
        side = "LONG" if float(pos.qty) > 0 else "SHORT"
        qty = abs(float(pos.qty))
        entry = float(pos.avg_entry_price)
        current = float(pos.current_price)
        market_value = float(pos.market_value)
        unrealized_pl = float(pos.unrealized_pl)
        unrealized_plpc = float(pos.unrealized_plpc) * 100
        
        print(f"  {pos.symbol} ({side}):")
        print(f"    Quantity:        {qty:.0f} shares")
        print(f"    Entry Price:     ${entry:.2f}")
        print(f"    Current Price:   ${current:.2f}")
        print(f"    Market Value:    {format_currency(market_value)}")
        print(f"    Unrealized P/L:  {format_currency(unrealized_pl)} ({unrealized_plpc:+.2f}%)")
        print()
    
    return positions

def check_recent_orders(alpaca):
    """Check recent orders"""
    print("\n" + "="*80)
    print("📋 RECENT ORDERS (Last 24 Hours)")
    print("="*80)
    
    orders = alpaca.get_orders(status='all')
    
    # Filter to last 24 hours
    cutoff = datetime.now() - timedelta(hours=24)
    recent_orders = []
    
    for order in orders:
        order_time = order.submitted_at
        if order_time.replace(tzinfo=None) > cutoff:
            recent_orders.append(order)
    
    if not recent_orders:
        print("\n  No orders in last 24 hours")
        return []
    
    print(f"\n  Total Recent Orders: {len(recent_orders)}")
    print()
    
    for order in recent_orders[:10]:  # Show last 10
        status = order.status.value
        side = order.side.value
        qty = order.qty
        symbol = order.symbol
        order_type = order.type.value
        submitted = order.submitted_at.strftime("%Y-%m-%d %H:%M:%S")
        
        filled_qty = order.filled_qty if hasattr(order, 'filled_qty') else 0
        filled_price = f"${float(order.filled_avg_price):.2f}" if hasattr(order, 'filled_avg_price') and order.filled_avg_price else "N/A"
        
        print(f"  {symbol} - {side.upper()} {qty} shares ({order_type})")
        print(f"    Status:      {status}")
        print(f"    Submitted:   {submitted}")
        print(f"    Filled:      {filled_qty}/{qty} @ {filled_price}")
        print()
    
    return recent_orders

def check_market_status(alpaca):
    """Check if market is open"""
    print("\n" + "="*80)
    print("🕐 MARKET STATUS")
    print("="*80)
    
    clock = alpaca.get_clock()
    
    print(f"\n  Market Open:     {clock.is_open}")
    print(f"  Current Time:    {clock.timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  Next Open:       {clock.next_open.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  Next Close:      {clock.next_close.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    return clock.is_open

def place_test_order(alpaca, supabase, risk_manager):
    """Place a small test order"""
    print("\n" + "="*80)
    print("🧪 TEST ORDER EXECUTION")
    print("="*80)
    
    # Check if market is open
    if not alpaca.is_market_open():
        print("\n  ⚠️  Market is closed - cannot place test order")
        print("  Market opens at 9:30 AM ET")
        return None
    
    # Test parameters - small position
    symbol = "SPY"
    side = "buy"
    test_qty = 1  # Just 1 share for testing
    
    print(f"\n  Test Order Parameters:")
    print(f"    Symbol:    {symbol}")
    print(f"    Side:      {side.upper()}")
    print(f"    Quantity:  {test_qty} share")
    print()
    
    # Get current price
    try:
        latest_bars = alpaca.get_latest_bars([symbol])
        if not latest_bars or symbol not in latest_bars:
            print("  ❌ Cannot get current price")
            return None
        
        price = float(latest_bars[symbol].close)
        print(f"  Current Price: ${price:.2f}")
        print(f"  Order Value:   ${price * test_qty:.2f}")
        print()
    except Exception as e:
        print(f"  ❌ Error getting price: {e}")
        return None
    
    # Run risk check
    print("  Running risk checks...")
    approved, reason = risk_manager.check_order(symbol, side, test_qty, price)
    
    if not approved:
        print(f"  ❌ Risk check FAILED: {reason}")
        return None
    
    print(f"  ✅ Risk check PASSED: {reason}")
    print()
    
    # Ask for confirmation
    print("  ⚠️  READY TO PLACE REAL ORDER")
    print(f"  This will {side.upper()} {test_qty} share of {symbol} at ~${price:.2f}")
    print()
    response = input("  Proceed with test order? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("  ❌ Test order cancelled by user")
        return None
    
    # Place order
    try:
        print("\n  📤 Submitting order to Alpaca...")
        
        order_manager = OrderManager(alpaca, supabase, risk_manager)
        
        # Calculate stop loss and take profit (1% each)
        stop_loss = price * 0.99 if side == "buy" else price * 1.01
        take_profit = price * 1.01 if side == "buy" else price * 0.99
        
        order = order_manager.submit_order(
            symbol=symbol,
            side=side,
            qty=test_qty,
            price=price,
            stop_loss_price=stop_loss,
            take_profit_price=take_profit,
            reason="Test order - verifying system functionality"
        )
        
        if order:
            print(f"  ✅ Order submitted successfully!")
            print(f"     Order ID: {order.id}")
            print(f"     Status: {order.status}")
            return order
        else:
            print(f"  ❌ Order submission failed")
            return None
            
    except Exception as e:
        print(f"  ❌ Error placing order: {e}")
        logger.error(f"Test order failed: {e}", exc_info=True)
        return None

def main():
    """Main execution"""
    print("\n" + "="*80)
    print("🚀 DAYTRADER AI - ACCOUNT CHECK & TEST TRADE")
    print("="*80)
    
    try:
        # Initialize clients
        alpaca = AlpacaClient()
        supabase = SupabaseClient()
        risk_manager = RiskManager(alpaca)
        
        # Run checks
        account = check_account_status(alpaca)
        positions = check_positions(alpaca)
        orders = check_recent_orders(alpaca)
        is_market_open = check_market_status(alpaca)
        
        # Summary
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        print(f"\n  Account Value:    {format_currency(account.equity)}")
        print(f"  Available Cash:   {format_currency(account.cash)}")
        print(f"  Open Positions:   {len(positions)}")
        print(f"  Recent Orders:    {len(orders)}")
        print(f"  Market Status:    {'🟢 OPEN' if is_market_open else '🔴 CLOSED'}")
        
        # Offer to place test order
        if is_market_open:
            print("\n" + "="*80)
            response = input("\nPlace a test order? (yes/no): ").strip().lower()
            if response == 'yes':
                place_test_order(alpaca, supabase, risk_manager)
        
        print("\n" + "="*80)
        print("✅ CHECK COMPLETE")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Check failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
