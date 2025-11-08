#!/usr/bin/env python3
"""
Diagnose current system issues:
1. Database connectivity
2. Buying power validation
3. AI opportunity caching
"""

import asyncio
from datetime import datetime
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from scanner.ai_opportunity_finder import AIOpportunityFinder

async def main():
    print("🔍 DayTraderAI System Diagnostics")
    print("=" * 50)
    
    # 1. Check Alpaca account status
    print("\n1. 📊 Alpaca Account Status")
    try:
        alpaca = AlpacaClient()
        account = alpaca.get_account()
        
        print(f"   ✅ Account connected")
        print(f"   💰 Equity: ${float(account.equity):,.2f}")
        print(f"   💳 Buying Power: ${float(account.buying_power):,.2f}")
        print(f"   🏃 Day Trading BP: ${float(account.daytrading_buying_power):,.2f}")
        print(f"   💵 Cash: ${float(account.cash):,.2f}")
        print(f"   📈 Pattern Day Trader: {account.pattern_day_trader}")
        
        # Check positions
        try:
            positions = alpaca.get_positions()
            print(f"   📍 Open Positions: {len(positions)}")
            for pos in positions[:3]:  # Show first 3
                print(f"      {pos.symbol}: {pos.qty} shares @ ${float(pos.avg_entry_price):.2f}")
        except Exception as e:
            print(f"   ⚠️  Positions check failed: {e}")
            
    except Exception as e:
        print(f"   ❌ Alpaca error: {e}")
    
    # 2. Check Supabase connectivity
    print("\n2. 🗄️  Supabase Database Status")
    try:
        supabase = SupabaseClient()
        
        # Test simple query
        trades = supabase.get_trades(limit=1)
        print(f"   ✅ Database connected")
        print(f"   📊 Recent trades accessible: {len(trades) > 0}")
        
        # Test features upsert (this was failing)
        test_data = {
            'symbol': 'TEST',
            'price': 100.0,
            'rsi': 50.0,
            'timestamp': datetime.now().isoformat()
        }
        result = supabase.upsert_features(test_data)
        if result:
            print(f"   ✅ Features upsert working")
        else:
            print(f"   ⚠️  Features upsert failed (but connection OK)")
            
    except Exception as e:
        print(f"   ❌ Supabase error: {e}")
    
    # 3. Check AI opportunity finder caching
    print("\n3. 🤖 AI Opportunity Finder Status")
    try:
        ai_finder = AIOpportunityFinder()
        
        print(f"   📅 Last scan: {ai_finder.last_discovery_time}")
        print(f"   📊 Cached opportunities: {len(ai_finder.last_opportunities)}")
        print(f"   ⏰ Cache duration: {ai_finder._cache_duration}s ({ai_finder._cache_duration/60:.0f} min)")
        
        # Check if cache is valid
        is_valid = ai_finder._is_cache_valid()
        print(f"   ✅ Cache valid: {is_valid}")
        
        if ai_finder.last_opportunities:
            print(f"   🎯 Sample opportunities: {', '.join(ai_finder.last_opportunities[:5])}")
            
    except Exception as e:
        print(f"   ❌ AI Finder error: {e}")
    
    # 4. Check current market regime
    print("\n4. 📈 Market Regime Status")
    try:
        from indicators.market_regime import get_regime_detector
        
        regime_detector = get_regime_detector(alpaca)
        regime_info = regime_detector.get_current_regime()
        
        print(f"   📊 Current regime: {regime_info['regime']}")
        print(f"   📈 Market breadth: {regime_info['breadth']}")
        print(f"   ⚖️  Risk multiplier: {regime_info['multiplier']:.2f}x")
        
    except Exception as e:
        print(f"   ❌ Market regime error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Diagnostics complete!")

if __name__ == "__main__":
    asyncio.run(main())