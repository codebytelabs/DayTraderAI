#!/usr/bin/env python3
"""Debug sentiment extraction to find the exact issue."""

import re

# This is the actual response from the previous test
test_response = """**PART 1: MARKET SENTIMENT**
- **Current Fear & Greed score:** 23.8[4]
- **Classification:** Extreme Fear[4][1]
- **Market context:** The market is exhibiting significant risk aversion, with sentiment deep in "extreme fear" territory; investors are actively reducing exposure to equities, suggesting heightened uncertainty and likely volatility. This is a marked shift from earlier in the year, with the recent reading near cycle lows, reflecting defensive positioning[1][4]."""

print("🎯 Testing Sentiment Extraction")
print("=" * 80)
print("\n📄 TEST RESPONSE:")
print("-" * 80)
print(test_response)
print("-" * 80)

print("\n🔍 TESTING EXTRACTION PATTERNS:")
print("=" * 80)

patterns = [
    (r'(?:score|index|rating)(?:\s+is)?[:\s]+(\d+)', 'Pattern 1: "score: X"'),
    (r'(\d+)/100', 'Pattern 2: "X/100"'),
    (r'(\d+)\s+out of 100', 'Pattern 3: "X out of 100"'),
    (r'Fear\s*&\s*Greed[^0-9]{0,50}?(\d+)', 'Pattern 4: Number near "Fear & Greed"'),
    (r'(\d+)\s*[-–—]\s*(?:Extreme Fear|Extreme Greed|Fear|Greed|Neutral)', 'Pattern 5: "X - Classification"'),
]

for pattern, description in patterns:
    match = re.search(pattern, test_response, re.IGNORECASE)
    if match:
        extracted = int(match.group(1))
        print(f"✅ {description}")
        print(f"   Matched: '{match.group(0)}'")
        print(f"   Extracted: {extracted}")
        if 0 <= extracted <= 100:
            print(f"   ✅ Valid score (0-100)")
        else:
            print(f"   ❌ Invalid score (not 0-100)")
        print()
    else:
        print(f"❌ {description}: No match\n")

print("=" * 80)
print("\n💡 ANALYSIS:")
print("-" * 80)
print("The response shows: 'score: 23.8[4]'")
print("This is NOT the actual score!")
print("[4] is a citation reference number")
print("23.8 appears to be some other metric")
print()
print("The ACTUAL CNN Fear & Greed score is 18 (as you verified)")
print("The AI is not providing the correct score in the combined query!")
print()
print("🔧 SOLUTION:")
print("We need to either:")
print("1. Make the query more explicit about getting the EXACT score")
print("2. Use a separate, focused query just for sentiment")
print("3. Parse the citations to find the CNN source directly")
print("=" * 80)
