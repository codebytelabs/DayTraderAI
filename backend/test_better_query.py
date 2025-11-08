#!/usr/bin/env python3
"""Test the improved query suggested by user."""

import asyncio
from advisory.perplexity import PerplexityClient

async def test():
    client = PerplexityClient()
    
    print("🎯 Testing Improved Query")
    print("=" * 80)
    
    # User's suggested query
    query = "according to top trading websites like cnn, yahoo finance etc., what is the fear and greed rating today?"
    
    print(f"\n📤 Query: {query}")
    print("-" * 80)
    
    result = await client.search(query)
    
    print("\n📄 RESPONSE:")
    print("-" * 80)
    print(result['content'])
    print("-" * 80)
    
    print("\n📚 CITATIONS:")
    for i, citation in enumerate(result.get('citations', []), 1):
        print(f"  {i}. {citation}")
    
    # Test extraction
    import re
    content = result['content']
    
    print("\n🔍 EXTRACTION TEST:")
    print("-" * 80)
    
    # Look for the number
    patterns = [
        (r'(?:rating|score|index)[:\s]+(\d+)', 'Pattern 1: "rating: X"'),
        (r'(\d+)/100', 'Pattern 2: "X/100"'),
        (r'(\d+)\s*[-–—]\s*(?:Extreme Fear|Extreme Greed|Fear|Greed|Neutral)', 'Pattern 3: "X - Classification"'),
        (r'(?:is|currently)\s+(\d+)', 'Pattern 4: "is X"'),
    ]
    
    for pattern, description in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            extracted = int(match.group(1))
            if 0 <= extracted <= 100:
                print(f"✅ {description}: {extracted}")
                print(f"   Matched: '{match.group(0)}'")
                break
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test())
