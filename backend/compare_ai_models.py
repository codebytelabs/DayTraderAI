import asyncio
import os
import sys
import time
import json
from typing import Dict, List, Any
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
# Try loading from backend/.env first, then .env
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'), override=True)
load_dotenv(override=True)

from config import settings
from advisory.perplexity import PerplexityClient
from advisory.openrouter_client import OpenRouterClient
from scanner.ai_opportunity_finder import AIOpportunityFinder
from utils.logger import setup_logger
import logging

# Configure logger to output to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_comparison():
    print("\n🧪 AI MODEL COMPARISON: Opportunity Discovery")
    print("=" * 80)
    
    # Debug Config
    key = settings.openrouter_api_key
    print(f"DEBUG: OpenRouter Key Loaded: {'Yes' if key else 'No'}")
    if key:
        print(f"DEBUG: Key Prefix: {key[:15]}...")
    print(f"DEBUG: Sonar Pro Model: {settings.openrouter_model_sonar_pro}")
    
    # Initialize clients
    perplexity = PerplexityClient()
    openrouter = OpenRouterClient()
    finder = AIOpportunityFinder()
    
    # Define models to test
    # Note: OpenRouter model IDs might need adjustment based on availability
    models_to_test = [
        {
            "name": "Perplexity (Direct)",
            "provider": "perplexity",
            "model": settings.perplexity_default_model
        },
        {
            "name": "OpenRouter: Sonar Pro",
            "provider": "openrouter",
            "model": settings.openrouter_model_sonar_pro
        },
        {
            "name": "OpenRouter: Sonar",
            "provider": "openrouter",
            "model": settings.openrouter_model_sonar
        },
        {
            "name": "OpenRouter: DeepSeek",
            "provider": "openrouter",
            "model": settings.openrouter_model_deepseek
        },
        {
            "name": "OpenRouter: Gemini 3 Pro Preview",
            "provider": "openrouter",
            "model": settings.openrouter_model_gemini
        }
    ]
    
    # Use the standard discovery query
    query = finder._build_discovery_query()
    print(f"📝 Query Length: {len(query)} chars")
    print("-" * 80)
    
    results = []
    
    for model_info in models_to_test:
        name = model_info["name"]
        provider = model_info["provider"]
        model_id = model_info["model"]
        
        print(f"\n🚀 Testing: {name} ({model_id})...")
        start_time = time.time()
        
        try:
            response = None
            if provider == "perplexity":
                # Direct Perplexity call
                response = await perplexity.search(query)
            else:
                # OpenRouter call with specific model
                response = await openrouter.search(query, model=model_id)
            
            duration = time.time() - start_time
            
            if response and response.get('content'):
                content = response['content']
                citations = response.get('citations', [])
                
                # Analyze content
                symbols = finder._extract_symbols(content)
                sentiment_score, sentiment_class = finder._extract_sentiment(content)
                
                # Check for specific required sections
                has_catalysts = "CATALYST" in content.upper()
                has_technicals = "TECHNICAL" in content.upper()
                
                result = {
                    "name": name,
                    "model": model_id,
                    "duration": f"{duration:.2f}s",
                    "symbols_found": len(symbols),
                    "sentiment": f"{sentiment_score} ({sentiment_class})",
                    "citations": len(citations),
                    "has_catalysts": "✅" if has_catalysts else "❌",
                    "has_technicals": "✅" if has_technicals else "❌",
                    "content_preview": content[:100].replace("\n", " ") + "..."
                }
                results.append(result)
                print(f"✅ Success! Found {len(symbols)} symbols in {duration:.2f}s")
            else:
                print("❌ Failed: No content returned")
                results.append({
                    "name": name,
                    "model": model_id,
                    "duration": f"{duration:.2f}s",
                    "error": "No content"
                })
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Error: {e}")
            results.append({
                "name": name,
                "model": model_id,
                "duration": f"{duration:.2f}s",
                "error": str(e)
            })
            
    # Print Comparison Table
    print("\n\n📊 COMPARISON RESULTS")
    print("=" * 120)
    print(f"{'Model':<25} | {'Time':<8} | {'Syms':<5} | {'Sentiment':<15} | {'Cits':<5} | {'Cat':<4} | {'Tech':<4} | {'Status'}")
    print("-" * 120)
    
    for r in results:
        if "error" in r:
            print(f"{r['name']:<25} | {r['duration']:<8} | {'-':<5} | {'-':<15} | {'-':<5} | {'-':<4} | {'-':<4} | ❌ {r['error']}")
        else:
            print(f"{r['name']:<25} | {r['duration']:<8} | {r['symbols_found']:<5} | {r['sentiment']:<15} | {r['citations']:<5} | {r['has_catalysts']:<4} | {r['has_technicals']:<4} | ✅ Success")
    print("=" * 120)
    
    # Recommendation logic
    print("\n💡 RECOMMENDATION:")
    best_model = None
    max_score = -1
    
    for r in results:
        if "error" in r:
            continue
            
        # Simple scoring: symbols * 2 + citations + (catalysts?10:0) + (technicals?10:0) - duration
        score = r['symbols_found'] * 2 + r['citations']
        if r['has_catalysts'] == "✅": score += 10
        if r['has_technicals'] == "✅": score += 10
        try:
            dur = float(r['duration'].replace('s', ''))
            score -= dur  # Penalize slowness
        except:
            pass
            
        if score > max_score:
            max_score = score
            best_model = r
            
    if best_model:
        print(f"Based on this test, **{best_model['name']}** performed best.")
        print(f"It found {best_model['symbols_found']} symbols with rich metadata in {best_model['duration']}.")
    else:
        print("No models completed successfully.")

if __name__ == "__main__":
    asyncio.run(run_comparison())
