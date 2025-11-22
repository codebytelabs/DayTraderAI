import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient
from core.state import trading_state
from core.supabase_client import SupabaseClient
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

def fix_on_protection():
    print("\n🛡️  Fixing protection for ON...\n")
    
    client = AlpacaClient()
    supabase = SupabaseClient()
    symbol = "ON"
    
    # 1. Get Position
    position = client.get_position(symbol)
    if not position:
        print("❌ No position found for ON")
        return
        
    current_price = float(position.current_price)
    entry_price = float(position.avg_entry_price)
    qty = float(position.qty)
    
    print(f"Position: Short {abs(qty)} @ ${entry_price:.2f} (Current: ${current_price:.2f})")
    
    # 2. Calculate New Stop (Lock in Profit)
    # Use 1.5% trail
    new_stop_price = current_price * 1.015
    new_stop_price = round(new_stop_price, 2)
    
    profit_locked = (entry_price - new_stop_price) * abs(qty)
    
    print(f"Proposed New Stop: ${new_stop_price}")
    print(f"Profit Locked: ${profit_locked:.2f}")
    
    if new_stop_price >= entry_price:
        print("⚠️  New stop is not better than entry! Aborting to be safe.")
        return

    # 3. Find and Replace Order
    orders = client.get_orders(status='open')
    stop_order = None
    for order in orders:
        if order.symbol == symbol and order.type.value == 'stop':
            stop_order = order
            break
            
    if stop_order:
        print(f"Found existing stop: {stop_order.id} @ ${stop_order.stop_price}")
        
        try:
            client.replace_order(
                order_id=stop_order.id,
                stop_price=new_stop_price
            )
            print(f"✅ SUCCESS: Order updated to ${new_stop_price}")
            
            # 4. Update Database to match
            # We need to update the position in Supabase so the bot knows the new state
            # and doesn't try to "fix" it back or get confused.
            
            # Fetch current DB record to get other fields
            # (Simplified: just update the stop_loss field)
            supabase.table('positions').update({'stop_loss': new_stop_price}).eq('symbol', symbol).execute()
            print(f"✅ Database updated")
            
        except Exception as e:
            print(f"❌ Failed to replace order: {e}")
    else:
        print("❌ No active stop order found to replace!")

if __name__ == "__main__":
    fix_on_protection()
