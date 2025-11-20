"""
Daily Data Cache - Sprint 7

Caches daily bars and calculations to avoid repeated API calls.
Refreshes once per day at market open.

Data Source: Twelve Data API (FREE tier - 800 credits/day)
Cost: ~50 credits/day for 50 symbols (6.25% of daily limit)

Cached Data:
- Daily bars (200+ days)
- 200-EMA
- Daily EMA(9/21)
- Daily trend direction
"""

from datetime import datetime, date
from typing import Dict, Optional
import pandas as pd
import numpy as np
import requests
import os
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DailyCache:
    """
    Cache daily market data and calculations.
    
    Refreshes once per day at market open to minimize API calls.
    """
    
    def __init__(self):
        self.cache: Dict[str, dict] = {}
        self.cache_date: Optional[date] = None
        
        # Primary and secondary API keys for fallback
        self.primary_api_key = settings.twelvedata_api_key or os.getenv('TWELVEDATA_API_KEY')
        self.secondary_api_key = settings.twelvedata_secondary_api_key or os.getenv('TWELVEDATA_SECONDARY_API_KEY')
        self.current_api_key = self.primary_api_key
        self.api_key_index = 0  # 0 = primary, 1 = secondary
        
        self.twelvedata_base_url = "https://api.twelvedata.com"
        
        # Track API usage
        self.primary_calls = 0
        self.secondary_calls = 0
        
        if self.secondary_api_key:
            logger.info("Daily cache initialized (Twelve Data API with fallback)")
        else:
            logger.info("Daily cache initialized (Twelve Data API - single key)")
    
    def is_cache_valid(self) -> bool:
        """Check if cache is still valid for today"""
        today = datetime.now().date()
        return self.cache_date == today
    
    def get_daily_data(self, symbol: str) -> Optional[dict]:
        """
        Get cached daily data for a symbol.
        
        Returns:
            dict with keys:
                - price: Current daily price
                - ema_200: 200-day EMA
                - ema_9: 9-day EMA
                - ema_21: 21-day EMA
                - trend: 'bullish' or 'bearish' (based on EMA 9/21)
                - bars: DataFrame of daily bars
        """
        if not self.is_cache_valid():
            logger.warning(f"Cache stale for {symbol}, needs refresh")
            return None
        
        return self.cache.get(symbol)
    
    def set_daily_data(self, symbol: str, data: dict):
        """Set cached daily data for a symbol"""
        self.cache[symbol] = data
        self.cache_date = datetime.now().date()
    
    def switch_api_key(self):
        """Switch to secondary API key if available"""
        if self.secondary_api_key and self.api_key_index == 0:
            self.current_api_key = self.secondary_api_key
            self.api_key_index = 1
            logger.info("🔄 Switched to secondary API key")
            return True
        elif self.api_key_index == 1:
            # Already on secondary, switch back to primary
            self.current_api_key = self.primary_api_key
            self.api_key_index = 0
            logger.info("🔄 Switched back to primary API key")
            return True
        return False
    
    def fetch_twelvedata_bars(self, symbol: str, retry_with_fallback: bool = True) -> Optional[list]:
        """
        Fetch daily bars from Twelve Data API with automatic fallback.
        
        Args:
            symbol: Stock symbol
            retry_with_fallback: If True, retry with secondary key on rate limit
            
        Returns:
            List of daily bars (oldest to newest) or None if failed
        """
        if not self.current_api_key:
            logger.error("TWELVEDATA_API_KEY not configured")
            return None
        
        try:
            params = {
                'symbol': symbol,
                'interval': '1day',
                'outputsize': 200,  # Need 200 days for 200-EMA
                'apikey': self.current_api_key
            }
            
            response = requests.get(
                f"{self.twelvedata_base_url}/time_series",
                params=params,
                timeout=10
            )
            
            # Track API usage
            if self.api_key_index == 0:
                self.primary_calls += 1
            else:
                self.secondary_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for rate limit error
                if 'status' in data and data['status'] == 'error':
                    error_msg = data.get('message', '')
                    
                    # Check if it's a rate limit error
                    if 'run out of API credits' in error_msg or 'rate limit' in error_msg.lower():
                        logger.warning(f"⚠️ Rate limit hit on {'secondary' if self.api_key_index == 1 else 'primary'} key for {symbol}")
                        
                        # Try fallback if available and not already retried
                        if retry_with_fallback and self.switch_api_key():
                            logger.info(f"🔄 Retrying {symbol} with fallback key...")
                            return self.fetch_twelvedata_bars(symbol, retry_with_fallback=False)
                        else:
                            logger.error(f"❌ Both API keys exhausted for {symbol}")
                            return None
                    else:
                        logger.error(f"Twelve Data API error for {symbol}: {error_msg}")
                        return None
                
                if 'values' in data:
                    # Reverse to get oldest first (Twelve Data returns newest first)
                    return list(reversed(data['values']))
                else:
                    logger.warning(f"No 'values' in Twelve Data response for {symbol}")
                    return None
            else:
                logger.error(f"Twelve Data API returned {response.status_code} for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch Twelve Data bars for {symbol}: {e}")
            return None
    
    def calculate_ema(self, prices: list, period: int) -> float:
        """
        Calculate EMA manually.
        
        Args:
            prices: List of prices (oldest to newest)
            period: EMA period
            
        Returns:
            Latest EMA value
        """
        if len(prices) < period:
            logger.warning(f"Insufficient data for EMA({period}): {len(prices)} prices")
            return prices[-1] if prices else 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]  # Start with first price
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def refresh_cache(self, alpaca_client=None, symbols: list = None):
        """
        Refresh cache for all symbols using Twelve Data API with intelligent key rotation.
        
        Strategy:
        - Use primary key for first 8 symbols
        - Switch to secondary key for next 8 symbols
        - Alternate between keys to maximize throughput
        
        Should be called once per day at market open.
        
        Args:
            alpaca_client: Not used (kept for compatibility)
            symbols: List of symbols to cache
        """
        if not symbols:
            logger.warning("No symbols provided for cache refresh")
            return
        
        try:
            if self.secondary_api_key:
                logger.info(f"🔄 Refreshing daily cache for {len(symbols)} symbols (Twelve Data API with fallback)")
            else:
                logger.info(f"🔄 Refreshing daily cache for {len(symbols)} symbols (Twelve Data API)")
            
            success_count = 0
            failed_symbols = []
            
            # Reset API call counters
            self.primary_calls = 0
            self.secondary_calls = 0
            
            # Start with primary key
            self.current_api_key = self.primary_api_key
            self.api_key_index = 0
            
            for i, symbol in enumerate(symbols):
                try:
                    # Intelligent key rotation: switch every 8 symbols if secondary key available
                    if self.secondary_api_key and i > 0 and i % 8 == 0:
                        self.switch_api_key()
                        logger.info(f"🔄 Switched to {'secondary' if self.api_key_index == 1 else 'primary'} key (processed {i} symbols)")
                    
                    # Fetch daily bars from Twelve Data
                    bars = self.fetch_twelvedata_bars(symbol)
                    
                    if not bars:
                        logger.warning(f"No daily bars for {symbol}")
                        failed_symbols.append(symbol)
                        continue
                    
                    if len(bars) < 200:
                        logger.warning(f"Insufficient daily bars for {symbol}: {len(bars)}")
                        failed_symbols.append(symbol)
                        continue
                    
                    # Extract closing prices
                    closes = [float(bar['close']) for bar in bars]
                    
                    # Calculate EMAs
                    ema_200 = self.calculate_ema(closes, 200)
                    ema_9 = self.calculate_ema(closes[-21:], 9)  # Last 21 days for 9-EMA
                    ema_21 = self.calculate_ema(closes[-21:], 21)  # Last 21 days for 21-EMA
                    
                    # Get latest price
                    latest_price = closes[-1]
                    
                    # Determine trend
                    trend = 'bullish' if ema_9 > ema_21 else 'bearish'
                    
                    # Cache data
                    self.set_daily_data(symbol, {
                        'price': latest_price,
                        'ema_200': ema_200,
                        'ema_9': ema_9,
                        'ema_21': ema_21,
                        'trend': trend,
                        'bars_count': len(bars),
                        'updated_at': datetime.now()
                    })
                    
                    logger.info(f"✅ {symbol}: ${latest_price:.2f} | 200-EMA: ${ema_200:.2f} | Trend: {trend}")
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to cache daily data for {symbol}: {e}")
                    failed_symbols.append(symbol)
                    continue
            
            self.cache_date = datetime.now().date()
            
            # Log API usage statistics
            if self.secondary_api_key:
                logger.info(f"📊 API Usage: Primary={self.primary_calls} calls, Secondary={self.secondary_calls} calls")
            
            logger.info(f"✓ Daily cache refreshed: {success_count}/{len(symbols)} symbols cached")
            
            if failed_symbols:
                logger.warning(f"Failed symbols: {', '.join(failed_symbols)}")
            
        except Exception as e:
            logger.error(f"Failed to refresh daily cache: {e}")
    
    def clear_cache(self):
        """Clear the cache (for testing)"""
        self.cache = {}
        self.cache_date = None
        logger.info("Daily cache cleared")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        return {
            'symbols_cached': len(self.cache),
            'cache_date': self.cache_date,
            'is_valid': self.is_cache_valid()
        }


# Global instance
_daily_cache = None


def get_daily_cache():
    """Get the global daily cache instance"""
    global _daily_cache
    if _daily_cache is None:
        _daily_cache = DailyCache()
    return _daily_cache
