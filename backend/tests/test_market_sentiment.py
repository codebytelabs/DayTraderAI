#!/usr/bin/env python3
"""
Test Market Sentiment Analyzer - Validate sentiment scoring and recommendations.
"""

from core.alpaca_client import AlpacaClient
from indicators.market_sentiment import MarketSentimentAnalyzer
import json

def test_sentiment_analyzer():
    print("🎯 Testing Market Sentiment Analyzer")
    print("=" * 70)
    
    # Initialize
    alpaca = AlpacaClient()
    analyzer = MarketSentimentAnalyzer(alpaca)
    
    # Get sentiment analysis
    print("\n📊 Fetching Market Sentiment...")
    print("-" * 70)
    
    sentiment = analyzer.get_sentiment_score()
    
    # Display overall sentiment
    print(f"\n🎭 OVERALL MARKET SENTIMENT")
    print("=" * 70)
    print(f"Score: {sentiment['overall_score']}/100")
    print(f"Classification: {sentiment['sentiment'].upper().replace('_', ' ')}")
    print(f"Recommendation: {sentiment['recommendation']}")
    
    # Display component scores
    print(f"\n📈 COMPONENT SCORES")
    print("=" * 70)
    print(f"VIX (Fear Index):     {sentiment['vix_score']:5.1f}/100")
    print(f"Market Breadth:       {sentiment['breadth_score']:5.1f}/100")
    print(f"Sector Rotation:      {sentiment['sector_score']:5.1f}/100")
    print(f"Volume Sentiment:     {sentiment['volume_score']:5.1f}/100")
    
    # Display detailed components
    print(f"\n🔍 DETAILED ANALYSIS")
    print("=" * 70)
    
    # VIX Details
    if 'vix' in sentiment['components']:
        vix_data = sentiment['components']['vix']
        print(f"\n📉 VIX (Fear Index):")
        print(f"  Current: {vix_data.get('current', 'N/A')}")
        print(f"  5-Day Avg: {vix_data.get('average_5d', 'N/A')}")
        print(f"  Trend: {vix_data.get('trend', 'N/A').upper()}")
        
        # Interpret VIX
        current_vix = vix_data.get('current', 20)
        if current_vix < 15:
            vix_interp = "Very Low Fear (Complacent)"
        elif current_vix < 20:
            vix_interp = "Low Fear (Normal)"
        elif current_vix < 25:
            vix_interp = "Moderate Fear"
        elif current_vix < 30:
            vix_interp = "High Fear"
        else:
            vix_interp = "Extreme Fear (Panic)"
        print(f"  Interpretation: {vix_interp}")
    
    # Breadth Details
    if 'breadth' in sentiment['components']:
        breadth_data = sentiment['components']['breadth']
        print(f"\n📊 Market Breadth:")
        print(f"  Advancing: {breadth_data.get('advancing', 'N/A')}")
        print(f"  Declining: {breadth_data.get('declining', 'N/A')}")
        print(f"  Advance %: {breadth_data.get('advance_pct', 'N/A')}%")
        print(f"  Breadth: {breadth_data.get('breadth', 'N/A').upper()}")
    
    # Sector Details
    if 'sectors' in sentiment['components']:
        sector_data = sentiment['components']['sectors']
        print(f"\n🏭 Sector Rotation:")
        print(f"  Growth Performance: {sector_data.get('growth_performance', 'N/A')}%")
        print(f"  Defensive Performance: {sector_data.get('defensive_performance', 'N/A')}%")
        print(f"  Leading: {sector_data.get('rotation', 'N/A').upper()}")
        
        rotation = sector_data.get('rotation', 'unknown')
        if rotation == 'growth':
            rotation_interp = "Risk-On (Bullish)"
        elif rotation == 'defensive':
            rotation_interp = "Risk-Off (Bearish)"
        else:
            rotation_interp = "Mixed"
        print(f"  Interpretation: {rotation_interp}")
    
    # Volume Details
    if 'volume' in sentiment['components']:
        volume_data = sentiment['components']['volume']
        print(f"\n📈 Volume Analysis:")
        print(f"  Up Volume: {volume_data.get('up_volume_pct', 'N/A')}%")
        latest_vol = volume_data.get('latest_volume', 0)
        avg_vol = volume_data.get('average_volume', 0)
        print(f"  Latest Volume: {latest_vol:,}" if isinstance(latest_vol, int) else f"  Latest Volume: {latest_vol}")
        print(f"  Average Volume: {avg_vol:,}" if isinstance(avg_vol, int) else f"  Average Volume: {avg_vol}")
        print(f"  Trend: {volume_data.get('trend', 'N/A').upper()}")
    
    # Trading implications
    print(f"\n💡 TRADING IMPLICATIONS")
    print("=" * 70)
    
    score = sentiment['overall_score']
    if score >= 80:
        print("⚠️  EXTREME GREED - Market may be overextended")
        print("   • Consider taking profits on long positions")
        print("   • Reduce position sizes")
        print("   • Look for short opportunities on weakness")
        print("   • Be cautious with new longs")
    elif score >= 60:
        print("✅ GREED - Bullish environment")
        print("   • Good for long positions")
        print("   • Ride trends with trailing stops")
        print("   • Avoid fighting the momentum")
        print("   • Watch for reversal signals")
    elif score >= 40:
        print("➖ NEUTRAL - Mixed signals")
        print("   • Trade both directions")
        print("   • Focus on technical setups")
        print("   • Use tighter stops")
        print("   • Be selective with entries")
    elif score >= 20:
        print("⚠️  FEAR - Bearish environment")
        print("   • Consider short positions")
        print("   • Wait for better long entries")
        print("   • Reduce exposure")
        print("   • Watch for capitulation")
    else:
        print("🎯 EXTREME FEAR - Potential opportunity")
        print("   • Look for oversold bounces")
        print("   • Extreme fear often marks bottoms")
        print("   • Start building long positions carefully")
        print("   • Use wide stops for volatility")
    
    # Position sizing recommendation
    print(f"\n📏 POSITION SIZING RECOMMENDATION")
    print("=" * 70)
    
    if score >= 70 or score <= 30:
        size_mult = 0.7
        print(f"Reduce position sizes to 70% of normal")
        print(f"Reason: Extreme sentiment increases risk")
    elif score >= 55 and score <= 45:
        size_mult = 0.8
        print(f"Reduce position sizes to 80% of normal")
        print(f"Reason: Neutral/choppy conditions")
    else:
        size_mult = 1.0
        print(f"Use normal position sizes")
        print(f"Reason: Favorable sentiment environment")
    
    # Test caching
    print(f"\n🔄 Testing Cache...")
    print("-" * 70)
    import time
    start = time.time()
    sentiment2 = analyzer.get_sentiment_score()
    elapsed = time.time() - start
    print(f"Second call took {elapsed*1000:.1f}ms (should be <1ms if cached)")
    print(f"Scores match: {sentiment['overall_score'] == sentiment2['overall_score']}")
    
    # Save to file for review
    print(f"\n💾 Saving detailed results...")
    with open('sentiment_test_results.json', 'w') as f:
        json.dump(sentiment, f, indent=2)
    print(f"Results saved to: sentiment_test_results.json")
    
    print("\n" + "=" * 70)
    print("✅ Sentiment analysis test complete!")
    
    return sentiment

if __name__ == "__main__":
    test_sentiment_analyzer()