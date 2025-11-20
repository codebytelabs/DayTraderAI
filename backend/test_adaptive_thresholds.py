#!/usr/bin/env python3
"""
Test Adaptive Thresholds
Shows how thresholds change based on market conditions
"""

from trading.adaptive_thresholds import AdaptiveThresholds
from datetime import datetime

def test_adaptive_thresholds():
    """Test adaptive thresholds in different scenarios"""
    
    at = AdaptiveThresholds()
    
    print("=" * 80)
    print("🎯 ADAPTIVE CONFIDENCE THRESHOLDS - TEST")
    print("=" * 80)
    print()
    
    scenarios = [
        {
            'name': '🟢 IDEAL CONDITIONS',
            'regime': 'trending',
            'multiplier': 0.9,
            'sentiment': 50,
            'time': datetime(2025, 11, 12, 10, 0)  # 10 AM
        },
        {
            'name': '🟡 MODERATE CONDITIONS',
            'regime': 'transitional',
            'multiplier': 0.7,
            'sentiment': 40,
            'time': datetime(2025, 11, 12, 14, 30)  # 2:30 PM
        },
        {
            'name': '🟠 CURRENT CONDITIONS (Your System)',
            'regime': 'choppy',
            'multiplier': 0.5,
            'sentiment': 26,
            'time': datetime(2025, 11, 12, 14, 40)  # 2:40 PM midday
        },
        {
            'name': '🔴 WORST CONDITIONS',
            'regime': 'choppy',
            'multiplier': 0.4,
            'sentiment': 15,
            'time': datetime(2025, 11, 12, 12, 0)  # 12 PM
        }
    ]
    
    for scenario in scenarios:
        print(f"{scenario['name']}")
        print("-" * 80)
        print(f"  Market Regime: {scenario['regime']}")
        print(f"  Regime Multiplier: {scenario['multiplier']}x")
        print(f"  Sentiment: {scenario['sentiment']}/100")
        print(f"  Time: {scenario['time'].strftime('%I:%M %p')}")
        print()
        
        # Get thresholds
        long_threshold, short_threshold = at.get_thresholds(
            market_regime=scenario['regime'],
            regime_multiplier=scenario['multiplier'],
            sentiment_score=scenario['sentiment'],
            current_time=scenario['time']
        )
        
        # Check if should pause
        should_pause, pause_reason = at.should_pause_trading(
            market_regime=scenario['regime'],
            regime_multiplier=scenario['multiplier'],
            sentiment_score=scenario['sentiment'],
            current_time=scenario['time']
        )
        
        # Get summary
        summary = at.get_summary(
            market_regime=scenario['regime'],
            regime_multiplier=scenario['multiplier'],
            sentiment_score=scenario['sentiment'],
            current_time=scenario['time']
        )
        
        print(f"  📊 THRESHOLDS:")
        print(f"     Long:  {long_threshold*100:.0f}% (base: 60%)")
        print(f"     Short: {short_threshold*100:.0f}% (base: 65%)")
        print()
        print(f"  🎯 DIFFICULTY: {summary['trading_difficulty']}")
        print()
        
        if should_pause:
            print(f"  ⏸️  TRADING PAUSED: {pause_reason}")
        else:
            print(f"  ✅ TRADING ALLOWED")
        
        print()
        print("=" * 80)
        print()
    
    # Show comparison
    print("📈 COMPARISON")
    print("=" * 80)
    print()
    print("Condition          | Long  | Short | Status")
    print("-------------------|-------|-------|------------------")
    
    for scenario in scenarios:
        long_threshold, short_threshold = at.get_thresholds(
            market_regime=scenario['regime'],
            regime_multiplier=scenario['multiplier'],
            sentiment_score=scenario['sentiment'],
            current_time=scenario['time']
        )
        
        should_pause, _ = at.should_pause_trading(
            market_regime=scenario['regime'],
            regime_multiplier=scenario['multiplier'],
            sentiment_score=scenario['sentiment'],
            current_time=scenario['time']
        )
        
        status = "PAUSED" if should_pause else "Active"
        name = scenario['name'].replace('🟢 ', '').replace('🟡 ', '').replace('🟠 ', '').replace('🔴 ', '')
        
        print(f"{name:18} | {long_threshold*100:4.0f}% | {short_threshold*100:4.0f}% | {status}")
    
    print()
    print("=" * 80)
    print()
    print("💡 KEY TAKEAWAY:")
    print()
    print("In your current conditions (choppy + midday + fear):")
    print("  - System requires 80% confidence for longs (was 60%)")
    print("  - System requires 85% confidence for shorts (was 65%)")
    print("  - Most signals will be rejected (protecting capital)")
    print("  - System may auto-pause if conditions worsen")
    print()
    print("This is GOOD - it prevents losses in poor market conditions!")
    print()


if __name__ == "__main__":
    test_adaptive_thresholds()
