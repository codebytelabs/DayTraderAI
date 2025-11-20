#!/usr/bin/env python3
"""
Comprehensive Perplexity API testing module.
Tests the Perplexity integration and helps debug issues.
"""

import asyncio
import sys
import os
import httpx
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from advisory.perplexity import PerplexityClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def test_direct_api_call():
    """Test Perplexity API directly with httpx."""
    print("\n" + "="*80)
    print("TEST 1: Direct API Call (bypassing client)")
    print("="*80)
    
    api_key = settings.perplexity_api_key
    base_url = settings.perplexity_api_base_url
    model = settings.perplexity_default_model
    
    print(f"\n📋 Configuration:")
    print(f"   API Key: {api_key[:20]}...{api_key[-10:] if api_key else 'NOT SET'}")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    
    if not api_key:
        print("\n❌ FAILED: Perplexity API key not configured!")
        print("   Set PERPLEXITY_API_KEY in .env file")
        return False
    
    try:
        print("\n🔄 Making direct API call...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant."
                        },
                        {
                            "role": "user",
                            "content": "What is the current price of Apple (AAPL) stock?"
                        }
                    ]
                }
            )
            
            print(f"\n📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS: Received response from Perplexity")
                print(f"\n📄 Response structure:")
                print(f"   Keys: {list(data.keys())}")
                
                if "choices" in data:
                    choice = data["choices"][0]
                    content = choice.get("message", {}).get("content", "")
                    print(f"\n💬 Content preview:")
                    print(f"   {content[:200]}...")
                    
                if "citations" in data:
                    citations = data["citations"]
                    print(f"\n📚 Citations: {len(citations)} found")
                    for i, citation in enumerate(citations[:3], 1):
                        print(f"   {i}. {citation}")
                
                return True
            else:
                print(f"❌ FAILED: HTTP {response.status_code}")
                print(f"\n📄 Response body:")
                print(f"   {response.text}")
                return False
                
    except httpx.TimeoutException as e:
        print(f"\n❌ FAILED: Request timed out after 30 seconds")
        print(f"   Error: {e}")
        return False
    except httpx.ConnectError as e:
        print(f"\n❌ FAILED: Could not connect to Perplexity API")
        print(f"   Error: {e}")
        print(f"   Check your internet connection and API base URL")
        return False
    except Exception as e:
        print(f"\n❌ FAILED: Unexpected error")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error: {e}")
        import traceback
        print(f"\n📋 Full traceback:")
        traceback.print_exc()
        return False


async def test_perplexity_client():
    """Test PerplexityClient class."""
    print("\n" + "="*80)
    print("TEST 2: PerplexityClient Class")
    print("="*80)
    
    try:
        print("\n🔄 Initializing PerplexityClient...")
        client = PerplexityClient()
        
        print(f"✅ Client initialized")
        print(f"   Model: {client.model}")
        print(f"   Base URL: {client.base_url}")
        
        print("\n🔄 Testing search method...")
        result = await client.search("What is the current price of Tesla (TSLA) stock?")
        
        if result:
            print(f"✅ SUCCESS: Search returned results")
            print(f"\n📄 Result structure:")
            print(f"   Keys: {list(result.keys())}")
            print(f"   Content length: {len(result.get('content', ''))} characters")
            print(f"   Citations: {len(result.get('citations', []))} found")
            print(f"\n💬 Content preview:")
            print(f"   {result.get('content', '')[:200]}...")
            return True
        else:
            print(f"❌ FAILED: Search returned None")
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED: Exception in PerplexityClient")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stock_analysis_query():
    """Test a comprehensive stock analysis query."""
    print("\n" + "="*80)
    print("TEST 3: Comprehensive Stock Analysis Query")
    print("="*80)
    
    try:
        client = PerplexityClient()
        
        query = """Conduct COMPREHENSIVE DEEP-DIVE ANALYSIS for: AAPL

For EACH symbol, provide:

1. TECHNICAL ANALYSIS:
   - Current price, 52-week range
   - Key support and resistance levels
   - RSI, MACD, moving averages

2. FUNDAMENTAL ANALYSIS:
   - Latest financials (revenue, net income)
   - Valuation metrics (P/E, P/B, PEG)
   - Growth rates

3. SENTIMENT & NEWS:
   - Recent news headlines (last 7 days)
   - Analyst ratings
   - Social media sentiment

Provide SPECIFIC NUMBERS and SOURCES."""
        
        print("\n🔄 Sending comprehensive analysis query...")
        print(f"   Query length: {len(query)} characters")
        
        result = await client.search(query)
        
        if result:
            content = result.get('content', '')
            citations = result.get('citations', [])
            
            print(f"\n✅ SUCCESS: Received comprehensive analysis")
            print(f"   Content length: {len(content)} characters")
            print(f"   Citations: {len(citations)} found")
            
            print(f"\n💬 Analysis preview:")
            print(f"{content[:500]}...")
            
            if citations:
                print(f"\n📚 Citations:")
                for i, citation in enumerate(citations[:5], 1):
                    print(f"   {i}. {citation}")
            
            return True
        else:
            print(f"❌ FAILED: No results returned")
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED: Exception during analysis")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_opportunities_query():
    """Test opportunities research query."""
    print("\n" + "="*80)
    print("TEST 4: Trading Opportunities Research Query")
    print("="*80)
    
    try:
        client = PerplexityClient()
        
        query = """Find the BEST trading opportunities RIGHT NOW.

Research:
1. High-momentum stocks (strong uptrend, breaking out)
2. Undervalued stocks (oversold, potential reversal)
3. Sector leaders (strongest in their sector)

For each opportunity, provide:
- Symbol and company name
- Current price
- Why it's a good opportunity RIGHT NOW
- Entry price range
- Stop loss level
- Take profit target

Use real-time market data."""
        
        print("\n🔄 Sending opportunities research query...")
        
        result = await client.search(query)
        
        if result:
            content = result.get('content', '')
            citations = result.get('citations', [])
            
            print(f"\n✅ SUCCESS: Received opportunities research")
            print(f"   Content length: {len(content)} characters")
            print(f"   Citations: {len(citations)} found")
            
            print(f"\n💬 Opportunities preview:")
            print(f"{content[:500]}...")
            
            return True
        else:
            print(f"❌ FAILED: No results returned")
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED: Exception during research")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_different_models():
    """Test different Perplexity models."""
    print("\n" + "="*80)
    print("TEST 5: Testing Different Models")
    print("="*80)
    
    models = [
        "sonar-pro",
        "sonar",
        "sonar-reasoning",
    ]
    
    client = PerplexityClient()
    query = "What is the current price of AAPL stock?"
    
    results = {}
    
    for model in models:
        print(f"\n🔄 Testing model: {model}")
        try:
            result = await client.search(query, model=model)
            if result:
                content_length = len(result.get('content', ''))
                citations_count = len(result.get('citations', []))
                print(f"   ✅ SUCCESS: {content_length} chars, {citations_count} citations")
                results[model] = "✅ Working"
            else:
                print(f"   ❌ FAILED: No results")
                results[model] = "❌ Failed"
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results[model] = f"❌ Error: {e}"
    
    print(f"\n📊 Model Test Results:")
    for model, status in results.items():
        print(f"   {model}: {status}")
    
    return any("✅" in status for status in results.values())


async def test_timeout_handling():
    """Test timeout handling."""
    print("\n" + "="*80)
    print("TEST 6: Timeout Handling")
    print("="*80)
    
    try:
        print("\n🔄 Testing with very short timeout (1 second)...")
        
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.post(
                f"{settings.perplexity_api_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.perplexity_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.perplexity_default_model,
                    "messages": [
                        {"role": "user", "content": "Test"}
                    ]
                }
            )
            print(f"✅ Response received within 1 second")
            return True
            
    except httpx.TimeoutException:
        print(f"⚠️  Request timed out (expected with 1 second timeout)")
        print(f"   This means Perplexity API takes > 1 second to respond")
        print(f"   Current timeout in production: 30 seconds")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def print_summary(results):
    """Print test summary."""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"\n✅ Perplexity integration is working correctly")
        print(f"✅ Ready to use in copilot")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        print(f"\n🔧 Troubleshooting steps:")
        print(f"   1. Check PERPLEXITY_API_KEY in .env")
        print(f"   2. Verify API key is valid at https://www.perplexity.ai/settings/api")
        print(f"   3. Check internet connection")
        print(f"   4. Try different model (sonar vs sonar-pro)")
        print(f"   5. Check Perplexity API status")


async def main():
    """Run all tests."""
    print("\n🚀 Perplexity API Testing Suite")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    
    results = {}
    
    # Run tests
    results["Direct API Call"] = await test_direct_api_call()
    
    if results["Direct API Call"]:
        results["PerplexityClient Class"] = await test_perplexity_client()
        results["Stock Analysis Query"] = await test_stock_analysis_query()
        results["Opportunities Query"] = await test_opportunities_query()
        results["Different Models"] = await test_different_models()
        results["Timeout Handling"] = await test_timeout_handling()
    else:
        print("\n⚠️  Skipping remaining tests due to API connection failure")
    
    # Print summary
    print_summary(results)
    
    # Return exit code
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
