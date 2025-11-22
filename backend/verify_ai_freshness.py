import asyncio
import os
import sys
from dotenv import load_dotenv

# Force load .env
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'), override=True)
load_dotenv(override=True)

from config import settings
from advisory.perplexity import PerplexityClient
from advisory.openrouter_client import OpenRouterClient
from datetime import datetime
import pytz

async def test_freshness():
    print("\n" + "="*80)
    print("🔍 AI FRESHNESS & ACCURACY VERIFICATION")
    print("="*80)
    
    # Initialize clients
    perplexity = PerplexityClient()
    openrouter = OpenRouterClient()
    
    # Current time for reference
    et_tz = pytz.timezone('US/Eastern')
    now = datetime.now(et_tz)
    print(f"🕒 System Time (ET): {now.strftime('%Y-%m-%d %I:%M:%S %p')}")
    print("-" * 80)
    
    # The "Freshness" Query
    query = (
        f"What is the EXACT current time in New York right now? "
        f"What are the top 3 breaking financial news headlines from the LAST HOUR? "
        f"Please cite your sources with timestamps."
    )
    
    print(f"❓ Query: {query}\n")
    
    results = []
    
    # 1. Test Native Perplexity
    print(f"🚀 Testing Native Perplexity ({settings.perplexity_default_model})...")
    start_time = datetime.now()
    try:
        px_result = await perplexity.search(query)
        duration = (datetime.now() - start_time).total_seconds()
        
        if px_result and px_result.get('content'):
            content = px_result['content']
            citations = px_result.get('citations', [])
            print(f"✅ Success ({duration:.2f}s)")
            results.append({
                "provider": "Perplexity (Native)",
                "model": settings.perplexity_default_model,
                "content": content,
                "citations": citations,
                "duration": duration
            })
        else:
            print("❌ Failed: No content")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("-" * 40)

    # 2. Test OpenRouter (Sonar Pro)
    or_model = settings.openrouter_model_sonar_pro
    print(f"🚀 Testing OpenRouter ({or_model})...")
    start_time = datetime.now()
    try:
        or_result = await openrouter.search(query, model=or_model)
        duration = (datetime.now() - start_time).total_seconds()
        
        if or_result and or_result.get('content'):
            content = or_result['content']
            citations = or_result.get('citations', [])
            print(f"✅ Success ({duration:.2f}s)")
            results.append({
                "provider": "OpenRouter",
                "model": or_model,
                "content": content,
                "citations": citations,
                "duration": duration
            })
        else:
            print("❌ Failed: No content")
    except Exception as e:
        print(f"❌ Error: {e}")
        
    # Compare Results
    print("\n" + "="*80)
    print("📊 SIDE-BY-SIDE COMPARISON")
    print("="*80)
    
    for res in results:
        print(f"\n🔹 PROVIDER: {res['provider']} ({res['model']})")
        print(f"⏱️ Time: {res['duration']:.2f}s")
        print(f"🔗 Citations: {len(res['citations'])}")
        print("-" * 20)
        print(res['content'][:1000] + "..." if len(res['content']) > 1000 else res['content'])
        print("-" * 20)
        if res['citations']:
            print("Sources:")
            for i, cit in enumerate(res['citations'][:3], 1):
                print(f"  {i}. {cit}")
        print("="*80)

if __name__ == "__main__":
    asyncio.run(test_freshness())
