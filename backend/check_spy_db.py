import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import SupabaseClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

def check_spy_db():
    print("\n🔍 Checking SPY database record...\n")
    
    supabase = SupabaseClient()
    symbol = "SPY"
    
    try:
        response = supabase.client.table('positions').select('*').eq('symbol', symbol).execute()
        if response.data:
            pos = response.data[0]
            print(f"✅ DB Record Found:")
            print(f"   • Symbol: {pos.get('symbol')}")
            print(f"   • Qty: {pos.get('qty')}")
            print(f"   • Stop Loss: {pos.get('stop_loss')}")
            print(f"   • Partial Profits Taken: {pos.get('partial_profits_taken')}")
            print(f"   • Keys: {list(pos.keys())}")
            print(f"   • Updated At: {pos.get('updated_at')}")
        else:
            print("❌ No DB record found for SPY")
            
    except Exception as e:
        print(f"❌ Error checking DB: {e}")

if __name__ == "__main__":
    check_spy_db()
