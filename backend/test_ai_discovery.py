"""Test AI-powered opportunity discovery."""

import asyncio
from scanner.ai_opportunity_finder import get_ai_opportunity_finder
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def test_ai_discovery():
    """Test AI opportunity discovery."""
    
    print("\n" + "="*80)
    print("TESTING AI-POWERED OPPORTUNITY DISCOVERY")
    print("="*80 + "\n")
    
    ai_finder = get_ai_opportunity_finder()
    
    # Test 1: Discover opportunities
    print("🤖 Asking Perplexity AI to discover trading opportunities...\n")
    symbols = await ai_finder.discover_opportunities(max_symbols=20)
    
    print(f"\n✅ AI discovered {len(symbols)} opportunities:")
    for i, symbol in enumerate(symbols, 1):
        print(f"  {i}. {symbol}")
    
    # Test 2: Get last discovery details
    last_discovery = ai_finder.get_last_discovery()
    if last_discovery:
        print(f"\n📊 AI Reasoning (first 500 chars):")
        print(last_discovery['reasoning'][:500] + "...")
        print(f"\n📚 Sources: {len(last_discovery.get('citations', []))} citations")
    
    # Test 3: Get market overview
    print("\n🌍 Getting market overview...")
    overview = await ai_finder.get_market_overview()
    if overview:
        print(f"\n{overview['overview'][:500]}...")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_ai_discovery())
