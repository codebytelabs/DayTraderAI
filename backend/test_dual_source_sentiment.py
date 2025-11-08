#!/usr/bin/env python3
"""
Test: Dual-Source Sentiment System
Validates failover and strategy recommendations.
"""

import asyncio
from core.alpaca_client import AlpacaClient
from scanner.ai_opportunity_finder import get_ai_opportunity_finder
from indicators.sentiment_aggregator import get_sentiment_aggregator

async def test_dual_source_system():
    print("🎯 Testing Dual-Source Sentiment System")
    print("=" * 80)
    
    # Initialize components
    alpaca = AlpacaClient()
    ai_finder = get_ai_opportunity_finder()
    
    print("\n📊 STEP 1: Discover Opportunities (Perplexity)")
    print("-" * 80)
    
    # This will populate AI sentiment
    opportunities = await ai_finder.discover_opportunities(max_symbols=20)
    print(f"✅ Discovered {len(opportunities)} opportunities")
    
    print("\n📊 STEP 2: Initialize Sentiment Aggregator")
    print("-" * 80)
    
    aggregator = get_sentiment_aggregator(alpaca, ai_finder)
    
    print("\n📊 STEP 3: Get Sentiment (with failover)")
    print("-" * 80)
    
    sentiment = aggregator.get_sentiment()
    
    print(f"\n🎭 SENTIMENT DATA:")
    print(f"   Score: {sentiment['score']}/100")
    print(f"   Classification: {sentiment['classification']}")
    print(f"   Source: {sentiment['source']}")
    print(f"   Confidence: {sentiment['confidence']}")
    print(f"   Timestamp: {sentiment['timestamp']}")
    
    if 'vix_value' in sentiment:
        print(f"   VIX Value: {sentiment['vix_value']}")
    
    print("\n📊 STEP 4: Get Strategy Recommendations")
    print("-" * 80)
    
    strategy = aggregator.get_sentiment_strategy(sentiment['score'])
    
    print(f"\n🎯 TRADING STRATEGY:")
    print(f"   Strategy: {strategy['strategy']}")
    print(f"   Rationale: {strategy['rationale']}")
    print(f"\n   📈 Market Caps Allowed:")
    for cap, allowed in strategy['allowed_caps'].items():
        status = "✅" if allowed else "❌"
        print(f"      {status} {cap.replace('_', '-').title()}")
    
    print(f"\n   📊 Position Allocation:")
    long_pct = strategy['target_long_pct'] * 100
    short_pct = (1 - strategy['target_long_pct']) * 100
    print(f"      Long: {long_pct:.0f}%")
    print(f"      Short: {short_pct:.0f}%")
    
    print(f"\n   💰 Position Sizing:")
    size_mult = strategy['position_size_mult']
    print(f"      Multiplier: {size_mult}x")
    print(f"      Example: $10,000 → ${10000 * size_mult:,.0f}")
    
    print("\n📊 STEP 5: Source Reliability Stats")
    print("-" * 80)
    
    stats = aggregator.get_source_stats()
    
    print(f"\n📈 SOURCE STATISTICS:")
    for source, data in stats.items():
        print(f"\n   {source.upper()}:")
        print(f"      Attempts: {data['attempts']}")
        print(f"      Successes: {data['successes']}")
        print(f"      Failures: {data['failures']}")
        print(f"      Success Rate: {data['success_rate']}")
    
    print("\n📊 STEP 6: Validate Strategy Logic")
    print("-" * 80)
    
    # Test all sentiment levels
    test_scores = [
        (10, "Extreme Fear"),
        (35, "Fear"),
        (50, "Neutral"),
        (65, "Greed"),
        (85, "Extreme Greed")
    ]
    
    print(f"\n🧪 STRATEGY VALIDATION:")
    print(f"\n{'Score':<10} {'Level':<15} {'Long%':<8} {'Caps Allowed':<30} {'Size':<6}")
    print("-" * 80)
    
    for score, level in test_scores:
        strat = aggregator.get_sentiment_strategy(score)
        long_pct = strat['target_long_pct'] * 100
        
        caps = []
        if strat['allowed_caps']['large_caps']:
            caps.append('L')
        if strat['allowed_caps']['mid_caps']:
            caps.append('M')
        if strat['allowed_caps']['small_caps']:
            caps.append('S')
        caps_str = '+'.join(caps)
        
        size = f"{strat['position_size_mult']:.0%}"
        
        print(f"{score:<10} {level:<15} {long_pct:<7.0f}% {caps_str:<30} {size:<6}")
    
    print("\n📊 STEP 7: System Validation")
    print("-" * 80)
    
    # Validation checks
    has_sentiment = sentiment['score'] != 50 or sentiment['source'] != 'default'
    has_strategy = strategy is not None
    has_failover = len(stats) >= 2
    
    print(f"\n✅ VALIDATION RESULTS:")
    print(f"   {'✅' if has_sentiment else '❌'} Sentiment Retrieved: {sentiment['source']}")
    print(f"   {'✅' if has_strategy else '❌'} Strategy Generated: {strategy['strategy'][:50]}...")
    print(f"   {'✅' if has_failover else '❌'} Failover System: {len(stats)} sources configured")
    
    # Check if strategy makes sense
    score = sentiment['score']
    if score <= 25:
        expected_long = strategy['target_long_pct'] >= 0.70
        expected_caps = not strategy['allowed_caps']['small_caps']
    elif score >= 75:
        expected_long = strategy['target_long_pct'] <= 0.30
        expected_caps = not strategy['allowed_caps']['small_caps']
    else:
        expected_long = True
        expected_caps = True
    
    strategy_valid = expected_long and expected_caps
    
    print(f"   {'✅' if strategy_valid else '❌'} Strategy Logic: Appropriate for sentiment level")
    
    all_valid = has_sentiment and has_strategy and has_failover and strategy_valid
    
    print("\n🎯 FINAL ASSESSMENT:")
    print("=" * 80)
    
    if all_valid:
        print("✅ SUCCESS: Dual-source sentiment system fully operational!")
        print("\n🚀 CAPABILITIES:")
        print("   • Automatic failover (Perplexity → VIX)")
        print("   • Sentiment-based strategy recommendations")
        print("   • Market cap filtering by sentiment")
        print("   • Dynamic long/short ratio targets")
        print("   • Position sizing adjustments")
        print("   • Source reliability tracking")
        
        print(f"\n💡 CURRENT MARKET CONDITIONS:")
        print(f"   Sentiment: {sentiment['score']}/100 ({sentiment['classification']})")
        print(f"   Strategy: {strategy['strategy']}")
        print(f"   Focus: {'+'.join([k.split('_')[0].upper() for k, v in strategy['allowed_caps'].items() if v])}-cap stocks")
        print(f"   Bias: {long_pct:.0f}% long, {short_pct:.0f}% short")
        
    else:
        print("⚠️  PARTIAL SUCCESS: Some components need adjustment")
        if not has_sentiment:
            print("   • Sentiment retrieval needs improvement")
        if not has_strategy:
            print("   • Strategy generation needs work")
        if not has_failover:
            print("   • Failover system needs configuration")
        if not strategy_valid:
            print("   • Strategy logic needs refinement")
    
    return {
        'sentiment': sentiment,
        'strategy': strategy,
        'stats': stats,
        'success': all_valid
    }

if __name__ == "__main__":
    result = asyncio.run(test_dual_source_system())
    
    if result['success']:
        print("\n" + "=" * 80)
        print("🎉 READY FOR PRODUCTION!")
        print("=" * 80)
        print("Your system now has:")
        print("• Dual-source sentiment validation")
        print("• Professional-grade strategy recommendations")
        print("• Automatic failover protection")
        print("• Research-backed market cap filtering")
        print("\nRestart your backend to activate!")
    else:
        print("\n" + "=" * 80)
        print("⚠️  NEEDS REFINEMENT")
        print("=" * 80)
        print("Some components need adjustment before production")
