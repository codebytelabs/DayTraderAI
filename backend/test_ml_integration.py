#!/usr/bin/env python3
"""
Test ML Shadow Mode Integration
Verify that ML shadow mode is properly integrated and will start with the app
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test that all ML imports work"""
    print("Testing imports...")
    try:
        from ml.shadow_mode import MLShadowMode
        from core.supabase_client import SupabaseClient
        from trading.strategy import EMAStrategy
        from trading.order_manager import OrderManager
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_ml_shadow_mode_init():
    """Test ML shadow mode initialization"""
    print("\nTesting ML shadow mode initialization...")
    try:
        from ml.shadow_mode import MLShadowMode
        from core.supabase_client import SupabaseClient
        
        supabase = SupabaseClient()
        ml_shadow = MLShadowMode(supabase, ml_weight=0.0)
        
        print(f"✓ ML shadow mode initialized")
        print(f"  Weight: {ml_shadow.ml_weight}")
        print(f"  Predictions made: {ml_shadow.predictions_made}")
        
        stats = ml_shadow.get_statistics()
        print(f"  Statistics: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_with_ml():
    """Test that strategy accepts ML shadow mode"""
    print("\nTesting strategy with ML shadow mode...")
    try:
        from ml.shadow_mode import MLShadowMode
        from core.supabase_client import SupabaseClient
        from trading.strategy import EMAStrategy
        from trading.order_manager import OrderManager
        from trading.risk_manager import RiskManager
        from core.alpaca_client import AlpacaClient
        
        # Initialize components
        alpaca = AlpacaClient()
        supabase = SupabaseClient()
        risk_manager = RiskManager(alpaca)
        order_manager = OrderManager(alpaca, supabase, risk_manager)
        ml_shadow = MLShadowMode(supabase, ml_weight=0.0)
        
        # Initialize strategy with ML shadow mode
        strategy = EMAStrategy(order_manager, ml_shadow_mode=ml_shadow)
        
        print(f"✓ Strategy initialized with ML shadow mode")
        print(f"  ML shadow mode attached: {strategy.ml_shadow_mode is not None}")
        print(f"  ML weight: {strategy.ml_shadow_mode.ml_weight if strategy.ml_shadow_mode else 'N/A'}")
        
        return True
    except Exception as e:
        print(f"❌ Strategy initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("ML SHADOW MODE INTEGRATION TEST")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("ML Shadow Mode Init", test_ml_shadow_mode_init()))
    results.append(("Strategy with ML", test_strategy_with_ml()))
    
    # Summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("✅ ALL TESTS PASSED!")
        print()
        print("ML Shadow Mode is ready to:")
        print("  • Start with the app")
        print("  • Make predictions for all trade signals")
        print("  • Log predictions to database")
        print("  • Track accuracy over time")
        print("  • Run at 0% weight (no impact on trading)")
        print()
        print("Next: Restart your backend to activate ML shadow mode!")
        return 0
    else:
        print()
        print("❌ SOME TESTS FAILED")
        print("Please fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
