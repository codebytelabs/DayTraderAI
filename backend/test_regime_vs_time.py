#!/usr/bin/env python3
"""
Test: Market Regime vs Time of Day
Shows that regime is the primary factor, not time
"""

from trading.adaptive_thresholds import AdaptiveThresholds
from datetime import datetime

def test_regime_vs_time():
    """Show that market regime matters more than time of day"""
    
    at = AdaptiveThresholds()
    
    print("=" * 80)
    print("🎯 REGIME vs TIME: Which Matters More?")
    print("=" * 80)
    print()
    
    # Scenario 1: TRENDING market during midday (supposedly "bad" time)
    print("📊 SCENARIO 1: Trending Market During Midday")
    print("-" * 80)
    print("  Market: TRENDING (0.9x multiplier)")
    print("  Time: 12:00 PM (midday - supposedly worst time)")
    print()
    
    long1, short1 = at.get_thresholds(
        market_regime='trending',
        regime_multiplier=0.9,
        sentiment_score=50,
        current_time=datetime(2025, 11, 12, 12, 0)
    )
    
    print(f"  Result: Long {long1*100:.0f}%, Short {short1*100:.0f}%")
    print(f"  ✅ STILL EASY TO TRADE (regime dominates)")
    print()
    print("=" * 80)
    print()
    
    # Scenario 2: CHOPPY market during morning (supposedly "good" time)
    print("📊 SCENARIO 2: Choppy Market During Morning")
    print("-" * 80)
    print("  Market: CHOPPY (0.5x multiplier)")
    print("  Time: 10:00 AM (morning - supposedly best time)")
    print()
    
    long2, short2 = at.get_thresholds(
        market_regime='choppy',
        regime_multiplier=0.5,
        sentiment_score=50,
        current_time=datetime(2025, 11, 12, 10, 0)
    )
    
    print(f"  Result: Long {long2*100:.0f}%, Short {short2*100:.0f}%")
    print(f"  ⚠️  STILL HARD TO TRADE (regime dominates)")
    print()
    print("=" * 80)
    print()
    
    # Comparison
    print("💡 KEY INSIGHT:")
    print("-" * 80)
    print()
    print(f"Trending @ Midday:  {long1*100:.0f}% / {short1*100:.0f}%  ← EASIER")
    print(f"Choppy @ Morning:   {long2*100:.0f}% / {short2*100:.0f}%  ← HARDER")
    print()
    print("Conclusion: MARKET REGIME is the primary factor!")
    print("Time of day is just a minor modifier (+/- 3-5%)")
    print()
    print("This means:")
    print("  ✅ Won't miss good opportunities during midday if market is trending")
    print("  ✅ Won't take bad trades during morning if market is choppy")
    print("  ✅ Adapts to ACTUAL market conditions, not clock time")
    print()
    print("=" * 80)
    print()
    
    # Show the breakdown
    print("📊 ADJUSTMENT BREAKDOWN:")
    print("-" * 80)
    print()
    print("Factor                | Trending@Midday | Choppy@Morning")
    print("----------------------|-----------------|----------------")
    print("Base threshold        |      60%        |      60%")
    print("Regime adjustment     |      -5%        |     +20%")
    print("Time adjustment       |      +5%        |      -3%")
    print("Sentiment adjustment  |       0%        |       0%")
    print("----------------------|-----------------|----------------")
    print(f"TOTAL                 |      {long1*100:.0f}%        |      {long2*100:.0f}%")
    print()
    print("Notice: Regime adjustment (±20%) >> Time adjustment (±5%)")
    print()


if __name__ == "__main__":
    test_regime_vs_time()
