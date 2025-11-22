#!/usr/bin/env python3
"""Verify ProfitTaker state hydration"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
load_dotenv()

from core.supabase_client import SupabaseClient
from trading.profit_taker import ProfitTaker

print("🔍 Testing ProfitTaker state hydration...\n")

# Initialize
supabase = SupabaseClient()
profit_taker = ProfitTaker(supabase)

# Check if SPY is in partial_profits_taken
if 'SPY' in profit_taker.partial_profits_taken:
    print("✅ SUCCESS: SPY found in partial_profits_taken!")
    spy_data = profit_taker.partial_profits_taken['SPY']
    print(f"   • Timestamp: {spy_data.get('timestamp')}")
    print(f"   • Shares Sold: {spy_data.get('shares_sold')}")
    print(f"   • Price: {spy_data.get('price')}")
    print("\n✅ State hydration working correctly - SPY won't double-dip!")
else:
    print("❌ FAILED: SPY NOT found in partial_profits_taken")
    print(f"   • Keys present: {list(profit_taker.partial_profits_taken.keys())}")
    print("\n⚠️  Risk of double-dipping on restart!")

print(f"\nTotal positions tracked: {len(profit_taker.partial_profits_taken)}")
