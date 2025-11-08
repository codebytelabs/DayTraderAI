#!/usr/bin/env python3
"""
Check what opportunities are currently in the live system database.
"""

import os
import sys
from pathlib import Path
import asyncio

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set minimal env vars
os.environ.setdefault('OPENROUTER_API_KEY', 'dummy')
os.environ.setdefault('ALPACA_API_KEY', 'dummy')
os.environ.setdefault('ALPACA_SECRET_KEY', 'dummy')
os.environ.setdefault('SUPABASE_URL', 'https://dummy.supabase.co')
os.environ.setdefault('SUPABASE_KEY', 'dummy')
os.environ.setdefault('SUPABASE_SERVICE_KEY', 'dummy')

from core.supabase_client import get_client


async def check_live_opportunities():
    """Check what opportunities are in the live database."""
    
    print("\n" + "=" * 80)
    print("🔍 LIVE SYSTEM OPPORTUNITIES CHECK")
    print("=" * 80)
    print()
    
    try:
        supabase = get_client()
        
        # Get recent opportunities from database
        print("📊 Fetching recent opportunities from database...")
        
        result = supabase.table('opportunities').select('*').order('created_at', desc=True).limit(50).execute()
        
        if not result.data:
            print("❌ No opportunities found in database")
            return
        
        opportunities = result.data
        print(f"✅ Found {len(opportunities)} recent opportunities")
        print()
        
        # Analyze the opportunities
        symbols = [opp['symbol'] for opp in opportunities]
        unique_symbols = list(set(symbols))
        
        print(f"📈 Total Opportunities: {len(opportunities)}")
        print(f"🎯 Unique Symbols: {len(unique_symbols)}")
        print()
        
        # Show recent opportunities
        print("🕒 Most Recent Opportunities:")
        print("-" * 80)
        
        for i, opp in enumerate(opportunities[:20], 1):
            symbol = opp['symbol']
            score = opp.get('score', 0)
            created = opp['created_at'][:19]  # Remove timezone info
            
            print(f"  {i:2}. {symbol:6} | Score: {score:5.1f} | {created}")
        
        if len(opportunities) > 20:
            print(f"       ... and {len(opportunities) - 20} more")
        
        print()
        
        # Analyze market cap distribution
        print("📊 Market Cap Analysis of Live Opportunities:")
        print("-" * 80)
        
        # Market cap classifications
        large_cap = {
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 
            'BAC', 'XOM', 'ORCL', 'CRM', 'AMD', 'NFLX', 'ADBE', 'DIS', 'TMO',
            'SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'PFE', 'JNJ', 'WMT', 'HD'
        }
        
        mid_cap = {
            'PLTR', 'COIN', 'SOFI', 'RIVN', 'SNOW', 'DKNG', 'CRWD', 'ZS', 'RBLX',
            'MDB', 'TEAM', 'WDAY', 'VEEV', 'TTD', 'TRADE', 'OPEN', 'RKT', 'HOOD'
        }
        
        small_cap = {
            'MARA', 'RIOT', 'AMC', 'GME', 'ENPH', 'SEDG', 'RUN', 'FSLY',
            'BRTX', 'SOUN', 'IONQ', 'RGTI', 'QUBT', 'AIMD', 'SMCI'
        }
        
        # Classify symbols
        large_found = [s for s in unique_symbols if s in large_cap]
        mid_found = [s for s in unique_symbols if s in mid_cap]
        small_found = [s for s in unique_symbols if s in small_cap]
        unknown = [s for s in unique_symbols if s not in large_cap and s not in mid_cap and s not in small_cap]
        
        print(f"🏢 Large-Cap ({len(large_found)}): {', '.join(large_found)}")
        print(f"🏭 Mid-Cap ({len(mid_found)}): {', '.join(mid_found)}")
        print(f"🏪 Small-Cap ({len(small_found)}): {', '.join(small_found)}")
        if unknown:
            print(f"❓ Unknown ({len(unknown)}): {', '.join(unknown)}")
        
        print()
        
        # Check if multi-cap coverage exists
        has_large = len(large_found) > 0
        has_mid = len(mid_found) > 0
        has_small = len(small_found) > 0
        
        print("✅ VALIDATION RESULTS:")
        print(f"   Large-Cap Coverage: {'✅ YES' if has_large else '❌ NO'}")
        print(f"   Mid-Cap Coverage: {'✅ YES' if has_mid else '❌ NO'}")
        print(f"   Small-Cap Coverage: {'✅ YES' if has_small else '❌ NO'}")
        print(f"   Multi-Cap System: {'✅ WORKING' if (has_large and has_mid and has_small) else '⚠️ PARTIAL'}")
        
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error checking opportunities: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(check_live_opportunities())