#!/usr/bin/env python3
"""
Test the Dynamic Universe Manager.

Verifies:
1. Universe has 150+ candidate stocks
2. Growth-focused scoring works
3. Mid-caps can outrank mega-caps
4. Fallback universe works
"""

import asyncio
import sys
sys.path.insert(0, '.')

from scanner.dynamic_universe import DynamicUniverseManager, get_dynamic_universe


def test_candidates():
    """Test that we have enough candidates."""
    manager = DynamicUniverseManager()
    candidates = manager.get_all_candidates()
    
    print(f"✅ Total candidates: {len(candidates)}")
    assert len(candidates) >= 150, f"Need 150+ candidates, got {len(candidates)}"
    
    # Count by category
    categories = {}
    for symbol, cat in candidates:
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📊 Candidates by category:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    
    return True


def test_growth_scoring():
    """Test that growth stocks score higher than stable mega-caps."""
    manager = DynamicUniverseManager()
    
    # Growth scores by category
    print("\n📈 Growth scores by category:")
    for cat, score in sorted(manager.category_growth_scores.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {score}")
    
    # Verify growth stocks score higher than mega-caps
    assert manager.category_growth_scores['high_beta_momentum'] > manager.category_growth_scores['mega_cap_stable']
    assert manager.category_growth_scores['high_growth_tech'] > manager.category_growth_scores['mega_cap_stable']
    
    print("\n✅ Growth stocks correctly score higher than stable mega-caps")
    return True


def test_fallback_universe():
    """Test fallback universe."""
    manager = DynamicUniverseManager()
    fallback = manager._get_fallback_universe()
    
    print(f"\n📦 Fallback universe: {len(fallback)} stocks")
    assert len(fallback) >= 100, f"Fallback should have 100+ stocks, got {len(fallback)}"
    
    # Check that growth stocks are prioritized (appear early)
    growth_stocks = ['PLTR', 'SNOW', 'DDOG', 'CRWD', 'NVDA', 'AMD']
    found_early = sum(1 for s in growth_stocks if s in fallback[:30])
    print(f"  Growth stocks in top 30: {found_early}/{len(growth_stocks)}")
    
    print(f"  Sample: {fallback[:20]}")
    return True


async def test_refresh():
    """Test universe refresh (without API)."""
    manager = DynamicUniverseManager()
    
    # This will use fallback since no API clients
    symbols = await manager.refresh_universe(force=True)
    
    print(f"\n🔄 Refreshed universe: {len(symbols)} stocks")
    assert len(symbols) >= 100, f"Should have 100+ stocks, got {len(symbols)}"
    
    return True


def main():
    print("=" * 60)
    print("DYNAMIC UNIVERSE MANAGER TEST")
    print("=" * 60)
    
    tests = [
        ("Candidates", test_candidates),
        ("Growth Scoring", test_growth_scoring),
        ("Fallback Universe", test_fallback_universe),
    ]
    
    passed = 0
    for name, test_fn in tests:
        try:
            if test_fn():
                passed += 1
        except Exception as e:
            print(f"❌ {name} FAILED: {e}")
    
    # Async test
    try:
        asyncio.run(test_refresh())
        passed += 1
    except Exception as e:
        print(f"❌ Refresh FAILED: {e}")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/4 tests passed")
    print("=" * 60)
    
    return passed == 4


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
