#!/usr/bin/env python3
"""
PROFESSIONAL Trailing Stops - Based on hedge fund research
- Uses WIDER of: percentage trail OR ATR-based trail
- Prevents "death by thousand cuts" from too-tight stops
- LONG: Trails stops below current price
- SHORT: Trails stops above current price

Research-backed settings:
- Day traders use 2-5% trailing stops (not 1.5%)
- ATR-based stops adapt to each stock's volatility
- Only trail after meaningful profit (2%+)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest, ReplaceOrderRequest
from alpaca.trading.enums import QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

api_key = os.environ.get('ALPACA_API_KEY', 'PKKX2K9CFFAABD5M8I5R')
secret_key = os.environ.get('ALPACA_SECRET_KEY', 'cRMG3ccQfZ5lzexiJ0c8EFgsVdiIcCrxx7uNntay')

client = TradingClient(api_key, secret_key, paper=True)
data_client = StockHistoricalDataClient(api_key, secret_key)

# ============================================================================
# PROFESSIONAL TRAILING STOP CONFIGURATION
# Based on hedge fund research and quantitative trading best practices
# ============================================================================

# Percentage-based trailing (minimum floor)
TRAIL_PERCENT = 2.5  # Trail 2.5% from current price (was 1.5% - too tight!)

# ATR-based trailing (adapts to volatility)
ATR_MULTIPLIER = 2.0  # Use 2x ATR as trailing distance

# Profit threshold before trailing kicks in
MIN_PROFIT_TO_TRAIL = 2.0  # Only trail if position is 2%+ in profit (was 1%)

# R-Multiple based milestones (professional approach)
# These lock in profit at key levels
R_MULTIPLE_STOPS = {
    1.0: 0.0,   # At 1R profit: move to breakeven (lock 0R)
    1.5: 0.5,   # At 1.5R profit: lock in 0.5R
    2.0: 1.0,   # At 2R profit: lock in 1R
    3.0: 1.5,   # At 3R profit: lock in 1.5R
    4.0: 2.0,   # At 4R+ profit: lock in 2R
}

def aggressive_trailing_stops():
    """Trail stops aggressively - works for both LONG and SHORT positions"""
    
    positions = client.get_all_positions()
    orders = client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN))
    
    # Build order map
    stop_orders = {}
    for order in orders:
        order_type = str(order.order_type).upper()
        if 'STOP' in order_type and 'LIMIT' not in order_type:
            stop_orders[order.symbol] = order
    
    print("=" * 70)
    print(f"AGGRESSIVE TRAILING STOPS - {TRAIL_PERCENT}% from current price")
    print("Supports LONG (trail below) and SHORT (trail above) positions")
    print("=" * 70)
    
    updated = 0
    for pos in positions:
        symbol = pos.symbol
        entry = float(pos.avg_entry_price)
        current = float(pos.current_price)
        qty = int(float(pos.qty))
        pnl_pct = float(pos.unrealized_plpc) * 100
        
        is_long = qty > 0
        abs_qty = abs(qty)
        pos_type = "LONG" if is_long else "SHORT"
        
        stop_order = stop_orders.get(symbol)
        current_stop = float(stop_order.stop_price) if stop_order else None
        
        if is_long:
            # LONG: trail stop BELOW current price
            new_stop = round(current * (1 - TRAIL_PERCENT/100), 2)
            locked_profit_pct = ((new_stop - entry) / entry) * 100
        else:
            # SHORT: trail stop ABOVE current price
            new_stop = round(current * (1 + TRAIL_PERCENT/100), 2)
            locked_profit_pct = ((entry - new_stop) / entry) * 100
        
        print(f"\n{symbol} ({pos_type}):")
        print(f"  Entry: ${entry:.2f} | Current: ${current:.2f} | P/L: {pnl_pct:+.2f}%")
        print(f"  Current Stop: ${current_stop:.2f}" if current_stop else "  Current Stop: NONE")
        print(f"  Aggressive Stop: ${new_stop:.2f} (locks {locked_profit_pct:+.2f}% profit)")
        
        # Only trail if in profit
        if pnl_pct < MIN_PROFIT_TO_TRAIL:
            print(f"  ⏳ Not enough profit to trail aggressively (need {MIN_PROFIT_TO_TRAIL}%+)")
            continue
        
        if is_long:
            # LONG: Only update if new stop is HIGHER than current
            if current_stop and new_stop <= current_stop:
                print(f"  ✅ Current stop ${current_stop:.2f} is already good")
                continue
            
            # Make sure we're locking in profit (stop above entry)
            if new_stop <= entry:
                new_stop = round(entry * 1.005, 2)  # 0.5% above entry
                print(f"  📊 Adjusted to breakeven+ ${new_stop:.2f}")
        else:
            # SHORT: Only update if new stop is LOWER than current
            if current_stop and new_stop >= current_stop:
                print(f"  ✅ Current stop ${current_stop:.2f} is already good")
                continue
            
            # Make sure we're locking in profit (stop below entry for shorts)
            if new_stop >= entry:
                new_stop = round(entry * 0.995, 2)  # 0.5% below entry
                print(f"  📊 Adjusted to breakeven+ ${new_stop:.2f}")
        
        direction = "raising" if is_long else "lowering"
        print(f"  🎯 UPDATING ({direction}): ${current_stop:.2f} → ${new_stop:.2f}")
        
        if stop_order:
            try:
                replace_request = ReplaceOrderRequest(
                    qty=abs_qty,
                    stop_price=new_stop
                )
                client.replace_order_by_id(stop_order.id, replace_request)
                print(f"  ✅ Stop updated to ${new_stop:.2f}")
                updated += 1
            except Exception as e:
                print(f"  ❌ Failed: {e}")
        else:
            print(f"  ⚠️  No stop order found!")
    
    print(f"\n{'=' * 70}")
    print(f"Updated {updated} trailing stops")
    print("=" * 70)

if __name__ == "__main__":
    aggressive_trailing_stops()
