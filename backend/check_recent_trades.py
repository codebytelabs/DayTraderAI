import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("Error: Supabase credentials not found in .env")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

def check_trades():
    print("🔍 Checking recent trades...")
    
    try:
        response = supabase.table('trades').select('*').order('timestamp', desc=True).limit(5).execute()
        if response.data:
            for trade in response.data:
                print(f"✅ Trade Found:")
                print(f"   • Keys: {list(trade.keys())}")
                print(f"   • Symbol: {trade.get('symbol')}")
                print(f"   • Side: {trade.get('side')}")
                print(f"   • Qty: {trade.get('qty')}")
                print(f"   • Price: {trade.get('price')}")
                print(f"   • Exit Type: {trade.get('exit_type')}")
                print(f"   • Timestamp: {trade.get('timestamp')}")
                print("-" * 30)
        else:
            print("❌ No recent trades found.")
            
    except Exception as e:
        print(f"❌ Error checking DB: {e}")

if __name__ == "__main__":
    check_trades()
