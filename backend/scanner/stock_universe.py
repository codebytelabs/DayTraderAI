"""Stock Universe - Define the stocks we scan for opportunities.

This module maintains the universe of stocks to scan, organized by category.
"""

from typing import List, Dict, Set


class StockUniverse:
    """Manage the universe of stocks to scan."""
    
    # Major indices
    INDICES = ['SPY', 'QQQ', 'DIA', 'IWM']
    
    # Mega cap tech (FAANG+)
    MEGA_CAP_TECH = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
        'NVDA', 'TSLA', 'NFLX', 'AMD', 'INTC'
    ]
    
    # High-volume tech
    HIGH_VOLUME_TECH = [
        'AVGO', 'ORCL', 'CRM', 'ADBE', 'CSCO',
        'QCOM', 'TXN', 'AMAT', 'MU', 'LRCX',
        'KLAC', 'SNPS', 'CDNS', 'MRVL', 'ASML'
    ]
    
    # Semiconductors
    SEMICONDUCTORS = [
        'NVDA', 'AMD', 'INTC', 'AVGO', 'QCOM',
        'TXN', 'AMAT', 'MU', 'LRCX', 'KLAC',
        'MRVL', 'NXPI', 'ADI', 'ON', 'MPWR'
    ]
    
    # Cloud & Software
    CLOUD_SOFTWARE = [
        'CRM', 'ADBE', 'NOW', 'SNOW', 'DDOG',
        'CRWD', 'ZS', 'PANW', 'WDAY', 'TEAM',
        'PLTR', 'NET', 'OKTA', 'DOCN', 'MDB'
    ]
    
    # E-commerce & Consumer
    ECOMMERCE_CONSUMER = [
        'AMZN', 'SHOP', 'EBAY', 'ETSY', 'W',
        'CHWY', 'DASH', 'UBER', 'LYFT', 'ABNB'
    ]
    
    # Finance & Fintech
    FINANCE = [
        'JPM', 'BAC', 'WFC', 'GS', 'MS',
        'C', 'BLK', 'SCHW', 'V', 'MA',
        'PYPL', 'SQ', 'COIN', 'HOOD', 'SOFI'
    ]
    
    # Healthcare & Biotech
    HEALTHCARE = [
        'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK',
        'PFE', 'TMO', 'ABT', 'DHR', 'BMY',
        'AMGN', 'GILD', 'VRTX', 'REGN', 'BIIB'
    ]
    
    # Energy
    ENERGY = [
        'XOM', 'CVX', 'COP', 'SLB', 'EOG',
        'MPC', 'PSX', 'VLO', 'OXY', 'HAL'
    ]
    
    # High-momentum movers
    MOMENTUM_STOCKS = [
        'TSLA', 'NVDA', 'AMD', 'PLTR', 'COIN',
        'RIVN', 'LCID', 'NIO', 'SOFI', 'HOOD',
        'RBLX', 'U', 'DKNG', 'ARKK', 'SOXL'
    ]
    
    @classmethod
    def get_full_universe(cls) -> List[str]:
        """Get complete stock universe (all categories)."""
        all_stocks = set()
        
        # Add all categories
        all_stocks.update(cls.INDICES)
        all_stocks.update(cls.MEGA_CAP_TECH)
        all_stocks.update(cls.HIGH_VOLUME_TECH)
        all_stocks.update(cls.SEMICONDUCTORS)
        all_stocks.update(cls.CLOUD_SOFTWARE)
        all_stocks.update(cls.ECOMMERCE_CONSUMER)
        all_stocks.update(cls.FINANCE)
        all_stocks.update(cls.HEALTHCARE)
        all_stocks.update(cls.ENERGY)
        all_stocks.update(cls.MOMENTUM_STOCKS)
        
        return sorted(list(all_stocks))
    
    @classmethod
    def get_high_priority(cls) -> List[str]:
        """Get high-priority stocks (most liquid, best for day trading)."""
        priority = set()
        
        priority.update(cls.INDICES)
        priority.update(cls.MEGA_CAP_TECH)
        priority.update(cls.MOMENTUM_STOCKS[:10])  # Top 10 momentum
        
        return sorted(list(priority))
    
    @classmethod
    def get_by_sector(cls, sector: str) -> List[str]:
        """Get stocks by sector."""
        sector_map = {
            'tech': cls.MEGA_CAP_TECH + cls.HIGH_VOLUME_TECH,
            'semiconductors': cls.SEMICONDUCTORS,
            'cloud': cls.CLOUD_SOFTWARE,
            'ecommerce': cls.ECOMMERCE_CONSUMER,
            'finance': cls.FINANCE,
            'healthcare': cls.HEALTHCARE,
            'energy': cls.ENERGY,
            'momentum': cls.MOMENTUM_STOCKS,
            'indices': cls.INDICES
        }
        
        return sector_map.get(sector.lower(), [])
    
    @classmethod
    def get_stats(cls) -> Dict[str, int]:
        """Get universe statistics."""
        return {
            'total_stocks': len(cls.get_full_universe()),
            'high_priority': len(cls.get_high_priority()),
            'indices': len(cls.INDICES),
            'mega_cap_tech': len(cls.MEGA_CAP_TECH),
            'semiconductors': len(cls.SEMICONDUCTORS),
            'cloud_software': len(cls.CLOUD_SOFTWARE),
            'finance': len(cls.FINANCE),
            'healthcare': len(cls.HEALTHCARE),
            'energy': len(cls.ENERGY),
            'momentum': len(cls.MOMENTUM_STOCKS)
        }


# Quick access
FULL_UNIVERSE = StockUniverse.get_full_universe()
HIGH_PRIORITY = StockUniverse.get_high_priority()

if __name__ == '__main__':
    print("Stock Universe Statistics:")
    print("=" * 50)
    stats = StockUniverse.get_stats()
    for key, value in stats.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    print(f"\nFull Universe ({len(FULL_UNIVERSE)} stocks):")
    print(", ".join(FULL_UNIVERSE[:20]) + "...")
    
    print(f"\nHigh Priority ({len(HIGH_PRIORITY)} stocks):")
    print(", ".join(HIGH_PRIORITY))
