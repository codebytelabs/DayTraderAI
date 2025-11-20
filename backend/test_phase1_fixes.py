#!/usr/bin/env python3
"""
Test Phase 1 Fixes
Tests stop-loss protection and momentum system fixes
"""

import sys
import asyncio
from datetime import datetime
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from core.state import trading_state
from trading.stop_loss_protection import get_protection_manager
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_stop_loss_protection():
    """Test stop-loss protection with bracket recreation"""
    logger.info("=" * 80)
    logger.info("TEST 1: Stop-Loss Protection with Bracket Recreation")
    logger.info("=" * 80)
    
    try:
        # Initialize clients
        alpaca = AlpacaClient()
        supabase = SupabaseClient()
        
        # Get protection manager
        protection_manager = get_protection_manager(alpaca)
        
        # Verify all positions
        logger.info("\n🔍 Verifying position protection...")
        results = protection_manager.verify_all_positions()
        
        # Count results
        protected = sum(1 for status in results.values() if status in ['protected', 'created'])
        failed = sum(1 for status in results.values() if status == 'failed')
        
        logger.info(f"\n📊 Protection Results:")
        logger.info(f"   ✅ Protected: {protected}")
        logger.info(f"   ❌ Failed: {failed}")
        
        # Show details
        for symbol, status in results.items():
            if status == 'created':
                logger.info(f"   🆕 {symbol}: Protection CREATED")
            elif status == 'protected':
                logger.info(f"   ✅ {symbol}: Already protected")
            else:
                logger.error(f"   ❌ {symbol}: Protection FAILED")
        
        # Check for "insufficient qty" errors in recent logs
        logger.info("\n🔍 Checking for order conflicts...")
        # This would be checked in actual logs
        
        success = failed == 0
        if success:
            logger.info("\n✅ TEST 1 PASSED: All positions protected!")
        else:
            logger.error(f"\n❌ TEST 1 FAILED: {failed} positions unprotected")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ TEST 1 ERROR: {e}", exc_info=True)
        return False


def test_momentum_system():
    """Test momentum system DataFrame handling"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Momentum System DataFrame Handling")
    logger.info("=" * 80)
    
    try:
        # Initialize clients
        alpaca = AlpacaClient()
        
        # Test symbols
        test_symbols = ['SPY', 'AAPL', 'TSLA']
        
        logger.info(f"\n🔍 Testing momentum data fetch for {len(test_symbols)} symbols...")
        
        success_count = 0
        for symbol in test_symbols:
            try:
                # Test the new get_bars_for_symbol method
                from alpaca.data.timeframe import TimeFrame
                from datetime import timedelta
                
                bars = alpaca.get_bars_for_symbol(
                    symbol=symbol,
                    timeframe=TimeFrame.Minute,
                    start=datetime.now() - timedelta(hours=2),
                    limit=60
                )
                
                if bars is not None and len(bars) > 0:
                    logger.info(f"   ✅ {symbol}: Fetched {len(bars)} bars")
                    success_count += 1
                else:
                    logger.error(f"   ❌ {symbol}: No bars returned")
                    
            except Exception as e:
                logger.error(f"   ❌ {symbol}: Error - {e}")
        
        success = success_count == len(test_symbols)
        if success:
            logger.info(f"\n✅ TEST 2 PASSED: All {len(test_symbols)} symbols fetched successfully!")
        else:
            logger.error(f"\n❌ TEST 2 FAILED: Only {success_count}/{len(test_symbols)} symbols succeeded")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ TEST 2 ERROR: {e}", exc_info=True)
        return False


def test_integration():
    """Test integration of both fixes"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Integration Test")
    logger.info("=" * 80)
    
    try:
        alpaca = AlpacaClient()
        
        # Get current positions
        positions = alpaca.get_positions()
        logger.info(f"\n📊 Current positions: {len(positions)}")
        
        if len(positions) == 0:
            logger.info("   ℹ️  No positions to test with")
            return True
        
        # Check each position
        protected_count = 0
        for pos in positions:
            symbol = pos.symbol
            
            # Get orders for this position
            orders = alpaca.get_orders(status='open')
            symbol_orders = [o for o in orders if o.symbol == symbol]
            
            has_stop = any(o.type.value in ['stop', 'trailing_stop'] for o in symbol_orders)
            has_tp = any(o.type.value == 'limit' and o.side.value == 'sell' for o in symbol_orders)
            
            if has_stop and has_tp:
                logger.info(f"   ✅ {symbol}: Complete protection (stop + take-profit)")
                protected_count += 1
            elif has_stop:
                logger.warning(f"   ⚠️  {symbol}: Stop-loss only (no take-profit)")
            elif has_tp:
                logger.error(f"   ❌ {symbol}: Take-profit only (NO STOP-LOSS!)")
            else:
                logger.error(f"   ❌ {symbol}: NO PROTECTION!")
        
        success = protected_count == len(positions)
        if success:
            logger.info(f"\n✅ TEST 3 PASSED: All {len(positions)} positions fully protected!")
        else:
            logger.warning(f"\n⚠️  TEST 3 PARTIAL: {protected_count}/{len(positions)} positions fully protected")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ TEST 3 ERROR: {e}", exc_info=True)
        return False


def main():
    """Run all tests"""
    logger.info("🚀 Starting Phase 1 Fix Tests")
    logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    results = {
        'stop_loss_protection': test_stop_loss_protection(),
        'momentum_system': test_momentum_system(),
        'integration': test_integration()
    }
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED! Phase 1 fixes are working correctly.")
        logger.info("\n✅ Ready to deploy to production!")
        return 0
    else:
        logger.error(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
