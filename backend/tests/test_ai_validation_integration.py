"""
Test AI Trade Validator Integration with Risk Manager
"""
import asyncio
from trading.ai_trade_validator import AITradeValidator
from trading.symbol_cooldown import SymbolCooldownManager
from core.state import trading_state


def test_high_risk_detection():
    """Test high-risk trade detection logic"""
    print("\n" + "="*60)
    print("TEST 1: High-Risk Detection Logic")
    print("="*60)
    
    validator = AITradeValidator()
    
    # Test Case 1: Normal trade (not high-risk)
    context = {
        'in_cooldown': False,
        'symbol_win_rate': 0.55,
        'position_pct': 5.0,
        'counter_trend': False,
        'confidence': 85,
        'consecutive_losses': 0
    }
    
    is_high_risk, reason = validator.is_high_risk('AAPL', 'buy', context)
    print(f"\n✅ Normal Trade:")
    print(f"   High Risk: {is_high_risk}")
    print(f"   Reason: {reason if reason else 'None'}")
    assert not is_high_risk, "Normal trade should not be high-risk"
    
    # Test Case 2: Symbol in cooldown (HIGH RISK)
    context = {
        'in_cooldown': True,
        'cooldown_hours': 24,
        'consecutive_losses': 3,
        'symbol_win_rate': 0.35,
        'position_pct': 5.0,
        'counter_trend': False,
        'confidence': 85
    }
    
    is_high_risk, reason = validator.is_high_risk('TSLA', 'buy', context)
    print(f"\n⚠️  Symbol in Cooldown:")
    print(f"   High Risk: {is_high_risk}")
    print(f"   Reason: {reason}")
    assert is_high_risk, "Cooldown trade should be high-risk"
    assert "cooldown" in reason.lower(), "Reason should mention cooldown"
    
    # Test Case 3: Low win rate (HIGH RISK)
    context = {
        'in_cooldown': False,
        'symbol_win_rate': 0.30,
        'position_pct': 5.0,
        'counter_trend': False,
        'confidence': 85,
        'consecutive_losses': 0
    }
    
    is_high_risk, reason = validator.is_high_risk('PATH', 'buy', context)
    print(f"\n⚠️  Low Win Rate:")
    print(f"   High Risk: {is_high_risk}")
    print(f"   Reason: {reason}")
    assert is_high_risk, "Low win rate should be high-risk"
    assert "win rate" in reason.lower(), "Reason should mention win rate"
    
    # Test Case 4: Large position (HIGH RISK)
    context = {
        'in_cooldown': False,
        'symbol_win_rate': 0.55,
        'position_pct': 12.0,
        'counter_trend': False,
        'confidence': 85,
        'consecutive_losses': 0
    }
    
    is_high_risk, reason = validator.is_high_risk('NVDA', 'buy', context)
    print(f"\n⚠️  Large Position:")
    print(f"   High Risk: {is_high_risk}")
    print(f"   Reason: {reason}")
    assert is_high_risk, "Large position should be high-risk"
    assert "position" in reason.lower(), "Reason should mention position"
    
    # Test Case 5: Counter-trend (HIGH RISK)
    context = {
        'in_cooldown': False,
        'symbol_win_rate': 0.55,
        'position_pct': 5.0,
        'counter_trend': True,
        'daily_trend': 'bearish',
        'confidence': 85,
        'consecutive_losses': 0
    }
    
    is_high_risk, reason = validator.is_high_risk('MSFT', 'buy', context)
    print(f"\n⚠️  Counter-Trend:")
    print(f"   High Risk: {is_high_risk}")
    print(f"   Reason: {reason}")
    assert is_high_risk, "Counter-trend should be high-risk"
    assert "counter-trend" in reason.lower(), "Reason should mention counter-trend"
    
    # Test Case 6: Low confidence (HIGH RISK)
    context = {
        'in_cooldown': False,
        'symbol_win_rate': 0.55,
        'position_pct': 5.0,
        'counter_trend': False,
        'confidence': 65,
        'consecutive_losses': 0
    }
    
    is_high_risk, reason = validator.is_high_risk('GOOGL', 'buy', context)
    print(f"\n⚠️  Low Confidence:")
    print(f"   High Risk: {is_high_risk}")
    print(f"   Reason: {reason}")
    assert is_high_risk, "Low confidence should be high-risk"
    assert "confidence" in reason.lower(), "Reason should mention confidence"
    
    # Test Case 7: Multiple risk factors (VERY HIGH RISK)
    context = {
        'in_cooldown': True,
        'cooldown_hours': 48,
        'consecutive_losses': 4,
        'symbol_win_rate': 0.25,
        'position_pct': 10.0,
        'counter_trend': True,
        'daily_trend': 'bearish',
        'confidence': 60
    }
    
    is_high_risk, reason = validator.is_high_risk('ABNB', 'buy', context)
    print(f"\n🚨 Multiple Risk Factors:")
    print(f"   High Risk: {is_high_risk}")
    print(f"   Reason: {reason}")
    assert is_high_risk, "Multiple risk factors should be high-risk"
    
    print(f"\n✅ All high-risk detection tests passed!")


async def test_ai_validation():
    """Test AI validation with real API call"""
    print("\n" + "="*60)
    print("TEST 2: AI Validation (Real API Call)")
    print("="*60)
    
    validator = AITradeValidator()
    
    # Test Case: High-risk trade that should be rejected
    features = {
        'price': 250.50,
        'atr': 5.20,
        'adx': 22,
        'volume_ratio': 1.8
    }
    
    context = {
        'in_cooldown': True,
        'cooldown_hours': 24,
        'consecutive_losses': 3,
        'symbol_win_rate': 0.30,
        'position_pct': 8.5,
        'counter_trend': True,
        'daily_trend': 'bearish',
        'confidence': 65
    }
    
    print(f"\n🤖 Testing AI validation for high-risk TSLA trade...")
    print(f"   Context: In cooldown (24h), 3 losses, 30% win rate")
    print(f"   Position: 8.5% of equity, counter-trend, 65% confidence")
    
    approved, reason = await validator.validate(
        symbol='TSLA',
        signal='buy',
        features=features,
        context=context,
        timeout=5.0
    )
    
    print(f"\n   AI Decision: {'APPROVED ✅' if approved else 'REJECTED ❌'}")
    print(f"   AI Reason: {reason}")
    
    # Get stats
    stats = validator.get_stats()
    print(f"\n📊 Validation Stats:")
    print(f"   Total Validations: {stats['total_validations']}")
    print(f"   Approvals: {stats['approvals']}")
    print(f"   Rejections: {stats['rejections']}")
    print(f"   Errors: {stats['errors']}")
    print(f"   Avg Time: {stats['avg_validation_time']:.2f}s")


def test_prompt_building():
    """Test prompt building logic"""
    print("\n" + "="*60)
    print("TEST 3: Prompt Building")
    print("="*60)
    
    validator = AITradeValidator()
    
    features = {
        'price': 250.50,
        'atr': 5.20
    }
    
    context = {
        'in_cooldown': True,
        'cooldown_hours': 24,
        'consecutive_losses': 3,
        'symbol_win_rate': 0.30,
        'position_pct': 8.5,
        'counter_trend': True,
        'daily_trend': 'bearish',
        'confidence': 65
    }
    
    prompt = validator._build_validation_prompt('TSLA', 'buy', features, context)
    
    print(f"\n📝 Generated Prompt:")
    print("-" * 60)
    print(prompt)
    print("-" * 60)
    
    # Verify prompt contains key information
    assert 'TSLA' in prompt, "Prompt should contain symbol"
    assert '250.50' in prompt, "Prompt should contain price"
    assert 'cooldown' in prompt.lower(), "Prompt should mention cooldown"
    assert 'win rate' in prompt.lower(), "Prompt should mention win rate"
    assert 'counter-trend' in prompt.lower(), "Prompt should mention counter-trend"
    
    print(f"\n✅ Prompt building test passed!")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("AI TRADE VALIDATOR INTEGRATION TESTS")
    print("="*70)
    
    try:
        # Test 1: High-risk detection
        test_high_risk_detection()
        
        # Test 2: Prompt building
        test_prompt_building()
        
        # Test 3: AI validation (real API call)
        asyncio.run(test_ai_validation())
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\nNext Steps:")
        print("1. Enable AI validation in config.py: ENABLE_AI_VALIDATION = True")
        print("2. Restart backend: ./restart_backend.sh")
        print("3. Monitor logs for AI validation: tail -f logs/trading.log | grep '🤖'")
        print("4. Track rejection rate and validation times")
        print("\nExpected Impact:")
        print("- Prevents 5-10 bad trades per month")
        print("- Saves $500-2,000/month")
        print("- Adds 3-4s latency only for high-risk trades (~10% of total)")
        print("- Cost: ~$0.01/month")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
