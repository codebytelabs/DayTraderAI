"""
VIX Data Provider - Provides VIX data with caching for position sizing caps.

Based on professional intraday trading research:
- VIX < 15: Low volatility, allow larger positions (up to 1.2x)
- VIX 15-25: Normal volatility, standard sizing (1.0x)
- VIX 25-35: High volatility, reduce positions (0.9x cap)
- VIX > 35: Extreme volatility, conservative sizing (0.7x cap)
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import logging
import os
import sys

logger = logging.getLogger(__name__)


@dataclass
class VIXData:
    """VIX data with metadata"""
    value: float
    timestamp: datetime
    is_fresh: bool = True
    source: str = "api"
    
    def to_dict(self) -> dict:
        return {
            "value": round(self.value, 2),
            "timestamp": self.timestamp.isoformat(),
            "is_fresh": self.is_fresh,
            "source": self.source
        }


class VIXDataProvider:
    """
    Provides VIX data with caching and fallback.
    
    VIX-based position size caps (from professional trading research):
    - VIX < 15: Low volatility, cap at 1.2x (can take larger positions)
    - VIX 15-25: Normal volatility, cap at 1.0x (standard sizing)
    - VIX 25-35: High volatility, cap at 0.9x (reduce exposure)
    - VIX > 35: Extreme volatility, cap at 0.7x (conservative)
    """
    
    # VIX thresholds and corresponding caps
    VIX_LOW = 15.0
    VIX_NORMAL = 25.0
    VIX_HIGH = 35.0
    
    CAP_LOW_VOL = 1.2      # Can increase size in calm markets
    CAP_NORMAL_VOL = 1.0   # Standard sizing
    CAP_HIGH_VOL = 0.9     # Reduce in elevated volatility
    CAP_EXTREME_VOL = 0.7  # Conservative in extreme volatility
    
    # Default VIX when data unavailable
    DEFAULT_VIX = 20.0
    
    def __init__(self, cache_ttl_minutes: int = 15):
        """
        Initialize VIX provider with caching.
        
        Args:
            cache_ttl_minutes: How long to cache VIX data (default 15 minutes)
        """
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self._cached_vix: Optional[float] = None
        self._last_update: datetime = datetime.min
        self._alpaca_client = None
        
        logger.info(f"VIXDataProvider initialized with {cache_ttl_minutes}min cache TTL")
    
    def _get_alpaca_client(self):
        """Lazy load Alpaca client to avoid circular imports"""
        if self._alpaca_client is None:
            try:
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from core.alpaca_client import AlpacaClient
                self._alpaca_client = AlpacaClient()
            except Exception as e:
                logger.warning(f"Could not initialize Alpaca client: {e}")
        return self._alpaca_client
    
    def get_vix(self) -> float:
        """
        Get current VIX value with caching and fallback.
        
        Returns:
            Current VIX value, or default (20) if unavailable
        """
        now = datetime.now()
        
        # Return cached value if fresh
        if self._cached_vix is not None and (now - self._last_update) < self.cache_ttl:
            return self._cached_vix
        
        # Try to fetch fresh VIX data
        try:
            vix = self._fetch_vix()
            if vix is not None:
                self._cached_vix = vix
                self._last_update = now
                logger.info(f"VIX updated: {vix:.2f}")
                return vix
        except Exception as e:
            logger.warning(f"Error fetching VIX: {e}")
        
        # Return cached value if available, otherwise default
        if self._cached_vix is not None:
            logger.warning(f"Using stale VIX cache: {self._cached_vix:.2f}")
            return self._cached_vix
        
        logger.warning(f"VIX unavailable, using default: {self.DEFAULT_VIX}")
        return self.DEFAULT_VIX
    
    def _fetch_vix(self) -> Optional[float]:
        """
        Fetch VIX from data source.
        
        Returns:
            VIX value or None if unavailable
        """
        try:
            client = self._get_alpaca_client()
            if client is None:
                return None
            
            # Try to get VIX quote
            # VIX is typically available as ^VIX or VIX
            symbols_to_try = ["VIX", "^VIX", "VIXY"]
            
            for symbol in symbols_to_try:
                try:
                    # Use latest quote or bar
                    bars = client.get_bars(symbol, "1Day", limit=1)
                    if bars and len(bars) > 0:
                        vix = float(bars[0].c)  # Close price
                        if 5.0 <= vix <= 100.0:  # Sanity check
                            return vix
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching VIX: {e}")
            return None
    
    def get_vix_cap(self, vix: Optional[float] = None) -> float:
        """
        Get position size cap based on VIX level.
        
        Args:
            vix: VIX value (if None, fetches current)
            
        Returns:
            Position size cap multiplier (0.7 to 1.2)
        """
        if vix is None:
            vix = self.get_vix()
        
        return self._calculate_vix_cap(vix)
    
    def _calculate_vix_cap(self, vix: float) -> float:
        """
        Calculate position size cap from VIX value.
        
        Args:
            vix: VIX value
            
        Returns:
            Position size cap (0.7 to 1.2)
        """
        if vix < self.VIX_LOW:
            return self.CAP_LOW_VOL
        elif vix < self.VIX_NORMAL:
            return self.CAP_NORMAL_VOL
        elif vix < self.VIX_HIGH:
            return self.CAP_HIGH_VOL
        else:
            return self.CAP_EXTREME_VOL
    
    def get_vix_data(self) -> VIXData:
        """
        Get full VIX data with metadata.
        
        Returns:
            VIXData object with value, timestamp, and freshness
        """
        vix = self.get_vix()
        is_fresh = (datetime.now() - self._last_update) < self.cache_ttl
        
        return VIXData(
            value=vix,
            timestamp=self._last_update if self._last_update != datetime.min else datetime.now(),
            is_fresh=is_fresh,
            source="api" if is_fresh else "cache" if self._cached_vix else "default"
        )
    
    def get_vix_summary(self) -> dict:
        """
        Get summary of VIX status for logging/API.
        
        Returns:
            Dictionary with VIX value, cap, and classification
        """
        vix = self.get_vix()
        cap = self._calculate_vix_cap(vix)
        
        # Classify volatility level
        if vix < self.VIX_LOW:
            classification = "low"
        elif vix < self.VIX_NORMAL:
            classification = "normal"
        elif vix < self.VIX_HIGH:
            classification = "high"
        else:
            classification = "extreme"
        
        return {
            "vix": round(vix, 2),
            "cap": cap,
            "classification": classification,
            "is_fresh": (datetime.now() - self._last_update) < self.cache_ttl,
            "last_update": self._last_update.isoformat() if self._last_update != datetime.min else None
        }
    
    def set_vix_for_testing(self, vix: float):
        """
        Set VIX value for testing purposes.
        
        Args:
            vix: VIX value to set
        """
        self._cached_vix = vix
        self._last_update = datetime.now()
        logger.info(f"VIX set for testing: {vix:.2f}")
