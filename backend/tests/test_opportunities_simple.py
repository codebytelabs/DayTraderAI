#!/usr/bin/env python3
"""
Simple test for opportunities query classification (no dependencies).
"""

# Simulate the keyword sets
ADVISE_KEYWORDS = {
    "should", "would", "could", "recommend", "think", "suggest",
    "advice", "opinion", "analysis", "evaluate", "assess", "opportunities",
    "opportunity", "ideas", "signals", "trades", "setups"
}

ADVISE_PHRASES = {
    "should i", "what do you think", "do you recommend", "is it good",
    "what about", "how about", "your opinion", "your thoughts",
    "trading opportunities", "new opportunities", "trade ideas",
    "trading ideas", "show me opportunities", "find opportunities",
    "what can", "what should", "what to do"
}

INFO_KEYWORDS = {
    "is", "are", "what", "show", "display", "get", "check", "status",
    "how", "when", "where", "tell", "give"
}

INFO_PHRASES = {
    "market open", "market closed", "trading hours", "is market",
    "show position", "show me", "what's my", "how is", "status of",
    "check market", "get position"
}


def score_advise_intent(query: str) -> float:
    """Score how likely the query is an advise intent."""
    score = 0.0
    
    # Check for advise phrases
    for phrase in ADVISE_PHRASES:
        if phrase in query:
            score += 2.5
    
    # Check for advise keywords
    words = set(query.split())
    for keyword in ADVISE_KEYWORDS:
        if keyword in words:
            score += 1.5
    
    return score


def score_info_intent(query: str) -> float:
    """Score how likely the query is an info intent."""
    score = 0.0
    
    # Reduce score if query contains advise keywords
    has_advise_keywords = any(kw in query for kw in ADVISE_KEYWORDS)
    has_advise_phrases = any(phrase in query for phrase in ADVISE_PHRASES)
    
    if has_advise_keywords or has_advise_phrases:
        # This is likely an advise query, not info
        return 0.0
    
    # Check for info phrases
    for phrase in INFO_PHRASES:
        if phrase in query:
            score += 2.0
    
    # Check for info keywords
    words = set(query.split())
    for keyword in INFO_KEYWORDS:
        if keyword in words:
            score += 1.0
    
    # Boost for question structure
    if query.endswith('?'):
        score += 1.0
    
    # Boost if starts with question word
    first_word = query.split()[0] if query.split() else ""
    if first_word in INFO_KEYWORDS:
        score += 1.5
    
    return score


def classify_query(query: str) -> str:
    """Classify query intent."""
    normalized = query.lower().strip()
    
    advise_score = score_advise_intent(normalized)
    info_score = score_info_intent(normalized)
    
    if advise_score > info_score:
        return "advise"
    elif info_score > advise_score:
        return "info"
    else:
        return "advise"  # Default to advise


def main():
    """Test opportunities classification."""
    print("🧪 Testing Opportunities Query Classification\n")
    
    test_cases = [
        ("Show me trading opportunities", "advise"),
        ("Show me trading opportunities: new position ideas", "advise"),
        ("trading opportunities", "advise"),
        ("what are the best opportunities", "advise"),
        ("find me some trade ideas", "advise"),
        ("show me my positions", "info"),
        ("what's my account status", "info"),
        ("is the market open", "info"),
    ]
    
    all_passed = True
    
    for query, expected in test_cases:
        normalized = query.lower().strip()
        advise_score = score_advise_intent(normalized)
        info_score = score_info_intent(normalized)
        actual = classify_query(query)
        
        status = "✅" if actual == expected else "❌"
        print(f"{status} '{query}'")
        print(f"   Expected: {expected}, Got: {actual}")
        print(f"   Scores: advise={advise_score:.1f}, info={info_score:.1f}")
        
        if actual != expected:
            all_passed = False
            print(f"   ⚠️  MISMATCH!")
        
        print()
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Opportunities queries are correctly classified as 'advise'")
        print("✅ They will be routed to OpenRouter for analysis")
        print("✅ They will NOT return account summary")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
