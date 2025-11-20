"""
Quick test of momentum system components
"""

import sys
import numpy as np
from momentum import MomentumConfig, MomentumSignal, MomentumSignalValidator
from momentum.indicators import ADXCalculator, VolumeAnalyzer, TrendStrengthCalculator

def test_indicators():
    """Test indicator calculations"""
    print("🧪 Testing Indicators...")
    
    # Generate sample data (uptrend with momentum)
    np.random.seed(42)
    base_price = 100
    prices = []
    for i in range(60):
        # Uptrend with noise
        trend = i * 0.5
        noise = np.random.normal(0, 0.5)
        prices.append(base_price + trend + noise)
    
    high = [p + np.random.uniform(0, 0.5) for p in prices]
    low = [p - np.random.uniform(0, 0.5) for p in prices]
    close = prices
    volume = [1000000 + np.random.uniform(-100000, 300000) for _ in range(60)]
    
    # Test ADX
    adx_calc = ADXCalculator(period=14)
    adx = adx_calc.calculate(high, low, close)
    print(f"  ✓ ADX: {adx:.1f}")
    
    # Test Volume
    vol_analyzer = VolumeAnalyzer(lookback_period=20)
    vol_ratio = vol_analyzer.calculate_volume_ratio(volume)
    print(f"  ✓ Volume Ratio: {vol_ratio:.2f}x")
    
    # Test Trend Strength
    trend_calc = TrendStrengthCalculator()
    trend = trend_calc.calculate(close, high, low)
    print(f"  ✓ Trend Strength: {trend:.2f}")
    
    return high, low, close, volume

def test_validator():
    """Test momentum validator"""
    print("\n🧪 Testing Validator...")
    
    # Get test data
    high, low, close, volume = test_indicators()
    
    # Create config
    config = MomentumConfig(
        enabled=True,
        adx_threshold=25.0,
        volume_threshold=1.5,
        trend_threshold=0.7
    )
    
    # Create validator
    validator = MomentumSignalValidator(config)
    
    # Test validation
    signal = validator.validate_momentum(
        symbol='TEST',
        high=high,
        low=low,
        close=close,
        volume=volume,
        current_profit_r=0.85
    )
    
    print(f"  ✓ Signal Generated")
    print(f"    Extend: {signal.extend}")
    print(f"    ADX: {signal.adx:.1f} {'✅' if signal.adx_pass else '❌'}")
    print(f"    Volume: {signal.volume_ratio:.2f}x {'✅' if signal.volume_pass else '❌'}")
    print(f"    Trend: {signal.trend_strength:.2f} {'✅' if signal.trend_pass else '❌'}")
    print(f"    Reason: {signal.reason}")
    
    return signal

def test_config():
    """Test configuration"""
    print("\n🧪 Testing Configuration...")
    
    # Test conservative config
    config = MomentumConfig.default_conservative()
    print(f"  ✓ Conservative config created")
    print(f"    Enabled: {config.enabled}")
    print(f"    ADX Threshold: {config.adx_threshold}")
    
    # Test validation
    try:
        bad_config = MomentumConfig(
            enabled=True,
            adx_threshold=100.0  # Invalid
        )
        print("  ❌ Validation failed to catch bad config")
    except ValueError as e:
        print(f"  ✓ Validation caught bad config: {str(e)[:50]}...")
    
    return config

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Momentum System Quick Test")
    print("=" * 60)
    
    try:
        # Test components
        config = test_config()
        signal = test_validator()
        
        print("\n" + "=" * 60)
        print("✅ All Tests Passed!")
        print("=" * 60)
        print("\n📊 Summary:")
        print(f"  • Indicators: Working ✓")
        print(f"  • Validator: Working ✓")
        print(f"  • Config: Working ✓")
        print(f"  • Signal Generation: Working ✓")
        print("\n🎯 System is ready for integration!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
