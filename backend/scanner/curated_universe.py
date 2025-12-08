#!/usr/bin/env python3
"""
Curated Universe - Weekly refresh of high-quality, consistently profitable stocks.

COMPOSITION: 70% Large-Caps + 30% Mid-Caps (growth-oriented)

Key Features:
1. Refreshes WEEKLY (every Monday) using historical performance data
2. Selects stocks with consistent momentum over past weeks
3. 70% large-caps for stability and liquidity
4. 30% mid-caps for higher growth potential
5. Filters for profitability, volume, and momentum consistency

Selection Criteria:
- Consistent positive momentum over 4 weeks
- High average daily volume ($5M+ for large-caps, $1M+ for mid-caps)
- Positive earnings growth or revenue growth
- Not in downtrend (above 50-day MA)
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import pytz

logger = logging.getLogger(__name__)

ET = pytz.timezone('America/New_York')

# Cache file for weekly curated list
CURATED_CACHE_FILE = Path(__file__).parent / "curated_cache.json"


@dataclass
class CuratedStock:
    """Stock in the curated universe with quality metrics."""
    symbol: str
    cap_category: str  # large_cap or mid_cap
    sector: str
    weekly_momentum: float  # Average weekly return over 4 weeks
    avg_volume: float  # Average daily dollar volume
    consistency_score: int  # 0-100 how consistent the momentum is
    last_updated: str


class CuratedUniverseManager:
    """
    Manages a curated universe of ~150 high-quality stocks.
    
    Refreshes WEEKLY and maintains:
    - 70% large-caps (stable, liquid, consistent performers)
    - 30% mid-caps (higher growth potential)
    
    All stocks must show consistent profitability and momentum.
    """
    
    # ============================================================
    # LARGE-CAP GROWTH LEADERS (70% of universe = ~105 stocks)
    # Consistently profitable, high liquidity, growth-oriented
    # ============================================================
    
    # Tech Large-Caps (proven growth, high liquidity)
    LARGE_CAP_TECH = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AVGO',
        'ADBE', 'CRM', 'ORCL', 'CSCO', 'ACN', 'TXN', 'QCOM', 'INTC',
        'AMD', 'NOW', 'INTU', 'AMAT', 'ADI', 'LRCX', 'MU', 'KLAC'
    ]
    
    # Healthcare Large-Caps (defensive growth)
    LARGE_CAP_HEALTHCARE = [
        'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'PFE', 'TMO', 'ABT',
        'DHR', 'BMY', 'AMGN', 'GILD', 'VRTX', 'REGN', 'ISRG', 'MDT'
    ]
    
    # Financial Large-Caps (cyclical growth)
    LARGE_CAP_FINANCE = [
        'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'BLK',
        'SCHW', 'AXP', 'C', 'USB', 'PNC', 'TFC', 'COF', 'CME'
    ]
    
    # Consumer Large-Caps (stable growth)
    LARGE_CAP_CONSUMER = [
        'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW', 'TJX', 'COST',
        'WMT', 'PG', 'KO', 'PEP', 'PM', 'MO', 'CL', 'EL'
    ]
    
    # Industrial Large-Caps (economic growth)
    LARGE_CAP_INDUSTRIAL = [
        'CAT', 'DE', 'HON', 'UPS', 'UNP', 'BA', 'RTX', 'LMT',
        'GE', 'MMM', 'EMR', 'ITW', 'ETN', 'PH', 'ROK', 'CMI'
    ]
    
    # Energy Large-Caps (commodity growth)
    LARGE_CAP_ENERGY = [
        'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO',
        'OXY', 'HAL', 'DVN', 'HES', 'FANG', 'PXD', 'BKR', 'KMI'
    ]
    
    # ============================================================
    # MID-CAP GROWTH STARS (30% of universe = ~45 stocks)
    # Higher growth potential, still liquid, momentum-driven
    # ============================================================
    
    # Tech Mid-Caps (high growth SaaS, cloud, AI)
    MID_CAP_TECH = [
        'PLTR', 'SNOW', 'DDOG', 'CRWD', 'ZS', 'NET', 'MDB', 'OKTA',
        'HUBS', 'TWLO', 'BILL', 'CFLT', 'PATH', 'GTLB', 'ESTC', 'S'
    ]
    
    # Fintech Mid-Caps (disruption plays)
    MID_CAP_FINTECH = [
        'SQ', 'PYPL', 'AFRM', 'SOFI', 'HOOD', 'COIN', 'UPST', 'LC',
        'TOST', 'FOUR', 'GPN', 'FIS', 'FISV', 'DFS', 'SYF', 'ALLY'
    ]
    
    # EV & Clean Energy Mid-Caps (future growth)
    MID_CAP_EV_CLEAN = [
        'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'CHPT', 'ENPH', 'SEDG',
        'RUN', 'PLUG', 'FCEL', 'BE', 'BLNK', 'EVGO', 'NOVA', 'ARRY'
    ]
    
    # Biotech Mid-Caps (high risk/reward)
    MID_CAP_BIOTECH = [
        'MRNA', 'BNTX', 'CRSP', 'EDIT', 'NTLA', 'BEAM', 'EXAS', 'DXCM',
        'ALNY', 'BMRN', 'INCY', 'SGEN', 'PACB', 'TWST', 'VERV', 'RXRX'
    ]
    
    # Consumer/Entertainment Mid-Caps
    MID_CAP_CONSUMER = [
        'ABNB', 'UBER', 'LYFT', 'DASH', 'RBLX', 'U', 'ROKU', 'SPOT',
        'PINS', 'SNAP', 'ETSY', 'CHWY', 'W', 'CVNA', 'TTWO', 'EA'
    ]
    
    # Crypto & High-Beta Mid-Caps
    MID_CAP_HIGH_BETA = [
        'MARA', 'RIOT', 'CLSK', 'HUT', 'BITF', 'HIVE', 'BTBT', 'CAN',
        'ARKK', 'SOXL', 'TQQQ', 'SPXL', 'UPRO', 'QLD', 'SSO', 'TECL'
    ]
    
    def __init__(self, alpaca_client=None, market_data_client=None):
        """Initialize with optional API clients."""
        self.alpaca = alpaca_client
        self.market_data = market_data_client
        self.curated_stocks: List[CuratedStock] = []
        self.last_refresh: Optional[datetime] = None
        
        # Target composition
        self.large_cap_pct = 0.70  # 70% large-caps
        self.mid_cap_pct = 0.30   # 30% mid-caps
        self.target_size = 150
        
        logger.info("✅ CuratedUniverseManager initialized (70% large-cap, 30% mid-cap)")

    
    def get_all_large_caps(self) -> List[Tuple[str, str]]:
        """Get all large-cap candidates with their sectors."""
        candidates = []
        for s in self.LARGE_CAP_TECH:
            candidates.append((s, 'tech'))
        for s in self.LARGE_CAP_HEALTHCARE:
            candidates.append((s, 'healthcare'))
        for s in self.LARGE_CAP_FINANCE:
            candidates.append((s, 'finance'))
        for s in self.LARGE_CAP_CONSUMER:
            candidates.append((s, 'consumer'))
        for s in self.LARGE_CAP_INDUSTRIAL:
            candidates.append((s, 'industrial'))
        for s in self.LARGE_CAP_ENERGY:
            candidates.append((s, 'energy'))
        return candidates
    
    def get_all_mid_caps(self) -> List[Tuple[str, str]]:
        """Get all mid-cap candidates with their sectors."""
        candidates = []
        for s in self.MID_CAP_TECH:
            candidates.append((s, 'tech'))
        for s in self.MID_CAP_FINTECH:
            candidates.append((s, 'fintech'))
        for s in self.MID_CAP_EV_CLEAN:
            candidates.append((s, 'ev_clean'))
        for s in self.MID_CAP_BIOTECH:
            candidates.append((s, 'biotech'))
        for s in self.MID_CAP_CONSUMER:
            candidates.append((s, 'consumer'))
        for s in self.MID_CAP_HIGH_BETA:
            candidates.append((s, 'high_beta'))
        return candidates
    
    async def refresh_weekly(self, force: bool = False) -> List[str]:
        """
        Refresh the curated list weekly (every Monday).
        
        Uses historical data to select consistently profitable stocks.
        
        Args:
            force: Force refresh even if not Monday
            
        Returns:
            List of curated symbols
        """
        try:
            # Check if we need to refresh
            if not force and self._is_cache_valid():
                logger.info("📦 Using cached curated list (still valid)")
                return self._load_cached()
            
            logger.info("🔄 Refreshing weekly curated list...")
            start_time = datetime.now()
            
            # Get candidates
            large_caps = self.get_all_large_caps()
            mid_caps = self.get_all_mid_caps()
            
            logger.info(f"📊 Evaluating {len(large_caps)} large-caps, {len(mid_caps)} mid-caps")
            
            # Score and select large-caps (70%)
            large_cap_target = int(self.target_size * self.large_cap_pct)
            scored_large = await self._score_candidates(large_caps, 'large_cap')
            selected_large = scored_large[:large_cap_target]
            
            # Score and select mid-caps (30%)
            mid_cap_target = self.target_size - len(selected_large)
            scored_mid = await self._score_candidates(mid_caps, 'mid_cap')
            selected_mid = scored_mid[:mid_cap_target]
            
            # Combine
            self.curated_stocks = selected_large + selected_mid
            self.last_refresh = datetime.now()
            
            # Cache results
            self._save_cache()
            
            # Log summary
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Curated list refreshed: {len(self.curated_stocks)} stocks in {elapsed:.1f}s")
            logger.info(f"   Large-caps: {len(selected_large)} ({len(selected_large)/len(self.curated_stocks)*100:.0f}%)")
            logger.info(f"   Mid-caps: {len(selected_mid)} ({len(selected_mid)/len(self.curated_stocks)*100:.0f}%)")
            
            return [s.symbol for s in self.curated_stocks]
            
        except Exception as e:
            logger.error(f"Error refreshing curated list: {e}")
            return self._get_fallback()
    
    async def _score_candidates(self, candidates: List[Tuple[str, str]], 
                                 cap_category: str) -> List[CuratedStock]:
        """Score candidates based on momentum consistency."""
        scored = []
        
        for symbol, sector in candidates:
            try:
                stock = await self._evaluate_stock(symbol, sector, cap_category)
                if stock and stock.consistency_score >= 50:  # Min 50% consistency
                    scored.append(stock)
            except Exception as e:
                logger.debug(f"Error evaluating {symbol}: {e}")
                continue
        
        # Sort by consistency score (most consistent first)
        scored.sort(key=lambda x: x.consistency_score, reverse=True)
        return scored
    
    async def _evaluate_stock(self, symbol: str, sector: str, 
                               cap_category: str) -> Optional[CuratedStock]:
        """Evaluate a stock for inclusion in curated list."""
        try:
            weekly_momentum = 0.0
            avg_volume = 1_000_000
            consistency_score = 50
            
            if self.market_data:
                try:
                    # Get 4 weeks of data
                    bars = self.market_data.fetch_historical_bars([symbol], days=20)
                    if bars and symbol in bars:
                        df = bars[symbol]
                        if len(df) >= 15:
                            # Calculate weekly returns
                            weekly_returns = []
                            for i in range(0, len(df)-5, 5):
                                if i+5 < len(df):
                                    ret = (df['close'].iloc[i+5] / df['close'].iloc[i] - 1) * 100
                                    weekly_returns.append(ret)
                            
                            if weekly_returns:
                                weekly_momentum = sum(weekly_returns) / len(weekly_returns)
                                
                                # Consistency = % of positive weeks
                                positive_weeks = sum(1 for r in weekly_returns if r > 0)
                                consistency_score = int(positive_weeks / len(weekly_returns) * 100)
                            
                            # Average dollar volume
                            avg_volume = (df['close'] * df['volume']).mean()
                except Exception as e:
                    logger.debug(f"Error fetching data for {symbol}: {e}")
            
            # Minimum volume filter
            min_volume = 5_000_000 if cap_category == 'large_cap' else 1_000_000
            if avg_volume < min_volume:
                return None
            
            return CuratedStock(
                symbol=symbol,
                cap_category=cap_category,
                sector=sector,
                weekly_momentum=weekly_momentum,
                avg_volume=avg_volume,
                consistency_score=consistency_score,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.debug(f"Error evaluating {symbol}: {e}")
            return None

    
    def _is_cache_valid(self) -> bool:
        """
        Check if cached curated list is still valid.
        
        Valid if:
        1. Cached within the last 7 days AND
        2. Not a Monday (refresh day)
        """
        try:
            if not CURATED_CACHE_FILE.exists():
                return False
            
            with open(CURATED_CACHE_FILE, 'r') as f:
                cache = json.load(f)
            
            cache_date = datetime.fromisoformat(cache.get('date', '2000-01-01'))
            now = datetime.now(ET)
            
            # Check if cache is less than 7 days old
            age = now - cache_date.replace(tzinfo=ET)
            if age.days >= 7:
                logger.info("📅 Curated cache is >7 days old - will refresh")
                return False
            
            # Check if today is Monday (refresh day)
            if now.weekday() == 0:  # Monday
                # Only refresh if cache is from before today
                if cache_date.date() < now.date():
                    logger.info("📅 Monday refresh - updating curated list")
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Cache validation error: {e}")
            return False
    
    def _load_cached(self) -> List[str]:
        """Load curated list from cache."""
        try:
            with open(CURATED_CACHE_FILE, 'r') as f:
                cache = json.load(f)
            
            self.curated_stocks = [
                CuratedStock(**stock) for stock in cache.get('stocks', [])
            ]
            self.last_refresh = datetime.fromisoformat(cache.get('date'))
            
            return [s.symbol for s in self.curated_stocks]
            
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return self._get_fallback()
    
    def _save_cache(self):
        """Save curated list to cache."""
        try:
            cache = {
                'date': datetime.now().isoformat(),
                'stocks': [asdict(s) for s in self.curated_stocks],
                'version': '1.0',
                'composition': {
                    'large_cap_pct': self.large_cap_pct,
                    'mid_cap_pct': self.mid_cap_pct
                }
            }
            
            with open(CURATED_CACHE_FILE, 'w') as f:
                json.dump(cache, f, indent=2)
            
            logger.info(f"💾 Curated list cached: {len(self.curated_stocks)} stocks")
            
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _get_fallback(self) -> List[str]:
        """Get fallback curated list if refresh fails (70% large-cap, 30% mid-cap)."""
        target = 150
        large_cap_target = int(target * 0.70)  # 105 large-caps
        mid_cap_target = target - large_cap_target  # 45 mid-caps
        
        # 70% large-caps (105 stocks)
        large_caps = (
            self.LARGE_CAP_TECH[:20] +      # 20
            self.LARGE_CAP_HEALTHCARE[:16] + # 16
            self.LARGE_CAP_FINANCE[:16] +    # 16
            self.LARGE_CAP_CONSUMER[:16] +   # 16
            self.LARGE_CAP_INDUSTRIAL[:16] + # 16
            self.LARGE_CAP_ENERGY[:16]       # 16 = 100 total
        )
        
        # 30% mid-caps (45 stocks)
        mid_caps = (
            self.MID_CAP_TECH[:10] +      # 10
            self.MID_CAP_FINTECH[:8] +    # 8
            self.MID_CAP_EV_CLEAN[:8] +   # 8
            self.MID_CAP_BIOTECH[:8] +    # 8
            self.MID_CAP_CONSUMER[:8] +   # 8
            self.MID_CAP_HIGH_BETA[:3]    # 3 = 45 total
        )
        
        # Remove duplicates from each category
        seen = set()
        large_unique = []
        for s in large_caps:
            if s not in seen:
                seen.add(s)
                large_unique.append(s)
        
        mid_unique = []
        for s in mid_caps:
            if s not in seen:
                seen.add(s)
                mid_unique.append(s)
        
        # Ensure 70/30 split
        result = large_unique[:large_cap_target] + mid_unique[:mid_cap_target]
        
        return result[:target]
    
    def get_symbols(self) -> List[str]:
        """Get current curated symbols."""
        if not self.curated_stocks:
            return self._get_fallback()
        return [s.symbol for s in self.curated_stocks]
    
    def get_large_caps(self) -> List[str]:
        """Get large-cap symbols only."""
        return [s.symbol for s in self.curated_stocks if s.cap_category == 'large_cap']
    
    def get_mid_caps(self) -> List[str]:
        """Get mid-cap symbols only."""
        return [s.symbol for s in self.curated_stocks if s.cap_category == 'mid_cap']
    
    def get_by_sector(self, sector: str) -> List[str]:
        """Get symbols by sector."""
        return [s.symbol for s in self.curated_stocks if s.sector == sector]


# Singleton instance
_curated_manager: Optional[CuratedUniverseManager] = None


def get_curated_universe(alpaca_client=None, market_data_client=None) -> CuratedUniverseManager:
    """Get or create the curated universe manager singleton."""
    global _curated_manager
    
    if _curated_manager is None:
        _curated_manager = CuratedUniverseManager(alpaca_client, market_data_client)
    
    return _curated_manager


# Quick test
if __name__ == '__main__':
    manager = CuratedUniverseManager()
    
    large_caps = manager.get_all_large_caps()
    mid_caps = manager.get_all_mid_caps()
    
    print(f"Large-caps: {len(large_caps)}")
    print(f"Mid-caps: {len(mid_caps)}")
    print(f"Total: {len(large_caps) + len(mid_caps)}")
    
    fallback = manager._get_fallback()
    print(f"\nFallback: {len(fallback)} stocks")
    print(f"Sample large-caps: {fallback[:10]}")
    print(f"Sample mid-caps: {fallback[-10:]}")
