#!/usr/bin/env python3
"""
Test module to debug Perplexity opportunity discovery.
Run: python test_perplexity_discovery.py
"""

import asyncio
import os
import sys

# Ensure we're in the backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from advisory.openrouter_client import OpenRouterClient
from advisory.perplexity import PerplexityClient


async def test_simple_query():
    """Test with a simple query to verify APIs work."""
    print("\n" + "="*80)
    print("TEST 1: Simple Query (verify API connectivity)")
    print("="*80)
    
    simple_query = "What are the top 5 stocks moving today in pre-market? Just list the tickers."
    
    # Test OpenRouter Perplexity
    print("\n📡 Testing OpenRouter Perplexity (perplexity/sonar-pro)...")
    try:
        client = OpenRouterClient()
        client.model = settings.openrouter_perplexity_model
        result = await client.search(simple_query)
        if result:
            print(f"✅ OpenRouter Perplexity responded: {len(result['content'])} chars")
            print(f"   Preview: {result['content'][:300]}...")
        else:
            print("❌ OpenRouter Perplexity returned None")
    except Exception as e:
        print(f"❌ OpenRouter Perplexity error: {e}")
    
    # Test Native Perplexity
    print("\n📡 Testing Native Perplexity (sonar-pro)...")
    try:
        client = PerplexityClient()
        result = await client.search(simple_query)
        if result:
            print(f"✅ Native Perplexity responded: {len(result['content'])} chars")
            print(f"   Preview: {result['content'][:300]}...")
        else:
            print("❌ Native Perplexity returned None")
    except Exception as e:
        print(f"❌ Native Perplexity error: {e}")


async def test_trading_query():
    """Test with a trading-focused query."""
    print("\n" + "="*80)
    print("TEST 2: Trading Query (what we actually need)")
    print("="*80)
    
    trading_query = """Find 5 large-cap stocks with unusual volume or news catalysts today.
For each stock provide:
- Ticker symbol
- Current price
- Why it's moving (catalyst)
- Direction (bullish/bearish)

Format: TICKER ($PRICE) - CATALYST - DIRECTION"""
    
    # Test OpenRouter Perplexity
    print("\n📡 Testing OpenRouter Perplexity...")
    try:
        client = OpenRouterClient()
        client.model = settings.openrouter_perplexity_model
        result = await client.search(trading_query)
        if result:
            content = result['content']
            print(f"✅ Response: {len(content)} chars")
            print("-" * 40)
            print(content[:1000])
            print("-" * 40)
            
            # Check for "can't help" indicators
            cant_help = ["i need to be transparent", "i cannot provide", "current limitations"]
            if any(ind in content.lower() for ind in cant_help):
                print("⚠️  DETECTED 'CAN'T HELP' RESPONSE!")
            else:
                print("✅ Response looks actionable!")
        else:
            print("❌ Returned None")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test Native Perplexity
    print("\n📡 Testing Native Perplexity...")
    try:
        client = PerplexityClient()
        result = await client.search(trading_query)
        if result:
            content = result['content']
            print(f"✅ Response: {len(content)} chars")
            print("-" * 40)
            print(content[:1000])
            print("-" * 40)
            
            # Check for "can't help" indicators
            cant_help = ["i need to be transparent", "i cannot provide", "current limitations"]
            if any(ind in content.lower() for ind in cant_help):
                print("⚠️  DETECTED 'CAN'T HELP' RESPONSE!")
            else:
                print("✅ Response looks actionable!")
        else:
            print("❌ Returned None")
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_full_discovery_query():
    """Test with the actual discovery query (simplified)."""
    print("\n" + "="*80)
    print("TEST 3: NEW Simplified Discovery Query")
    print("="*80)
    
    # New simplified query that Perplexity can actually answer
    discovery_query = """List stocks with unusual trading activity or news catalysts.

Search for:
1. Stocks with high pre-market/after-hours volume
2. Stocks with recent news (earnings, FDA, upgrades/downgrades, M&A)
3. Stocks making significant moves (gaps, breakouts)

Focus on large-cap (>$10B), mid-cap ($2B-$10B) stocks.

For each stock, provide:
- Ticker symbol
- Brief reason (catalyst or why it's moving)
- Direction (bullish or bearish)

Format your response as:
**LARGE-CAP LONG:**
1. TICKER - reason
2. TICKER - reason

**LARGE-CAP SHORT:**
1. TICKER - reason

**MID-CAP LONG:**
1. TICKER - reason

List 10-20 stocks total across categories. Include the ticker symbols clearly."""

    print("\n📡 Testing OpenRouter Perplexity with discovery query...")
    try:
        client = OpenRouterClient()
        client.model = settings.openrouter_perplexity_model
        result = await client.search(discovery_query)
        if result:
            content = result['content']
            print(f"✅ Response: {len(content)} chars")
            print("-" * 40)
            print(content[:1500])
            print("-" * 40)
            
            # Check for symbols
            import re
            symbols = re.findall(r'\b([A-Z]{2,5})\b', content)
            unique_symbols = list(set(symbols))
            print(f"\n📊 Found {len(unique_symbols)} potential symbols: {unique_symbols[:20]}")
            
            # Check for "can't help" indicators
            cant_help = ["i need to be transparent", "i cannot provide", "current limitations", "unable to access"]
            if any(ind in content.lower() for ind in cant_help):
                print("⚠️  DETECTED 'CAN'T HELP' RESPONSE!")
            else:
                print("✅ Response looks actionable!")
        else:
            print("❌ Returned None")
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    print("="*80)
    print("🔍 PERPLEXITY OPPORTUNITY DISCOVERY TEST")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  OpenRouter Perplexity Model: {settings.openrouter_perplexity_model}")
    print(f"  Native Perplexity Model: {settings.perplexity_default_model}")
    print(f"  OpenRouter API Key: {settings.openrouter_api_key[:20]}...")
    print(f"  Perplexity API Key: {settings.perplexity_api_key[:20]}...")
    
    await test_simple_query()
    await test_trading_query()
    await test_full_discovery_query()
    
    print("\n" + "="*80)
    print("🏁 TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
