"""
Test Multi-Cap Opportunity Discovery System

This script tests the new multi-tier Perplexity query system that discovers
opportunities across large-cap, mid-cap, and small-cap segments with both
LONG and SHORT directions.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from scanner.ai_opportunity_finder import AIOpportunityFinder
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def test_multi_cap_discovery():
    """Test the multi-cap discovery system."""
    
    print("=" * 80)
    print("🚀 MULTI-CAP OPPORTUNITY DISCOVERY TEST")
    print("=" * 80)
    print()
    
    # Initialize finder
    finder = AIOpportunityFinder()
    
    print("📡 Querying Perplexity for opportunities across all market caps...")
    print("   - Large-cap (>$10B): 15 opportunities")
    print("   - Mid-cap ($2B-$10B): 12 opportunities")
    print("   - Small-cap ($300M-$2B): 10 opportunities")
    print()
    
    # Discover opportunities
    symbols = await finder.discover_opportunities(max_symbols=50)
    
    print()
    print("=" * 80)
    print("📊 DISCOVERY RESULTS")
    print("=" * 80)
    print()
    
    if not symbols:
        print("❌ No opportunities found")
        return
    
    print(f"✅ Total opportunities discovered: {len(symbols)}")
    print()
    
    # Check if we have detailed metadata
    if hasattr(finder, 'last_opportunities_detailed') and finder.last_opportunities_detailed:
        detailed = finder.last_opportunities_detailed
        
        # Group by tier and direction
        by_tier = {}
        for opp in detailed:
            tier = opp['tier']
            direction = opp['direction']
            key = f"{tier}_{direction}"
            
            if key not in by_tier:
                by_tier[key] = []
            by_tier[key].append(opp)
        
        # Display by tier
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
            if key in by_tier:
                opps = by_tier[key]
                
                emoji = "📈" if direction == "LONG" else "📉"
                tier_name = tier.replace('_', '-').upper()
                
                print(f"{emoji} {tier_name} {direction} ({len(opps)} opportunities)")
                print("-" * 80)
                
                for i, opp in enumerate(opps[:5], 1):  # Show first 5
                    symbol = opp['symbol']
                    price = opp['price']
                    target = opp['target']
                    volume = opp['volume_mult']
                    catalyst = opp['catalyst'][:50] + "..." if len(opp['catalyst']) > 50 else opp['catalyst']
                    
                    potential = ((target - price) / price * 100) if direction == 'LONG' else ((price - target) / price * 100)
                    
                    print(f"  {i}. {symbol:6} ${price:7.2f} → ${target:7.2f} (+{potential:5.1f}%) | Vol {volume}x")
                    print(f"     Catalyst: {catalyst}")
                
                if len(opps) > 5:
                    print(f"     ... and {len(opps) - 5} more")
                
                print()
        
        # Summary statistics
        print("=" * 80)
        print("📈 SUMMARY STATISTICS")
        print("=" * 80)
        print()
        
        total_long = sum(1 for opp in detailed if opp['direction'] == 'LONG')
        total_short = sum(1 for opp in detailed if opp['direction'] == 'SHORT')
        
        large_cap = sum(1 for opp in detailed if opp['tier'] == 'large_cap')
        mid_cap = sum(1 for opp in detailed if opp['tier'] == 'mid_cap')
        small_cap = sum(1 for opp in detailed if opp['tier'] == 'small_cap')
        
        avg_volume = sum(opp['volume_mult'] for opp in detailed) / len(detailed)
        
        print(f"Direction Split:")
        print(f"  LONG:  {total_long:2} opportunities ({total_long/len(detailed)*100:.1f}%)")
        print(f"  SHORT: {total_short:2} opportunities ({total_short/len(detailed)*100:.1f}%)")
        print()
        
        print(f"Market Cap Split:")
        print(f"  Large-cap: {large_cap:2} opportunities ({large_cap/len(detailed)*100:.1f}%)")
        print(f"  Mid-cap:   {mid_cap:2} opportunities ({mid_cap/len(detailed)*100:.1f}%)")
        print(f"  Small-cap: {small_cap:2} opportunities ({small_cap/len(detailed)*100:.1f}%)")
        print()
        
        print(f"Average Volume Multiplier: {avg_volume:.1f}x")
        print()
        
        # Calculate potential returns
        long_opps = [opp for opp in detailed if opp['direction'] == 'LONG']
        short_opps = [opp for opp in detailed if opp['direction'] == 'SHORT']
        
        if long_opps:
            avg_long_potential = sum((opp['target'] - opp['price']) / opp['price'] * 100 for opp in long_opps) / len(long_opps)
            print(f"Average LONG Potential: +{avg_long_potential:.1f}%")
        
        if short_opps:
            avg_short_potential = sum((opp['price'] - opp['target']) / opp['price'] * 100 for opp in short_opps) / len(short_opps)
            print(f"Average SHORT Potential: +{avg_short_potential:.1f}%")
        
        print()
        
    else:
        # Fallback: just show symbols
        print("Symbols discovered:")
        for i, symbol in enumerate(symbols[:20], 1):
            print(f"  {i:2}. {symbol}")
        
        if len(symbols) > 20:
            print(f"  ... and {len(symbols) - 20} more")
        print()
    
    print("=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Review the opportunities above")
    print("  2. System will score and rank these opportunities")
    print("  3. Portfolio will be constructed with proper allocation")
    print("  4. Trades will be executed with bracket orders")
    print()


if __name__ == '__main__':
    asyncio.run(test_multi_cap_discovery())
