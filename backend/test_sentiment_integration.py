#!/usr/bin/env python3
"""
Integration Test: Market Sentiment + Opportunity Scoring
Shows the real impact of sentiment on trading decisions.
"""

from core.alpaca_client import AlpacaClient
from indicators.market_sentiment import get_sentiment_analyzer
from scanner.opportunity_scorer import OpportunityScorer
from data.market_data import MarketDataManager
from data.features import FeatureEngine

def test_sentiment_integration():
    print("🎯 SENTIMENT INTEGRATION TEST")
    print("=" * 80)
    
    # Initialize components
    from core.supabase_client import SupabaseClient
    
    alpaca = AlpacaClient()
    supabase = SupabaseClient()
    sentiment_analyzer = get_sentiment_analyzer(alpaca)
    market_data = MarketDataManager(alpaca, supabase)
    feature_engine = FeatureEngine()
    
    # Get current market sentiment
    print("\n📊 STEP 1: Get Market Sentiment")
    print("-" * 80)
    sentiment = sentiment_analyzer.get_sentiment_score()
    
    print(f"Overall Sentiment: {sentiment['overall_score']}/100 ({sentiment['sentiment']})")
    print(f"VIX Score: {sentiment['vix_score']}/100")
    print(f"Breadth Score: {sentiment['breadth_score']}/100")
    print(f"Sector Score: {sentiment['sector_score']}/100")
    print(f"Volume Score: {sentiment['volume_score']}/100")
    print(f"\n💡 Recommendation: {sentiment['recommendation']}")
    
    # Test stocks
    test_symbols = ['AAPL', 'NVDA', 'TSLA', 'SPY', 'QQQ']
    
    print(f"\n📈 STEP 2: Score Opportunities WITHOUT Sentiment")
    print("-" * 80)
    
    scorer_no_sentiment = OpportunityScorer()  # No sentiment
    scores_without = {}
    
    for symbol in test_symbols:
        try:
            features = feature_engine.get_features(symbol)
            if features:
                score = scorer_no_sentiment.calculate_total_score(features)
                scores_without[symbol] = score
                print(f"{symbol:5s}: {score['total_score']:5.1f}/110 ({score['grade']})")
        except Exception as e:
            print(f"{symbol:5s}: Error - {e}")
    
    print(f"\n📈 STEP 3: Score Opportunities WITH Sentiment")
    print("-" * 80)
    
    scorer_with_sentiment = OpportunityScorer(sentiment_analyzer=sentiment_analyzer)
    scores_with = {}
    
    for symbol in test_symbols:
        try:
            features = feature_engine.get_features(symbol)
            if features:
                score = scorer_with_sentiment.calculate_total_score(features, direction='long')
                scores_with[symbol] = score
                print(f"{symbol:5s}: {score['total_score']:5.1f}/120 ({score['grade']}) "
                      f"[Sentiment: {score.get('sentiment_score', 0):.1f}/10]")
        except Exception as e:
            print(f"{symbol:5s}: Error - {e}")
    
    # Compare impact
    print(f"\n📊 STEP 4: Impact Analysis")
    print("=" * 80)
    
    print(f"\n{'Symbol':<8} {'Old Score':<12} {'New Score':<12} {'Change':<10} {'Impact'}")
    print("-" * 80)
    
    total_impact = 0
    for symbol in test_symbols:
        if symbol in scores_without and symbol in scores_with:
            old_score = scores_without[symbol]['total_score']
            new_score = scores_with[symbol]['total_score']
            sentiment_pts = scores_with[symbol].get('sentiment_score', 0)
            
            # Normalize for comparison (old was /110, new is /120)
            old_normalized = (old_score / 110) * 100
            new_normalized = (new_score / 120) * 100
            change = new_normalized - old_normalized
            total_impact += abs(change)
            
            impact_icon = "📈" if change > 0 else "📉" if change < 0 else "➖"
            print(f"{symbol:<8} {old_score:5.1f}/110   {new_score:5.1f}/120   "
                  f"{change:+5.1f}%    {impact_icon} Sentiment: {sentiment_pts:.1f}/10")
    
    avg_impact = total_impact / len(test_symbols) if test_symbols else 0
    
    print(f"\n💡 INSIGHTS")
    print("=" * 80)
    
    # Sentiment-based recommendations
    sentiment_score = sentiment['overall_score']
    
    if sentiment_score >= 70:
        print("⚠️  HIGH SENTIMENT (Greed)")
        print("   • Stocks score HIGHER for longs (easier to find opportunities)")
        print("   • But market may be overextended")
        print("   • Consider: Taking profits, reducing sizes, looking for shorts")
        print(f"   • Average impact: {avg_impact:.1f}% boost to long scores")
    elif sentiment_score >= 55:
        print("✅ BULLISH SENTIMENT")
        print("   • Good environment for long positions")
        print("   • Sentiment adds points to bullish setups")
        print("   • Ride the momentum with proper stops")
        print(f"   • Average impact: {avg_impact:.1f}% adjustment to scores")
    elif sentiment_score >= 45:
        print("➖ NEUTRAL SENTIMENT")
        print("   • Mixed signals - trade both directions")
        print("   • Sentiment has minimal impact on scores")
        print("   • Focus on technical setups")
        print(f"   • Average impact: {avg_impact:.1f}% (minimal)")
    elif sentiment_score >= 30:
        print("⚠️  BEARISH SENTIMENT")
        print("   • Difficult environment for longs")
        print("   • Sentiment REDUCES points from long setups")
        print("   • Consider shorts or wait for better entries")
        print(f"   • Average impact: -{avg_impact:.1f}% penalty to long scores")
    else:
        print("🎯 EXTREME FEAR (Opportunity)")
        print("   • Longs score LOWER (harder to find)")
        print("   • But extreme fear often marks bottoms")
        print("   • Look for oversold bounce plays")
        print(f"   • Average impact: -{avg_impact:.1f}% penalty, but opportunity exists")
    
    # Position sizing recommendation
    print(f"\n📏 POSITION SIZING IMPACT")
    print("=" * 80)
    
    if sentiment_score > 70 or sentiment_score < 30:
        size_mult = 0.7
        print(f"⚠️  Reduce position sizes to 70% of normal")
        print(f"   Reason: Extreme sentiment ({sentiment_score}/100) increases risk")
        print(f"   Example: $10,000 position → $7,000 position")
    elif 45 <= sentiment_score <= 55:
        size_mult = 0.8
        print(f"⚠️  Reduce position sizes to 80% of normal")
        print(f"   Reason: Neutral/choppy conditions")
        print(f"   Example: $10,000 position → $8,000 position")
    else:
        size_mult = 1.0
        print(f"✅ Use normal position sizes")
        print(f"   Reason: Favorable sentiment environment")
        print(f"   Example: $10,000 position → $10,000 position")
    
    # Real-world example
    print(f"\n💰 REAL-WORLD EXAMPLE")
    print("=" * 80)
    print(f"Scenario: You have $13,000 day trading buying power")
    print(f"")
    print(f"WITHOUT Sentiment:")
    print(f"  • Find top 5 stocks by technical score")
    print(f"  • Place $10,000 positions (10% of equity)")
    print(f"  • No adjustment for market conditions")
    print(f"")
    print(f"WITH Sentiment:")
    print(f"  • Find top 5 stocks by technical + sentiment score")
    print(f"  • Adjust position size: $10,000 × {size_mult} = ${10000 * size_mult:,.0f}")
    print(f"  • Better alignment with market conditions")
    print(f"  • Avoid buying tops / selling bottoms")
    
    # Expected outcomes
    print(f"\n🎯 EXPECTED OUTCOMES")
    print("=" * 80)
    print(f"1. Better Timing:")
    print(f"   • Avoid aggressive longs in extreme greed")
    print(f"   • Identify contrarian opportunities in extreme fear")
    print(f"")
    print(f"2. Improved Risk Management:")
    print(f"   • Smaller positions in extreme conditions")
    print(f"   • Larger positions in favorable conditions")
    print(f"")
    print(f"3. Higher Win Rate:")
    print(f"   • Trade with the sentiment tide, not against it")
    print(f"   • Better opportunity selection")
    print(f"")
    print(f"4. Reduced Drawdowns:")
    print(f"   • Less exposure during market extremes")
    print(f"   • More defensive in bearish sentiment")
    
    print("\n" + "=" * 80)
    print("✅ Integration test complete!")
    
    return {
        'sentiment': sentiment,
        'scores_without': scores_without,
        'scores_with': scores_with,
        'avg_impact': avg_impact,
        'size_multiplier': size_mult
    }

if __name__ == "__main__":
    results = test_sentiment_integration()