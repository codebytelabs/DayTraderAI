"""
Momentum-Confirmed Regime Manager - Professional intraday position sizing.

Combines Fear & Greed regime with real-time momentum confirmation and VIX caps
to make smarter position sizing decisions that match professional trading practices.

Key insight from research:
- Extreme greed + strong momentum = ride the wave (1.2x)
- Extreme greed + weak momentum = protect against reversal (0.7x)
- Extreme fear = always conservative with wider stops
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.regime_manager import RegimeManager, MarketRegime
from trading.momentum_strength import MomentumStrengthCalculator, MomentumStrengthResult
from trading.vix_provider import VIXDataProvider

logger = logging.getLogger(__name__)


@dataclass
class EffectiveMultiplierResult:
    """Result of effective multiplier calculation"""
    
    # Final multiplier (bounded 0.5 to 1.5)
    multiplier: float
    
    # Component multipliers
    regime_multiplier: float
    momentum_multiplier: float
    vix_cap: float
    
    # Context
    regime: MarketRegime
    momentum_strength: float
    vix_level: float
    
    # Reasoning for audit
    reasoning: str
    
    # Raw (unbounded) multiplier
    raw_multiplier: float = 1.0
    
    def to_dict(self) -> dict:
        return {
            "multiplier": round(self.multiplier, 3),
            "regime_multiplier": round(self.regime_multiplier, 3),
            "momentum_multiplier": round(self.momentum_multiplier, 3),
            "vix_cap": round(self.vix_cap, 3),
            "raw_multiplier": round(self.raw_multiplier, 3),
            "regime": self.regime.value,
            "momentum_strength": round(self.momentum_strength, 3),
            "vix_level": round(self.vix_level, 2),
            "reasoning": self.reasoning
        }


@dataclass
class MomentumAdjustedParams:
    """Trading parameters adjusted for momentum"""
    
    profit_target_r: float
    trailing_stop_r: float
    position_multiplier: float
    
    regime: MarketRegime
    momentum_strength: float
    
    # Base values before adjustment
    base_profit_target_r: float = 2.0
    base_trailing_stop_r: float = 0.75
    
    def to_dict(self) -> dict:
        return {
            "profit_target_r": round(self.profit_target_r, 2),
            "trailing_stop_r": round(self.trailing_stop_r, 2),
            "position_multiplier": round(self.position_multiplier, 3),
            "regime": self.regime.value,
            "momentum_strength": round(self.momentum_strength, 3),
            "base_profit_target_r": self.base_profit_target_r,
            "base_trailing_stop_r": self.base_trailing_stop_r
        }


class MomentumConfirmedRegimeManager:
    """
    Combines regime, momentum, and VIX for professional position sizing.
    
    Position Sizing Logic (from professional trading research):
    
    EXTREME GREED:
    - Strong momentum (>0.8): 1.2x - ride the wave
    - Medium momentum (0.5-0.8): 0.9x - cautious
    - Weak momentum (<0.5): 0.7x - high reversal risk
    
    EXTREME FEAR:
    - Strong momentum (>0.7): 1.0x - standard
    - Weak momentum (<=0.7): 0.8x - conservative
    
    OTHER REGIMES:
    - Use base regime multiplier from RegimeManager
    
    VIX CAPS:
    - VIX < 15: Allow up to 1.2x
    - VIX 15-25: Standard 1.0x
    - VIX 25-35: Cap at 0.9x
    - VIX > 35: Cap at 0.7x
    
    FINAL MULTIPLIER:
    - regime_mult × momentum_mult × min(1.0, vix_cap)
    - Bounded to [0.5, 1.5]
    """
    
    # Multiplier bounds
    MIN_MULTIPLIER = 0.5
    MAX_MULTIPLIER = 1.5
    
    # Momentum thresholds
    STRONG_MOMENTUM = 0.8
    MEDIUM_MOMENTUM = 0.5
    FEAR_MOMENTUM_THRESHOLD = 0.7
    
    # Extreme greed multipliers
    EXTREME_GREED_STRONG = 1.2
    EXTREME_GREED_MEDIUM = 0.9
    EXTREME_GREED_WEAK = 0.7
    
    # Extreme fear multipliers
    EXTREME_FEAR_STRONG = 1.0
    EXTREME_FEAR_WEAK = 0.8
    
    # R-target adjustments
    R_TARGET_STRONG_BOOST = 0.5
    R_TARGET_WEAK_REDUCTION = 0.5
    EXTREME_FEAR_R_CAP = 2.0
    
    # Trailing stop settings
    EXTREME_GREED_TIGHT_STOP = 0.5
    EXTREME_FEAR_WIDE_STOP = 1.0
    
    def __init__(self, regime_manager: Optional[RegimeManager] = None):
        """
        Initialize with optional existing RegimeManager.
        
        Args:
            regime_manager: Existing RegimeManager instance (creates new if None)
        """
        self.regime_manager = regime_manager or RegimeManager()
        self.momentum_calculator = MomentumStrengthCalculator()
        self.vix_provider = VIXDataProvider()
        
        logger.info("MomentumConfirmedRegimeManager initialized")
    
    def get_momentum_multiplier(
        self,
        regime: MarketRegime,
        momentum_strength: float
    ) -> float:
        """
        Get position multiplier based on regime and momentum.
        
        Args:
            regime: Current market regime
            momentum_strength: Momentum strength score (0-1)
            
        Returns:
            Position multiplier (before VIX cap)
        """
        if regime == MarketRegime.EXTREME_GREED:
            if momentum_strength > self.STRONG_MOMENTUM:
                return self.EXTREME_GREED_STRONG
            elif momentum_strength >= self.MEDIUM_MOMENTUM:
                return self.EXTREME_GREED_MEDIUM
            else:
                return self.EXTREME_GREED_WEAK
        
        elif regime == MarketRegime.EXTREME_FEAR:
            if momentum_strength > self.FEAR_MOMENTUM_THRESHOLD:
                return self.EXTREME_FEAR_STRONG
            else:
                return self.EXTREME_FEAR_WEAK
        
        else:
            # For other regimes, use base regime multiplier
            params = self.regime_manager.get_params(regime)
            return params.get("position_size_mult", 1.0)
    
    def get_effective_multiplier(
        self,
        momentum_strength: float,
        vix: Optional[float] = None,
        regime: Optional[MarketRegime] = None
    ) -> EffectiveMultiplierResult:
        """
        Calculate effective position multiplier combining all factors.
        
        Args:
            momentum_strength: Momentum strength score (0-1)
            vix: VIX value (fetches current if None)
            regime: Market regime (uses current if None)
            
        Returns:
            EffectiveMultiplierResult with multiplier and breakdown
        """
        # Get current regime if not provided
        if regime is None:
            regime = self.regime_manager.get_current_regime()
        
        # Get VIX if not provided
        if vix is None:
            vix = self.vix_provider.get_vix()
        
        # Get component multipliers
        regime_params = self.regime_manager.get_params(regime)
        regime_mult = regime_params.get("position_size_mult", 1.0)
        momentum_mult = self.get_momentum_multiplier(regime, momentum_strength)
        vix_cap = self.vix_provider._calculate_vix_cap(vix)
        
        # Calculate raw multiplier
        # For extreme regimes, momentum_mult replaces regime_mult
        if regime in [MarketRegime.EXTREME_GREED, MarketRegime.EXTREME_FEAR]:
            raw_mult = momentum_mult * min(1.0, vix_cap)
        else:
            raw_mult = regime_mult * min(1.0, vix_cap)
        
        # Apply bounds
        final_mult = max(self.MIN_MULTIPLIER, min(self.MAX_MULTIPLIER, raw_mult))
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            regime, momentum_strength, vix, regime_mult, momentum_mult, vix_cap, final_mult
        )
        
        result = EffectiveMultiplierResult(
            multiplier=final_mult,
            regime_multiplier=regime_mult,
            momentum_multiplier=momentum_mult,
            vix_cap=vix_cap,
            regime=regime,
            momentum_strength=momentum_strength,
            vix_level=vix,
            reasoning=reasoning,
            raw_multiplier=raw_mult
        )
        
        logger.info(f"Effective multiplier: {final_mult:.2f}x | {reasoning}")
        
        return result
    
    def _generate_reasoning(
        self,
        regime: MarketRegime,
        momentum: float,
        vix: float,
        regime_mult: float,
        momentum_mult: float,
        vix_cap: float,
        final_mult: float
    ) -> str:
        """Generate human-readable reasoning for the multiplier decision."""
        
        parts = [f"Regime={regime.value}"]
        
        if regime == MarketRegime.EXTREME_GREED:
            if momentum > self.STRONG_MOMENTUM:
                parts.append(f"Strong momentum ({momentum:.2f}) → ride wave")
            elif momentum >= self.MEDIUM_MOMENTUM:
                parts.append(f"Medium momentum ({momentum:.2f}) → cautious")
            else:
                parts.append(f"Weak momentum ({momentum:.2f}) → reversal risk")
        elif regime == MarketRegime.EXTREME_FEAR:
            if momentum > self.FEAR_MOMENTUM_THRESHOLD:
                parts.append(f"Strong momentum ({momentum:.2f}) → standard")
            else:
                parts.append(f"Weak momentum ({momentum:.2f}) → conservative")
        else:
            parts.append(f"Momentum={momentum:.2f}")
        
        if vix_cap < 1.0:
            parts.append(f"VIX={vix:.1f} (capped)")
        else:
            parts.append(f"VIX={vix:.1f}")
        
        parts.append(f"Final={final_mult:.2f}x")
        
        return " | ".join(parts)
    
    def get_momentum_adjusted_params(
        self,
        momentum_strength: float,
        regime: Optional[MarketRegime] = None
    ) -> MomentumAdjustedParams:
        """
        Get trading parameters adjusted for momentum.
        
        Args:
            momentum_strength: Momentum strength score (0-1)
            regime: Market regime (uses current if None)
            
        Returns:
            MomentumAdjustedParams with R-targets and stops
        """
        if regime is None:
            regime = self.regime_manager.get_current_regime()
        
        # Get base params from regime
        base_params = self.regime_manager.get_params(regime)
        base_r_target = base_params.get("profit_target_r", 2.0)
        base_trailing = base_params.get("trailing_stop_r", 0.75)
        
        # Adjust R-target based on momentum
        r_target = base_r_target
        if momentum_strength > self.STRONG_MOMENTUM:
            r_target += self.R_TARGET_STRONG_BOOST
        elif momentum_strength < self.MEDIUM_MOMENTUM:
            r_target -= self.R_TARGET_WEAK_REDUCTION
        
        # Cap R-target in extreme fear
        if regime == MarketRegime.EXTREME_FEAR:
            r_target = min(r_target, self.EXTREME_FEAR_R_CAP)
        
        # Ensure minimum R-target
        r_target = max(1.0, r_target)
        
        # Adjust trailing stop
        trailing = base_trailing
        if regime == MarketRegime.EXTREME_FEAR:
            trailing = self.EXTREME_FEAR_WIDE_STOP
        elif regime == MarketRegime.EXTREME_GREED and momentum_strength > self.STRONG_MOMENTUM:
            trailing = self.EXTREME_GREED_TIGHT_STOP
        
        # Get position multiplier
        multiplier_result = self.get_effective_multiplier(momentum_strength, regime=regime)
        
        return MomentumAdjustedParams(
            profit_target_r=r_target,
            trailing_stop_r=trailing,
            position_multiplier=multiplier_result.multiplier,
            regime=regime,
            momentum_strength=momentum_strength,
            base_profit_target_r=base_r_target,
            base_trailing_stop_r=base_trailing
        )
    
    def get_summary(self, momentum_strength: Optional[float] = None) -> Dict[str, Any]:
        """
        Get comprehensive summary of current state.
        
        Args:
            momentum_strength: Momentum strength (uses 0.5 default if None)
            
        Returns:
            Dictionary with all current values and decisions
        """
        if momentum_strength is None:
            momentum_strength = 0.5  # Neutral default
        
        regime = self.regime_manager.get_current_regime()
        vix_summary = self.vix_provider.get_vix_summary()
        multiplier_result = self.get_effective_multiplier(momentum_strength)
        params = self.get_momentum_adjusted_params(momentum_strength)
        
        return {
            "regime": regime.value,
            "fear_greed_index": self.regime_manager.get_current_index_value(),
            "momentum_strength": momentum_strength,
            "vix": vix_summary,
            "effective_multiplier": multiplier_result.to_dict(),
            "adjusted_params": params.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
