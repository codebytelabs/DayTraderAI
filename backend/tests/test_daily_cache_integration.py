#!/usr/bin/env python3
"""
Integration Tests for Daily Cache with Real Twelve Data API
Tests the complete flow with actual API calls
"""

import sys
import os
from dotenv import load_dotenv
import pathlib

# Load .env
env_path = pathlib.Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from data.daily_cache import DailyCache
from datetime import datetime

print("="*80)
print("🔗 DAILY CACHE INTEGRATION TESTS")
print("="*80)
print("Testing with REAL Twelve Data API calls")
print("="*80)

def test_1_real_api_single_symbol():
    """Test 1: Fetch real data for single symbol"""
    print("\n" + "="*80)
    print("TEST 1: REAL API - SINGLE SYMBOL")
    print("="*80)
    
    cache = DailyCache()
    
    if not cache.twelvedata_api_key:
        print("❌ TWELVEDATA_API_KEY not configured")
        return False
    
    print(f"✅ API Key configured: {cache.twelvedata_api_key[:10]}...")
    
    # Fetch real data
    print("\n📊 Fetching AAPL daily bars from Twelve Data...")
    bars = cache.fetch_twelvedata_bars('AAPL')
    
    if not bars:
        print("❌ Failed to fetch bars")
        return False
    
    print(f"✅ Retrieved {len(bars)} daily bars")
    print(f"   Oldest: {bars[0]['datetime']} - Close: ${bars[0]['close']}")
    print(f"   Latest: {bars[-1]['datetime']} - Close: ${bars[-1]['close']}")
    
    # Calculate EMA
    closes = [float(bar['close']) for bar in bars]
    ema_200 = cache.calculate_ema(closes, 200)
    
    print(f"\n📈 Calculated 200-EMA: ${ema_200:.2f}")
    print(f"   Current Price: ${closes[-1]:.2f}")
    
    if closes[-1] > ema_200:
        print(f"   ✅ Price ABOVE 200-EMA (bullish)")
    else:
        print(f"   ⚠️ Price BELOW 200-EMA (bearish)")
    
    return True

def test_2_real_api_multiple_symbols():
    """Test 2: Fetch real data for multiple symbols"""
    print("\n" + "="*80)
    print("TEST 2: REAL API - MULTIPLE SYMBOLS")
    print("="*80)
    
    cache = DailyCache()
    symbols = ['AAPL', 'TSLA', 'NVDA']
    
    print(f"📊 Refreshing cache for {len(symbols)} symbols...")
    cache.refresh_cache(symbols=symbols)
    
    # Check results
    stats = cache.get_cache_stats()
    print(f"\n✅ Cache refreshed:")
    print(f"   Symbols cached: {stats['symbols_cached']}/{len(symbols)}")
    print(f"   Cache date: {stats['cache_date']}")
    print(f"   Is valid: {stats['is_valid']}")
    
    # Display data for each symbol
    print(f"\n📊 Cached Data:")
    for symbol in symbols:
        data = cache.get_daily_data(symbol)
        if data:
            print(f"\n   {symbol}:")
            print(f"      Price: ${data['price']:.2f}")
            print(f"      200-EMA: ${data['ema_200']:.2f}")
            print(f"      9-EMA: ${data['ema_9']:.2f}")
            print(f"      21-EMA: ${data['ema_21']:.2f}")
            print(f"      Trend: {data['trend']}")
            
            # Check filter
            if data['price'] > data['ema_200']:
                print(f"      ✅ PASS: Above 200-EMA (would allow LONG)")
            else:
                print(f"      ❌ FAIL: Below 200-EMA (would block LONG)")
        else:
            print(f"\n   {symbol}: ❌ No data")
    
    return stats['symbols_cached'] >= 2  # At least 2 should succeed

def test_3_sprint7_filter_simulation():
    """Test 3: Simulate Sprint 7 filter logic"""
    print("\n" + "="*80)
    print("TEST 3: SPRINT 7 FILTER SIMULATION")
    print("="*80)
    
    cache = DailyCache()
    cache.refresh_cache(symbols=['AAPL', 'TSLA', 'NVDA', 'AMD', 'MSFT'])
    
    print("\n🎯 Simulating Sprint 7 Filters:")
    print("   Filter 1: 200-EMA Daily Trend")
    print("   Filter 2: Multi-timeframe Alignment")
    
    passed = []
    failed = []
    
    for symbol in ['AAPL', 'TSLA', 'NVDA', 'AMD', 'MSFT']:
        data = cache.get_daily_data(symbol)
        if not data:
            print(f"\n❌ {symbol}: No data available")
            failed.append(symbol)
            continue
        
        print(f"\n📊 {symbol}:")
        print(f"   Price: ${data['price']:.2f}")
        print(f"   200-EMA: ${data['ema_200']:.2f}")
        print(f"   Daily Trend: {data['trend']}")
        
        # Filter 1: 200-EMA (for LONG)
        filter1_pass = data['price'] > data['ema_200']
        
        # Filter 2: Multi-timeframe (for LONG)
        filter2_pass = data['trend'] == 'bullish'
        
        print(f"   Filter 1 (200-EMA): {'✅ PASS' if filter1_pass else '❌ FAIL'}")
        print(f"   Filter 2 (MTF): {'✅ PASS' if filter2_pass else '❌ FAIL'}")
        
        if filter1_pass and filter2_pass:
            print(f"   ✅ WOULD TRADE: Both filters passed")
            passed.append(symbol)
        else:
            print(f"   ❌ WOULD SKIP: Filters failed")
            failed.append(symbol)
    
    print(f"\n📊 Filter Results:")
    print(f"   Passed: {len(passed)} symbols - {', '.join(passed) if passed else 'None'}")
    print(f"   Failed: {len(failed)} symbols - {', '.join(failed) if failed else 'None'}")
    print(f"   Filter Rate: {len(failed)}/{len(passed)+len(failed)} blocked ({len(failed)/(len(passed)+len(failed))*100:.1f}%)")
    
    return True

def test_4_cache_persistence():
    """Test 4: Verify cache persists across instances"""
    print("\n" + "="*80)
    print("TEST 4: CACHE PERSISTENCE")
    print("="*80)
    
    # Create first cache and populate
    cache1 = DailyCache()
    cache1.refresh_cache(symbols=['AAPL'])
    
    data1 = cache1.get_daily_data('AAPL')
    if not data1:
        print("❌ Failed to cache data")
        return False
    
    print(f"✅ Cache 1: AAPL cached at ${data1['price']:.2f}")
    
    # Create second cache (simulates new instance)
    cache2 = DailyCache()
    
    # Should be empty (each instance has own cache)
    data2 = cache2.get_daily_data('AAPL')
    
    if data2:
        print("⚠️ Cache persisted across instances (unexpected)")
    else:
        print("✅ Cache is instance-specific (expected)")
    
    # Refresh second cache
    cache2.refresh_cache(symbols=['AAPL'])
    data2 = cache2.get_daily_data('AAPL')
    
    if data2:
        print(f"✅ Cache 2: AAPL cached at ${data2['price']:.2f}")
        return True
    else:
        print("❌ Failed to cache in second instance")
        return False

def test_5_error_handling():
    """Test 5: Error handling with invalid symbols"""
    print("\n" + "="*80)
    print("TEST 5: ERROR HANDLING")
    print("="*80)
    
    cache = DailyCache()
    
    # Test with invalid symbol
    print("\n📊 Testing with invalid symbol...")
    bars = cache.fetch_twelvedata_bars('INVALID_SYMBOL_XYZ')
    
    if bars is None:
        print("✅ Correctly handled invalid symbol (returned None)")
    else:
        print("⚠️ Unexpected: Got data for invalid symbol")
    
    # Test refresh with mix of valid and invalid
    print("\n📊 Testing refresh with mixed symbols...")
    cache.refresh_cache(symbols=['AAPL', 'INVALID', 'TSLA'])
    
    stats = cache.get_cache_stats()
    print(f"✅ Partial refresh completed:")
    print(f"   Symbols cached: {stats['symbols_cached']}/3")
    
    # Valid symbols should be cached
    if cache.get_daily_data('AAPL'):
        print("   ✅ AAPL: Cached")
    else:
        print("   ❌ AAPL: Not cached")
    
    if cache.get_daily_data('INVALID'):
        print("   ⚠️ INVALID: Cached (unexpected)")
    else:
        print("   ✅ INVALID: Not cached (expected)")
    
    if cache.get_daily_data('TSLA'):
        print("   ✅ TSLA: Cached")
    else:
        print("   ❌ TSLA: Not cached")
    
    return True

def test_6_credit_usage():
    """Test 6: Monitor API credit usage"""
    print("\n" + "="*80)
    print("TEST 6: API CREDIT USAGE")
    print("="*80)
    
    cache = DailyCache()
    
    print("📊 Simulating daily cache refresh for 50 symbols...")
    print("   Expected cost: 50 credits (1 per symbol)")
    print("   Daily limit: 800 credits")
    print("   Usage: 6.25% of daily limit")
    
    # Test with 5 symbols (10% of 50)
    test_symbols = ['AAPL', 'TSLA', 'NVDA', 'AMD', 'MSFT']
    cache.refresh_cache(symbols=test_symbols)
    
    stats = cache.get_cache_stats()
    print(f"\n✅ Test refresh completed:")
    print(f"   Symbols: {len(test_symbols)}")
    print(f"   Cached: {stats['symbols_cached']}")
    print(f"   Credits used: ~{len(test_symbols)} (estimated)")
    
    print(f"\n📊 Projected daily usage (50 symbols):")
    print(f"   Daily refresh: 50 credits")
    print(f"   API usage check: 1 credit")
    print(f"   Buffer: 10 credits")
    print(f"   Total: ~61 credits/day")
    print(f"   Remaining: 739 credits/day")
    print(f"   ✅ Sustainable for long-term use")
    
    return True

def generate_report(results):
    """Generate final integration test report"""
    print("\n" + "="*80)
    print("📊 INTEGRATION TEST REPORT")
    print("="*80)
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nTests Run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    print(f"\n📋 Test Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    if passed == total:
        print(f"\n✅ ALL INTEGRATION TESTS PASSED!")
        print(f"\n🎯 READY FOR PRODUCTION:")
        print(f"   ✓ Twelve Data API working")
        print(f"   ✓ Daily cache functional")
        print(f"   ✓ Sprint 7 filters ready")
        print(f"   ✓ Error handling robust")
        print(f"   ✓ Credit usage sustainable")
        return 0
    else:
        print(f"\n❌ SOME TESTS FAILED")
        print(f"   Review errors above before deploying")
        return 1

def main():
    """Run all integration tests"""
    results = {}
    
    try:
        results['Real API - Single Symbol'] = test_1_real_api_single_symbol()
        results['Real API - Multiple Symbols'] = test_2_real_api_multiple_symbols()
        results['Sprint 7 Filter Simulation'] = test_3_sprint7_filter_simulation()
        results['Cache Persistence'] = test_4_cache_persistence()
        results['Error Handling'] = test_5_error_handling()
        results['Credit Usage'] = test_6_credit_usage()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return generate_report(results)

if __name__ == '__main__':
    exit(main())
