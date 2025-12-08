#!/usr/bin/env python3
"""
Smart Watchlist Manager - Efficient stock selection.

Creates a 50-stock watchlist with:
- 70% large-cap (35 stocks) - stable, liquid
- 30% mid-cap (15 stocks) - growth potential

EFFICIENT: Uses Alpaca snapshots for quick filtering (no bars fetch).
Only fetches detailed data for final candidates.

Refreshes every 2 hours for base watchlist.
Breakout detection runs every 5 minutes via momentum scanner.
"""

import asyncio
from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
import pytz

logger = logging.getLogger(__name__)

ET = pytz.timezone('America/New_York')

MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)


@dataclass
class WatchlistStock:
    """Stock with scoring metrics."""
    symbol: str
    cap_category: str  # 'large' or 'mid'
    dollar_volume: float  # Daily dollar volume
    change_pct: float  # Daily change %
    price: float
    composite_score: float


class SmartWatchlistManager:
    """
    Manages a 50-stock watchlist with 70/30 large/mid cap split.
    
    EFFICIENT APPROACH:
    1. Use Alpaca snapshots for quick filtering (1 API call for all)
    2. Score based on volume and price change (no bars needed)
    3. Only fetch detailed bars for momentum scanner (separate process)
    """
    
    # Large-cap pool (market cap > $50B, highly liquid)
    LARGE_CAP_POOL = [
        # Tech giants
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSLA',
        'AVGO', 'ORCL', 'CRM', 'ADBE', 'AMD', 'INTC', 'CSCO', 'QCOM',
        'TXN', 'IBM', 'NOW', 'INTU', 'AMAT', 'MU', 'LRCX', 'ADI',
        # Finance
        'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'AXP', 'BLK', 'C',
        # Healthcare
        'UNH', 'JNJ', 'LLY', 'PFE', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR',
        # Consumer
        'WMT', 'HD', 'COST', 'PG', 'KO', 'PEP', 'MCD', 'NKE', 'SBUX',
        # Industrial
        'CAT', 'DE', 'BA', 'HON', 'UPS', 'RTX', 'LMT', 'GE',
        # Energy
        'XOM', 'CVX', 'COP', 'SLB', 'EOG',
        # ETFs
        'SPY', 'QQQ', 'IWM', 'DIA'
    ]
    
    # Mid-cap pool (market cap $10B-$50B, growth potential)
    MID_CAP_POOL = [
        # High-growth tech
        'PLTR', 'SNOW', 'DDOG', 'CRWD', 'ZS', 'NET', 'MDB', 'OKTA',
        'PANW', 'FTNT', 'CYBR', 'HUBS', 'TWLO', 'BILL', 'DOCN',
        # Semiconductors
        'MRVL', 'ON', 'MPWR', 'SWKS', 'WOLF', 'CRUS',
        # Fintech
        'SQ', 'PYPL', 'COIN', 'HOOD', 'SOFI', 'AFRM', 'UPST',
        # EV & Clean energy
        'RIVN', 'LCID', 'ENPH', 'SEDG', 'PLUG', 'CHPT',
        # Consumer growth
        'ABNB', 'UBER', 'LYFT', 'DASH', 'RBLX', 'ROKU', 'SNAP',
        # Biotech
        'MRNA', 'REGN', 'VRTX', 'CRSP', 'DXCM',
        # E-commerce
        'SHOP', 'ETSY', 'CHWY', 'W',
        # Other growth
        'MARA', 'RIOT', 'PATH', 'U', 'TTWO'
    ]
    
    def __init__(self, alpaca_client=None, market_data_client=None):
        self.alpaca = alpaca_client
        self.market_data = market_data_client
        self.watchlist: List[WatchlistStock] = []
        self.last_refresh: Optional[datetime] = None
        self.refresh_interval_hours = 2
        
        # Target composition
        self.target_size = 50
        self.large_cap_count = 35  # 70%
        self.mid_cap_count = 15    # 30%
        
        logger.info("✅ SmartWatchlistManager initialized (50 stocks, 70/30 split, 2hr refresh)")
    
    async def get_watchlist(self, force_refresh: bool = False) -> List[str]:
        """Get current watchlist, refreshing if needed."""
        if force_refresh or self._needs_refresh():
            await self.refresh_watchlist()
        
        if not self.watchlist:
            return self._get_fallback_watchlist()
        
        return [s.symbol for s in self.watchlist]
    
    def _needs_refresh(self) -> bool:
        """Check if watchlist needs refresh."""
        if not self.last_refresh:
            return True
        
        now = datetime.now(ET)
        hours_since = (now - self.last_refresh.replace(tzinfo=ET)).total_seconds() / 3600
        
        if hours_since >= self.refresh_interval_hours:
            return True
        
        if self.last_refresh.date() < now.date() and now.time() >= MARKET_OPEN:
            return True
        
        return False
    
    async def refresh_watchlist(self) -> List[str]:
        """
        Refresh watchlist EFFICIENTLY using Alpaca snapshots.
        
        NO BARS FETCHING - uses snapshot data only (1 API call).
        """
        logger.info("🔄 Refreshing smart watchlist (efficient snapshot-based)...")
        start_time = datetime.now()
        
        try:
            # Get all symbols to check
            all_large = self.LARGE_CAP_POOL.copy()
            all_mid = self.MID_CAP_POOL.copy()
            all_symbols = list(set(all_large + all_mid))
            
            # EFFICIENT: Get snapshots for all symbols in ONE API call
            snapshots = await self._get_snapshots(all_symbols)
            
            if not snapshots:
                logger.warning("No snapshots available, using fallback")
                return self._get_fallback_watchlist()
            
            # Score large-caps
            large_scored = []
            for symbol in all_large:
                if symbol in snapshots:
                    score = self._score_from_snapshot(symbol, snapshots[symbol], 'large')
                    if score:
                        large_scored.append(score)
            
            # Score mid-caps
            mid_scored = []
            for symbol in all_mid:
                if symbol in snapshots:
                    score = self._score_from_snapshot(symbol, snapshots[symbol], 'mid')
                    if score:
                        mid_scored.append(score)
            
            # Sort by score and take top N
            large_scored.sort(key=lambda x: x.composite_score, reverse=True)
            mid_scored.sort(key=lambda x: x.composite_score, reverse=True)
            
            top_large = large_scored[:self.large_cap_count]
            top_mid = mid_scored[:self.mid_cap_count]
            
            # Combine
            self.watchlist = top_large + top_mid
            self.watchlist.sort(key=lambda x: x.composite_score, reverse=True)
            self.last_refresh = datetime.now()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Watchlist refreshed: {len(self.watchlist)} stocks in {elapsed:.1f}s")
            logger.info(f"   Large-cap: {len(top_large)} | Mid-cap: {len(top_mid)}")
            
            top_10 = [s.symbol for s in self.watchlist[:10]]
            logger.info(f"   Top 10: {', '.join(top_10)}")
            
            return [s.symbol for s in self.watchlist]
            
        except Exception as e:
            logger.error(f"Error refreshing watchlist: {e}")
            return self._get_fallback_watchlist()
    
    async def _get_snapshots(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get snapshots for all symbols in ONE API call.
        
        Returns dict of {symbol: snapshot_data}
        """
        try:
            if not self.alpaca:
                return {}
            
            # Alpaca allows up to 1000 symbols per snapshot request
            snapshots = {}
            
            # Use Alpaca's get_snapshots method
            if hasattr(self.alpaca, 'client') and hasattr(self.alpaca.client, 'get_snapshots'):
                from alpaca.data.requests import StockSnapshotRequest
                request = StockSnapshotRequest(symbol_or_symbols=symbols)
                result = self.alpaca.client.get_snapshots(request)
                
                for symbol, snap in result.items():
                    if snap and snap.daily_bar:
                        snapshots[symbol] = {
                            'price': snap.daily_bar.close,
                            'volume': snap.daily_bar.volume,
                            'open': snap.daily_bar.open,
                            'high': snap.daily_bar.high,
                            'low': snap.daily_bar.low,
                            'prev_close': snap.previous_daily_bar.close if snap.previous_daily_bar else snap.daily_bar.open,
                        }
            else:
                # Fallback: use market data client
                if self.market_data and hasattr(self.market_data, 'get_latest_quotes'):
                    quotes = self.market_data.get_latest_quotes(symbols)
                    for symbol, quote in quotes.items():
                        snapshots[symbol] = {
                            'price': quote.ask_price if quote.ask_price else quote.bid_price,
                            'volume': 1_000_000,  # Default
                            'prev_close': quote.bid_price,
                        }
            
            logger.info(f"📊 Got snapshots for {len(snapshots)}/{len(symbols)} symbols")
            return snapshots
            
        except Exception as e:
            logger.warning(f"Snapshot fetch failed: {e}")
            return {}
    
    def _score_from_snapshot(self, symbol: str, snapshot: Dict, cap_category: str) -> Optional[WatchlistStock]:
        """
        Score stock from snapshot data (NO BARS NEEDED).
        
        Scoring:
        - Volume score (40%): Higher volume = better liquidity
        - Movement score (35%): Stocks moving today = more opportunity
        - Category bonus (25%): Mid-caps get slight boost for growth potential
        """
        try:
            price = snapshot.get('price', 0)
            volume = snapshot.get('volume', 0)
            prev_close = snapshot.get('prev_close', price)
            
            if price <= 0 or volume <= 0:
                return None
            
            # Dollar volume
            dollar_volume = price * volume
            
            # Change %
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
            
            # Volume score (0-100): $100M+ = 100, $10M = 50, <$1M = 0
            if dollar_volume >= 100_000_000:
                volume_score = 100
            elif dollar_volume >= 10_000_000:
                volume_score = 50 + (dollar_volume - 10_000_000) / 1_800_000
            elif dollar_volume >= 1_000_000:
                volume_score = (dollar_volume - 1_000_000) / 180_000
            else:
                return None  # Too illiquid
            
            # Movement score (0-100): More movement = more opportunity
            # 3%+ move = 100, 1% = 50, 0% = 25
            abs_change = abs(change_pct)
            if abs_change >= 3:
                movement_score = 100
            elif abs_change >= 1:
                movement_score = 50 + (abs_change - 1) * 25
            else:
                movement_score = 25 + abs_change * 25
            
            # Category bonus: mid-caps get 10 point boost for growth potential
            category_bonus = 10 if cap_category == 'mid' else 0
            
            # Composite score
            composite = (
                volume_score * 0.40 +
                movement_score * 0.35 +
                category_bonus + 25 * 0.25  # Base 25 + category bonus
            )
            
            return WatchlistStock(
                symbol=symbol,
                cap_category=cap_category,
                dollar_volume=dollar_volume,
                change_pct=change_pct,
                price=price,
                composite_score=composite
            )
            
        except Exception as e:
            logger.debug(f"Score error for {symbol}: {e}")
            return None
    
    def _get_fallback_watchlist(self) -> List[str]:
        """Fallback watchlist if scoring fails."""
        large = self.LARGE_CAP_POOL[:35]
        mid = self.MID_CAP_POOL[:15]
        return large + mid
    
    def get_large_caps(self) -> List[str]:
        """Get large-cap symbols from current watchlist."""
        return [s.symbol for s in self.watchlist if s.cap_category == 'large']
    
    def get_mid_caps(self) -> List[str]:
        """Get mid-cap symbols from current watchlist."""
        return [s.symbol for s in self.watchlist if s.cap_category == 'mid']


# Singleton
_watchlist_manager: Optional[SmartWatchlistManager] = None


def get_smart_watchlist(alpaca_client=None, market_data_client=None) -> SmartWatchlistManager:
    """Get or create the smart watchlist manager singleton."""
    global _watchlist_manager
    
    if _watchlist_manager is None:
        _watchlist_manager = SmartWatchlistManager(alpaca_client, market_data_client)
    
    return _watchlist_manager
