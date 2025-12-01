#!/usr/bin/env python3
"""
Test module to optimize Perplexity opportunity discovery prompts.
Run: python test_perplexity_discovery.py
"""

import asyncio
import os
import re

# Ensure we're in the backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from advisory.openrouter_client import OpenRouterClient


# ============================================================================
# PROMPT VARIATIONS TO TEST
# ============================================================================

PROMPTS = {
    "v1_simple": """List 15 stocks with unusual trading activity or news today.

For each stock provide: TICKER - brief reason (catalyst)

Format:
**LONG:**
1. TICKER - reason
2. TICKER - reason

**SHORT:**
1. TICKER - reason

Focus on large-cap and mid-cap stocks with real catalysts.""",

    "v2_structured": """Search for stocks moving today with catalysts.

Find stocks with:
- Earnings surprises
- Analyst upgrades/downgrades  
- FDA news
- M&A activity
- Unusual options activity
- High volume movers

List 15-20 stocks in this format:

**LARGE-CAP LONG:**
1. TICKER - catalyst reason - BULLISH
2. TICKER - catalyst reason - BULLISH

**LARGE-CAP SHORT:**
1. TICKER - catalyst reason - BEARISH

**MID-CAP LONG:**
1. TICKER - catalyst reason - BULLISH

Include the stock ticker symbols clearly.""",

    "v3_news_focused": """What stocks are in the news today? Search for:

1. Stocks with earnings releases this week
2. Stocks with analyst rating changes
3. Stocks with FDA/regulatory news
4. Stocks with unusual volume or price moves
5. Stocks mentioned in financial news headlines

List each stock as:
TICKER: reason it's newsworthy

Provide at least 15 different stock tickers.""",

    "v4_momentum": """Find momentum stocks for day trading.

Search for stocks with:
- Pre-market gainers/losers
- High relative volume
- Breaking news catalysts
- Technical breakouts
- Options flow signals

Output format:
**BULLISH MOMENTUM:**
- TICKER: catalyst
- TICKER: catalyst

**BEARISH MOMENTUM:**
- TICKER: catalyst

List 15+ stocks with clear ticker symbols.""",

    "v5_institutional": """Search for institutional-quality trading opportunities.

Look for:
1. Stocks with heavy institutional buying/selling
2. Unusual options activity (large call/put purchases)
3. Analyst upgrades from Goldman, Morgan Stanley, JPM
4. Earnings beats/misses with guidance changes
5. Sector rotation plays

Format each as:
TICKER ($approx_price) - CATALYST - DIRECTION (long/short)

Provide 15-20 opportunities across sectors.""",

    "v6_direct": """List stock tickers moving today.

Search financial news and market data for:
- Top gainers and losers
- Stocks with news catalysts
- High volume stocks
- Stocks with analyst actions

Just list the tickers with brief reasons:

AAPL - reason
NVDA - reason
TSLA - reason
(continue for 15-20 stocks)

Include both bullish and bearish opportunities.""",
}


async def test_prompt(name: str, prompt: str):
    """Test a single prompt and analyze results."""
    print(f"\n{'='*80}")
    print(f"TESTING: {name}")
    print(f"{'='*80}")
    print(f"Prompt length: {len(prompt)} chars")
    
    try:
        client = OpenRouterClient()
        client.model = settings.openrouter_perplexity_model
        result = await client.search(prompt)
        
        if not result or not result.get('content'):
            print("❌ No response")
            return {'name': name, 'symbols': 0, 'quality': 0}
        
        content = result['content']
        print(f"Response length: {len(content)} chars")
        
        # Extract symbols
        all_caps = re.findall(r'\b([A-Z]{2,5})\b', content)
        non_stocks = {'THE', 'AND', 'FOR', 'WITH', 'FROM', 'THIS', 'THAT', 'HAVE', 'ARE', 'NOT', 
                      'BUT', 'CAN', 'ALL', 'HAS', 'HAD', 'WAS', 'WILL', 'MAY', 'FDA', 'CEO', 
                      'IPO', 'ETF', 'NYSE', 'SEC', 'AI', 'ML', 'API', 'USA', 'USD', 'EPS',
                      'LONG', 'SHORT', 'CAP', 'MID', 'LARGE', 'SMALL', 'MAP', 'TPU', 'DOE'}
        symbols = list(set([s for s in all_caps if s not in non_stocks]))
        
        # Quality indicators
        has_structure = any(x in content for x in ['**LONG', '**SHORT', '**BULL', '**BEAR', 'LARGE-CAP', 'MID-CAP'])
        has_catalysts = any(x in content.lower() for x in ['earnings', 'upgrade', 'fda', 'analyst', 'volume'])
        has_directions = any(x in content.lower() for x in ['bullish', 'bearish', 'long', 'short'])
        no_disclaimer = 'transparent' not in content.lower() and 'cannot provide' not in content.lower()
        
        quality_score = len(symbols) * 2
        if has_structure: quality_score += 10
        if has_catalysts: quality_score += 10
        if has_directions: quality_score += 5
        if no_disclaimer: quality_score += 15
        
        print(f"\n📊 RESULTS:")
        print(f"   Symbols found: {len(symbols)}")
        print(f"   Has structure: {'✅' if has_structure else '❌'}")
        print(f"   Has catalysts: {'✅' if has_catalysts else '❌'}")
        print(f"   Has directions: {'✅' if has_directions else '❌'}")
        print(f"   No disclaimer: {'✅' if no_disclaimer else '❌'}")
        print(f"   Quality score: {quality_score}")
        print(f"\n   Symbols: {symbols[:15]}...")
        
        print(f"\n📝 RESPONSE PREVIEW:")
        print("-" * 40)
        print(content[:1200])
        print("-" * 40)
        
        return {
            'name': name,
            'symbols': len(symbols),
            'quality': quality_score,
            'has_structure': has_structure,
            'has_catalysts': has_catalysts,
            'no_disclaimer': no_disclaimer,
            'content': content
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'name': name, 'symbols': 0, 'quality': 0}


async def main():
    print("="*80)
    print("🔍 PERPLEXITY PROMPT OPTIMIZATION TEST")
    print("="*80)
    print(f"\nModel: {settings.openrouter_perplexity_model}")
    print(f"Testing {len(PROMPTS)} prompt variations...\n")
    
    results = []
    
    for name, prompt in PROMPTS.items():
        result = await test_prompt(name, prompt)
        results.append(result)
        await asyncio.sleep(2)  # Rate limiting
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY - RANKED BY QUALITY SCORE")
    print("="*80)
    
    results.sort(key=lambda x: x['quality'], reverse=True)
    
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['name']}")
        print(f"   Quality: {r['quality']} | Symbols: {r['symbols']} | Structure: {'✅' if r.get('has_structure') else '❌'} | No Disclaimer: {'✅' if r.get('no_disclaimer') else '❌'}")
    
    # Best prompt
    best = results[0]
    print(f"\n{'='*80}")
    print(f"🏆 BEST PROMPT: {best['name']} (Score: {best['quality']})")
    print(f"{'='*80}")
    
    # Show the winning prompt
    print(f"\nWinning prompt:\n{PROMPTS[best['name']]}")


if __name__ == "__main__":
    asyncio.run(main())



async def test_optimized_prompt():
    """Test the final optimized prompt."""
    print("\n" + "="*80)
    print("🚀 TESTING OPTIMIZED PRODUCTION PROMPT")
    print("="*80)
    
    # Import the actual query builder
    from scanner.ai_opportunity_finder import AIOpportunityFinder
    
    finder = AIOpportunityFinder()
    query = finder._build_discovery_query(allowed_caps={'large_caps': True, 'mid_caps': True, 'small_caps': False})
    
    print(f"\nQuery ({len(query)} chars):")
    print("-" * 40)
    print(query)
    print("-" * 40)
    
    # Test it
    client = OpenRouterClient()
    client.model = settings.openrouter_perplexity_model
    result = await client.search(query)
    
    if result and result.get('content'):
        content = result['content']
        print(f"\n✅ Response: {len(content)} chars")
        
        # Extract symbols
        all_caps = re.findall(r'\b([A-Z]{2,5})\b', content)
        non_stocks = {'THE', 'AND', 'FOR', 'WITH', 'FROM', 'THIS', 'THAT', 'HAVE', 'ARE', 'NOT', 
                      'BUT', 'CAN', 'ALL', 'HAS', 'HAD', 'WAS', 'WILL', 'MAY', 'FDA', 'CEO', 
                      'IPO', 'ETF', 'NYSE', 'SEC', 'AI', 'ML', 'API', 'USA', 'USD', 'EPS',
                      'LONG', 'SHORT', 'CAP', 'MID', 'LARGE', 'SMALL', 'MAP', 'TPU', 'DOE',
                      'BULLISH', 'BEARISH', 'NEWS', 'WEEK', 'TODAY'}
        symbols = list(set([s for s in all_caps if s not in non_stocks]))
        
        print(f"📊 Symbols found: {len(symbols)}")
        print(f"   {symbols[:20]}...")
        
        print(f"\n📝 Response:")
        print("-" * 40)
        print(content[:2000])
        print("-" * 40)
    else:
        print("❌ No response")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--optimized":
        asyncio.run(test_optimized_prompt())
    else:
        asyncio.run(main())
