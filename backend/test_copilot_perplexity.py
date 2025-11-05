#!/usr/bin/env python3
"""
Test Perplexity integration in the copilot system.
Tests both /analyze and /opportunities commands.
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_copilot_chat(message: str, test_name: str):
    """Test the /chat endpoint with a specific message."""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    print(f"Message: {message}")
    print(f"Started at: {datetime.now().strftime('%H:%M:%S')}")
    
    url = "http://localhost:8006/chat"
    payload = {
        "message": message,
        "history": [],
        "trace_id": f"test_{test_name}_{datetime.now().timestamp()}"
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            start_time = asyncio.get_event_loop().time()
            response = await client.post(url, json=payload)
            elapsed = asyncio.get_event_loop().time() - start_time
            
            print(f"Completed in: {elapsed:.2f}s")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n✅ SUCCESS")
                print(f"Provider: {data.get('provider', 'Unknown')}")
                print(f"Confidence: {data.get('confidence', 0):.2%}")
                
                # Check for Perplexity in provider
                provider = data.get('provider', '')
                if 'Perplexity' in provider:
                    print(f"✅ Perplexity was used!")
                else:
                    print(f"⚠️  Perplexity NOT in provider chain")
                
                # Show content preview
                content = data.get('content', '')
                print(f"\nContent length: {len(content)} characters")
                print(f"\nContent preview (first 500 chars):")
                print("-" * 80)
                print(content[:500])
                if len(content) > 500:
                    print("...")
                print("-" * 80)
                
                # Show citations if present
                citations = data.get('citations', [])
                if citations:
                    print(f"\n📚 Citations: {len(citations)}")
                    for i, citation in enumerate(citations[:3], 1):
                        print(f"  {i}. {citation}")
                
                # Show route info
                route = data.get('route', {})
                if route:
                    print(f"\nRoute:")
                    print(f"  Category: {route.get('category')}")
                    print(f"  Targets: {route.get('targets')}")
                    print(f"  Symbols: {route.get('symbols')}")
                
                # Show notes
                notes = data.get('notes', [])
                if notes:
                    print(f"\nNotes:")
                    for note in notes:
                        print(f"  - {note}")
                
                return True
            else:
                print(f"\n❌ FAILED")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all copilot tests."""
    print("="*80)
    print("COPILOT PERPLEXITY INTEGRATION TEST")
    print("="*80)
    print(f"Testing backend at: http://localhost:8006")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Simple analyze command
    test1 = await test_copilot_chat(
        "/analyze AAPL",
        "analyze_command"
    )
    
    await asyncio.sleep(2)
    
    # Test 2: Opportunities command
    test2 = await test_copilot_chat(
        "/opportunities",
        "opportunities_command"
    )
    
    await asyncio.sleep(2)
    
    # Test 3: Deep analysis with multiple symbols
    test3 = await test_copilot_chat(
        "Give me a deep analysis of NVDA and AMD",
        "deep_analysis_multi"
    )
    
    await asyncio.sleep(2)
    
    # Test 4: Market research query
    test4 = await test_copilot_chat(
        "What are the best tech stocks to trade today?",
        "market_research"
    )
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    results = [
        ("Analyze Command", test1),
        ("Opportunities Command", test2),
        ("Deep Analysis Multi", test3),
        ("Market Research", test4),
    ]
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    asyncio.run(main())
