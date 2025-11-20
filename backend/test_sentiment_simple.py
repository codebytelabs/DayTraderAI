#!/usr/bin/env python3
"""
Simple test for Fear & Greed Index fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from indicators.fear_greed_scraper import FearGreedScraper

def test_fear_greed():
    print("🧪 Testing Simplified Fear & Greed Index")
    print("=" * 60)
    
    scraper = FearGreedScraper()
    result = scraper.get_fear_greed_index()
    
    print(f"\n📊 Result:")
    print(f"   Score: {result['score']}/100")
    print(f"   Classification: {result['classification']}")
    print(f"   Source: {result['source']}")
    print(f"   Success: {result['success']}")
    
    print(f"\n🎯 Trading Impact:")
    score = result['score']
    
    if score < 15:
        print(f"   ⛔ Extreme fear ({score}/100) - All shorts blocked")
    elif score < 35:
        print(f"   ⚠️  Fear ({score}/100) - Shorts need 3+ confirmations")
    elif score < 55:
        print(f"   ✅ Neutral ({score}/100) - Normal trading")
    elif score < 75:
        print(f"   📈 Greed ({score}/100) - Favorable for shorts")
    else:
        print(f"   🚀 Extreme greed ({score}/100) - Very favorable for shorts")
    
    print("\n" + "=" * 60)
    
    if result['source'] == 'default_neutral':
        print("✅ Using default neutral (50) - allows normal trading")
    elif score >= 15:
        print("✅ Sentiment allows trading with proper confirmations")
    else:
        print("⚠️  Extreme fear - shorts will be blocked")
    
    return result

if __name__ == "__main__":
    test_fear_greed()
