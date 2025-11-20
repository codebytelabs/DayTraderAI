#!/usr/bin/env python3
"""
Comprehensive Autopilot Test Script
Tests all components needed for automated trading
"""

import asyncio
from datetime import datetime, timedelta
from config import settings
from core.alpaca_client import AlpacaClient
from data.market_data import MarketDataManager
from core.supabase_client import SupabaseClient
from trading.strategy import EMAStrategy
from trading.order_manager import OrderManager
from trading.risk_manager import RiskManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def test_alpaca_connection():
    """Test 1: Alpaca API connection"""
    print("\n" + "="*80)
    print("TEST 1: Alpaca API Connection")
    print("="*80)
    
    try:
        client = AlpacaClient()
        account = client.get_account()
        
        print(f"✅ Connected to Alpaca")
        print(f"   Account: {account.account_number}")
        print(f"   Equity: ${float(account.equity):,.2f}")
        print(f"   Cash: ${float(account.cash):,.2f}")
        print(f"   Buying Power: ${float(account.buying_power):,.2f}")
        
        return True, client
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False, None


async def test_market_status(client):
    """Test 2: Market status check"""
    print("\n" + "="*80)
    print("TEST 2: Market Status")
    print("="*80)
    
    try:
        clock = client.get_clock()
        is_open = clock.is_open
        
        print(f"Market Status: {'🟢 OPEN' if is_open else '🔴 CLOSED'}")
        print(f"Current Time: {clock.timestamp}")
        print(f"Next Open: {clock.next_open}")
        print(f"Next Close: {clock.next_close}")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


async def test_data_fetching(client):
    """Test 3: Market data fetching with IEX feed"""
    print("\n" + "="*80)
    print("TEST 3: Market Data Fetching (IEX Feed)")
    print("="*80)
    
    try:
        symbols = ["AAPL", "MSFT", "NVDA"]
        print(f"Fetching data for: {', '.join(symbols)}")
        
        # Test latest bars
        latest_bars = client.get_latest_bars(symbols)
        
        if latest_bars:
            print(f"✅ Successfully fetched latest bars")
            for symbol in symbols:
                if symbol in latest_bars:
                    bar = latest_bars[symbol]
                    print(f"   {symbol}: ${bar.close:.2f} (Vol: {bar.volume:,})")
                else:
                    print(f"   ⚠️  {symbol}: No data")
        else:
            print(f"❌ No bars returned")
            return False
        
        # Test historical bars
        print(f"\nFetching historical bars (last 100 minutes)...")
        from alpaca.data.timeframe import TimeFrame
        
        bars = client.get_bars(
            symbols=symbols,
            timeframe=TimeFrame.Minute,
            start=datetime.now() - timedelta(hours=2),
            limit=100
        )
        
        if bars is not None and not bars.empty:
            print(f"✅ Successfully fetched {len(bars)} historical bars")
            print(f"   Date range: {bars.index[0]} to {bars.index[-1]}")
        else:
            print(f"⚠️  No historical bars (market may be closed)")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_feature_calculation(client):
    """Test 4: Feature calculation (EMA, ATR, etc.)"""
    print("\n" + "="*80)
    print("TEST 4: Feature Calculation")
    print("="*80)
    
    try:
        supabase = SupabaseClient()
        market_data = MarketDataManager(client, supabase)
        
        symbols = ["AAPL", "MSFT"]
        print(f"Calculating features for: {', '.join(symbols)}")
        
        market_data.update_all_features(symbols)
        
        for symbol in symbols:
            features = market_data.get_latest_features(symbol)
            if features:
                print(f"✅ {symbol} features:")
                print(f"   Price: ${features.get('price', 0):.2f}")
                print(f"   EMA(9): ${features.get('ema_short', 0):.2f}")
                print(f"   EMA(21): ${features.get('ema_long', 0):.2f}")
                print(f"   ATR: ${features.get('atr', 0):.2f}")
                print(f"   Volume: {features.get('volume', 0):,}")
            else:
                print(f"⚠️  {symbol}: No features calculated")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_signal_detection(client):
    """Test 5: Signal detection"""
    print("\n" + "="*80)
    print("TEST 5: Signal Detection")
    print("="*80)
    
    try:
        supabase = SupabaseClient()
        risk_manager = RiskManager(client)
        order_manager = OrderManager(client, supabase, risk_manager)
        strategy = EMAStrategy(order_manager)
        market_data = MarketDataManager(client, supabase)
        
        symbols = settings.watchlist_symbols[:5]  # Test first 5
        print(f"Checking signals for: {', '.join(symbols)}")
        
        market_data.update_all_features(symbols)
        
        signals_found = 0
        for symbol in symbols:
            features = market_data.get_latest_features(symbol)
            if features:
                signal = strategy.evaluate(symbol, features)
                if signal:
                    print(f"🚨 {symbol}: {signal.upper()} signal detected!")
                    signals_found += 1
                else:
                    print(f"   {symbol}: No signal")
            else:
                print(f"   {symbol}: No features")
        
        if signals_found > 0:
            print(f"\n✅ Found {signals_found} signal(s)")
        else:
            print(f"\n➖ No signals found (this is normal if no crossovers)")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_connection():
    """Test 6: Database connection"""
    print("\n" + "="*80)
    print("TEST 6: Database Connection")
    print("="*80)
    
    try:
        supabase = SupabaseClient()
        
        # Test metrics insert
        test_metric = {
            "equity": 100000.0,
            "cash": 50000.0,
            "buying_power": 100000.0,
            "daily_pl": 0.0,
            "daily_pl_pct": 0.0,
            "total_pl": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "wins": 0,
            "losses": 0,
            "total_trades": 0,
            "open_positions": 0,
            "circuit_breaker_triggered": False
        }
        
        supabase.insert_metrics(test_metric)
        print(f"✅ Successfully inserted test metric")
        
        # Test advisory insert with long model name
        test_advisory = {
            "source": "Test",
            "model": "Perplexity (sonar-pro), OpenRouter (openai/gpt-oss-safeguard-20b)",
            "content": "Test advisory",
            "type": "test",
            "confidence": 0.95,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        supabase.insert_advisory(test_advisory)
        print(f"✅ Successfully inserted test advisory (long model name)")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        print(f"   This may indicate database schema needs migration")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🚀 DAYTRADERAI AUTOPILOT DIAGNOSTIC TEST")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Watchlist: {', '.join(settings.watchlist_symbols)}")
    
    results = []
    
    # Test 1: Alpaca connection
    success, client = await test_alpaca_connection()
    results.append(("Alpaca Connection", success))
    
    if not success:
        print("\n❌ Cannot proceed without Alpaca connection")
        return
    
    # Test 2: Market status
    success = await test_market_status(client)
    results.append(("Market Status", success))
    
    # Test 3: Data fetching
    success = await test_data_fetching(client)
    results.append(("Data Fetching", success))
    
    # Test 4: Feature calculation
    success = await test_feature_calculation(client)
    results.append(("Feature Calculation", success))
    
    # Test 5: Signal detection
    success = await test_signal_detection(client)
    results.append(("Signal Detection", success))
    
    # Test 6: Database
    success = await test_database_connection()
    results.append(("Database Connection", success))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL SYSTEMS GO! Autopilot ready for deployment!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")


if __name__ == "__main__":
    asyncio.run(main())
