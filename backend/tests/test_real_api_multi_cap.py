"""
Real API Test for Multi-Cap Opportunity Discovery

This test makes an actual call to Perplexity API to verify the system works end-to-end.
"""

import asyncio
import os
import sys
from pathlib import Path

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


async def test_real_api():
    """Test with real Perplexity API call."""
    
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "REAL API TEST" + " " * 40 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    print("🚀 Initializing AI Opportunity Finder...")
    finder = AIOpportunityFinder()
    
    print("📡 Making REAL API call to Perplexity...")
    print("   This will discover actual opportunities in the market RIGHT NOW")
    print()
    
    try:
        # Make real API call
        print("🔍 Calling discover_opportunities...")
        symbols = await finder.discover_opportunities(max_symbols=60)
        print(f"🎯 Got {len(symbols)} symbols back")
        
        print()
        print("=" * 80)
        print("✅ API CALL SUCCESSFUL")
        print("=" * 80)
        print()
        
        print(f"Total opportunities discovered: {len(symbols)}")
        print()
        
        # Check if we have detailed metadata
        if hasattr(finder, 'last_opportunities_detailed') and finder.last_opportunities_detailed:
            detailed = finder.last_opportunities_detailed
            
            print(f"Detailed opportunities with metadata: {len(detailed)}")
            print()
            
            # Group by tier and direction
            by_tier_direction = {}
            for opp in detailed:
                key = f"{opp['tier']}_{opp['direction']}"
                if key not in by_tier_direction:
                    by_tier_direction[key] = []
                by_tier_direction[key].append(opp)
            
            # Display summary
            print("=" * 80)
            print("OPPORTUNITIES BY TIER AND DIRECTION")
            print("=" * 80)
            print()
            
            tier_order = [
                ('large_cap', 'LONG'),
                ('large_cap', 'SHORT'),
                ('mid_cap', 'LONG'),
                ('mid_cap', 'SHORT'),
                ('small_cap', 'LONG'),
                ('small_cap', 'SHORT')
            ]
            
            for tier, direction in tier_order:
                key = f"{tier}_{direction}"
                if key in by_tier_direction:
                    opps = by_tier_direction[key]
                    
                    emoji = "📈" if direction == "LONG" else "📉"
                    tier_name = tier.replace('_', '-').upper()
                    
                    print(f"{emoji} {tier_name} {direction}: {len(opps)} opportunities")
                    print("-" * 80)
                    
                    # Show first 5
                    for i, opp in enumerate(opps[:5], 1):
                        symbol = opp['symbol']
                        price = opp.get('price', 0)
                        target = opp.get('target', 0)
                        volume = opp.get('volume_mult', 0)
                        catalyst = opp.get('catalyst', 'N/A')[:50]
                        
                        if price and target:
                            potential = ((target - price) / price * 100) if direction == 'LONG' else ((price - target) / price * 100)
                            print(f"  {i}. {symbol:6} ${price:7.2f} → ${target:7.2f} (+{potential:5.1f}%) | Vol {volume}x")
                        else:
                            print(f"  {i}. {symbol:6} | Vol {volume}x")
                        
                        if catalyst != 'N/A':
                            print(f"     {catalyst}...")
                    
                    if len(opps) > 5:
                        print(f"     ... and {len(opps) - 5} more")
                    
                    print()
            
            # Statistics
            print("=" * 80)
            print("STATISTICS")
            print("=" * 80)
            print()
            
            total_long = sum(1 for opp in detailed if opp['direction'] == 'LONG')
            total_short = sum(1 for opp in detailed if opp['direction'] == 'SHORT')
            
            large_cap = sum(1 for opp in detailed if opp['tier'] == 'large_cap')
            mid_cap = sum(1 for opp in detailed if opp['tier'] == 'mid_cap')
            small_cap = sum(1 for opp in detailed if opp['tier'] == 'small_cap')
            
            print(f"Direction Split:")
            print(f"  LONG:  {total_long:2} ({total_long/len(detailed)*100:.1f}%)")
            print(f"  SHORT: {total_short:2} ({total_short/len(detailed)*100:.1f}%)")
            print()
            
            print(f"Market Cap Split:")
            print(f"  Large-cap: {large_cap:2} ({large_cap/len(detailed)*100:.1f}%)")
            print(f"  Mid-cap:   {mid_cap:2} ({mid_cap/len(detailed)*100:.1f}%)")
            print(f"  Small-cap: {small_cap:2} ({small_cap/len(detailed)*100:.1f}%)")
            print()
            
            # Average volume
            avg_volume = sum(opp.get('volume_mult', 0) for opp in detailed) / len(detailed)
            print(f"Average Volume Multiplier: {avg_volume:.1f}x")
            print()
            
            # Potential returns
            long_opps = [opp for opp in detailed if opp['direction'] == 'LONG' and opp.get('price') and opp.get('target')]
            short_opps = [opp for opp in detailed if opp['direction'] == 'SHORT' and opp.get('price') and opp.get('target')]
            
            if long_opps:
                avg_long_potential = sum((opp['target'] - opp['price']) / opp['price'] * 100 for opp in long_opps) / len(long_opps)
                print(f"Average LONG Potential: +{avg_long_potential:.1f}%")
            
            if short_opps:
                avg_short_potential = sum((opp['price'] - opp['target']) / opp['price'] * 100 for opp in short_opps) / len(short_opps)
                print(f"Average SHORT Potential: +{avg_short_potential:.1f}%")
            
            print()
            
            # Validation checks
            print("=" * 80)
            print("VALIDATION CHECKS")
            print("=" * 80)
            print()
            
            checks = {
                "Got opportunities": len(detailed) > 0,
                "Multiple tiers": len(set(opp['tier'] for opp in detailed)) > 1,
                "Both directions": len(set(opp['direction'] for opp in detailed)) == 2,
                "Has metadata": all('tier' in opp and 'direction' in opp for opp in detailed),
                "More than old system": len(detailed) > 15,
                "Large-cap present": large_cap > 0,
                "Mid-cap present": mid_cap > 0,
                "Small-cap present": small_cap > 0
            }
            
            all_passed = True
            for check, result in checks.items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  {status}: {check}")
                if not result:
                    all_passed = False
            
            print()
            print("=" * 80)
            if all_passed:
                print("🎉 ALL CHECKS PASSED! Multi-cap system working perfectly!")
            else:
                print("⚠️  Some checks failed. Review results above.")
            print("=" * 80)
            print()
            
        else:
            # Fallback: just show symbols
            print("Symbols discovered (fallback mode):")
            for i, symbol in enumerate(symbols[:20], 1):
                print(f"  {i:2}. {symbol}")
            
            if len(symbols) > 20:
                print(f"  ... and {len(symbols) - 20} more")
            print()
            
            print("⚠️  Detailed metadata not available. Check extraction logic.")
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ API CALL FAILED")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        print("Possible causes:")
        print("  - Perplexity API key not set or invalid")
        print("  - Network connection issue")
        print("  - API rate limit reached")
        print()
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_real_api())
