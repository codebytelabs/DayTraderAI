#!/usr/bin/env python3
"""
Test with a simpler query to see if the large query is the issue.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set minimal env vars for testing
os.environ.setdefault('OPENROUTER_API_KEY', 'dummy')
os.environ.setdefault('ALPACA_API_KEY', 'dummy')
os.environ.setdefault('ALPACA_SECRET_KEY', 'dummy')
os.environ.setdefault('SUPABASE_URL', 'https://dummy.supabase.co')
os.environ.setdefault('SUPABASE_KEY', 'dummy')
os.environ.setdefault('SUPABASE_SERVICE_KEY', 'dummy')

from advisory.perplexity import PerplexityClient


async def test_simple_query():
    """Test with a simple trading query."""
    
    print("\n" + "=" * 60)
    print("SIMPLE TRADING QUERY TEST")
    print("=" * 60)
    print()
    
    client = PerplexityClient()
    
    # Simple query similar to what we need
    query = """Find the top 10 stocks with the best trading opportunities right now.

Focus on:
- Stocks with high volume today
- Recent price breakouts
- Positive news catalysts

Provide the list in this format:
1. SYMBOL - reason
2. SYMBOL - reason
etc."""

    print("📡 Testing simple trading query...")
    print(f"Query length: {len(query)} chars")
    print()
    
    try:
        result = await client.search(query)
        
        if result:
            print("✅ SUCCESS!")
            content = result.get('content', '')
            print(f"Response length: {len(content)} chars")
            print(f"Citations: {len(result.get('citations', []))}")
            print()
            print("Response:")
            print(content)
            print()
        else:
            print("❌ FAILED - No result returned")
            
    except Exception as e:
        print(f"❌ FAILED - Exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_simple_query())