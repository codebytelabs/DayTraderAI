"""VIX Fetcher - Get real VIX volatility data."""

import requests
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VIXFetcher:
    """Fetch real VIX (CBOE Volatility Index) data."""
    
    def __init__(self):
        self.last_vix = None
        self.cache_duration = 300  # 5 minutes
        self.last_fetch_time = 0
    
    def get_vix(self) -> Optional[float]:
        """
        Get current VIX value.
        
        Returns:
            float: VIX value (e.g., 18.27) or None if unavailable
        """
        import time
        
        # Use cache if recent
        if self.last_vix and (time.time() - self.last_fetch_time) < self.cache_duration:
            return self.last_vix
        
        try:
            # Try Yahoo Finance API (free, no key needed)
            url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"
            params = {
                'interval': '1d',
                'range': '1d'
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract current VIX value
            result = data.get('chart', {}).get('result', [{}])[0]
            meta = result.get('meta', {})
            vix_value = meta.get('regularMarketPrice')
            
            if vix_value:
                self.last_vix = float(vix_value)
                self.last_fetch_time = time.time()
                logger.info(f"✓ VIX fetched: {self.last_vix:.2f}")
                return self.last_vix
            
            logger.warning("⚠️  VIX data not found in response")
            return self._get_fallback_vix()
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to fetch VIX: {e}")
            return self._get_fallback_vix()
    
    def _get_fallback_vix(self) -> float:
        """
        Fallback VIX estimate.
        
        Returns:
            float: Conservative estimate of 20.0 (historical average)
        """
        if self.last_vix:
            logger.info(f"Using cached VIX: {self.last_vix:.2f}")
            return self.last_vix
        
        logger.info("Using default VIX: 20.0 (historical average)")
        return 20.0


# Singleton instance
_vix_fetcher = None

def get_vix_fetcher() -> VIXFetcher:
    """Get singleton VIX fetcher instance."""
    global _vix_fetcher
    if _vix_fetcher is None:
        _vix_fetcher = VIXFetcher()
    return _vix_fetcher
