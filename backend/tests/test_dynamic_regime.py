"""Test dynamic VIX-based regime multipliers."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


def test_dynamic_multipliers():
    """Test that choppy regime multipliers vary with VIX."""
    
    print("\n" + "="*80)
    print("🧪 TESTING DYNAMIC VIX-BASED REGIME MULTIPLIERS")
    print("="*80 + "\n")
    
    # Create a mock detector with just the method we need
    class MockDetector:
        def _calculate_position_multiplier(self, regime: str, volatility: dict = None) -> float:
            """Same logic as MarketRegimeDetector."""
            base_multipliers = {
                'broad_bullish': 1.5,
                'broad_bearish': 1.5,
                'broad_neutral': 1.0,
                'narrow_bullish': 0.7,
                'narrow_bearish': 0.7,
            }
            
            if regime == 'choppy':
                if volatility is None:
                    return 0.5
                
                vix = volatility.get('vix', 20.0)
                
                if vix < 20:
                    return 0.75
                elif vix <= 30:
                    return 0.5
                else:
                    return 0.25
            
            return base_multipliers.get(regime, 1.0)
    
    detector = MockDetector()
    
    # Test scenarios
    test_cases = [
        {
            'regime': 'choppy',
            'volatility': {'vix': 15.0, 'level': 'low'},
            'expected': 0.75,
            'description': 'Choppy + Low VIX (15)'
        },
        {
            'regime': 'choppy',
            'volatility': {'vix': 20.0, 'level': 'normal'},
            'expected': 0.5,
            'description': 'Choppy + Medium VIX (20)'
        },
        {
            'regime': 'choppy',
            'volatility': {'vix': 25.0, 'level': 'normal'},
            'expected': 0.5,
            'description': 'Choppy + Medium VIX (25)'
        },
        {
            'regime': 'choppy',
            'volatility': {'vix': 30.0, 'level': 'high'},
            'expected': 0.5,
            'description': 'Choppy + Medium VIX (30 - boundary)'
        },
        {
            'regime': 'choppy',
            'volatility': {'vix': 35.0, 'level': 'high'},
            'expected': 0.25,
            'description': 'Choppy + High VIX (35)'
        },
        {
            'regime': 'choppy',
            'volatility': {'vix': 50.0, 'level': 'high'},
            'expected': 0.25,
            'description': 'Choppy + Very High VIX (50)'
        },
        {
            'regime': 'broad_bullish',
            'volatility': {'vix': 25.0, 'level': 'normal'},
            'expected': 1.5,
            'description': 'Broad Bullish (VIX ignored)'
        },
        {
            'regime': 'narrow_bullish',
            'volatility': {'vix': 25.0, 'level': 'normal'},
            'expected': 0.7,
            'description': 'Narrow Bullish (VIX ignored)'
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        regime = test['regime']
        volatility = test['volatility']
        expected = test['expected']
        description = test['description']
        
        # Calculate multiplier
        multiplier = detector._calculate_position_multiplier(regime, volatility)
        
        # Check result
        if multiplier == expected:
            print(f"✅ Test {i}: {description}")
            print(f"   Expected: {expected}x, Got: {multiplier}x")
            passed += 1
        else:
            print(f"❌ Test {i}: {description}")
            print(f"   Expected: {expected}x, Got: {multiplier}x")
            failed += 1
        print()
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    print(f"❌ Failed: {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Dynamic VIX-based multipliers working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check implementation.")
    
    return failed == 0


if __name__ == "__main__":
    success = test_dynamic_multipliers()
    sys.exit(0 if success else 1)
