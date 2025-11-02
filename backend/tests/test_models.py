"""
Model Testing Script for OpenRouter
Tests various models for quality, speed, and cost optimization
"""
import asyncio
import httpx
import time
from typing import Dict, List, Tuple
import json
from config import settings

# Models to test
MODELS_TO_TEST = [
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-haiku-4.5", 
    "anthropic/claude-3.5-haiku",
    "google/gemini-2.5-flash-preview-09-2025",
    "google/gemini-2.5-flash-lite-preview-09-2025",
    "openai/gpt-5-mini",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-safeguard-20b"
]

# Test scenarios
TRADE_ANALYSIS_PROMPT = """Analyze this trade:

Symbol: AAPL
Action: BUY
Price: $178.50

Technical Indicators:
- EMA Short (9): $177.20
- EMA Long (21): $175.80
- ATR: $2.40
- Volume Z-Score: 1.8

The short EMA just crossed above the long EMA with strong volume.

Provide:
1. Trade quality score (1-10)
2. Key risks (2-3 points)
3. Recommended action (GO/WAIT/PASS)

Be concise and actionable."""

COPILOT_PROMPT = """Current Trading State:
- Equity: $102,450.00
- Daily P/L: $2,450.00 (2.39%)
- Open Positions: 3
- Win Rate: 65.2%
- Trading Enabled: true

User: What's my current performance and should I take more positions?"""

MARKET_ANALYSIS_PROMPT = """Analyze current market conditions for day trading these symbols:
SPY, QQQ, AAPL, NVDA, TSLA

Consider:
- Overall market sentiment
- Best opportunities for intraday trades
- Symbols to avoid today
- Key risks

Provide actionable insights in 3-4 bullet points."""


async def test_model(
    model: str,
    prompt: str,
    system_prompt: str,
    test_name: str
) -> Dict:
    """Test a single model and return metrics."""
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.openrouter_api_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})
                
                # Extract cost info if available
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
                
                return {
                    "model": model,
                    "test": test_name,
                    "success": True,
                    "response_time": round(elapsed_time, 2),
                    "content": content,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "content_length": len(content),
                    "error": None
                }
            else:
                return {
                    "model": model,
                    "test": test_name,
                    "success": False,
                    "response_time": round(elapsed_time, 2),
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
    except Exception as e:
        elapsed_time = time.time() - start_time
        return {
            "model": model,
            "test": test_name,
            "success": False,
            "response_time": round(elapsed_time, 2),
            "error": str(e)
        }


async def run_all_tests():
    """Run all test scenarios for all models."""
    
    print("=" * 80)
    print("OPENROUTER MODEL TESTING")
    print("=" * 80)
    print(f"\nTesting {len(MODELS_TO_TEST)} models across 3 scenarios...")
    print(f"Priority: Quality > Speed > Cost\n")
    
    results = []
    
    # Test 1: Trade Analysis (most critical)
    print("\n" + "=" * 80)
    print("TEST 1: TRADE ANALYSIS (Critical - needs best quality)")
    print("=" * 80)
    
    for model in MODELS_TO_TEST:
        print(f"\nTesting {model}...")
        result = await test_model(
            model,
            TRADE_ANALYSIS_PROMPT,
            "You are an expert day trading analyst. Provide concise, actionable analysis.",
            "trade_analysis"
        )
        results.append(result)
        
        if result["success"]:
            print(f"✓ Success - {result['response_time']}s - {result['total_tokens']} tokens")
            print(f"  Response preview: {result['content'][:150]}...")
        else:
            print(f"✗ Failed - {result['error']}")
        
        await asyncio.sleep(1)  # Rate limiting
    
    # Test 2: Copilot Chat (needs speed + quality)
    print("\n" + "=" * 80)
    print("TEST 2: COPILOT CHAT (Needs speed + good quality)")
    print("=" * 80)
    
    for model in MODELS_TO_TEST:
        print(f"\nTesting {model}...")
        result = await test_model(
            model,
            COPILOT_PROMPT,
            "You are a helpful trading assistant. Be concise and actionable.",
            "copilot_chat"
        )
        results.append(result)
        
        if result["success"]:
            print(f"✓ Success - {result['response_time']}s - {result['total_tokens']} tokens")
            print(f"  Response preview: {result['content'][:150]}...")
        else:
            print(f"✗ Failed - {result['error']}")
        
        await asyncio.sleep(1)
    
    # Test 3: Market Analysis (needs quality)
    print("\n" + "=" * 80)
    print("TEST 3: MARKET ANALYSIS (Needs quality + reasonable speed)")
    print("=" * 80)
    
    for model in MODELS_TO_TEST:
        print(f"\nTesting {model}...")
        result = await test_model(
            model,
            MARKET_ANALYSIS_PROMPT,
            "You are a market analyst. Provide actionable insights for day traders.",
            "market_analysis"
        )
        results.append(result)
        
        if result["success"]:
            print(f"✓ Success - {result['response_time']}s - {result['total_tokens']} tokens")
            print(f"  Response preview: {result['content'][:150]}...")
        else:
            print(f"✗ Failed - {result['error']}")
        
        await asyncio.sleep(1)
    
    return results


def analyze_results(results: List[Dict]):
    """Analyze test results and provide recommendations."""
    
    print("\n" + "=" * 80)
    print("ANALYSIS & RECOMMENDATIONS")
    print("=" * 80)
    
    # Group by test type
    by_test = {}
    for result in results:
        test = result["test"]
        if test not in by_test:
            by_test[test] = []
        by_test[test].append(result)
    
    recommendations = {}
    
    for test_name, test_results in by_test.items():
        print(f"\n{test_name.upper().replace('_', ' ')}:")
        print("-" * 80)
        
        # Filter successful results
        successful = [r for r in test_results if r["success"]]
        
        if not successful:
            print("❌ No successful results for this test")
            continue
        
        # Sort by quality indicators
        # Quality = longer, more detailed responses + reasonable speed
        for r in successful:
            # Quality score: content length + inverse of response time
            r["quality_score"] = r["content_length"] / max(r["response_time"], 0.1)
        
        # Sort by quality score
        successful.sort(key=lambda x: x["quality_score"], reverse=True)
        
        print(f"\n{'Rank':<5} {'Model':<50} {'Time':<8} {'Tokens':<8} {'Quality':<10}")
        print("-" * 80)
        
        for i, r in enumerate(successful[:5], 1):
            print(f"{i:<5} {r['model']:<50} {r['response_time']:<8}s {r['total_tokens']:<8} {r['quality_score']:<10.1f}")
        
        # Recommendation
        best = successful[0]
        recommendations[test_name] = best["model"]
        
        print(f"\n✓ RECOMMENDED: {best['model']}")
        print(f"  - Response time: {best['response_time']}s")
        print(f"  - Tokens: {best['total_tokens']}")
        print(f"  - Quality score: {best['quality_score']:.1f}")
    
    # Final recommendations
    print("\n" + "=" * 80)
    print("FINAL CONFIGURATION RECOMMENDATIONS")
    print("=" * 80)
    
    print("\nBased on quality and speed priorities:\n")
    
    if "trade_analysis" in recommendations:
        print(f"PRIMARY MODEL (Trade Analysis, Market Analysis):")
        print(f"  {recommendations['trade_analysis']}")
    
    if "copilot_chat" in recommendations:
        print(f"\nSECONDARY MODEL (Copilot Chat, Quick Responses):")
        print(f"  {recommendations['copilot_chat']}")
    
    # Suggest backup
    print(f"\nBACKUP MODEL (Fallback):")
    print(f"  minimax/minimax-m2:free")
    
    print("\n" + "=" * 80)
    print("UPDATE YOUR .env FILE")
    print("=" * 80)
    print("\nAdd these lines to backend/.env:\n")
    
    if "trade_analysis" in recommendations:
        print(f"OPENROUTER_PRIMARY_MODEL={recommendations['trade_analysis']}")
    if "copilot_chat" in recommendations:
        print(f"OPENROUTER_SECONDARY_MODEL={recommendations['copilot_chat']}")
    print(f"OPENROUTER_BACKUP_MODEL=minimax/minimax-m2:free")
    
    # Save detailed results
    with open("backend/model_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✓ Detailed results saved to: backend/model_test_results.json")
    
    return recommendations


async def main():
    """Main test runner."""
    
    if not settings.openrouter_api_key:
        print("❌ Error: OPENROUTER_API_KEY not set in .env")
        return
    
    print(f"Using OpenRouter API: {settings.openrouter_api_base_url}")
    print(f"API Key: {settings.openrouter_api_key[:20]}...")
    
    try:
        results = await run_all_tests()
        recommendations = analyze_results(results)
        
        print("\n" + "=" * 80)
        print("TESTING COMPLETE!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Review the recommendations above")
        print("2. Update backend/.env with recommended models")
        print("3. Restart the backend")
        print("4. Start trading with optimized models!")
        
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
