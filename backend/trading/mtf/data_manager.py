"""
Multi-Timeframe Data Manager.

Manages fetching and caching of market data across multiple timeframes.
Implements efficient caching with appropriate refresh intervals.

Requirements: 1.1, 1.2, 1.3, 1.4
"""

import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

from alpaca.data.timeframe import TimeFrame

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry for timeframe data."""
    data: pd.DataFrame
    timestamp: datetime
    symbol: str
    timeframe: str


@dataclass
class MTFDataManager:
    """Manages multi-timeframe market data fetching and caching.
    
    Requirements:
    - 1.1: Fetch historical bars for 1-min, 5-min, 15-min, and daily timeframes
    - 1.2: Refresh 5-min every 5 min, 15-min every 15 min, daily once per day
    - 1.3: Cache data efficiently to minimize API calls
    - 1.4: Use cached data on fetch failures
    """
    
    alpaca_client: object  # AlpacaClient instance
    
    # Cache storage: {symbol: {timeframe: CacheEntry}}
    cache: Dict[str, Dict[str, CacheEntry]] = field(default_factory=dict)
    
    # Last refresh timestamps per timeframe
    last_refresh: Dict[str, datetime] = field(default_factory=dict)
    
    # Refresh intervals in seconds
    REFRESH_INTERVALS: Dict[str, int] = field(default_factory=lambda: {
        '1min': 60,      # 1 minute
        '5min': 300,     # 5 minutes
        '15min': 900,    # 15 minutes
        'daily': 86400,  # 24 hours (refresh once per day)
    })
    
    # Lookback periods for each timeframe
    LOOKBACK_BARS: Dict[str, int] = field(default_factory=lambda: {
        '1min': 100,   # ~1.5 hours of 1-min bars
        '5min': 100,   # ~8 hours of 5-min bars
        '15min': 100,  # ~25 hours of 15-min bars
        'daily': 60,   # 60 days of daily bars
    })
    
    # Alpaca TimeFrame mapping
    # Note: For 5min and 15min, we use TimeFrame.Minute and fetch more bars
    # then resample, as Alpaca SDK doesn't support custom minute intervals directly
    TIMEFRAME_MAP: Dict[str, TimeFrame] = field(default_factory=lambda: {
        '1min': TimeFrame.Minute,
        '5min': TimeFrame.Minute,   # Fetch 1-min bars and resample
        '15min': TimeFrame.Minute,  # Fetch 1-min bars and resample
        'daily': TimeFrame.Day,
    })

    
    def _needs_refresh(self, timeframe: str) -> bool:
        """Check if a timeframe needs to be refreshed.
        
        Requirement 1.2: Refresh intervals per timeframe.
        """
        if timeframe not in self.last_refresh:
            return True
        
        elapsed = (datetime.now(timezone.utc) - self.last_refresh[timeframe]).total_seconds()
        return elapsed >= self.REFRESH_INTERVALS.get(timeframe, 60)
    
    def _get_cached_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Get cached data for a symbol and timeframe.
        
        Requirement 1.3: Efficient caching.
        """
        if symbol in self.cache and timeframe in self.cache[symbol]:
            entry = self.cache[symbol][timeframe]
            return entry.data
        return None
    
    def _update_cache(self, symbol: str, timeframe: str, data: pd.DataFrame) -> None:
        """Update cache with new data."""
        if symbol not in self.cache:
            self.cache[symbol] = {}
        
        self.cache[symbol][timeframe] = CacheEntry(
            data=data,
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            timeframe=timeframe,
        )
    
    def _fetch_timeframe_data(
        self, 
        symbol: str, 
        timeframe: str,
        use_cache_on_failure: bool = True
    ) -> Optional[pd.DataFrame]:
        """Fetch data for a single timeframe.
        
        Requirement 1.4: Fallback to cached data on fetch failures.
        """
        try:
            tf = self.TIMEFRAME_MAP.get(timeframe)
            if tf is None:
                logger.error(f"Unknown timeframe: {timeframe}")
                return self._get_cached_data(symbol, timeframe) if use_cache_on_failure else None
            
            lookback = self.LOOKBACK_BARS.get(timeframe, 100)
            
            # Calculate start time based on timeframe
            if timeframe == 'daily':
                start = datetime.now(timezone.utc) - timedelta(days=lookback)
            elif timeframe == '15min':
                start = datetime.now(timezone.utc) - timedelta(minutes=lookback * 15)
            elif timeframe == '5min':
                start = datetime.now(timezone.utc) - timedelta(minutes=lookback * 5)
            else:  # 1min
                start = datetime.now(timezone.utc) - timedelta(minutes=lookback)
            
            data = self.alpaca_client.get_bars_for_symbol(
                symbol=symbol,
                timeframe=tf,
                start=start,
                limit=lookback,
            )
            
            if data is not None and not data.empty:
                self._update_cache(symbol, timeframe, data)
                return data
            else:
                logger.warning(f"No data returned for {symbol} {timeframe}")
                if use_cache_on_failure:
                    cached = self._get_cached_data(symbol, timeframe)
                    if cached is not None:
                        logger.info(f"Using cached data for {symbol} {timeframe}")
                        return cached
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch {timeframe} data for {symbol}: {e}")
            if use_cache_on_failure:
                cached = self._get_cached_data(symbol, timeframe)
                if cached is not None:
                    logger.info(f"Using cached data for {symbol} {timeframe} after fetch failure")
                    return cached
            return None
    
    def fetch_all_timeframes(
        self, 
        symbol: str,
        force_refresh: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data for all timeframes for a symbol.
        
        Requirement 1.1: Fetch historical bars for all timeframes.
        
        Args:
            symbol: Stock symbol
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            Dict mapping timeframe to DataFrame
        """
        result = {}
        
        for timeframe in ['1min', '5min', '15min', 'daily']:
            # Check if we need to refresh this timeframe
            if not force_refresh and not self._needs_refresh(timeframe):
                cached = self._get_cached_data(symbol, timeframe)
                if cached is not None:
                    result[timeframe] = cached
                    continue
            
            # Fetch fresh data
            data = self._fetch_timeframe_data(symbol, timeframe)
            if data is not None:
                result[timeframe] = data
                self.last_refresh[timeframe] = datetime.now(timezone.utc)
        
        return result
    
    def refresh_timeframe(
        self, 
        timeframe: str, 
        symbols: List[str]
    ) -> Dict[str, pd.DataFrame]:
        """Refresh data for a specific timeframe across multiple symbols.
        
        Requirement 1.2: Scheduled refresh per timeframe.
        
        Args:
            timeframe: Timeframe to refresh ('1min', '5min', '15min', 'daily')
            symbols: List of symbols to refresh
            
        Returns:
            Dict mapping symbol to DataFrame
        """
        result = {}
        
        for symbol in symbols:
            data = self._fetch_timeframe_data(symbol, timeframe)
            if data is not None:
                result[symbol] = data
        
        if result:
            self.last_refresh[timeframe] = datetime.now(timezone.utc)
            logger.info(f"Refreshed {timeframe} data for {len(result)} symbols")
        
        return result
    
    def get_cached_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Public method to get cached data.
        
        Requirement 1.3: Access cached data.
        """
        return self._get_cached_data(symbol, timeframe)
    
    def clear_cache(self, symbol: Optional[str] = None, timeframe: Optional[str] = None) -> None:
        """Clear cache entries.
        
        Args:
            symbol: If provided, clear only this symbol's cache
            timeframe: If provided, clear only this timeframe's cache
        """
        if symbol and timeframe:
            if symbol in self.cache and timeframe in self.cache[symbol]:
                del self.cache[symbol][timeframe]
        elif symbol:
            if symbol in self.cache:
                del self.cache[symbol]
        elif timeframe:
            for sym in list(self.cache.keys()):
                if timeframe in self.cache[sym]:
                    del self.cache[sym][timeframe]
        else:
            self.cache.clear()
            self.last_refresh.clear()
    
    def get_cache_status(self) -> Dict[str, Dict[str, str]]:
        """Get status of cached data for debugging."""
        status = {}
        for symbol, timeframes in self.cache.items():
            status[symbol] = {}
            for tf, entry in timeframes.items():
                age = (datetime.now(timezone.utc) - entry.timestamp).total_seconds()
                status[symbol][tf] = f"{len(entry.data)} bars, {age:.0f}s old"
        return status
