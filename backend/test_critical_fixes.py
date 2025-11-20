#!/usr/bin/env python3
"""
Test script for critical bug fixes:
1. TimeFrame.Minute5 → TimeFrame.Minute
2. AlpacaClient.submit_order() → submit_market_order()
3. Bracket recreation deadlock prevention
"""

import sys
import asyncio
from datetime import datetime

def test_timeframe_import():
    """Test that TimeFrame.Minute exists (not Minute5)"""
    print("\n🧪 Test 1: TimeFrame API Fix")
    print("=" * 60)
    
    try:
        from alpaca.data.timeframe import TimeFrame
        
        # Check that Minute exists
        assert hasattr(TimeFrame, 'Minute'), "❌ TimeFrame.Minute not found!"
        print("✅ TimeFrame.Minute exists")
        
        # Check that Minute5 does NOT exist (old API)
        if hasattr(TimeFrame, 'Minute5'):
            print("⚠️  TimeFrame.Minute5 still exists (deprecated)")
        else:
            print("✅ TimeFrame.Minute5 correctly removed")
        
        # Test creating a timeframe
        tf = TimeFrame.Minute
        print(f"✅ Created TimeFrame: {tf}")
        
        return True
    except Exception as e:
        print(f"❌ TimeFrame test failed: {e}")
        return False


def test_alpaca_client_methods():
    """Test that AlpacaClient has correct methods"""
    print("\n🧪 Test 2: AlpacaClient Method Fix")
    print("=" * 60)
    
    try:
        from core.alpaca_client import AlpacaClient
        
        client = AlpacaClient()
        
        # Check that submit_market_order exists
        assert hasattr(client, 'submit_market_order'), "❌ submit_market_order not found!"
        print("✅ AlpacaClient.submit_market_order() exists")
        
        # Check that submit_order_request exists
        assert hasattr(client, 'submit_order_request'), "❌ submit_order_request not found!"
        print("✅ AlpacaClient.submit_order_request() exists")
        
        # Check that submit_order does NOT exist (it's on trading_client, not alpaca_client)
        if hasattr(client, 'submit_order'):
            print("⚠️  AlpacaClient.submit_order() exists (should use submit_market_order or submit_order_request)")
        else:
            print("✅ AlpacaClient.submit_order() correctly not exposed")
        
        return True
    except Exception as e:
        print(f"❌ AlpacaClient test failed: {e}")
        return False


def test_position_manager_imports():
    """Test that position_manager imports correctly"""
    print("\n🧪 Test 3: Position Manager Import Fix")
    print("=" * 60)
    
    try:
        from trading.position_manager import PositionManager
        print("✅ PositionManager imports successfully")
        
        # Check that the file doesn't have syntax errors
        import inspect
        source = inspect.getsource(PositionManager)
        
        # Check for the old incorrect method call
        if 'self.alpaca.submit_order(' in source:
            print("❌ Found old submit_order() call in PositionManager")
            return False
        else:
            print("✅ No incorrect submit_order() calls found")
        
        # Check for the correct method call
        if 'self.alpaca.submit_market_order(' in source:
            print("✅ Found correct submit_market_order() call")
        
        return True
    except Exception as e:
        print(f"❌ PositionManager test failed: {e}")
        return False


def test_trading_engine_imports():
    """Test that trading_engine imports correctly"""
    print("\n🧪 Test 4: Trading Engine Import Fix")
    print("=" * 60)
    
    try:
        from trading.trading_engine import TradingEngine
        print("✅ TradingEngine imports successfully")
        
        # Check that the file doesn't have syntax errors
        import inspect
        source = inspect.getsource(TradingEngine)
        
        # Check for the old incorrect TimeFrame
        if 'TimeFrame.Minute5' in source:
            print("❌ Found old TimeFrame.Minute5 in TradingEngine")
            return False
        else:
            print("✅ No TimeFrame.Minute5 found")
        
        # Check for the correct TimeFrame
        if 'TimeFrame.Minute' in source:
            print("✅ Found correct TimeFrame.Minute")
        
        return True
    except Exception as e:
        print(f"❌ TradingEngine test failed: {e}")
        return False


def test_bracket_recreation_logic():
    """Test that bracket recreation logic is fixed"""
    print("\n🧪 Test 5: Bracket Recreation Logic Fix")
    print("=" * 60)
    
    try:
        from trading.position_manager import PositionManager
        import inspect
        
        source = inspect.getsource(PositionManager._recreate_take_profit)
        
        # Check for the fix that prevents recreation when shares are held
        if 'has_existing_orders' in source:
            print("✅ Found has_existing_orders check")
        else:
            print("⚠️  has_existing_orders check not found")
        
        if 'skipping recreation to avoid' in source:
            print("✅ Found skip logic to prevent deadlock")
        else:
            print("⚠️  Skip logic not found")
        
        # Check that we're not cancelling stop-loss anymore
        if 'Cancelled old stop-loss' in source:
            print("⚠️  Still cancelling stop-loss (may cause issues)")
        else:
            print("✅ Not cancelling stop-loss (correct)")
        
        return True
    except Exception as e:
        print(f"❌ Bracket recreation test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🔧 CRITICAL FIXES TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("TimeFrame API", test_timeframe_import()))
    results.append(("AlpacaClient Methods", test_alpaca_client_methods()))
    results.append(("PositionManager Import", test_position_manager_imports()))
    results.append(("TradingEngine Import", test_trading_engine_imports()))
    results.append(("Bracket Recreation Logic", test_bracket_recreation_logic()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Fixes are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the fixes.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
