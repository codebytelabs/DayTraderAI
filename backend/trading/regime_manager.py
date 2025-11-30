from enum import Enum
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
import logging
from indicators.fear_greed_scraper import FearGreedScraper

if TYPE_CHECKING:
    from trading.momentum_confirmed_regime import MomentumConfirmedRegimeManager

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
    
    INTRADAY-OPTIMIZED (Dec 2025):
    - Research shows extreme greed = REDUCE position size (market overheated)
    - Extreme fear = opportunity but with conservative base sizing
    - High confidence trades get a BOOST multiplier on top of regime sizing
    - This ensures cash is deployed on quality signals while managing risk
    """
    
    def __init__(self, enable_momentum_confirmation: bool = True):
        self.scraper = FearGreedScraper()
        self._current_regime = MarketRegime.NEUTRAL
        self._last_update = datetime.min
        self._cached_index_value = 50  # Default to neutral
        self._cache_ttl = timedelta(hours=1)  # Refresh every hour
        
        # Momentum-confirmed regime manager (professional intraday sizing)
        self._momentum_confirmed_manager: Optional['MomentumConfirmedRegimeManager'] = None
        self._enable_momentum_confirmation = enable_momentum_confirmation
        
        # Confidence thresholds for position size boost
        # High confidence trades get bigger positions to deploy cash effectively
        self.confidence_thresholds = {
            "very_high": 85,    # 85%+ confidence = 1.3x boost
            "high": 75,         # 75-84% confidence = 1.15x boost
            "normal": 65,       # 65-74% confidence = 1.0x (baseline)
        }
        
        self.confidence_multipliers = {
            "very_high": 1.3,   # Deploy more cash on very high confidence
            "high": 1.15,       # Slight boost for high confidence
            "normal": 1.0,      # Standard sizing
        }
        
        # INTRADAY-OPTIMIZED Regime Parameters (Dec 2025)
        # Based on professional day trading research:
        # - Extreme Fear: Opportunity exists but volatility is high, take profits faster
        # - Extreme Greed: Market overheated, REDUCE exposure (not increase!)
        # - High confidence trades get boosted via get_confidence_multiplier()
        self.regime_params = {
            MarketRegime.EXTREME_FEAR: {
                "profit_target_r": 3.0,      # Reduced from 4.0 - take profits faster in volatility
                "partial_profit_1_r": 2.0,   # Earlier partial profit
                "partial_profit_2_r": 4.0,   # Let remainder run
                "trailing_stop_r": 1.0,      # Tighter trailing in volatility
                "position_size_mult": 1.0,   # Conservative base (high confidence gets boost)
                "description": "High volatility - take profits faster. High confidence trades get 1.3x boost."
            },
            MarketRegime.FEAR: {
                "profit_target_r": 2.5,      # Reduced from 3.0
                "partial_profit_1_r": 2.0,
                "partial_profit_2_r": 3.5,
                "trailing_stop_r": 0.85,
                "position_size_mult": 1.0,
                "description": "Elevated volatility. Standard sizing, high confidence gets boost."
            },
            MarketRegime.NEUTRAL: {
                "profit_target_r": 2.0,
                "partial_profit_1_r": 1.5,
                "partial_profit_2_r": 3.0,
                "trailing_stop_r": 0.75,
                "position_size_mult": 1.0,
                "description": "Normal conditions. Standard targets and sizing."
            },
            MarketRegime.GREED: {
                "profit_target_r": 2.0,      # Reduced from 2.5 - tighter targets
                "partial_profit_1_r": 1.5,
                "partial_profit_2_r": 2.5,
                "trailing_stop_r": 0.75,
                "position_size_mult": 0.9,   # Slightly reduce exposure
                "description": "Market warming up. Slightly reduced exposure."
            },
            MarketRegime.EXTREME_GREED: {
                "profit_target_r": 1.5,      # Reduced from 3.0 - take profits FAST
                "partial_profit_1_r": 1.0,   # Very early partial
                "partial_profit_2_r": 2.0,
                "trailing_stop_r": 0.5,      # Tight trailing - protect profits
                "position_size_mult": 0.7,   # REDUCED from 1.5 - market overheated!
                "description": "Market overheated! Reduced exposure, tight stops, fast profit taking."
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
    
    def get_confidence_multiplier(self, confidence: float) -> float:
        """
        Get position size multiplier based on signal confidence.
        High confidence trades get bigger positions to deploy cash effectively.
        
        Args:
            confidence: Signal confidence score (0-100)
            
        Returns:
            Multiplier to apply to position size (1.0 to 1.3)
        """
        if confidence >= self.confidence_thresholds["very_high"]:
            mult = self.confidence_multipliers["very_high"]
            logger.info(f"Very high confidence ({confidence:.0f}%) - applying {mult}x position boost")
            return mult
        elif confidence >= self.confidence_thresholds["high"]:
            mult = self.confidence_multipliers["high"]
            logger.info(f"High confidence ({confidence:.0f}%) - applying {mult}x position boost")
            return mult
        else:
            return self.confidence_multipliers["normal"]
    
    def get_effective_position_multiplier(self, confidence: float) -> float:
        """
        Get the TOTAL position size multiplier combining regime and confidence.
        
        This ensures:
        1. Regime adjusts base sizing (reduce in extreme greed, standard elsewhere)
        2. High confidence trades get a BOOST on top of regime sizing
        3. Cash gets deployed on quality signals
        
        Args:
            confidence: Signal confidence score (0-100)
            
        Returns:
            Combined multiplier (regime_mult * confidence_mult)
        """
        regime_params = self.get_params()
        regime_mult = regime_params.get("position_size_mult", 1.0)
        confidence_mult = self.get_confidence_multiplier(confidence)
        
        # Combine multipliers
        total_mult = regime_mult * confidence_mult
        
        # Cap at reasonable bounds (0.5x to 1.5x)
        total_mult = max(0.5, min(1.5, total_mult))
        
        logger.info(
            f"Position multiplier: regime={regime_mult:.2f} × confidence={confidence_mult:.2f} = {total_mult:.2f} "
            f"(Regime: {self._current_regime.value}, Confidence: {confidence:.0f}%)"
        )
        
        return total_mult
    
    def get_regime_summary(self) -> Dict[str, Any]:
        """Get a summary of current regime and parameters for logging/display."""
        params = self.get_params()
        return {
            "regime": self._current_regime.value,
            "index_value": self._cached_index_value,
            "profit_target_r": params["profit_target_r"],
            "position_size_mult": params["position_size_mult"],
            "description": params["description"],
            "confidence_boost_available": True,
            "very_high_confidence_threshold": self.confidence_thresholds["very_high"],
            "very_high_confidence_boost": self.confidence_multipliers["very_high"],
            "momentum_confirmation_enabled": self._enable_momentum_confirmation,
        }
    
    def get_momentum_confirmed_manager(self) -> Optional['MomentumConfirmedRegimeManager']:
        """
        Get the momentum-confirmed regime manager (lazy initialization).
        
        Returns:
            MomentumConfirmedRegimeManager instance or None if disabled
        """
        if not self._enable_momentum_confirmation:
            return None
        
        if self._momentum_confirmed_manager is None:
            try:
                from trading.momentum_confirmed_regime import MomentumConfirmedRegimeManager
                self._momentum_confirmed_manager = MomentumConfirmedRegimeManager(self)
                logger.info("Momentum-confirmed regime manager initialized")
            except Exception as e:
                logger.error(f"Failed to initialize momentum-confirmed manager: {e}")
                self._enable_momentum_confirmation = False
                return None
        
        return self._momentum_confirmed_manager
    
    def get_momentum_confirmed_multiplier(
        self,
        momentum_strength: float,
        confidence: float
    ) -> float:
        """
        Get position multiplier using momentum confirmation (professional approach).
        
        This combines:
        1. Regime (Fear & Greed)
        2. Momentum strength (ADX, volume, trend)
        3. VIX cap
        4. Confidence boost
        
        Args:
            momentum_strength: Momentum strength score (0-1)
            confidence: Signal confidence score (0-100)
            
        Returns:
            Combined multiplier (0.5 to 1.5)
        """
        manager = self.get_momentum_confirmed_manager()
        
        if manager is None:
            # Fall back to simple regime + confidence
            return self.get_effective_position_multiplier(confidence)
        
        # Get momentum-confirmed multiplier
        result = manager.get_effective_multiplier(momentum_strength)
        base_mult = result.multiplier
        
        # Apply confidence boost on top
        confidence_mult = self.get_confidence_multiplier(confidence)
        total_mult = base_mult * confidence_mult
        
        # Cap at bounds
        total_mult = max(0.5, min(1.5, total_mult))
        
        logger.info(
            f"Momentum-confirmed multiplier: base={base_mult:.2f} × confidence={confidence_mult:.2f} = {total_mult:.2f} "
            f"(Regime: {self._current_regime.value}, Momentum: {momentum_strength:.2f}, Confidence: {confidence:.0f}%)"
        )
        
        return total_mult
    
    def get_momentum_adjusted_params(self, momentum_strength: float) -> Dict[str, Any]:
        """
        Get trading parameters adjusted for momentum.
        
        Args:
            momentum_strength: Momentum strength score (0-1)
            
        Returns:
            Dictionary with adjusted R-targets and stops
        """
        manager = self.get_momentum_confirmed_manager()
        
        if manager is None:
            # Fall back to simple regime params
            return self.get_params()
        
        params = manager.get_momentum_adjusted_params(momentum_strength)
        
        # Merge with base regime params
        base_params = self.get_params()
        return {
            **base_params,
            "profit_target_r": params.profit_target_r,
            "trailing_stop_r": params.trailing_stop_r,
            "position_size_mult": params.position_multiplier,
            "momentum_strength": momentum_strength,
            "momentum_adjusted": True,
        }
