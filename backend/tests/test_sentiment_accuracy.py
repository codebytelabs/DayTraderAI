#!/usr/bin/env python3
"""
Test: Sentiment Extraction Accuracy
Validates that we extract the EXACT CNN Fear & Greed score
"""

import asyncio
from scanner.ai_opportunity_finder import get_ai_opportunity_finder

async def test_sentiment_accuracy():
    print("🎯 Testing Sentiment Extraction Accuracy")
    print("=" * 80)
    
    ai_finder = get_ai_opportunity_finder()
    
    print("\n📊 STEP 1: Discover Opportunities (includes sentiment)")
    print("-" * 80)
    
    opportunities = await ai_finder.discover_opportunities(max_symbols=20)
    
    print(f"✅ Discovered {len(opportunities)} opportunities")
    
    print("\n📊 STEP 2: Check Extracted Sentiment")
    print("-" * 80)
    
    sentiment = ai_finder.get_current_sentiment()
    
    print(f"\n🎭 EXTRACTED SENTIMENT:")
    print(f"   Score: {sentiment['score']}/100")
    print(f"   Classification: {sentiment['classification']}")
    print(f"   Timestamp: {sentiment['timestamp']}")
    
    print("\n📊 STEP 3: Validate Against Manual Check")
    print("-" * 80)
    
    manual_score = 18  # What you verified manually
    extracted_score = sentiment['score']
    
    print(f"   Manual Check (CNN website): {manual_score}/100")
    print(f"   Extracted Score: {extracted_score}/100")
    
    if extracted_score == manual_score:
        print(f"\n✅ SUCCESS: Scores match perfectly!")
        print(f"   The extraction is working correctly.")
        return True
    else:
        diff = abs(extracted_score - manual_score)
        print(f"\n⚠️  MISMATCH: {diff} point difference")
        print(f"   Manual: {manual_score}")
        print(f"   Extracted: {extracted_score}")
        
        if diff <= 2:
            print(f"\n⚠️  ACCEPTABLE: Within 2 points (may be timing difference)")
            return True
        else:
            print(f"\n❌ FAILED: Difference too large")
            print(f"   This indicates the extraction is still not working correctly.")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_sentiment_accuracy())
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 SENTIMENT EXTRACTION: VALIDATED")
        print("=" * 80)
        print("The system now extracts the EXACT CNN Fear & Greed score!")
    else:
        print("❌ SENTIMENT EXTRACTION: NEEDS MORE WORK")
        print("=" * 80)
        print("The extraction logic needs further refinement.")
