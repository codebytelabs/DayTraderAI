#!/usr/bin/env python3
"""
Quick diagnostic to check regime manager status
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading.regime_manager import RegimeManager, MarketRegime
from indicators.fear_greed_scraper import FearGreedScraper

async def main():
    print("=" * 80)
    print("🌍 REGIME MANAGER DIAGNOSTIC")
    print("=" * 80)
    
    # Test Fear & Greed Scraper directly
    print("\n1. Testing Fear & Greed Scraper...")
    scraper = FearGreedScraper()
    result = scraper.get_fear_greed_index()
    print(f"   Raw result: {result}")
    if result and ('value' in result or 'score' in result):
        index_value = int(result.get('value') or result.get('score'))
        print(f"   ✅ Index Value: {index_value}/100")
    else:
        print(f"   ❌ Failed to get index")
        return
    
    # Test RegimeManager
    print("\n2. Testing RegimeManager...")
    manager = RegimeManager()
    print(f"   Initial regime: {manager.get_current_regime()}")
    print(f"   Initial index: {manager.get_current_index_value()}")
    
    # Update regime
    print("\n3. Updating regime...")
    regime = await manager.update_regime()
    print(f"   ✅ Updated regime: {regime.value}")
    print(f"   ✅ Index value: {manager.get_current_index_value()}")
    
    # Get parameters
    print("\n4. Getting regime parameters...")
    params = manager.get_params()
    print(f"   Profit Target: {params['profit_target_r']}R")
    print(f"   Partial 1: {params['partial_profit_1_r']}R")
    print(f"   Partial 2: {params['partial_profit_2_r']}R")
    print(f"   Trailing Stop: {params['trailing_stop_r']}R")
    print(f"   Position Size Mult: {params['position_size_mult']}x")
    print(f"   Description: {params['description']}")
    
    # Test classification
    print("\n5. Testing classification logic...")
    test_values = [15, 16, 20, 21, 40, 41, 60, 61, 80, 81, 100]
    for val in test_values:
        classified = manager._classify_regime(val)
        print(f"   Index {val:3d} → {classified.value}")
    
    print("\n" + "=" * 80)
    print("✅ DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
