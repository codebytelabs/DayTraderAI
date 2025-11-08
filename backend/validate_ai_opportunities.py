#!/usr/bin/env python3
"""
AI Opportunity Finder Validation Tool

This tool validates that the AI opportunity system is working correctly:
1. Checks if AI is finding real opportunities vs hardcoded fallbacks
2. Validates multi-cap coverage (large, mid, small)
3. Analyzes the quality and diversity of discoveries
4. Shows actual AI reasoning and catalysts
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set minimal env vars for testing
os.environ.setdefault('OPENROUTER_API_KEY', 'dummy')
os.environ.setdefault('ALPACA_API_KEY', 'dummy')
os.environ.setdefault('ALPACA_SECRET_KEY', 'dummy')
os.environ.setdefault('SUPABASE_URL', 'https://dummy.supabase.co')
os.environ.setdefault('SUPABASE_KEY', 'dummy')
os.environ.setdefault('SUPABASE_SERVICE_KEY', 'dummy')

from scanner.ai_opportunity_finder import AIOpportunityFinder


def analyze_market_caps(symbols: List[str]) -> Dict:
    """Analyze market cap distribution of discovered symbols."""
    
    # Market cap classifications (approximate)
    large_cap = {
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 
        'BRK.A', 'BRK.B', 'UNH', 'JNJ', 'JPM', 'V', 'PG', 'HD', 'MA', 
        'AVGO', 'CVX', 'LLY', 'ABBV', 'PFE', 'KO', 'PEP', 'COST', 'WMT',
        'BAC', 'XOM', 'ORCL', 'CRM', 'AMD', 'NFLX', 'ADBE', 'DIS', 'TMO',
        'SPY', 'QQQ', 'IWM', 'VTI', 'VOO'  # ETFs
    }
    
    mid_cap = {
        'PLTR', 'COIN', 'SOFI', 'RIVN', 'SNOW', 'DKNG', 'CRWD', 'ZS', 'RBLX',
        'ROKU', 'SQ', 'TWLO', 'DOCU', 'OKTA', 'DDOG', 'NET', 'FSLY', 'ESTC',
        'MDB', 'TEAM', 'WDAY', 'VEEV', 'SPLK', 'NOW', 'CZR', 'PENN', 'MGM',
        'TTD', 'TRADE', 'OPEN', 'RKT', 'AFRM', 'UPST', 'LC', 'HOOD'
    }
    
    small_cap = {
        'MARA', 'RIOT', 'AMC', 'GME', 'BBBY', 'CLOV', 'WISH', 'SPCE', 'NKLA',
        'LCID', 'BABA', 'NIO', 'XPEV', 'LI', 'PLUG', 'FCEL', 'BLNK', 'CHPT',
        'ENPH', 'SEDG', 'RUN', 'NOVA', 'SNDL', 'TLRY', 'CGC', 'ACB', 'CRON',
        'BRTX', 'SOUN', 'IONQ', 'RGTI', 'QUBT', 'AIMD', 'SMCI', 'ARM'
    }
    
    # Classify symbols
    large_found = [s for s in symbols if s in large_cap]
    mid_found = [s for s in symbols if s in mid_cap]
    small_found = [s for s in symbols if s in small_cap]
    unknown = [s for s in symbols if s not in large_cap and s not in mid_cap and s not in small_cap]
    
    return {
        'large_cap': {
            'count': len(large_found),
            'symbols': large_found,
            'percentage': len(large_found) / len(symbols) * 100 if symbols else 0
        },
        'mid_cap': {
            'count': len(mid_found),
            'symbols': mid_found,
            'percentage': len(mid_found) / len(symbols) * 100 if symbols else 0
        },
        'small_cap': {
            'count': len(small_found),
            'symbols': small_found,
            'percentage': len(small_found) / len(symbols) * 100 if symbols else 0
        },
        'unknown': {
            'count': len(unknown),
            'symbols': unknown,
            'percentage': len(unknown) / len(symbols) * 100 if symbols else 0
        },
        'total_symbols': len(symbols)
    }


def analyze_ai_quality(finder: AIOpportunityFinder) -> Dict:
    """Analyze the quality of AI discoveries."""
    
    last_discovery = finder.get_last_discovery()
    if not last_discovery:
        return {'error': 'No recent AI discovery found'}
    
    reasoning = last_discovery.get('reasoning', '')
    citations = last_discovery.get('citations', [])
    
    # Check for AI vs fallback indicators
    is_fallback = False
    fallback_indicators = [
        'fallback symbols',
        'using fallback',
        'default symbols',
        'hardcoded'
    ]
    
    for indicator in fallback_indicators:
        if indicator.lower() in reasoning.lower():
            is_fallback = True
            break
    
    # Analyze reasoning quality
    quality_indicators = {
        'has_catalysts': any(word in reasoning.lower() for word in ['catalyst', 'earnings', 'news', 'announcement']),
        'has_technical_analysis': any(word in reasoning.lower() for word in ['breakout', 'support', 'resistance', 'volume']),
        'has_price_targets': any(word in reasoning.lower() for word in ['target', '$', 'price']),
        'has_market_context': any(word in reasoning.lower() for word in ['market', 'sector', 'trend']),
        'has_citations': len(citations) > 0,
        'reasoning_length': len(reasoning)
    }
    
    return {
        'is_fallback': is_fallback,
        'quality_score': sum(quality_indicators.values()) / len(quality_indicators) * 100,
        'quality_indicators': quality_indicators,
        'citations_count': len(citations),
        'reasoning_preview': reasoning[:300] + '...' if len(reasoning) > 300 else reasoning
    }


async def validate_ai_opportunities():
    """Comprehensive validation of AI opportunity finder."""
    
    print("\n" + "=" * 80)
    print("🔍 AI OPPORTUNITY FINDER VALIDATION")
    print("=" * 80)
    print()
    
    # Initialize AI finder
    print("🚀 Initializing AI Opportunity Finder...")
    finder = AIOpportunityFinder()
    print()
    
    # Run AI discovery
    print("🤖 Running AI opportunity discovery...")
    print("   This will make a real API call to Perplexity AI...")
    print()
    
    try:
        symbols = await finder.discover_opportunities(max_symbols=30)
        
        print("✅ AI Discovery Complete!")
        print(f"   Found {len(symbols)} opportunities")
        print()
        
        # Analyze market cap distribution
        print("=" * 80)
        print("📊 MARKET CAP ANALYSIS")
        print("=" * 80)
        print()
        
        cap_analysis = analyze_market_caps(symbols)
        
        print(f"Total Symbols Discovered: {cap_analysis['total_symbols']}")
        print()
        
        for cap_type in ['large_cap', 'mid_cap', 'small_cap']:
            data = cap_analysis[cap_type]
            print(f"🏢 {cap_type.replace('_', '-').upper()}:")
            print(f"   Count: {data['count']} ({data['percentage']:.1f}%)")
            print(f"   Symbols: {', '.join(data['symbols'][:10])}")
            if len(data['symbols']) > 10:
                print(f"            ... and {len(data['symbols']) - 10} more")
            print()
        
        if cap_analysis['unknown']['count'] > 0:
            print(f"❓ UNKNOWN/OTHER:")
            print(f"   Count: {cap_analysis['unknown']['count']} ({cap_analysis['unknown']['percentage']:.1f}%)")
            print(f"   Symbols: {', '.join(cap_analysis['unknown']['symbols'])}")
            print()
        
        # Analyze AI quality
        print("=" * 80)
        print("🧠 AI QUALITY ANALYSIS")
        print("=" * 80)
        print()
        
        quality = analyze_ai_quality(finder)
        
        if 'error' in quality:
            print(f"❌ Error: {quality['error']}")
        else:
            print(f"🎯 AI vs Fallback: {'🔄 FALLBACK MODE' if quality['is_fallback'] else '🤖 REAL AI DISCOVERY'}")
            print(f"📈 Quality Score: {quality['quality_score']:.1f}/100")
            print(f"📚 Citations: {quality['citations_count']}")
            print()
            
            print("Quality Indicators:")
            for indicator, value in quality['quality_indicators'].items():
                status = "✅" if value else "❌"
                print(f"   {status} {indicator.replace('_', ' ').title()}: {value}")
            print()
            
            print("AI Reasoning Preview:")
            print("-" * 40)
            print(quality['reasoning_preview'])
            print("-" * 40)
            print()
        
        # Detailed opportunity analysis
        if hasattr(finder, 'last_opportunities_detailed') and finder.last_opportunities_detailed:
            print("=" * 80)
            print("🎯 DETAILED OPPORTUNITY BREAKDOWN")
            print("=" * 80)
            print()
            
            detailed = finder.last_opportunities_detailed
            
            # Group by tier and direction
            by_category = {}
            for opp in detailed:
                key = f"{opp['tier']}_{opp['direction']}"
                if key not in by_category:
                    by_category[key] = []
                by_category[key].append(opp)
            
            for category, opps in by_category.items():
                tier, direction = category.split('_')
                emoji = "📈" if direction == "LONG" else "📉"
                tier_name = tier.replace('_', '-').upper()
                
                print(f"{emoji} {tier_name} {direction}: {len(opps)} opportunities")
                print("-" * 60)
                
                for i, opp in enumerate(opps[:5], 1):  # Show first 5
                    symbol = opp['symbol']
                    catalyst = opp.get('catalyst', 'N/A')[:50]
                    confidence = opp.get('confidence', 'UNKNOWN')
                    
                    print(f"  {i}. {symbol:6} | {confidence:6} | {catalyst}...")
                
                if len(opps) > 5:
                    print(f"     ... and {len(opps) - 5} more")
                print()
        
        # Validation summary
        print("=" * 80)
        print("✅ VALIDATION SUMMARY")
        print("=" * 80)
        print()
        
        # Check multi-cap coverage
        has_large = cap_analysis['large_cap']['count'] > 0
        has_mid = cap_analysis['mid_cap']['count'] > 0
        has_small = cap_analysis['small_cap']['count'] > 0
        
        checks = {
            "AI Discovery Working": not quality.get('is_fallback', True),
            "Multi-Cap Coverage": has_large and has_mid and has_small,
            "Large-Cap Present": has_large,
            "Mid-Cap Present": has_mid,
            "Small-Cap Present": has_small,
            "Quality Reasoning": quality.get('quality_score', 0) > 50,
            "Has Citations": quality.get('citations_count', 0) > 0,
            "Sufficient Diversity": len(symbols) >= 15
        }
        
        all_passed = True
        for check, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {check}")
            if not passed:
                all_passed = False
        
        print()
        if all_passed:
            print("🎉 ALL VALIDATIONS PASSED!")
            print("   The AI opportunity system is working correctly!")
        else:
            print("⚠️  Some validations failed. Review the results above.")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(validate_ai_opportunities())