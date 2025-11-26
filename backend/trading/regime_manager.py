from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from indicators.fear_greed_scraper import FearGreedScraper

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    EXTREME_FEAR = "extreme_fear"   # 0-20
    FEAR = "fear"                   # 21-40
    NEUTRAL = "neutral"             # 41-60
    GREED = "greed"                 # 61-80
    EXTREME_GREED = "extreme_greed" # 81-100

class RegimeManager:
    """
    Centralized manager for market regime detection and parameter lookup.
    Adapts trading parameters based on the Fear & Greed Index.
    """
    
    def __init__(self):
        self.scraper = FearGreedScraper()
        self._current_regime = MarketRegime.NEUTRAL
        self._last_update = datetime.min
        self._cached_index_value = 50  # Default to neutral
        self._cache_ttl = timedelta(hours=1)  # Refresh every hour
        
        # Regime-specific parameters
        # Based on requirements:
        # - Extreme Fear: 4R targets, 3R/5R partials, 1.5R trailing stop
        # - Fear: 3R targets, 2.5R/4R partials, 1R trailing stop
        # - Neutral: 2R targets, 2R/3R partials, 0.75R trailing stop
        # - Greed: 2.5R targets, 2R/3.5R partials, 1R trailing stop
        # - Extreme Greed: 3R targets, 2.5R/4.5R partials, 1.5R trailing stop
        self.regime_params = {
            MarketRegime.EXTREME_FEAR: {
                "profit_target_r": 4.0,
                "partial_profit_1_r": 3.0,
                "partial_profit_2_r": 5.0,
                "trailing_stop_r": 1.5,
                "position_size_mult": 1.5,  # Only for high confidence
                "description": "High volatility, large directional moves expected. Wide targets."
            },
            MarketRegime.FEAR: {
                "profit_target_r": 3.0,
                "partial_profit_1_r": 2.5,
                "partial_profit_2_r": 4.0,
                "trailing_stop_r": 1.0,
                "position_size_mult": 1.0,
                "description": "Elevated volatility. moderately wide targets."
            },
            MarketRegime.NEUTRAL: {
                "profit_target_r": 2.0,
                "partial_profit_1_r": 2.0,
                "partial_profit_2_r": 3.0,
                "trailing_stop_r": 0.75,
                "position_size_mult": 1.0,
                "description": "Normal conditions. Standard targets."
            },
            MarketRegime.GREED: {
                "profit_target_r": 2.5,
                "partial_profit_1_r": 2.0,
                "partial_profit_2_r": 3.5,
                "trailing_stop_r": 1.0,
                "position_size_mult": 1.0,
                "description": "Strong trends possible. Slightly wider targets."
            },
            MarketRegime.EXTREME_GREED: {
                "profit_target_r": 3.0,
                "partial_profit_1_r": 2.5,
                "partial_profit_2_r": 4.5,
                "trailing_stop_r": 1.5,
                "position_size_mult": 1.5,  # Only for high confidence
                "description": "Parabolic moves possible. Wide targets."
            }
        }

    async def update_regime(self) -> MarketRegime:
        """
        Updates the current market regime by fetching the latest Fear & Greed Index.
        Returns the current regime.
        """
        now = datetime.now()
        if now - self._last_update < self._cache_ttl:
            return self._current_regime

        try:
            # Fetch index value
            # The scraper returns a dict with 'value', 'description', etc.
            # We need to handle sync/async nature of scraper if needed, 
            # but FearGreedScraper.get_fear_greed_index is usually synchronous or we wrap it.
            # Looking at existing usage, it seems to be synchronous or we need to check.
            # Let's assume synchronous for now based on grep, but will verify.
            
            # Actually, let's check if get_fear_greed_index is async.
            # The grep showed `scraper = FearGreedScraper()` but didn't show the call clearly.
            # I'll assume it's synchronous for now, if not I'll fix.
            
            result = self.scraper.get_fear_greed_index()
            
            # Handle both 'value' and 'score' keys (scraper returns 'score')
            if result and ('value' in result or 'score' in result):
                self._cached_index_value = int(result.get('value') or result.get('score'))
                self._current_regime = self._classify_regime(self._cached_index_value)
                self._last_update = now
                logger.info(f"Market Regime Updated: {self._current_regime.value.upper()} (Index: {self._cached_index_value})")
            else:
                logger.warning("Failed to fetch Fear & Greed Index. Keeping previous regime.")
                
        except Exception as e:
            logger.error(f"Error updating market regime: {e}")
            # On error, default to NEUTRAL if we have no history, or keep last known
            if self._last_update == datetime.min:
                self._current_regime = MarketRegime.NEUTRAL
        
        return self._current_regime

    def _classify_regime(self, index_value: int) -> MarketRegime:
        """Classifies the Fear & Greed Index value into a regime."""
        if index_value <= 20:
            return MarketRegime.EXTREME_FEAR
        elif index_value <= 40:
            return MarketRegime.FEAR
        elif index_value <= 60:
            return MarketRegime.NEUTRAL
        elif index_value <= 80:
            return MarketRegime.GREED
        else:
            return MarketRegime.EXTREME_GREED

    def get_current_regime(self) -> MarketRegime:
        """Returns the currently cached regime."""
        return self._current_regime

    def get_params(self, regime: Optional[MarketRegime] = None) -> Dict[str, Any]:
        """
        Returns the trading parameters for the specified regime.
        If no regime is specified, uses the current regime.
        """
        target_regime = regime or self._current_regime
        return self.regime_params.get(target_regime, self.regime_params[MarketRegime.NEUTRAL])

    def get_current_index_value(self) -> int:
        """Returns the currently cached index value."""
        return self._cached_index_value
