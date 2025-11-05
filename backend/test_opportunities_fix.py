#!/usr/bin/env python3
"""
Test that opportunities queries are classified correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from copilot.action_classifier import ActionClassifier


def test_opportunities_classification():
    """Test that opportunities queries are classified as advise, not info."""
    print("🧪 Testing Opportunities Query Classification\n")
    
    classifier = ActionClassifier()
    
    test_queries = [
        ("Show me trading opportunities", "advise"),
        ("Show me trading opportunities: new position ideas, strong signals", "advise"),
        ("trading opportunities", "advise"),
        ("what are the best opportunities", "advise"),
        ("find me some trade ideas", "advise"),
        ("show me my positions", "info"),  # This should still be info
        ("what's my account status", "info"),  # This should still be info
    ]
    
    print("Testing query classifications:\n")
    
    all_passed = True
    for query, expected_intent in test_queries:
        intent = classifier.classify(query, {})
        actual_intent = intent.intent_type
        
        status = "✅" if actual_intent == expected_intent else "❌"
        print(f"{status} '{query}'")
        print(f"   Expected: {expected_intent}, Got: {actual_intent}, Confidence: {intent.confidence:.2f}")
        
        if actual_intent != expected_intent:
            all_passed = False
            print(f"   ⚠️  MISMATCH!")
        
        print()
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Opportunities queries are now correctly classified as 'advise'")
        print("✅ They will be routed to OpenRouter for analysis")
        print("✅ They will NOT return account summary")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("\n⚠️  Opportunities queries are still being misclassified")
        return 1


if __name__ == "__main__":
    exit(test_opportunities_classification())
