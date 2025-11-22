import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

def check_spy_status():
    print("\n🔍 Checking status for SPY...\n")
    
    client = AlpacaClient()
    symbol = "SPY"
    
    # 1. Check Position
    position = client.get_position(symbol)
    if position:
        print(f"✅ POSITION FOUND:")
        print(f"   • Quantity: {position.qty}")
        print(f"   • Available to Trade: {position.qty_available}") # Check if this field exists/is useful
        print(f"   • Entry: ${position.avg_entry_price}")
        print(f"   • Current: ${position.current_price}")
        print(f"   • P/L: ${position.unrealized_pl} ({float(position.unrealized_plpc)*100:.2f}%)")
    else:
        print(f"❌ NO OPEN POSITION for {symbol}")
        return

    # 2. Check Orders
    print(f"\n📋 ACTIVE ORDERS:")
    orders = client.get_orders(status='open')
    spy_orders = [o for o in orders if o.symbol == symbol]
    
    if not spy_orders:
        print("   • No active orders found!")
    else:
        for order in spy_orders:
            print(f"   • {order.type.value.upper()} {order.side.value.upper()} - Qty: {order.qty}")
            print(f"     - Status: {order.status.value}")
            print(f"     - ID: {order.id}")
            if order.type.value == 'limit':
                 print(f"     - Limit Price: ${order.limit_price}")
            if order.type.value == 'stop':
                 print(f"     - Stop Price: ${order.stop_price}")

if __name__ == "__main__":
    check_spy_status()
