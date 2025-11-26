#!/usr/bin/env python3
"""
PROFESSIONAL Trailing Stops - Based on hedge fund research
============================================================

Key principles from quantitative trading research:
1. Use WIDER of: percentage trail OR ATR-based trail
2. Prevents "death by thousand cuts" from too-tight stops
3. Only trail after meaningful profit (2%+)
4. Use R-multiple milestones for systematic profit locking
5. Always use avg_entry_price (accounts for slippage)

Research sources:
- Day traders use 2-5% trailing stops (not 1.5%)
- ATR-based stops adapt to each stock's volatility
- Hedge funds use R-multiple based profit locking
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


def get_atr(symbol: str, period: int = 14) -> float:
    """
    Calculate Average True Range for a symbol.
    ATR measures volatility - higher ATR = more volatile stock.
    """
    try:
        end = datetime.now()
        start = end - timedelta(days=30)
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start,
            end=end
        )
        bars = data_client.get_stock_bars(request)
        
        if symbol not in bars or len(bars[symbol]) < period + 1:
            return 0.0
        
        # Calculate True Range for each bar
        true_ranges = []
        bar_list = list(bars[symbol])
        
        for i in range(1, len(bar_list)):
            high = float(bar_list[i].high)
            low = float(bar_list[i].low)
            prev_close = float(bar_list[i-1].close)
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        # Calculate ATR (simple moving average of TR)
        if len(true_ranges) >= period:
            atr = sum(true_ranges[-period:]) / period
            return atr
        
        return 0.0
    except Exception as e:
        print(f"  ⚠️  Could not calculate ATR for {symbol}: {e}")
        return 0.0


def calculate_r_multiple(entry: float, current: float, initial_stop: float, is_long: bool) -> float:
    """
    Calculate R-multiple (how many R's of profit).
    R = initial risk amount
    """
    if is_long:
        initial_risk = entry - initial_stop
        profit = current - entry
    else:
        initial_risk = initial_stop - entry
        profit = entry - current
    
    if initial_risk <= 0:
        return 0.0
    
    return profit / initial_risk


def get_r_based_stop(entry: float, initial_risk: float, r_multiple: float, is_long: bool) -> float:
    """
    Calculate stop price based on R-multiple milestones.
    This is the professional hedge fund approach.
    """
    # Find the appropriate R-lock level
    r_to_lock = -1.0  # Default: keep original stop
    for r_threshold, lock_level in sorted(R_MULTIPLE_STOPS.items()):
        if r_multiple >= r_threshold:
            r_to_lock = lock_level
    
    if r_to_lock < 0:
        return None  # Not at any milestone yet
    
    if is_long:
        return entry + (r_to_lock * initial_risk)
    else:
        return entry - (r_to_lock * initial_risk)


def professional_trailing_stops():
    """
    Professional-grade trailing stops based on hedge fund research.
    
    Key principles:
    1. Use WIDER of percentage trail OR ATR-based trail
    2. Only trail after meaningful profit (2%+)
    3. Use R-multiple milestones for profit locking
    4. Always use avg_entry_price (accounts for slippage)
    """
    
    positions = client.get_all_positions()
    orders = client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN))
    
    # Build order map
    stop_orders = {}
    for order in orders:
        order_type = str(order.order_type).upper()
        if 'STOP' in order_type and 'LIMIT' not in order_type:
            stop_orders[order.symbol] = order
    
    print("=" * 70)
    print("🏦 PROFESSIONAL TRAILING STOPS")
    print(f"   Percentage Trail: {TRAIL_PERCENT}% | ATR Multiplier: {ATR_MULTIPLIER}x")
    print(f"   Min Profit to Trail: {MIN_PROFIT_TO_TRAIL}%")
    print("   Uses WIDER of percentage OR ATR-based distance")
    print("=" * 70)
    
    updated = 0
    for pos in positions:
        symbol = pos.symbol
        entry = float(pos.avg_entry_price)  # Uses avg entry (accounts for slippage!)
        current = float(pos.current_price)
        qty = int(float(pos.qty))
        pnl_pct = float(pos.unrealized_plpc) * 100
        
        is_long = qty > 0
        abs_qty = abs(qty)
        pos_type = "LONG" if is_long else "SHORT"
        
        stop_order = stop_orders.get(symbol)
        current_stop = float(stop_order.stop_price) if stop_order else None
        
        # Calculate ATR for this symbol
        atr = get_atr(symbol)
        atr_trail_distance = atr * ATR_MULTIPLIER if atr > 0 else 0
        pct_trail_distance = current * (TRAIL_PERCENT / 100)
        
        # Use the WIDER of the two (prevents death by thousand cuts)
        trail_distance = max(pct_trail_distance, atr_trail_distance)
        trail_method = "ATR" if atr_trail_distance > pct_trail_distance else "PCT"
        
        if is_long:
            pct_stop = round(current - pct_trail_distance, 2)
            atr_stop = round(current - atr_trail_distance, 2) if atr > 0 else pct_stop
            new_stop = round(current - trail_distance, 2)
            locked_profit_pct = ((new_stop - entry) / entry) * 100
        else:
            pct_stop = round(current + pct_trail_distance, 2)
            atr_stop = round(current + atr_trail_distance, 2) if atr > 0 else pct_stop
            new_stop = round(current + trail_distance, 2)
            locked_profit_pct = ((entry - new_stop) / entry) * 100
        
        # Calculate R-multiple if we have initial stop
        r_multiple = 0.0
        r_based_stop = None
        if current_stop:
            # Estimate initial risk (use 3% as default if stop is at breakeven)
            if is_long:
                initial_risk = max(entry - current_stop, entry * 0.03)
            else:
                initial_risk = max(current_stop - entry, entry * 0.03)
            
            r_multiple = calculate_r_multiple(entry, current, current_stop, is_long)
            r_based_stop = get_r_based_stop(entry, initial_risk, r_multiple, is_long)
        
        print(f"\n{symbol} ({pos_type}):")
        print(f"  📊 Entry: ${entry:.2f} | Current: ${current:.2f} | P/L: {pnl_pct:+.2f}%")
        print(f"  📈 ATR: ${atr:.2f} | R-Multiple: {r_multiple:.2f}R")
        print(f"  🎯 Current Stop: ${current_stop:.2f}" if current_stop else "  🎯 Current Stop: NONE")
        print(f"  📐 PCT Stop: ${pct_stop:.2f} ({TRAIL_PERCENT}%) | ATR Stop: ${atr_stop:.2f} ({ATR_MULTIPLIER}x ATR)")
        print(f"  ✨ Trail Stop: ${new_stop:.2f} ({trail_method}) - would lock {locked_profit_pct:+.2f}%")
        if r_based_stop:
            r_locked = ((r_based_stop - entry) / entry * 100) if is_long else ((entry - r_based_stop) / entry * 100)
            print(f"  🏆 R-Based Stop: ${r_based_stop:.2f} (at {r_multiple:.2f}R) - would lock {r_locked:+.2f}%")
        
        # Only trail if in meaningful profit
        if pnl_pct < MIN_PROFIT_TO_TRAIL:
            print(f"  ⏳ Not enough profit to trail (need {MIN_PROFIT_TO_TRAIL}%+)")
            continue
        
        # Use the BETTER of trailing stop or R-based stop (whichever locks more profit)
        if r_based_stop:
            if is_long:
                new_stop = max(new_stop, r_based_stop)
            else:
                new_stop = min(new_stop, r_based_stop)
        
        # Recalculate locked profit with final stop
        if is_long:
            locked_profit_pct = ((new_stop - entry) / entry) * 100
        else:
            locked_profit_pct = ((entry - new_stop) / entry) * 100
        
        if is_long:
            # LONG: Only update if new stop is HIGHER than current
            if current_stop and new_stop <= current_stop:
                print(f"  ✅ Current stop ${current_stop:.2f} is already optimal")
                continue
            
            # Make sure we're locking in profit (stop above entry)
            if new_stop <= entry:
                new_stop = round(entry * 1.002, 2)  # 0.2% above entry (breakeven+)
                locked_profit_pct = 0.2
                print(f"  📊 Adjusted to breakeven+ ${new_stop:.2f}")
        else:
            # SHORT: Only update if new stop is LOWER than current
            if current_stop and new_stop >= current_stop:
                print(f"  ✅ Current stop ${current_stop:.2f} is already optimal")
                continue
            
            # Make sure we're locking in profit (stop below entry for shorts)
            if new_stop >= entry:
                new_stop = round(entry * 0.998, 2)  # 0.2% below entry (breakeven+)
                locked_profit_pct = 0.2
                print(f"  📊 Adjusted to breakeven+ ${new_stop:.2f}")
        
        direction = "raising" if is_long else "lowering"
        print(f"  🚀 UPDATING ({direction}): ${current_stop:.2f} → ${new_stop:.2f} (locks {locked_profit_pct:+.2f}%)")
        
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
    print(f"📊 Updated {updated} trailing stops using professional methodology")
    print("=" * 70)


if __name__ == "__main__":
    professional_trailing_stops()
