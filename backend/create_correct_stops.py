#!/usr/bin/env python3
"""Create correct stop-loss orders for short positions"""

import sys
sys.path.insert(0, '/Users/vishnuvardhanmedara/DayTraderAI/backend')

from core.alpaca_client import AlpacaClient
from alpaca.trading.requests import StopOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

alpaca_client = AlpacaClient()

def create_stops():
    print("=" * 80)
    print("🛠️  CREATING CORRECT STOP-LOSS ORDERS")
    print("=" * 80)
    
    # Get positions
    positions = alpaca_client.get_positions()
    
    for pos in positions:
        symbol = pos.symbol
        qty = abs(float(pos.qty))
        side = pos.side
        entry = float(pos.avg_entry_price)
        
        if side != 'short':
            continue
        
        print(f"\n📊 {symbol} - SHORT {qty} shares @ ${entry:.2f}")
        
        # For short positions: stop-loss is ABOVE entry (1.5%)
        stop_price = round(entry * 1.015, 2)
        
        print(f"   Creating BUY stop-loss @ ${stop_price:.2f}")
        
        try:
            stop_request = StopOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY,  # Correct side for short positions
                time_in_force=TimeInForce.GTC,
                stop_price=stop_price
            )
            
            order = alpaca_client.trading_client.submit_order(stop_request)
            print(f"   ✅ Stop-loss created: {order.id}")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print(f"\n{'='*80}")
    print("✅ Stop-loss creation complete")
    print("=" * 80)

if __name__ == "__main__":
    create_stops()
