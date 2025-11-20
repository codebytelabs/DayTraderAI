#!/usr/bin/env python3
"""Test exact sentiment extraction from Perplexity."""

import asyncio
from advisory.perplexity import PerplexityClient

async def test():
    client = PerplexityClient()
    
    print("🎯 Testing Exact Sentiment Extraction")
    print("=" * 80)
    
    result = await client.search(
        'According to https://edition.cnn.com/markets/fear-and-greed, '
        'what is the exact Fear and Greed Index score today? '
        'Provide ONLY the number (0-100) and classification.'
    )
    
    print("\n📄 FULL RESPONSE:")
    print("-" * 80)
    print(result['content'])
    print("-" * 80)
    
    print("\n📚 CITATIONS:")
    for i, citation in enumerate(result.get('citations', []), 1):
        print(f"  {i}. {citation}")
    
    # Test extraction
    import re
    content = result['content']
    
    print("\n🔍 TESTING EXTRACTION PATTERNS:")
    print("-" * 80)
    
    patterns = [
        (r'(?:score|index|rating).*?(\d+)/100', 'Pattern 1: "score X/100"'),
        (r'(?:is|rating)\s+(\d+)', 'Pattern 2: "is X"'),
        (r'(\d+)\s*out of 100', 'Pattern 3: "X out of 100"'),
        (r'(\d+)/100', 'Pattern 4: "X/100"'),
        (r'(\d+\\.\\d+)\\[\\d+\\]', 'Pattern 5: "X.X[Y]" (reference notation)'),
    ]
    
    for pattern, description in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            print(f"✅ {description}: Found '{match.group(0)}' → Extracted: {match.group(1)}")
        else:
            print(f"❌ {description}: No match")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test())
