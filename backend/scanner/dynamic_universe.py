#!/usr/bin/env python3
"""
Dynamic Universe Manager - Daily refresh of 150 high-quality trading opportunities.

TIMING: Refreshes AFTER market opens (9:35-9:45 AM ET) to capture real movers.

Key Features:
1. Refreshes daily AFTER market open (to see actual movers)
2. Uses Alpaca API to discover top gainers, losers, most active
3. Prioritizes GROWTH POTENTIAL over market cap
4. Includes mid-caps and high-beta stocks for better opportunities
5. Filters for liquidity (min $1M daily volume)
6. Scores stocks by momentum potential, not just size

Scoring Philosophy:
- Higher growth potential = higher score
- Mid-caps with momentum > stable mega-caps
- Recent price action matters more than market cap
- Volume surge indicates institutional interest
"""

import asyncio
import json
import os
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import pytz

logger = logging.getLogger(__name__)

# Timezone for market hours
ET = pytz.timezone('America/New_York')

# Market timing constants
MARKET_OPEN = time(9, 30)   # 9:30 AM ET
FIRST_REFRESH = time(9, 35)  # 9:35 AM ET - quick refresh to catch early movers
MARKET_CLOSE = time(16, 0)  # 4:00 PM ET

# Cache file for daily universe
UNIVERSE_CACHE_FILE = Path(__file__).parent / "universe_cache.json"


@dataclass
class UniverseStock:
    """Stock in the dynamic universe with quality metrics."""
    symbol: str
    category: str  # mega_cap, large_cap, mid_cap, growth, momentum
    avg_volume: float  # Average daily dollar volume
    volatility: float  # Historical volatility (higher = more opportunity)
    growth_score: int  # 0-100 growth potential score
    momentum_rank: int  # Rank by recent momentum
    liquidity_score: int  # 0-100 liquidity score


class DynamicUniverseManager:
    """
    Manages a dynamic universe of 150 high-quality stocks.
    
    Refreshes daily and prioritizes:
    1. Growth potential (mid-caps often score higher)
    2. Momentum characteristics
    3. Liquidity (tradeable with good fills)
    4. Volatility (opportunity for day trading)
    """
    
    # EXPANDED UNIVERSE - 200+ candidates to select top 150 from
    # Organized by GROWTH POTENTIAL, not just market cap
    
    # Tier 1: High-Growth Tech (often mid-cap, high momentum)
    HIGH_GROWTH_TECH = [
        'PLTR', 'SNOW', 'DDOG', 'CRWD', 'ZS', 'NET', 'MDB', 'OKTA',
        'DOCN', 'CFLT', 'S', 'PATH', 'GTLB', 'ESTC', 'SUMO', 'NEWR',
        'BILL', 'HUBS', 'TWLO', 'SHOP', 'SQ', 'AFRM', 'UPST', 'SOFI',
        'HOOD', 'COIN', 'MARA', 'RIOT', 'CLSK', 'HUT'
    ]
    
    # Tier 2: Semiconductor Growth (high beta, momentum plays)
    SEMICONDUCTOR_GROWTH = [
        'NVDA', 'AMD', 'AVGO', 'MRVL', 'ON', 'MPWR', 'SWKS', 'QRVO',
        'WOLF', 'CRUS', 'SLAB', 'LSCC', 'RMBS', 'SITM', 'ACLS', 'FORM',
        'SMTC', 'POWI', 'DIOD', 'ALGM'
    ]
    
    # Tier 3: AI & Cloud Leaders (growth + momentum)
    AI_CLOUD = [
        'MSFT', 'GOOGL', 'AMZN', 'META', 'CRM', 'NOW', 'WDAY', 'TEAM',
        'ADBE', 'ORCL', 'IBM', 'PANW', 'FTNT', 'CYBR', 'TENB', 'QLYS',
        'VRNS', 'SAIL', 'AI', 'BBAI', 'SOUN', 'GFAI'
    ]
    
    # Tier 4: EV & Clean Energy (high volatility, momentum)
    EV_CLEANTECH = [
        'TSLA', 'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'FSR', 'GOEV',
        'CHPT', 'BLNK', 'EVGO', 'PLUG', 'FCEL', 'BE', 'ENPH', 'SEDG',
        'RUN', 'NOVA', 'ARRY', 'MAXN'
    ]
    
    # Tier 5: Biotech & Healthcare Growth
    BIOTECH_GROWTH = [
        'MRNA', 'BNTX', 'REGN', 'VRTX', 'SGEN', 'ALNY', 'BMRN', 'INCY',
        'EXAS', 'DXCM', 'ISRG', 'ILMN', 'PACB', 'TWST', 'CRSP', 'EDIT',
        'NTLA', 'BEAM', 'VERV', 'RXRX'
    ]
    
    # Tier 6: Consumer Growth & E-commerce
    CONSUMER_GROWTH = [
        'ABNB', 'UBER', 'LYFT', 'DASH', 'RBLX', 'U', 'TTWO', 'EA',
        'NFLX', 'DIS', 'ROKU', 'PARA', 'WBD', 'SPOT', 'PINS', 'SNAP',
        'ETSY', 'CHWY', 'W', 'CVNA'
    ]
    
    # Tier 7: Fintech & Payments
    FINTECH = [
        'V', 'MA', 'PYPL', 'GPN', 'FIS', 'FISV', 'AXP', 'DFS',
        'SYF', 'ALLY', 'LC', 'OPEN', 'UWMC', 'RKT', 'TREE', 'LDI',
        'LPRO', 'ESMT', 'TOST', 'FOUR'
    ]
    
    # Tier 8: Industrial & Aerospace Growth
    INDUSTRIAL_GROWTH = [
        'BA', 'LMT', 'RTX', 'NOC', 'GD', 'TDG', 'HWM', 'AXON',
        'TXT', 'HII', 'KTOS', 'RKLB', 'SPCE', 'ASTS', 'RDW', 'LUNR',
        'JOBY', 'ACHR', 'LILM', 'EVTL'
    ]

    
    # Tier 9: Mega-Cap Anchors (stable, liquid, but lower growth score)
    MEGA_CAP_STABLE = [
        'AAPL', 'GOOG', 'BRK.B', 'JPM', 'JNJ', 'UNH', 'PG', 'HD',
        'KO', 'PEP', 'MRK', 'ABBV', 'LLY', 'TMO', 'ABT', 'DHR',
        'COST', 'WMT', 'MCD', 'NKE'
    ]
    
    # Tier 10: High-Beta Momentum (volatile, opportunity-rich)
    HIGH_BETA_MOMENTUM = [
        'GME', 'AMC', 'BBBY', 'SPCE', 'CLOV', 'WISH', 'SKLZ', 'SOFI',
        'OPEN', 'UPST', 'AFRM', 'HOOD', 'RIVN', 'LCID', 'MARA', 'RIOT',
        'COIN', 'ARKK', 'SOXL', 'TQQQ'
    ]
    
    # Market ETFs (always include for reference)
    MARKET_ETFS = ['SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO']
    
    # Sector ETFs (for sector rotation plays)
    SECTOR_ETFS = [
        'XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLY', 'XLP', 'XLU', 'XLB', 'XLRE',
        'SMH', 'IBB', 'XBI', 'ARKK', 'ARKG', 'ARKF', 'ARKW', 'ARKQ'
    ]
    
    def __init__(self, alpaca_client=None, market_data_client=None):
        """Initialize with optional API clients for real-time data."""
        self.alpaca = alpaca_client
        self.market_data = market_data_client
        self.universe: List[UniverseStock] = []
        self.last_refresh: Optional[datetime] = None
        self.target_size = 150
        
        # Growth potential weights (higher = more growth-focused)
        self.category_growth_scores = {
            # API-discovered stocks get HIGH scores (they're moving TODAY)
            'api_top_gainer': 98,      # Top gainers = highest momentum
            'api_most_active': 92,     # Most active = institutional interest
            'api_top_loser': 75,       # Losers = potential bounce (lower score)
            # Weekly curated list (70/30 large/mid cap split)
            'curated_large_cap': 80,   # Consistent large-caps (stable growth)
            'curated_mid_cap': 88,     # Consistent mid-caps (higher growth)
            # Additional growth categories
            'high_growth_tech': 90,
            'semiconductor_growth': 85,
            'ai_cloud': 80,
            'ev_cleantech': 88,
            'biotech_growth': 82,
            'consumer_growth': 75,
            'fintech': 78,
            'industrial_growth': 70,
            'mega_cap_stable': 50,     # Lower score - stable but less upside
            'high_beta_momentum': 95,  # Highest curated - most opportunity
            'market_etfs': 60,
            'sector_etfs': 65
        }
        
        logger.info("✅ DynamicUniverseManager initialized")
    
    def get_all_candidates(self) -> List[Tuple[str, str]]:
        """
        Get all candidate symbols with their categories.
        
        Now uses CURATED UNIVERSE (weekly refresh, 70/30 large/mid cap split)
        as the base, plus additional growth categories.
        """
        candidates = []
        
        # FIRST: Try to get from weekly curated list (70% large-cap, 30% mid-cap)
        try:
            from scanner.curated_universe import get_curated_universe
            curated = get_curated_universe(self.alpaca, self.market_data)
            curated_symbols = curated.get_symbols()
            
            if len(curated_symbols) >= 100:
                logger.info(f"📋 Using curated universe: {len(curated_symbols)} stocks (70/30 split)")
                for symbol in curated_symbols:
                    # Determine category based on curated stock data
                    if symbol in curated.get_large_caps():
                        candidates.append((symbol, 'curated_large_cap'))
                    else:
                        candidates.append((symbol, 'curated_mid_cap'))
        except Exception as e:
            logger.debug(f"Curated universe not available: {e}")
        
        # THEN: Add additional growth categories (for diversity)
        for symbol in self.HIGH_GROWTH_TECH:
            candidates.append((symbol, 'high_growth_tech'))
        for symbol in self.SEMICONDUCTOR_GROWTH:
            candidates.append((symbol, 'semiconductor_growth'))
        for symbol in self.AI_CLOUD:
            candidates.append((symbol, 'ai_cloud'))
        for symbol in self.EV_CLEANTECH:
            candidates.append((symbol, 'ev_cleantech'))
        for symbol in self.BIOTECH_GROWTH:
            candidates.append((symbol, 'biotech_growth'))
        for symbol in self.CONSUMER_GROWTH:
            candidates.append((symbol, 'consumer_growth'))
        for symbol in self.FINTECH:
            candidates.append((symbol, 'fintech'))
        for symbol in self.INDUSTRIAL_GROWTH:
            candidates.append((symbol, 'industrial_growth'))
        for symbol in self.MEGA_CAP_STABLE:
            candidates.append((symbol, 'mega_cap_stable'))
        for symbol in self.HIGH_BETA_MOMENTUM:
            candidates.append((symbol, 'high_beta_momentum'))
        for symbol in self.MARKET_ETFS:
            candidates.append((symbol, 'market_etfs'))
        for symbol in self.SECTOR_ETFS:
            candidates.append((symbol, 'sector_etfs'))
        
        # Remove duplicates, keeping first occurrence (curated has priority)
        seen = set()
        unique = []
        for symbol, category in candidates:
            if symbol not in seen:
                seen.add(symbol)
                unique.append((symbol, category))
        
        return unique

    
    async def refresh_universe(self, force: bool = False) -> List[str]:
        """
        Refresh the universe daily with top 150 stocks.
        
        NOW USES ALPACA API to discover new opportunities dynamically!
        
        Selection criteria (in order of importance):
        1. API-discovered movers (top gainers, losers, most active)
        2. Growth potential score (category-based)
        3. Recent momentum (price action from API)
        4. Volume/liquidity (tradeable)
        5. Volatility (opportunity)
        
        Args:
            force: Force refresh even if already done today
            
        Returns:
            List of 150 symbols for today's trading
        """
        try:
            # Check if we need to refresh
            if not force and self._is_cache_valid():
                logger.info("📦 Using cached universe (still valid)")
                return self._load_cached_universe()
            
            logger.info("🔄 Refreshing dynamic universe from market data...")
            start_time = datetime.now()
            
            # STEP 1: Discover new stocks from Alpaca API (top movers)
            # Only works AFTER market opens - before that, use curated list
            if self._should_use_premarket_fallback():
                logger.info("⏰ Pre-market/weekend - using curated list (API movers not available)")
                api_discovered = []
            else:
                api_discovered = await self._discover_from_api()
                logger.info(f"🌐 API discovered {len(api_discovered)} new candidates")
            
            # STEP 2: Get base candidates from curated list
            base_candidates = self.get_all_candidates()
            logger.info(f"📋 Base candidates: {len(base_candidates)}")
            
            # STEP 3: Merge API-discovered with base (API gets priority)
            all_candidates = api_discovered + [
                (s, c) for s, c in base_candidates 
                if s not in [x[0] for x in api_discovered]
            ]
            logger.info(f"📊 Total candidates to evaluate: {len(all_candidates)}")
            
            # Score each candidate using real market data
            scored_stocks = []
            
            for symbol, category in all_candidates:
                try:
                    stock_score = await self._score_stock(symbol, category)
                    if stock_score:
                        scored_stocks.append(stock_score)
                except Exception as e:
                    logger.debug(f"Error scoring {symbol}: {e}")
                    continue
            
            # Sort by composite score (growth + momentum + liquidity)
            scored_stocks.sort(key=lambda x: self._calculate_composite_score(x), reverse=True)
            
            # Take top 150
            self.universe = scored_stocks[:self.target_size]
            self.last_refresh = datetime.now()
            
            # Cache results
            self._save_cache()
            
            # Log summary
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Universe refreshed: {len(self.universe)} stocks in {elapsed:.1f}s")
            self._log_universe_summary()
            
            return [s.symbol for s in self.universe]
            
        except Exception as e:
            logger.error(f"Error refreshing universe: {e}")
            # Fallback to static universe
            return self._get_fallback_universe()
    
    async def _discover_from_api(self) -> List[Tuple[str, str]]:
        """
        Discover new trading opportunities from Alpaca API.
        
        Fetches:
        1. Top gainers (momentum plays)
        2. Top losers (potential bounces or shorts)
        3. Most active by volume (institutional interest)
        
        Returns:
            List of (symbol, category) tuples discovered from API
        """
        discovered = []
        
        if not self.alpaca:
            logger.debug("No Alpaca client - skipping API discovery")
            return discovered
        
        try:
            # Try to get market movers from Alpaca
            # Alpaca provides top movers through their screener API
            
            # Method 1: Get most active stocks
            try:
                most_active = await self._get_most_active_stocks(50)
                for symbol in most_active:
                    discovered.append((symbol, 'api_most_active'))
                logger.info(f"📈 Most active: {len(most_active)} stocks")
            except Exception as e:
                logger.debug(f"Could not fetch most active: {e}")
            
            # Method 2: Get top gainers
            try:
                top_gainers = await self._get_top_movers('gainers', 30)
                for symbol in top_gainers:
                    if symbol not in [d[0] for d in discovered]:
                        discovered.append((symbol, 'api_top_gainer'))
                logger.info(f"🚀 Top gainers: {len(top_gainers)} stocks")
            except Exception as e:
                logger.debug(f"Could not fetch top gainers: {e}")
            
            # Method 3: Get top losers (potential bounce plays)
            try:
                top_losers = await self._get_top_movers('losers', 20)
                for symbol in top_losers:
                    if symbol not in [d[0] for d in discovered]:
                        discovered.append((symbol, 'api_top_loser'))
                logger.info(f"📉 Top losers: {len(top_losers)} stocks")
            except Exception as e:
                logger.debug(f"Could not fetch top losers: {e}")
            
        except Exception as e:
            logger.warning(f"API discovery failed: {e}")
        
        return discovered
    
    async def _get_most_active_stocks(self, limit: int = 50) -> List[str]:
        """Get most active stocks by volume from Alpaca."""
        try:
            if hasattr(self.alpaca, 'client') and hasattr(self.alpaca.client, 'get_most_actives'):
                # Use Alpaca's most actives endpoint
                actives = self.alpaca.client.get_most_actives(by='volume', top=limit)
                return [a.symbol for a in actives if self._is_valid_symbol(a.symbol)]
            
            # Fallback: Use market data to find high-volume stocks
            if self.market_data:
                # Get bars for a broad set and sort by volume
                test_symbols = (
                    self.HIGH_GROWTH_TECH[:20] + 
                    self.SEMICONDUCTOR_GROWTH[:10] +
                    self.AI_CLOUD[:10] +
                    self.EV_CLEANTECH[:10]
                )
                
                bars = self.market_data.fetch_historical_bars(test_symbols, days=1)
                if bars:
                    volume_data = []
                    for symbol, df in bars.items():
                        if len(df) > 0:
                            total_volume = df['volume'].sum()
                            avg_price = df['close'].mean()
                            dollar_volume = total_volume * avg_price
                            volume_data.append((symbol, dollar_volume))
                    
                    # Sort by dollar volume
                    volume_data.sort(key=lambda x: x[1], reverse=True)
                    return [s for s, v in volume_data[:limit]]
            
            return []
            
        except Exception as e:
            logger.debug(f"Error getting most active: {e}")
            return []
    
    async def _get_top_movers(self, direction: str, limit: int = 30) -> List[str]:
        """Get top movers (gainers or losers) from Alpaca."""
        try:
            if hasattr(self.alpaca, 'client') and hasattr(self.alpaca.client, 'get_top_market_movers'):
                # Use Alpaca's market movers endpoint
                movers = self.alpaca.client.get_top_market_movers(top=limit)
                if direction == 'gainers':
                    return [m.symbol for m in movers.gainers if self._is_valid_symbol(m.symbol)]
                else:
                    return [m.symbol for m in movers.losers if self._is_valid_symbol(m.symbol)]
            
            # Fallback: Calculate from market data
            if self.market_data:
                test_symbols = list(set(
                    self.HIGH_GROWTH_TECH + 
                    self.SEMICONDUCTOR_GROWTH +
                    self.EV_CLEANTECH +
                    self.HIGH_BETA_MOMENTUM
                ))[:100]
                
                bars = self.market_data.fetch_historical_bars(test_symbols, days=1)
                if bars:
                    changes = []
                    for symbol, df in bars.items():
                        if len(df) >= 2:
                            pct_change = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
                            changes.append((symbol, pct_change))
                    
                    # Sort by change
                    if direction == 'gainers':
                        changes.sort(key=lambda x: x[1], reverse=True)
                    else:
                        changes.sort(key=lambda x: x[1])
                    
                    return [s for s, c in changes[:limit]]
            
            return []
            
        except Exception as e:
            logger.debug(f"Error getting top movers: {e}")
            return []
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """Check if symbol is valid for trading (no penny stocks, OTC, etc.)."""
        if not symbol or len(symbol) > 5:
            return False
        # Skip common invalid patterns
        invalid_patterns = ['.', '-', '$', '/', 'TEST', 'DUMMY']
        return not any(p in symbol for p in invalid_patterns)
    
    async def _score_stock(self, symbol: str, category: str) -> Optional[UniverseStock]:
        """
        Score a stock for inclusion in the universe.
        
        Prioritizes growth potential over market cap.
        """
        try:
            # Base growth score from category
            growth_score = self.category_growth_scores.get(category, 50)
            
            # Get real-time data if available
            volatility = 0.02  # Default 2% daily volatility
            avg_volume = 1_000_000  # Default $1M volume
            momentum_rank = 50  # Default middle rank
            
            if self.market_data:
                try:
                    # Fetch recent bars for momentum calculation
                    bars = self.market_data.fetch_historical_bars([symbol], days=5)
                    if bars and symbol in bars:
                        df = bars[symbol]
                        if len(df) >= 10:
                            # Calculate volatility (higher = more opportunity)
                            returns = df['close'].pct_change().dropna()
                            volatility = returns.std() * (252 ** 0.5)  # Annualized
                            
                            # Calculate momentum (recent performance)
                            price_change = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
                            momentum_rank = min(100, max(0, 50 + price_change * 10))
                            
                            # Calculate average dollar volume
                            avg_volume = (df['close'] * df['volume']).mean()
                except Exception as e:
                    logger.debug(f"Error fetching data for {symbol}: {e}")
            
            # Liquidity score (0-100)
            # $10M+ = 100, $1M = 50, <$100K = 0
            if avg_volume >= 10_000_000:
                liquidity_score = 100
            elif avg_volume >= 1_000_000:
                liquidity_score = 50 + (avg_volume - 1_000_000) / 180_000
            elif avg_volume >= 100_000:
                liquidity_score = avg_volume / 20_000
            else:
                liquidity_score = 0  # Too illiquid
            
            # Filter out illiquid stocks
            if liquidity_score < 30:
                return None
            
            return UniverseStock(
                symbol=symbol,
                category=category,
                avg_volume=avg_volume,
                volatility=volatility,
                growth_score=growth_score,
                momentum_rank=int(momentum_rank),
                liquidity_score=int(liquidity_score)
            )
            
        except Exception as e:
            logger.debug(f"Error scoring {symbol}: {e}")
            return None

    
    def _calculate_composite_score(self, stock: UniverseStock) -> float:
        """
        Calculate composite score prioritizing GROWTH over stability.
        
        Weights:
        - Growth potential: 40% (category-based, mid-caps score higher)
        - Momentum: 30% (recent price action)
        - Volatility: 20% (opportunity for day trading)
        - Liquidity: 10% (tradeable, but not dominant factor)
        
        This ensures mid-cap growth stocks can outrank stable mega-caps.
        """
        # Normalize volatility to 0-100 (2% daily = 50, 5% = 100)
        volatility_score = min(100, stock.volatility * 100 / 0.05 * 50)
        
        composite = (
            stock.growth_score * 0.40 +      # Growth potential (40%)
            stock.momentum_rank * 0.30 +      # Recent momentum (30%)
            volatility_score * 0.20 +         # Volatility/opportunity (20%)
            stock.liquidity_score * 0.10      # Liquidity (10%)
        )
        
        return composite
    
    def _is_cache_valid(self) -> bool:
        """
        Check if cached universe is still valid.
        
        Cache is valid if:
        1. Cached today AND
        2. Cached after market open (9:35 AM ET) - so we have real movers
        
        This ensures we refresh shortly AFTER market opens to catch early movers.
        """
        try:
            if not UNIVERSE_CACHE_FILE.exists():
                return False
            
            with open(UNIVERSE_CACHE_FILE, 'r') as f:
                cache = json.load(f)
            
            cache_datetime = datetime.fromisoformat(cache.get('date', '2000-01-01'))
            now_et = datetime.now(ET)
            today = now_et.date()
            
            # Check if cached today
            if cache_datetime.date() != today:
                logger.info("📅 Cache is from a different day - will refresh")
                return False
            
            # Check if cache was created after market open (9:35 AM ET)
            cache_time = cache_datetime.time()
            if cache_time < FIRST_REFRESH:
                # Cache was created before market opened - need fresh data
                if now_et.time() >= FIRST_REFRESH:
                    logger.info("⏰ Cache is pre-market - refreshing with live movers")
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Cache validation error: {e}")
            return False
    
    def _is_market_open(self) -> bool:
        """Check if market is currently open."""
        now_et = datetime.now(ET)
        current_time = now_et.time()
        
        # Check if it's a weekday
        if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        return MARKET_OPEN <= current_time <= MARKET_CLOSE
    
    def _should_use_premarket_fallback(self) -> bool:
        """
        Check if we should use fallback (pre-market or weekend).
        
        Before market opens, API movers won't be available,
        so we use the curated list as fallback.
        
        NOTE: During first 5 mins (9:30-9:35), we still try API but
        fall back gracefully if data isn't ready yet.
        """
        now_et = datetime.now(ET)
        current_time = now_et.time()
        
        # Weekend - use fallback
        if now_et.weekday() >= 5:
            return True
        
        # Before market open - use fallback
        if current_time < MARKET_OPEN:
            return True
        
        # During market hours, always try API (even in first 5 mins)
        # The API methods have their own fallbacks
        return False
    
    def _load_cached_universe(self) -> List[str]:
        """Load universe from cache."""
        try:
            with open(UNIVERSE_CACHE_FILE, 'r') as f:
                cache = json.load(f)
            
            self.universe = [
                UniverseStock(**stock) for stock in cache.get('stocks', [])
            ]
            self.last_refresh = datetime.fromisoformat(cache.get('date'))
            
            return [s.symbol for s in self.universe]
            
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return self._get_fallback_universe()
    
    def _save_cache(self):
        """Save universe to cache."""
        try:
            cache = {
                'date': datetime.now().isoformat(),
                'stocks': [asdict(s) for s in self.universe],
                'version': '2.0'
            }
            
            with open(UNIVERSE_CACHE_FILE, 'w') as f:
                json.dump(cache, f, indent=2)
            
            logger.info(f"💾 Universe cached: {len(self.universe)} stocks")
            
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _get_fallback_universe(self) -> List[str]:
        """Get fallback universe if refresh fails."""
        # Return a balanced mix prioritizing growth
        fallback = (
            self.HIGH_GROWTH_TECH[:15] +
            self.SEMICONDUCTOR_GROWTH[:10] +
            self.AI_CLOUD[:15] +
            self.EV_CLEANTECH[:10] +
            self.BIOTECH_GROWTH[:10] +
            self.CONSUMER_GROWTH[:10] +
            self.FINTECH[:10] +
            self.INDUSTRIAL_GROWTH[:10] +
            self.MEGA_CAP_STABLE[:10] +
            self.HIGH_BETA_MOMENTUM[:10] +
            self.MARKET_ETFS +
            self.SECTOR_ETFS[:10]
        )
        
        # Remove duplicates
        seen = set()
        unique = []
        for s in fallback:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        
        return unique[:150]
    
    def _log_universe_summary(self):
        """Log summary of universe composition."""
        if not self.universe:
            return
        
        # Count by category
        category_counts = {}
        for stock in self.universe:
            cat = stock.category
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        logger.info("📊 Universe Composition:")
        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  {cat}: {count} stocks")
        
        # Top 10 by score
        top_10 = self.universe[:10]
        logger.info("🏆 Top 10 by Growth Potential:")
        for i, stock in enumerate(top_10, 1):
            score = self._calculate_composite_score(stock)
            logger.info(f"  {i}. {stock.symbol} ({stock.category}): {score:.1f}")

    
    def get_symbols(self) -> List[str]:
        """Get current universe symbols."""
        if not self.universe:
            return self._get_fallback_universe()
        return [s.symbol for s in self.universe]
    
    def get_by_category(self, category: str) -> List[str]:
        """Get symbols by category."""
        return [s.symbol for s in self.universe if s.category == category]
    
    def get_high_growth(self, n: int = 50) -> List[str]:
        """Get top N high-growth stocks."""
        sorted_stocks = sorted(
            self.universe, 
            key=lambda x: x.growth_score, 
            reverse=True
        )
        return [s.symbol for s in sorted_stocks[:n]]
    
    def get_high_momentum(self, n: int = 50) -> List[str]:
        """Get top N momentum stocks."""
        sorted_stocks = sorted(
            self.universe,
            key=lambda x: x.momentum_rank,
            reverse=True
        )
        return [s.symbol for s in sorted_stocks[:n]]
    
    def get_high_volatility(self, n: int = 50) -> List[str]:
        """Get top N volatile stocks (more opportunity)."""
        sorted_stocks = sorted(
            self.universe,
            key=lambda x: x.volatility,
            reverse=True
        )
        return [s.symbol for s in sorted_stocks[:n]]


# Singleton instance
_universe_manager: Optional[DynamicUniverseManager] = None


def get_dynamic_universe(alpaca_client=None, market_data_client=None) -> DynamicUniverseManager:
    """Get or create the dynamic universe manager singleton."""
    global _universe_manager
    
    if _universe_manager is None:
        _universe_manager = DynamicUniverseManager(alpaca_client, market_data_client)
    
    return _universe_manager


async def refresh_daily_universe(alpaca_client=None, market_data_client=None) -> List[str]:
    """Convenience function to refresh the daily universe."""
    manager = get_dynamic_universe(alpaca_client, market_data_client)
    return await manager.refresh_universe()


# Quick test
if __name__ == '__main__':
    import asyncio
    
    async def test():
        manager = DynamicUniverseManager()
        candidates = manager.get_all_candidates()
        print(f"Total candidates: {len(candidates)}")
        
        # Test fallback
        fallback = manager._get_fallback_universe()
        print(f"Fallback universe: {len(fallback)} stocks")
        print(f"Sample: {fallback[:20]}")
    
    asyncio.run(test())
