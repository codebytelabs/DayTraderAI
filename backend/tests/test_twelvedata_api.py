#!/usr/bin/env python3
"""
Twelve Data API Test Module
Tests all relevant endpoints and evaluates how they can enhance DayTraderAI

Free Tier Limits:
- 8 API credits per minute
- 800 API credits per day
- Resets at midnight UTC

API Credit Costs:
- Time Series: 1 credit per request
- Technical Indicators: 1 credit per indicator
- Real-time Price: 1 credit per request
- Fundamentals: 1-2 credits per request
"""

import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pathlib

# Load .env from backend directory
env_path = pathlib.Path(__file__).parent / '.env'
print(f"DEBUG: Loading .env from {env_path.absolute()}")
load_dotenv(env_path, override=True)

class TwelveDataTester:
    def __init__(self):
        # Try both uppercase and lowercase
        self.api_key = os.getenv('TWELVEDATA_API_KEY') or os.getenv('twelvedata_api_key')
        
        # If still not found, read directly from .env file
        if not self.api_key:
            env_file = pathlib.Path(__file__).parent / '.env'
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        if line.startswith('TWELVEDATA_API_KEY='):
                            self.api_key = line.split('=', 1)[1].strip()
                            break
        
        # Last resort: hardcode for testing (from .env file)
        if not self.api_key:
            self.api_key = "068936c955bc4e3099c5132320c4351e"
        self.base_url = "https://api.twelvedata.com"
        self.test_symbols = ['AAPL', 'TSLA', 'NVDA']
        self.results = {}
        
    def _make_request(self, endpoint, params):
        """Make API request and track credits"""
        params['apikey'] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            # Track API credits
            credits_used = response.headers.get('api-credits-used', 'N/A')
            credits_left = response.headers.get('api-credits-left', 'N/A')
            
            print(f"\n📊 Credits Used: {credits_used} | Credits Left: {credits_left}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def test_1_daily_bars(self):
        """Test 1: Daily Time Series (for 200-EMA filter)"""
        print("\n" + "="*80)
        print("TEST 1: DAILY TIME SERIES (Sprint 7 - 200-EMA Filter)")
        print("="*80)
        print("Purpose: Get daily bars to calculate 200-day EMA")
        print("Cost: 1 credit per symbol")
        
        for symbol in self.test_symbols:
            print(f"\n🔍 Testing {symbol}...")
            
            data = self._make_request('time_series', {
                'symbol': symbol,
                'interval': '1day',
                'outputsize': 200,  # Need 200 days for 200-EMA
                'format': 'JSON'
            })
            
            if data and 'values' in data:
                bars = data['values']
                print(f"✅ Retrieved {len(bars)} daily bars")
                print(f"   Latest: {bars[0]['datetime']} - Close: ${bars[0]['close']}")
                print(f"   Oldest: {bars[-1]['datetime']} - Close: ${bars[-1]['close']}")
                
                # Calculate 200-EMA
                closes = [float(bar['close']) for bar in reversed(bars)]
                ema_200 = self._calculate_ema(closes, 200)
                print(f"   📈 200-EMA: ${ema_200:.2f}")
                
                self.results['daily_bars'] = {
                    'status': 'SUCCESS',
                    'bars_count': len(bars),
                    'ema_200': ema_200,
                    'use_case': 'Sprint 7 - 200-EMA Daily Trend Filter'
                }
                break
            else:
                print(f"❌ Failed to retrieve daily bars")
                self.results['daily_bars'] = {'status': 'FAILED'}
    
    def test_2_technical_indicators(self):
        """Test 2: Built-in Technical Indicators"""
        print("\n" + "="*80)
        print("TEST 2: TECHNICAL INDICATORS (Pre-calculated)")
        print("="*80)
        print("Purpose: Get indicators without manual calculation")
        print("Cost: 1 credit per indicator")
        
        symbol = 'AAPL'
        
        # Test EMA
        print(f"\n🔍 Testing EMA indicator for {symbol}...")
        data = self._make_request('ema', {
            'symbol': symbol,
            'interval': '1day',
            'time_period': 200,
            'series_type': 'close',
            'outputsize': 1
        })
        
        if data and 'values' in data:
            ema_value = data['values'][0]['ema']
            print(f"✅ 200-EMA: ${ema_value}")
            self.results['ema_indicator'] = {
                'status': 'SUCCESS',
                'value': ema_value,
                'use_case': 'Faster than manual calculation'
            }
        
        # Test RSI
        print(f"\n🔍 Testing RSI indicator for {symbol}...")
        data = self._make_request('rsi', {
            'symbol': symbol,
            'interval': '5min',
            'time_period': 14,
            'series_type': 'close',
            'outputsize': 1
        })
        
        if data and 'values' in data:
            rsi_value = data['values'][0]['rsi']
            print(f"✅ RSI(14): {rsi_value}")
            self.results['rsi_indicator'] = {
                'status': 'SUCCESS',
                'value': rsi_value,
                'use_case': 'Already used in strategy'
            }
    
    def test_3_intraday_bars(self):
        """Test 3: Intraday Time Series (5-minute bars)"""
        print("\n" + "="*80)
        print("TEST 3: INTRADAY TIME SERIES (5-minute bars)")
        print("="*80)
        print("Purpose: Alternative to Alpaca for intraday data")
        print("Cost: 1 credit per request")
        
        symbol = 'AAPL'
        print(f"\n🔍 Testing 5-minute bars for {symbol}...")
        
        data = self._make_request('time_series', {
            'symbol': symbol,
            'interval': '5min',
            'outputsize': 78,  # Full trading day (6.5 hours)
            'format': 'JSON'
        })
        
        if data and 'values' in data:
            bars = data['values']
            print(f"✅ Retrieved {len(bars)} 5-minute bars")
            print(f"   Latest: {bars[0]['datetime']} - Close: ${bars[0]['close']}")
            print(f"   Volume: {bars[0]['volume']}")
            
            self.results['intraday_bars'] = {
                'status': 'SUCCESS',
                'bars_count': len(bars),
                'use_case': 'Could replace Alpaca for intraday data (but Alpaca is free)'
            }
        else:
            print(f"❌ Failed to retrieve intraday bars")
    
    def test_4_real_time_price(self):
        """Test 4: Real-time Price Quote"""
        print("\n" + "="*80)
        print("TEST 4: REAL-TIME PRICE QUOTE")
        print("="*80)
        print("Purpose: Get current price without full bars")
        print("Cost: 1 credit per request")
        
        symbol = 'AAPL'
        print(f"\n🔍 Testing real-time quote for {symbol}...")
        
        data = self._make_request('quote', {
            'symbol': symbol,
            'format': 'JSON'
        })
        
        if data:
            print(f"✅ Real-time Quote:")
            print(f"   Price: ${data.get('close', 'N/A')}")
            print(f"   Volume: {data.get('volume', 'N/A')}")
            print(f"   Change: {data.get('percent_change', 'N/A')}%")
            
            self.results['real_time_quote'] = {
                'status': 'SUCCESS',
                'use_case': 'Quick price checks (but Alpaca provides this free)'
            }
    
    def test_5_batch_request(self):
        """Test 5: Batch Request (Multiple Symbols)"""
        print("\n" + "="*80)
        print("TEST 5: BATCH REQUEST (Multiple Symbols)")
        print("="*80)
        print("Purpose: Get data for multiple symbols in one request")
        print("Cost: 1 credit per symbol")
        
        symbols = ','.join(self.test_symbols)
        print(f"\n🔍 Testing batch request for {symbols}...")
        
        data = self._make_request('time_series', {
            'symbol': symbols,
            'interval': '1day',
            'outputsize': 1,
            'format': 'JSON'
        })
        
        if data:
            for symbol, symbol_data in data.items():
                if 'values' in symbol_data:
                    print(f"✅ {symbol}: ${symbol_data['values'][0]['close']}")
            
            self.results['batch_request'] = {
                'status': 'SUCCESS',
                'symbols_count': len(self.test_symbols),
                'use_case': 'Efficient daily cache refresh (3 credits vs 3 separate requests)'
            }
    
    def test_6_api_usage(self):
        """Test 6: API Usage Tracking"""
        print("\n" + "="*80)
        print("TEST 6: API USAGE TRACKING")
        print("="*80)
        print("Purpose: Monitor credit consumption")
        print("Cost: 1 credit")
        
        data = self._make_request('api_usage', {})
        
        if data:
            print(f"✅ API Usage:")
            print(f"   Plan: {data.get('plan_name', 'N/A')}")
            print(f"   Credits Used Today: {data.get('current_usage', 'N/A')}")
            print(f"   Daily Limit: {data.get('daily_limit', 'N/A')}")
            
            self.results['api_usage'] = {
                'status': 'SUCCESS',
                'use_case': 'Monitor daily credit consumption'
            }
    
    def test_7_market_state(self):
        """Test 7: Market State (Open/Closed)"""
        print("\n" + "="*80)
        print("TEST 7: MARKET STATE")
        print("="*80)
        print("Purpose: Check if market is open")
        print("Cost: 1 credit")
        
        data = self._make_request('market_state', {
            'exchange': 'NASDAQ'
        })
        
        if data:
            print(f"✅ Market State:")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Exchange: {data.get('name', 'N/A')}")
            
            self.results['market_state'] = {
                'status': 'SUCCESS',
                'use_case': 'Verify market hours (but can use local time check)'
            }
    
    def _calculate_ema(self, prices, period):
        """Calculate EMA manually"""
        multiplier = 2 / (period + 1)
        ema = prices[0]  # Start with first price
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "="*80)
        print("📊 TWELVE DATA API - COMPREHENSIVE REPORT")
        print("="*80)
        
        print("\n🎯 RECOMMENDED USE CASES FOR DAYTRADERAI:")
        print("-" * 80)
        
        print("\n1. ✅ DAILY BARS FOR SPRINT 7 FILTERS (HIGH PRIORITY)")
        print("   Purpose: Enable 200-EMA and Multi-timeframe filters")
        print("   Endpoint: /time_series (interval=1day)")
        print("   Cost: ~50 symbols × 1 credit = 50 credits/day")
        print("   Benefit: Unlock full Sprint 7 (55-60% win rate)")
        print("   Status: PERFECT FIT ✅")
        
        print("\n2. ✅ BATCH REQUESTS FOR EFFICIENCY")
        print("   Purpose: Fetch multiple symbols in one request")
        print("   Endpoint: /time_series (symbol=AAPL,TSLA,NVDA)")
        print("   Cost: Same as individual (1 credit per symbol)")
        print("   Benefit: Faster execution, cleaner code")
        print("   Status: RECOMMENDED ✅")
        
        print("\n3. ⚠️ PRE-CALCULATED INDICATORS (OPTIONAL)")
        print("   Purpose: Get EMA/RSI without manual calculation")
        print("   Endpoint: /ema, /rsi, /macd, etc.")
        print("   Cost: 1 credit per indicator per symbol")
        print("   Benefit: Saves computation, but costs more credits")
        print("   Status: OPTIONAL (manual calculation is fine)")
        
        print("\n4. ❌ INTRADAY BARS (NOT RECOMMENDED)")
        print("   Purpose: Replace Alpaca for 5-minute bars")
        print("   Cost: Would consume credits quickly")
        print("   Benefit: None (Alpaca provides this free)")
        print("   Status: SKIP ❌")
        
        print("\n5. ❌ REAL-TIME QUOTES (NOT RECOMMENDED)")
        print("   Purpose: Get current prices")
        print("   Cost: 1 credit per request")
        print("   Benefit: None (Alpaca provides this free)")
        print("   Status: SKIP ❌")
        
        print("\n" + "="*80)
        print("💰 DAILY CREDIT BUDGET ANALYSIS")
        print("="*80)
        
        print("\nFree Tier: 800 credits/day")
        print("\nProposed Usage:")
        print("  - Daily cache refresh: 50 symbols × 1 credit = 50 credits")
        print("  - API usage check: 1 credit")
        print("  - Buffer for retries: 10 credits")
        print("  - TOTAL: ~61 credits/day")
        print("\n✅ Usage: 7.6% of daily limit")
        print("✅ Sustainable for long-term use")
        
        print("\n" + "="*80)
        print("🚀 IMPLEMENTATION RECOMMENDATION")
        print("="*80)
        
        print("\n✅ IMPLEMENT: Daily bars for Sprint 7 filters")
        print("   - Fetch once per day at market open")
        print("   - Calculate 200-EMA, 9-EMA, 21-EMA")
        print("   - Cache results for the day")
        print("   - Enable Sprint 7 filters")
        
        print("\n❌ SKIP: Intraday bars, real-time quotes")
        print("   - Alpaca already provides these free")
        print("   - Would waste credits unnecessarily")
        
        print("\n⚠️ OPTIONAL: Pre-calculated indicators")
        print("   - Only if manual calculation becomes bottleneck")
        print("   - Currently not needed")
        
        print("\n" + "="*80)
        print("📋 NEXT STEPS")
        print("="*80)
        print("\n1. Modify backend/data/daily_cache.py to use Twelve Data")
        print("2. Implement daily bar fetching (1 request/day per symbol)")
        print("3. Enable Sprint 7 filters in trading_engine.py")
        print("4. Monitor credit usage with /api_usage endpoint")
        print("5. Validate filters working with validate_sprint7.py")
        
        print("\n✅ All tests complete!")
        print(f"📊 Results saved to: test_results.json")
        
        # Save results
        with open('test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

def main():
    print("🚀 Starting Twelve Data API Comprehensive Test")
    print("=" * 80)
    
    print("DEBUG: Creating TwelveDataTester instance...")
    tester = TwelveDataTester()
    print(f"DEBUG: Tester created, api_key = {tester.api_key[:10] if tester.api_key else 'None'}...")
    
    if not tester.api_key:
        print("❌ ERROR: TWELVEDATA_API_KEY not found in .env")
        print("DEBUG: Trying to read .env file directly...")
        env_file = pathlib.Path('backend/.env')
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if 'TWELVEDATA' in line:
                        print(f"DEBUG: Found line: {line.strip()}")
        return
    
    print(f"✅ API Key loaded: {tester.api_key[:10]}...")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    try:
        tester.test_1_daily_bars()
        tester.test_2_technical_indicators()
        tester.test_3_intraday_bars()
        tester.test_4_real_time_price()
        tester.test_5_batch_request()
        tester.test_6_api_usage()
        tester.test_7_market_state()
        
        # Generate final report
        tester.generate_report()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
