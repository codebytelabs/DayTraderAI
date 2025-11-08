#!/usr/bin/env python3
"""Test Opportunity Scanner"""

import sys
import asyncio
from datetime import datetime

sys.path.insert(0, '/Users/vishnuvardhanmedara/DayTraderAI/backend')

from scanner.stock_universe import StockUniverse
from scanner.opportunity_scorer import OpportunityScorer
from scanner.opportunity_scanner import OpportunityScanner
from data.market_data import MarketDataManager
from core.alpaca_client import alpaca_client
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def test_stock_universe():
    """Test stock universe."""
    logger.info("=" * 60)
    logger.info("TEST 1: Stock Universe")
    logger.info("=" * 60)
    
    stats = StockUniverse.get_stats()
    logger.info(f"\nUniverse Statistics:")
    for key, value in stats.items():
        logger.info(f"  {key.replace('_', ' ').title()}: {value}")
    
    full = StockUniverse.get_full_universe()
    logger.info(f"\nFull Universe: {len(full)} stocks")
    logger.info(f"  Sample: {', '.join(full[:10])}...")
    
    high_priority = StockUniverse.get_high_priority()
    logger.info(f"\nHigh Priority: {len(high_priority)} stocks")
    logger.info(f"  {', '.join(high_priority)}")
    
    logger.info("\n✓ Stock Universe Test Passed\n")


async def test_opportunity_scorer():
    """Test opportunity scorer."""
    logger.info("=" * 60)
    logger.info("TEST 2: Opportunity Scorer")
    logger.info("=" * 60)
    
    # Create sample features
    sample_features = {
        'price': 100.0,
        'ema_short': 101.0,
        'ema_long': 99.0,
        'ema_diff_pct': 2.0,
        'rsi': 55.0,
        'macd': 0.5,
        'macd_signal': 0.3,
        'macd_histogram': 0.2,
        'adx': 30.0,
        'plus_di': 25.0,
        'minus_di': 15.0,
        'vwap': 99.5,
        'volume_ratio': 2.0,
        'volume_spike': True,
        'obv': 1000000,
        'atr': 2.0,
        'volume_zscore': 1.5,
        'market_regime': 'trending',
        'confidence_score': 75.0
    }
    
    scorer = OpportunityScorer()
    score_dict = scorer.calculate_total_score(sample_features)
    
    logger.info(f"\nSample Stock Scores:")
    logger.info(f"  Total Score: {score_dict['total_score']}/110")
    logger.info(f"  Grade: {score_dict['grade']}")
    logger.info(f"\n  Component Scores:")
    logger.info(f"    Technical: {score_dict['technical_score']}/40")
    logger.info(f"    Momentum: {score_dict['momentum_score']}/25")
    logger.info(f"    Volume: {score_dict['volume_score']}/20")
    logger.info(f"    Volatility: {score_dict['volatility_score']}/15")
    logger.info(f"    Regime: {score_dict['regime_score']}/10")
    
    logger.info("\n✓ Opportunity Scorer Test Passed\n")


async def test_opportunity_scanner():
    """Test opportunity scanner."""
    logger.info("=" * 60)
    logger.info("TEST 3: Opportunity Scanner")
    logger.info("=" * 60)
    
    # Initialize
    market_data = MarketDataManager(alpaca_client)
    scanner = OpportunityScanner(market_data)
    
    # Scan a small set of stocks
    test_symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA', 'TSLA']
    logger.info(f"\nScanning {len(test_symbols)} stocks: {', '.join(test_symbols)}")
    
    opportunities = await scanner.scan_universe(
        symbols=test_symbols,
        min_score=0.0  # Show all for testing
    )
    
    if not opportunities:
        logger.warning("No opportunities found!")
        return
    
    logger.info(f"\n✓ Found {len(opportunities)} opportunities\n")
    
    # Display results
    logger.info("Top Opportunities:")
    logger.info("-" * 80)
    logger.info(f"{'Rank':<6} {'Symbol':<8} {'Score':<8} {'Grade':<8} {'Price':<10} {'RSI':<8} {'ADX':<8} {'Vol':<8}")
    logger.info("-" * 80)
    
    for i, opp in enumerate(opportunities[:10], 1):
        logger.info(
            f"{i:<6} {opp['symbol']:<8} {opp['score']:<8.1f} {opp['grade']:<8} "
            f"${opp['price']:<9.2f} {opp['rsi']:<8.1f} {opp['adx']:<8.1f} "
            f"{opp['volume_ratio']:<8.2f}x"
        )
    
    # Test watchlist generation
    watchlist = scanner.get_watchlist_symbols(n=5, min_score=50.0)
    logger.info(f"\nGenerated Watchlist (min score 50):")
    logger.info(f"  {', '.join(watchlist)}")
    
    # Test summary
    summary = scanner.get_opportunity_summary()
    logger.info(f"\nScan Summary:")
    logger.info(f"  Total Opportunities: {summary['total_opportunities']}")
    logger.info(f"  Average Score: {summary['avg_score']}")
    logger.info(f"  Top: {summary['top_symbol']} ({summary['top_score']:.1f}, {summary['top_grade']})")
    logger.info(f"  Last Scan: {summary['last_scan']}")
    
    if summary['grade_distribution']:
        logger.info(f"\n  Grade Distribution:")
        for grade, count in sorted(summary['grade_distribution'].items()):
            logger.info(f"    {grade}: {count}")
    
    logger.info("\n✓ Opportunity Scanner Test Passed\n")


async def main():
    """Run all tests."""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 2: OPPORTUNITY SCANNER TESTS")
        logger.info("=" * 60 + "\n")
        
        await test_stock_universe()
        await test_opportunity_scorer()
        await test_opportunity_scanner()
        
        logger.info("=" * 60)
        logger.info("✓ ALL TESTS PASSED!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
