import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

def check_on_status():
    print("\n🔍 Checking status for ON (ON Semiconductor)...\n")
    
    client = AlpacaClient()
    symbol = "ON"
    
    # 1. Check Position
    position = client.get_position(symbol)
    if position:
        entry_price = float(position.avg_entry_price)
        current_price = float(position.current_price)
        qty = float(position.qty)
        pl = float(position.unrealized_pl)
        pl_pct = float(position.unrealized_plpc) * 100
        
        print(f"✅ POSITION FOUND:")
        print(f"   • Quantity: {qty}")
        print(f"   • Entry Price: ${entry_price:.2f}")
        print(f"   • Current Price: ${current_price:.2f}")
        print(f"   • P/L: ${pl:.2f} ({pl_pct:.2f}%)")
        
        if pl > 0:
            print(f"   • Status: PROFITABLE 🟢")
        else:
            print(f"   • Status: LOSING 🔴")
            
    else:
        print(f"❌ NO OPEN POSITION for {symbol}")
        return

    # 2. Check Orders
    print(f"\n📋 ACTIVE ORDERS:")
    orders = client.get_orders(status='open')
    on_orders = [o for o in orders if o.symbol == symbol]
    
    if not on_orders:
        print("   • No active orders found! ⚠️ (Position is unprotected?)")
    else:
        for order in on_orders:
            print(f"   • {order.type.value.upper()} {order.side.value.upper()} - Status: {order.status.value}")
            
            if order.type.value == 'stop':
                stop_price = float(order.stop_price)
                dist_pct = abs(current_price - stop_price) / current_price * 100
                print(f"     - Stop Price: ${stop_price:.2f}")
                print(f"     - Distance: {dist_pct:.2f}% from current")
                
                if position.side == 'long' and stop_price > entry_price:
                    print(f"     - 🔒 PROFIT LOCKED: ${stop_price - entry_price:.2f} per share")
                elif position.side == 'short' and stop_price < entry_price:
                    print(f"     - 🔒 PROFIT LOCKED: ${entry_price - stop_price:.2f} per share")
                    
            elif order.type.value == 'limit':
                limit_price = float(order.limit_price)
                print(f"     - Limit Price: ${limit_price:.2f}")
                
            print(f"     - ID: {order.id}")

if __name__ == "__main__":
    check_on_status()
