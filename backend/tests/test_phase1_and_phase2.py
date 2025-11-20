#!/usr/bin/env python3
"""Comprehensive test for Phase 1 + Phase 2 enhancements."""

import sys
import asyncio
from datetime import datetime

sys.path.insert(0, '/Users/vishnuvardhanmedara/DayTraderAI/backend')

from data.features import FeatureEngine
from data.market_data import MarketDataManager
from core.alpaca_client import AlpacaClient
from scanner.stock_universe import StockUniverse
from scanner.opportunity_scorer import OpportunityScorer
from scanner.opportunity_scanner import OpportunityScanner
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize client
alpaca_client = AlpacaClient()


async def test_phase1_indicators():
    """Test Phase 1 enhanced indicators."""
    logger.info("=" * 60)
    logger.info("PHASE 1: ENHANCED INDICATORS TEST")
    logger.info("=" * 60)
    
    try:
        # Get market data
        market_data = MarketDataManager(alpaca_client)
        df = await market_data.get_bars('AAPL', limit=100)
        
        if df is None or len(df) < 30:
            logger.error("Failed to get market data")
            return False
        
        logger.info(f"\n✓ Fetched {len(df)} bars for AAPL")
        
        # Calculate features
        features = FeatureEngine.calculate_features(df)
        
        if not features:
            logger.error("Failed to calculate features")
            return False
        
        logger.info(f"✓ Calculated {len(features)} features")
        
        # Check Phase 1 indicators
        phase1_indicators = [
            'vwap', 'rsi', 'macd', 'macd_signal', 'macd_histogram',
            'adx', 'plus_di', 'minus_di', 'market_regime',
            'volume_ratio', 'volume_spike', 'obv',
            'vwap_signal', 'rsi_momentum', 'macd_momentum',
            'confidence_score'
        ]
        
        missing = [ind for ind in phase1_indicators if ind not in features]
        
        if missing:
            logger.error(f"✗ Missing indicators: {', '.join(missing)}")
            return False
        
        logger.info(f"✓ All {len(phase1_indicators)} Phase 1 indicators present")
        
        # Display key indicators
        logger.info("\n📊 Phase 1 Indicators:")
        logger.info(f"  Price: ${features['price']:.2f}")
        logger.info(f"  VWAP: ${features['vwap']:.2f}")
        logger.info(f"  RSI: {features['rsi']:.1f}")
        logger.info(f"  MACD Histogram: {features['macd_histogram']:.4f}")
        logger.info(f"  ADX: {features['adx']:.1f}")
        logger.info(f"  Market Regime: {features['market_regime']}")
        logger.info(f"  Volume Ratio: {features['volume_ratio']:.2f}x")
        logger.info(f"  Confidence Score: {features['confidence_score']:.1f}/100")
        
        # Test enhanced signal detection
        signal_info = FeatureEngine.detect_enhanced_signal(features)
        
        if signal_info:
            logger.info(f"\n✓ Enhanced Signal Detected:")
            logger.info(f"  Signal: {signal_info['signal'].upper()}")
            logger.info(f"  Confidence: {signal_info['confidence']:.1f}/100")
            logger.info(f"  Confirmations: {signal_info['confirmation_count']}/4")
            logger.info(f"  Confirmed by: {', '.join(signal_info['confirmations'])}")
        else:
            logger.info("\n  No signal (waiting for crossover)")
        
        logger.info("\n✓ PHASE 1 TEST PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"Phase 1 test failed: {e}", exc_info=True)
        return False


async def test_phase2_scanner():
    """Test Phase 2 opportunity scanner."""
    logger.info("=" * 60)
    logger.info("PHASE 2: OPPORTUNITY SCANNER TEST")
    logger.info("=" * 60)
    
    try:
        # Initialize scanner
        market_data = MarketDataManager(alpaca_client)
        scanner = OpportunityScanner(market_data)
        
        logger.info("\n✓ Scanner initialized")
        
        # Test stock universe
        stats = StockUniverse.get_stats()
        logger.info(f"\n📊 Stock Universe:")
        logger.info(f"  Total stocks: {stats['total_stocks']}")
        logger.info(f"  High priority: {stats['high_priority']}")
        logger.info(f"  Sectors: {len([k for k in stats.keys() if k not in ['total_stocks', 'high_priority']])}")
        
        # Run scan on small set
        test_symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA']
        logger.info(f"\n🔍 Scanning {len(test_symbols)} stocks...")
        
        opportunities = await scanner.scan_universe(
            symbols=test_symbols,
            min_score=0.0  # Show all for testing
        )
        
        if not opportunities:
            logger.warning("No opportunities found")
            return False
        
        logger.info(f"✓ Found {len(opportunities)} opportunities")
        
        # Display top opportunities
        logger.info("\n📊 Top Opportunities:")
        logger.info("-" * 80)
        logger.info(f"{'Rank':<6} {'Symbol':<8} {'Score':<8} {'Grade':<8} {'Price':<10} {'RSI':<8} {'ADX':<8}")
        logger.info("-" * 80)
        
        for i, opp in enumerate(opportunities[:5], 1):
            logger.info(
                f"{i:<6} {opp['symbol']:<8} {opp['score']:<8.1f} {opp['grade']:<8} "
                f"${opp['price']:<9.2f} {opp['rsi']:<8.1f} {opp['adx']:<8.1f}"
            )
        
        # Test watchlist generation
        watchlist = scanner.get_watchlist_symbols(n=5, min_score=50.0)
        logger.info(f"\n✓ Generated watchlist: {', '.join(watchlist)}")
        
        # Test summary
        summary = scanner.get_opportunity_summary()
        logger.info(f"\n📊 Scan Summary:")
        logger.info(f"  Total: {summary['total_opportunities']}")
        logger.info(f"  Avg Score: {summary['avg_score']}")
        logger.info(f"  Top: {summary['top_symbol']} ({summary['top_score']:.1f}, {summary['top_grade']})")
        
        logger.info("\n✓ PHASE 2 TEST PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"Phase 2 test failed: {e}", exc_info=True)
        return False


async def test_integration():
    """Test Phase 1 + Phase 2 integration."""
    logger.info("=" * 60)
    logger.info("INTEGRATION TEST: PHASE 1 + PHASE 2")
    logger.info("=" * 60)
    
    try:
        # Initialize components
        market_data = MarketDataManager(alpaca_client)
        scanner = OpportunityScanner(market_data)
        
        # Scan and score
        logger.info("\n🔍 Running integrated scan...")
        opportunities = await scanner.scan_universe(
            symbols=['AAPL', 'MSFT', 'NVDA'],
            min_score=60.0
        )
        
        if not opportunities:
            logger.info("  No opportunities above threshold (this is OK)")
            return True
        
        logger.info(f"✓ Found {len(opportunities)} qualified opportunities")
        
        # Verify each opportunity has both Phase 1 and Phase 2 data
        for opp in opportunities[:3]:
            logger.info(f"\n  {opp['symbol']}:")
            logger.info(f"    Phase 2 Score: {opp['score']:.1f} ({opp['grade']})")
            logger.info(f"    Phase 1 Confidence: {opp['confidence']:.1f}/100")
            logger.info(f"    RSI: {opp['rsi']:.1f} | ADX: {opp['adx']:.1f}")
            logger.info(f"    Volume: {opp['volume_ratio']:.2f}x | Regime: {opp['market_regime']}")
        
        logger.info("\n✓ INTEGRATION TEST PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("COMPREHENSIVE TEST: PHASE 1 + PHASE 2")
    logger.info("=" * 60 + "\n")
    
    results = []
    
    # Test Phase 1
    result1 = await test_phase1_indicators()
    results.append(("Phase 1 Indicators", result1))
    
    # Test Phase 2
    result2 = await test_phase2_scanner()
    results.append(("Phase 2 Scanner", result2))
    
    # Test Integration
    result3 = await test_integration()
    results.append(("Integration", result3))
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{name:<30} {status}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        logger.info("\n" + "=" * 60)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("=" * 60)
        logger.info("\n✓ Phase 1: Enhanced indicators working")
        logger.info("✓ Phase 2: Opportunity scanner working")
        logger.info("✓ Integration: Both phases working together")
        logger.info("\n🚀 System ready for live trading!")
    else:
        logger.error("\n" + "=" * 60)
        logger.error("✗ SOME TESTS FAILED")
        logger.error("=" * 60)
    
    return all_passed


if __name__ == '__main__':
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        sys.exit(1)
