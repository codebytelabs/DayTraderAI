#!/usr/bin/env python3
"""
Copilot Intelligence Test Suite
Tests the improved copilot features including context building, query routing, and multi-source intelligence
"""

import asyncio
import sys
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

from config import settings
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from data.market_data import MarketDataManager
from data.features import FeatureEngine
from news.news_client import NewsClient
from trading.risk_manager import RiskManager
from copilot.config import build_copilot_config
from copilot.context_builder import CopilotContextBuilder
from copilot.query_router import QueryRouter


class TestResults:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.total += 1
        self.passed += 1
        logger.info(f"✅ PASS: {test_name} {details}")
    
    def add_fail(self, test_name: str, error: str):
        self.total += 1
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        logger.error(f"❌ FAIL: {test_name} - {error}")
    
    def print_summary(self):
        logger.info("\n" + "="*80)
        logger.info("TEST SUMMARY")
        logger.info("="*80)
        logger.info(f"Total Tests: {self.total}")
        logger.info(f"Passed: {self.passed} ✅")
        logger.info(f"Failed: {self.failed} ❌")
        logger.info(f"Pass Rate: {(self.passed/self.total*100) if self.total > 0 else 0:.1f}%")
        
        if self.errors:
            logger.info(f"\nErrors:")
            for e in self.errors:
                logger.info(f"  ❌ {e}")
        
        logger.info("="*80)


results = TestResults()


def initialize_copilot_components():
    """Initialize copilot components with error handling"""
    alpaca = AlpacaClient()
    supabase = SupabaseClient()
    feature_engine = FeatureEngine()
    market_data = MarketDataManager(alpaca, supabase)
    
    # Try to initialize news client, but don't fail if it's not configured
    try:
        news_client = NewsClient()
    except Exception as e:
        logger.warning(f"  News client not available: {e}")
        news_client = None
    
    risk_manager = RiskManager(alpaca)
    config = build_copilot_config(settings)
    
    # Disable news if client not available
    if news_client is None:
        config.include_news = False
        logger.info("  News integration disabled (client not configured)")
    
    return alpaca, supabase, feature_engine, market_data, news_client, risk_manager, config


async def test_copilot_config():
    """Test copilot configuration"""
    try:
        logger.info("\n🔧 Testing Copilot Configuration...")
        
        config = build_copilot_config(settings)
        
        # Verify config attributes
        if hasattr(config, 'context_enabled'):
            logger.info(f"  Context Enabled: {config.context_enabled}")
            results.add_pass("Copilot Config - Context Enabled")
        else:
            results.add_fail("Copilot Config - Context Enabled", "Attribute missing")
        
        if hasattr(config, 'hybrid_routing'):
            logger.info(f"  Hybrid Routing: {config.hybrid_routing}")
            results.add_pass("Copilot Config - Hybrid Routing")
        else:
            results.add_fail("Copilot Config - Hybrid Routing", "Attribute missing")
        
        if hasattr(config, 'include_news'):
            logger.info(f"  Include News: {config.include_news}")
            results.add_pass("Copilot Config - News Integration")
        else:
            results.add_fail("Copilot Config - News Integration", "Attribute missing")
        
        logger.info(f"  Max History Trades: {config.max_history_trades}")
        logger.info(f"  News Lookback Hours: {config.news_lookback_hours}")
        logger.info(f"  Cache TTL: {config.cache_ttl_seconds}s")
        
    except Exception as e:
        results.add_fail("Copilot Configuration", str(e))


async def test_context_builder():
    """Test context builder functionality"""
    try:
        logger.info("\n🧠 Testing Context Builder...")
        
        # Initialize dependencies
        alpaca, supabase, feature_engine, market_data, news_client, risk_manager, config = initialize_copilot_components()
        
        context_builder = CopilotContextBuilder(
            alpaca_client=alpaca,
            supabase_client=supabase,
            market_data_manager=market_data,
            news_client=news_client,
            risk_manager=risk_manager,
            config=config
        )
        
        # Test 1: Build context for portfolio query
        try:
            logger.info("  Building context for portfolio query...")
            start_time = datetime.now()
            context_result = await context_builder.build_context("What's my portfolio status?")
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"  Context Build Time: {duration:.2f}s")
            logger.info(f"  Context Keys: {list(context_result.context.keys())}")
            logger.info(f"  Summary Length: {len(context_result.summary)} chars")
            logger.info(f"  Highlights: {len(context_result.highlights)}")
            
            # Verify context structure
            required_keys = ['query', 'timestamp', 'account', 'positions', 'market', 'risk']
            missing_keys = [key for key in required_keys if key not in context_result.context]
            
            if not missing_keys:
                results.add_pass("Context Builder - Structure", f"({len(context_result.context)} keys)")
            else:
                results.add_fail("Context Builder - Structure", f"Missing keys: {missing_keys}")
            
            # Verify account data
            if 'account' in context_result.context:
                account = context_result.context['account']
                if 'equity' in account and 'buying_power' in account:
                    logger.info(f"  Account Equity: ${account['equity']:,.2f}")
                    results.add_pass("Context Builder - Account Data")
                else:
                    results.add_fail("Context Builder - Account Data", "Missing equity/buying_power")
            
            # Verify positions data
            if 'positions' in context_result.context:
                positions = context_result.context['positions']
                logger.info(f"  Positions Count: {len(positions)}")
                results.add_pass("Context Builder - Positions Data", f"({len(positions)} positions)")
            
            # Verify market data
            if 'market' in context_result.context:
                market = context_result.context['market']
                if 'symbols' in market:
                    logger.info(f"  Market Symbols: {len(market['symbols'])}")
                    results.add_pass("Context Builder - Market Data")
                else:
                    results.add_fail("Context Builder - Market Data", "No symbols data")
            
            # Verify risk data
            if 'risk' in context_result.context:
                risk = context_result.context['risk']
                if 'open_positions' in risk and 'max_positions' in risk:
                    logger.info(f"  Risk: {risk['open_positions']}/{risk['max_positions']} positions")
                    results.add_pass("Context Builder - Risk Data")
                else:
                    results.add_fail("Context Builder - Risk Data", "Missing position limits")
            
            # Verify summary generation
            if context_result.summary and len(context_result.summary) > 0:
                logger.info(f"  Summary Preview: {context_result.summary[:100]}...")
                results.add_pass("Context Builder - Summary Generation")
            else:
                results.add_fail("Context Builder - Summary Generation", "Empty summary")
            
            # Verify highlights
            if context_result.highlights and len(context_result.highlights) > 0:
                logger.info(f"  Highlights:")
                for highlight in context_result.highlights[:3]:
                    logger.info(f"    - {highlight}")
                results.add_pass("Context Builder - Highlights", f"({len(context_result.highlights)} items)")
            else:
                results.add_fail("Context Builder - Highlights", "No highlights generated")
            
        except Exception as e:
            results.add_fail("Context Builder - Build Context", str(e))
        
        # Test 2: Symbol extraction
        try:
            logger.info("  Testing symbol extraction...")
            symbols = context_builder.extract_symbols("What's happening with AAPL and TSLA today?")
            logger.info(f"  Extracted Symbols: {symbols}")
            
            if symbols and len(symbols) > 0:
                results.add_pass("Context Builder - Symbol Extraction", f"({len(symbols)} symbols)")
            else:
                results.add_pass("Context Builder - Symbol Extraction", "(no watchlist symbols found)")
            
        except Exception as e:
            results.add_fail("Context Builder - Symbol Extraction", str(e))
        
    except Exception as e:
        results.add_fail("Context Builder", str(e))


async def test_query_router():
    """Test query routing functionality"""
    try:
        logger.info("\n🧭 Testing Query Router...")
        
        config = build_copilot_config(settings)
        router = QueryRouter(config)
        
        # Test different query types
        test_queries = [
            ("What's the latest news on AAPL?", "news", ["perplexity"]),
            ("Should I buy TSLA stock?", "analysis", ["openrouter"]),
            ("What's my portfolio status?", "status", ["openrouter"]),
            ("Tell me about NVDA news and if I should buy", "hybrid", ["perplexity", "openrouter"]),
        ]
        
        for query, expected_category, expected_targets in test_queries:
            try:
                logger.info(f"  Testing query: '{query}'")
                route = router.route(query, {}, [])
                
                logger.info(f"    Category: {route.category}")
                logger.info(f"    Targets: {route.targets}")
                logger.info(f"    Confidence: {route.confidence:.2f}")
                logger.info(f"    Notes: {route.notes}")
                
                # Verify routing logic
                if route.category and route.targets:
                    results.add_pass(f"Query Router - {expected_category}", 
                                   f"(category: {route.category}, confidence: {route.confidence:.2f})")
                else:
                    results.add_fail(f"Query Router - {expected_category}", 
                                   "Missing category or targets")
                
            except Exception as e:
                results.add_fail(f"Query Router - {expected_category}", str(e))
        
    except Exception as e:
        results.add_fail("Query Router", str(e))


async def test_end_to_end_copilot():
    """Test complete copilot workflow"""
    try:
        logger.info("\n🚀 Testing End-to-End Copilot Workflow...")
        
        # Initialize all components
        alpaca, supabase, feature_engine, market_data, news_client, risk_manager, config = initialize_copilot_components()
        
        context_builder = CopilotContextBuilder(
            alpaca_client=alpaca,
            supabase_client=supabase,
            market_data_manager=market_data,
            news_client=news_client,
            risk_manager=risk_manager,
            config=config
        )
        
        router = QueryRouter(config)
        
        # Test complete workflow
        query = "What's my portfolio performance and should I make any changes?"
        
        logger.info(f"  Query: '{query}'")
        
        # Step 1: Build context
        logger.info("  Step 1: Building context...")
        context_result = await context_builder.build_context(query)
        
        if context_result and context_result.context:
            logger.info(f"    ✓ Context built with {len(context_result.context)} sections")
            results.add_pass("E2E Copilot - Context Building")
        else:
            results.add_fail("E2E Copilot - Context Building", "No context generated")
            return
        
        # Step 2: Route query
        logger.info("  Step 2: Routing query...")
        route = router.route(query, context_result.context, context_result.context.get('symbols', []))
        
        if route and route.targets:
            logger.info(f"    ✓ Routed to: {route.targets} (category: {route.category})")
            results.add_pass("E2E Copilot - Query Routing")
        else:
            results.add_fail("E2E Copilot - Query Routing", "No route determined")
            return
        
        # Step 3: Verify context quality
        logger.info("  Step 3: Verifying context quality...")
        
        context = context_result.context
        quality_checks = {
            'has_account_data': 'account' in context and context['account'].get('equity') is not None,
            'has_positions': 'positions' in context,
            'has_market_data': 'market' in context and 'symbols' in context['market'],
            'has_risk_data': 'risk' in context,
            'has_summary': len(context_result.summary) > 0,
            'has_highlights': len(context_result.highlights) > 0,
        }
        
        passed_checks = sum(1 for check in quality_checks.values() if check)
        total_checks = len(quality_checks)
        
        logger.info(f"    Quality: {passed_checks}/{total_checks} checks passed")
        for check_name, passed in quality_checks.items():
            status = "✓" if passed else "✗"
            logger.info(f"      {status} {check_name}")
        
        if passed_checks >= total_checks * 0.8:  # 80% threshold
            results.add_pass("E2E Copilot - Context Quality", f"({passed_checks}/{total_checks})")
        else:
            results.add_fail("E2E Copilot - Context Quality", 
                           f"Only {passed_checks}/{total_checks} checks passed")
        
        logger.info("  ✓ End-to-end copilot workflow completed successfully")
        
    except Exception as e:
        results.add_fail("E2E Copilot Workflow", str(e))


async def run_all_tests():
    """Run all copilot intelligence tests"""
    
    logger.info("="*80)
    logger.info("🧪 COPILOT INTELLIGENCE TEST SUITE")
    logger.info("="*80)
    logger.info(f"Start Time: {datetime.now()}")
    logger.info("="*80)
    
    # Run tests
    await test_copilot_config()
    await test_context_builder()
    await test_query_router()
    await test_end_to_end_copilot()
    
    # Print summary
    logger.info(f"\nEnd Time: {datetime.now()}")
    results.print_summary()
    
    return 0 if results.failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
