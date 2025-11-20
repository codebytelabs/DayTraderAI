#!/usr/bin/env python3
"""
Test: Combined Sentiment + Opportunities Discovery
Validates getting market sentiment from Perplexity along with opportunities.
"""

import asyncio
from datetime import datetime
from advisory.perplexity import PerplexityClient
import re

async def test_combined_query():
    print("🎯 Testing Combined Sentiment + Opportunities Query")
    print("=" * 80)
    
    perplexity = PerplexityClient()
    
    # Build combined query
    current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p ET")
    
    query = f"""Provide TWO things for day trading on {current_time}:

**PART 1: MARKET SENTIMENT**
Check CNN Fear & Greed Index (https://edition.cnn.com/markets/fear-and-greed) and provide:
- Current Fear & Greed score (0-100)
- Classification (Extreme Fear/Fear/Neutral/Greed/Extreme Greed)
- Brief market context (1-2 sentences)

**PART 2: TRADING OPPORTUNITIES**
Find the best day trading opportunities across market caps:

**LARGE-CAP LONG:**
1. SYMBOL - $price, catalyst, setup, volume Xx, Target $target
2. SYMBOL - $price, catalyst, setup, volume Xx, Target $target
(5-10 opportunities)

**LARGE-CAP SHORT:**
1. SYMBOL - $price, catalyst, setup, volume Xx, Target $target
(3-5 opportunities)

**MID-CAP LONG:**
1. SYMBOL - $price, catalyst, setup, volume Xx, Target $target
(5-10 opportunities)

**MID-CAP SHORT:**
1. SYMBOL - $price, catalyst, setup, volume Xx, Target $target
(3-5 opportunities)

**SMALL-CAP LONG:**
1. SYMBOL - $price, catalyst, setup, volume Xx, Target $target
(3-5 opportunities)

Focus on high volume stocks with clear catalysts."""

    print("\n📤 Sending Combined Query to Perplexity...")
    print("-" * 80)
    
    try:
        result = await perplexity.search(query)
        
        if not result or not result.get('content'):
            print("❌ No response from Perplexity")
            return None
        
        content = result['content']
        citations = result.get('citations', [])
        
        print(f"\n✅ Got Response: {len(content)} characters")
        print(f"📚 Citations: {len(citations)}")
        print("\n" + "=" * 80)
        print("📄 FULL RESPONSE:")
        print("=" * 80)
        print(content)
        print("=" * 80)
        
        # Parse sentiment
        print("\n🎭 PARSING SENTIMENT...")
        print("-" * 80)
        
        sentiment_score = None
        sentiment_class = None
        
        # Try to extract Fear & Greed score
        score_patterns = [
            r'Fear\s*&\s*Greed.*?(\d+)',
            r'score.*?(\d+)',
            r'rating.*?(\d+)',
            r'(\d+)\s*out of 100',
            r'(\d+)/100'
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                sentiment_score = int(match.group(1))
                break
        
        # Try to extract classification
        class_patterns = [
            r'(Extreme Fear|Extreme Greed|Fear|Greed|Neutral)',
        ]
        
        for pattern in class_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                sentiment_class = match.group(1)
                break
        
        print(f"📊 Sentiment Score: {sentiment_score}/100")
        print(f"🎭 Classification: {sentiment_class}")
        
        # Parse opportunities
        print("\n📈 PARSING OPPORTUNITIES...")
        print("-" * 80)
        
        # Count opportunities by looking for ticker patterns
        symbols = set()
        
        # Look for patterns like "**SYMBOL**" or "SYMBOL -"
        symbol_patterns = [
            r'\*\*([A-Z]{1,5})\*\*',
            r'^\d+\.\s+([A-Z]{1,5})\s*[-–]',
            r'^\d+\.\s+\*\*([A-Z]{1,5})\*\*'
        ]
        
        for line in content.split('\n'):
            for pattern in symbol_patterns:
                matches = re.findall(pattern, line, re.MULTILINE)
                symbols.update(matches)
        
        # Filter out common false positives
        exclude = {'PART', 'LONG', 'SHORT', 'CAP', 'TARGET', 'SYMBOL'}
        symbols = {s for s in symbols if s not in exclude and len(s) <= 5}
        
        print(f"✅ Found {len(symbols)} unique symbols")
        print(f"📋 Symbols: {', '.join(sorted(symbols)[:20])}")
        
        # Validation
        print("\n✅ VALIDATION RESULTS:")
        print("=" * 80)
        
        has_sentiment = sentiment_score is not None
        has_opportunities = len(symbols) > 10
        has_citations = len(citations) > 0
        
        print(f"{'✅' if has_sentiment else '❌'} Sentiment Score Extracted: {sentiment_score}")
        print(f"{'✅' if sentiment_class else '❌'} Sentiment Classification: {sentiment_class}")
        print(f"{'✅' if has_opportunities else '❌'} Opportunities Found: {len(symbols)} symbols")
        print(f"{'✅' if has_citations else '❌'} Citations: {len(citations)} sources")
        
        # Overall assessment
        print("\n🎯 ASSESSMENT:")
        print("=" * 80)
        
        if has_sentiment and has_opportunities:
            print("✅ SUCCESS: Combined query works perfectly!")
            print("   • Sentiment data extracted")
            print("   • Opportunities discovered")
            print("   • Single API call (efficient)")
            print("\n💡 RECOMMENDATION: Implement this approach")
        elif has_sentiment:
            print("⚠️  PARTIAL: Sentiment works, opportunities need parsing improvement")
        elif has_opportunities:
            print("⚠️  PARTIAL: Opportunities work, sentiment extraction needs improvement")
        else:
            print("❌ FAILED: Neither sentiment nor opportunities extracted properly")
        
        # Check if CNN Fear & Greed was mentioned
        has_cnn_reference = 'cnn' in content.lower() or 'fear' in content.lower()
        print(f"\n{'✅' if has_cnn_reference else '❌'} CNN Fear & Greed referenced: {has_cnn_reference}")
        
        return {
            'sentiment_score': sentiment_score,
            'sentiment_class': sentiment_class,
            'symbols': list(symbols),
            'citations': citations,
            'success': has_sentiment and has_opportunities
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_combined_query())
    
    if result and result['success']:
        print("\n" + "=" * 80)
        print("🚀 READY TO IMPLEMENT!")
        print("=" * 80)
        print("This approach will:")
        print("1. Reduce Perplexity API calls by 50%")
        print("2. Get real-time CNN Fear & Greed data")
        print("3. Discover opportunities in same call")
        print("4. More reliable than Alpaca VIX")
    else:
        print("\n" + "=" * 80)
        print("⚠️  NEEDS REFINEMENT")
        print("=" * 80)
        print("Query or parsing needs adjustment")