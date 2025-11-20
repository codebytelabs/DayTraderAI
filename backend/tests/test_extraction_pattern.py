#!/usr/bin/env python3
"""Test extraction on the actual response."""

import re

response = """**PART 1: MARKET SENTIMENT**   - **PRIMARY SCORE:** 17 (CNN Fear & Greed Index, as of November 7, 2025, 02:39 AM ET)   - **CLASSIFICATION:** Extreme Fear   - **BRIEF MARKET CONTEXT:** Investor sentiment remains deeply negative, with widespread risk-off behavior and strong demand for safe-haven assets."""

print("🔍 Testing Extraction Patterns")
print("=" * 80)
print("\n📄 RESPONSE:")
print(response)
print("\n" + "=" * 80)

patterns = [
    (r'PRIMARY\s+SCORE[:\s*]+(\d+)', 'Pattern 1: "PRIMARY SCORE: X"'),
    (r'(?:Fear\s*(?:and|&)\s*Greed\s+)?Index\s+is\s+(\d+)', 'Pattern 2: "Index is X"'),
    (r'(?:score|rating)[:\s]+(\d+)(?:\s|$|[^\d])', 'Pattern 3: "score: X"'),
    (r'(\d+)/100', 'Pattern 4: "X/100"'),
    (r'(\d+)\s+out of 100', 'Pattern 5: "X out of 100"'),
    (r'(\d+)\s*[-–—]\s*(?:Extreme Fear|Extreme Greed|Fear|Greed|Neutral)', 'Pattern 6: "X - Classification"'),
]

for i, (pattern, description) in enumerate(patterns, 1):
    match = re.search(pattern, response, re.IGNORECASE)
    if match:
        extracted = int(match.group(1))
        print(f"✅ {description}")
        print(f"   Matched: '{match.group(0)}'")
        print(f"   Extracted: {extracted}")
        if 0 <= extracted <= 100:
            print(f"   ✅ Valid (0-100)")
            print(f"   🎯 THIS SHOULD BE USED!")
            break
        print()
    else:
        print(f"❌ {description}: No match")

print("\n" + "=" * 80)
print("💡 SOLUTION: Add 'PRIMARY SCORE' pattern to extraction!")
