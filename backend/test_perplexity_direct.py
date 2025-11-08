#!/usr/bin/env python3
"""
Direct test of Perplexity client to isolate the issue.
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
from config import settings


async def test_perplexity_direct():
    """Test Perplexity client directly."""
    
    print("\n" + "=" * 60)
    print("DIRECT PERPLEXITY CLIENT TEST")
    print("=" * 60)
    print()
    
    # Check config
    print("🔧 Configuration Check:")
    print(f"  API Key: {'SET (' + str(len(settings.perplexity_api_key)) + ' chars)' if settings.perplexity_api_key else 'NOT SET'}")
    print(f"  Base URL: {settings.perplexity_api_base_url}")
    print(f"  Model: {settings.perplexity_default_model}")
    print()
    
    # Initialize client
    print("🚀 Initializing Perplexity client...")
    client = PerplexityClient()
    print()
    
    # Test simple query
    print("📡 Testing simple query...")
    query = "What are the top 3 trending stocks today?"
    
    try:
        result = await client.search(query)
        
        if result:
            print("✅ SUCCESS!")
            print(f"Content length: {len(result.get('content', ''))}")
            print(f"Citations: {len(result.get('citations', []))}")
            print()
            print("Content preview:")
            content = result.get('content', '')
            print(content[:500] + "..." if len(content) > 500 else content)
            print()
        else:
            print("❌ FAILED - No result returned")
            
    except Exception as e:
        print(f"❌ FAILED - Exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_perplexity_direct())