#!/usr/bin/env python3
"""
Momentum Wave Exit System
=========================
Exits positions when momentum weakens, not at fixed targets.

Your Strategy: "Ride waves, get off when momentum reduces"

This system:
1. Classifies wave strength (tsunami, strong, medium, weak)
2. Tracks momentum decay in real-time
3. Exits when momentum drops X% from peak (not at fixed R targets)
4. Lets winners run while cutting losers fast
"""

import logging
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class WaveStrength(Enum):
    """Wave strength classification"""
    TSUNAMI = "tsunami"      # 10R+ potential, ride until momentum breaks
    STRONG = "strong"        # 5-10R potential
    MEDIUM = "medium"        # 2-5R potential
    WEAK = "weak"            # 1-2R quick scalp


@dataclass
class WaveMetrics:
    """Track wave momentum metrics for a position"""
    symbol: str
    entry_time: datetime
    peak_momentum: float
    current_momentum: float
    momentum_history: List[float] = field(default_factory=list)
    wave_strength: WaveStrength = WaveStrength.MEDIUM
    r_multiple: float = 0.0
    peak_r_multiple: float = 0.0
    volume_surge: float = 1.0
    
    def momentum_decay_ratio(self) -> float:
        """Calculate current momentum as ratio of peak"""
        if self.peak_momentum <= 0:
            return 1.0
        return self.current_momentum / self.peak_momentum


class MomentumWaveExit:
    """
    Dynamic exit system based on momentum decay.
    
    Instead of fixed 2R/3R/4R targets, this system:
    - Tracks momentum strength in real-time
    - Exits when momentum decays significantly from peak
    - Lets strong waves run to 5R, 10R, 15R+
    - Cuts weak waves quickly at 1-2R
    """
    
    def __init__(self):
        self.wave_metrics: Dict[str, WaveMetrics] = {}
        
        # Momentum decay thresholds by wave strength
        self.decay_thresholds = {
            WaveStrength.TSUNAMI: 0.50,  # Exit when momentum drops 50% from peak
            WaveStrength.STRONG: 0.60,   # Exit when momentum drops 40% from peak
            WaveStrength.MEDIUM: 0.70,   # Exit when momentum drops 30% from peak
            WaveStrength.WEAK: 0.80,     # Exit when momentum drops 20% from peak
        }
        
        # Minimum R-multiple before momentum exit kicks in
        self.min_r_for_momentum_exit = {
            WaveStrength.TSUNAMI: 5.0,   # Let tsunami waves run to at least 5R
            WaveStrength.STRONG: 3.0,    # Strong waves to at least 3R
            WaveStrength.MEDIUM: 2.0,    # Medium waves to at least 2R
            WaveStrength.WEAK: 1.5,      # Weak waves quick exit at 1.5R
        }
        
        # Minimum hold time before momentum exit
        self.min_hold_time = timedelta(minutes=5)
        
        logger.info("🌊 Momentum Wave Exit System initialized")
        logger.info("   • Tsunami waves: Exit on 50% momentum decay, min 5R")
        logger.info("   • Strong waves: Exit on 40% momentum decay, min 3R")
        logger.info("   • Medium waves: Exit on 30% momentum decay, min 2R")
        logger.info("   • Weak waves: Exit on 20% momentum decay, min 1.5R")
    
    def classify_wave_strength(
        self, 
        momentum: float, 
        volume_ratio: float,
        confidence: float = 70.0
    ) -> WaveStrength:
        """
        Classify wave strength for dynamic targets.
        
        Args:
            momentum: Momentum score (0-10+)
            volume_ratio: Volume vs average (1.0 = normal)
            confidence: Signal confidence (0-100)
            
        Returns:
            WaveStrength classification
        """
        # Tsunami: Very high momentum + volume surge + high confidence
        if momentum > 8.0 and volume_ratio >= 3.0 and confidence >= 80:
            return WaveStrength.TSUNAMI
        
        # Strong: High momentum + good volume
        if momentum > 5.0 and volume_ratio >= 2.0:
            return WaveStrength.STRONG
        
        # Medium: Decent momentum
        if momentum > 3.0:
            return WaveStrength.MEDIUM
        
        # Weak: Low momentum - quick scalp
        return WaveStrength.WEAK
    
    def start_tracking(
        self,
        symbol: str,
        initial_momentum: float,
        volume_ratio: float = 1.0,
        confidence: float = 70.0
    ) -> WaveStrength:
        """
        Start tracking a new position's momentum.
        
        Args:
            symbol: Stock symbol
            initial_momentum: Initial momentum score
            volume_ratio: Volume surge ratio
            confidence: Signal confidence
            
        Returns:
            Classified wave strength
        """
        wave_strength = self.classify_wave_strength(
            initial_momentum, volume_ratio, confidence
        )
        
        self.wave_metrics[symbol] = WaveMetrics(
            symbol=symbol,
            entry_time=datetime.now(),
            peak_momentum=initial_momentum,
            current_momentum=initial_momentum,
            momentum_history=[initial_momentum],
            wave_strength=wave_strength,
            volume_surge=volume_ratio
        )
        
        logger.info(
            f"🌊 New {wave_strength.value.upper()} wave: {symbol} "
            f"| Momentum: {initial_momentum:.2f} "
            f"| Volume: {volume_ratio:.1f}x "
            f"| Confidence: {confidence:.0f}%"
        )
        
        return wave_strength
    
    def update_metrics(
        self,
        symbol: str,
        current_momentum: float,
        r_multiple: float
    ) -> Optional[WaveMetrics]:
        """
        Update momentum tracking for a position.
        
        Args:
            symbol: Stock symbol
            current_momentum: Current momentum score
            r_multiple: Current R-multiple
            
        Returns:
            Updated WaveMetrics or None if not tracking
        """
        if symbol not in self.wave_metrics:
            # Auto-start tracking with default values
            self.start_tracking(symbol, current_momentum)
        
        metrics = self.wave_metrics[symbol]
        metrics.current_momentum = current_momentum
        metrics.r_multiple = r_multiple
        metrics.momentum_history.append(current_momentum)
        
        # Keep history manageable
        if len(metrics.momentum_history) > 60:
            metrics.momentum_history = metrics.momentum_history[-60:]
        
        # Update peak momentum
        if current_momentum > metrics.peak_momentum:
            metrics.peak_momentum = current_momentum
            logger.info(
                f"🚀 {symbol} wave strengthening: "
                f"{current_momentum:.2f} (new peak)"
            )
        
        # Update peak R-multiple
        if r_multiple > metrics.peak_r_multiple:
            metrics.peak_r_multiple = r_multiple
        
        return metrics
    
    def should_exit_on_momentum_decay(
        self,
        symbol: str
    ) -> Tuple[bool, str]:
        """
        Check if position should exit due to momentum decay.
        
        This is the core of "ride waves, get off when momentum reduces".
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Tuple of (should_exit, reason)
        """
        if symbol not in self.wave_metrics:
            return False, "No metrics available"
        
        metrics = self.wave_metrics[symbol]
        
        # Don't exit too early
        hold_time = datetime.now() - metrics.entry_time
        if hold_time < self.min_hold_time:
            return False, f"Min hold time not reached ({hold_time.seconds}s < {self.min_hold_time.seconds}s)"
        
        # Get thresholds for this wave strength
        decay_threshold = self.decay_thresholds[metrics.wave_strength]
        min_r = self.min_r_for_momentum_exit[metrics.wave_strength]
        
        # Check if we've reached minimum R for this wave type
        if metrics.r_multiple < min_r:
            return False, f"Below min R ({metrics.r_multiple:.2f}R < {min_r}R)"
        
        # Calculate momentum decay
        decay_ratio = metrics.momentum_decay_ratio()
        
        # Check for momentum decay exit
        if decay_ratio < decay_threshold:
            reason = (
                f"🌊 MOMENTUM EXIT: {metrics.wave_strength.value} wave "
                f"momentum collapsed {decay_ratio:.0%} of peak "
                f"(threshold: {decay_threshold:.0%}) "
                f"| R: {metrics.r_multiple:.2f} | Peak R: {metrics.peak_r_multiple:.2f}"
            )
            return True, reason
        
        return False, f"Momentum still strong ({decay_ratio:.0%} of peak)"
    
    def get_dynamic_target(self, symbol: str) -> Optional[float]:
        """
        Get dynamic R-multiple target based on wave strength.
        
        Unlike fixed 2R targets, this returns higher targets for stronger waves.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Target R-multiple or None
        """
        if symbol not in self.wave_metrics:
            return 2.0  # Default
        
        wave_strength = self.wave_metrics[symbol].wave_strength
        
        # Dynamic targets based on wave strength
        targets = {
            WaveStrength.TSUNAMI: 10.0,  # Let tsunami waves run to 10R+
            WaveStrength.STRONG: 6.0,    # Strong waves to 6R
            WaveStrength.MEDIUM: 3.0,    # Medium waves to 3R
            WaveStrength.WEAK: 1.5,      # Quick scalp at 1.5R
        }
        
        return targets.get(wave_strength, 2.0)
    
    def get_partial_profit_schedule(self, symbol: str) -> Dict[float, float]:
        """
        Get dynamic partial profit schedule based on wave strength.
        
        Stronger waves = later profit taking to let them run.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict mapping R-multiple to percentage to take
        """
        if symbol not in self.wave_metrics:
            # Default schedule
            return {2.0: 0.50, 3.0: 0.25, 4.0: 0.25}
        
        wave_strength = self.wave_metrics[symbol].wave_strength
        
        schedules = {
            WaveStrength.TSUNAMI: {
                5.0: 0.25,   # Take 25% at 5R
                8.0: 0.25,   # Take 25% at 8R
                10.0: 0.25,  # Take 25% at 10R
                # Let final 25% ride until momentum breaks
            },
            WaveStrength.STRONG: {
                3.0: 0.33,   # Take 33% at 3R
                5.0: 0.33,   # Take 33% at 5R
                # Let final 33% ride
            },
            WaveStrength.MEDIUM: {
                2.0: 0.50,   # Take 50% at 2R
                3.0: 0.25,   # Take 25% at 3R
                4.0: 0.25,   # Take final 25% at 4R
            },
            WaveStrength.WEAK: {
                1.5: 0.75,   # Take 75% at 1.5R (quick scalp)
                2.0: 0.25,   # Take remaining at 2R
            },
        }
        
        return schedules.get(wave_strength, {2.0: 0.50, 3.0: 0.25, 4.0: 0.25})
    
    def cleanup_position(self, symbol: str):
        """
        Clean up tracking when position is closed.
        
        Args:
            symbol: Stock symbol
        """
        if symbol in self.wave_metrics:
            metrics = self.wave_metrics[symbol]
            logger.info(
                f"🏁 Wave ride complete: {symbol} "
                f"| {metrics.wave_strength.value} wave "
                f"| Peak momentum: {metrics.peak_momentum:.2f} "
                f"| Final R: {metrics.r_multiple:.2f} "
                f"| Peak R: {metrics.peak_r_multiple:.2f}"
            )
            del self.wave_metrics[symbol]
    
    def get_wave_status(self, symbol: str) -> Optional[Dict]:
        """
        Get current wave status for a position.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with wave status or None
        """
        if symbol not in self.wave_metrics:
            return None
        
        metrics = self.wave_metrics[symbol]
        
        return {
            'symbol': symbol,
            'wave_strength': metrics.wave_strength.value,
            'current_momentum': metrics.current_momentum,
            'peak_momentum': metrics.peak_momentum,
            'momentum_decay': metrics.momentum_decay_ratio(),
            'r_multiple': metrics.r_multiple,
            'peak_r_multiple': metrics.peak_r_multiple,
            'hold_time_minutes': (datetime.now() - metrics.entry_time).seconds / 60,
            'dynamic_target': self.get_dynamic_target(symbol),
        }
    
    def get_all_wave_statuses(self) -> List[Dict]:
        """Get status of all tracked waves."""
        return [
            self.get_wave_status(symbol) 
            for symbol in self.wave_metrics.keys()
        ]


# Global instance
_wave_exit_system: Optional[MomentumWaveExit] = None


def get_wave_exit_system() -> MomentumWaveExit:
    """Get or create the global wave exit system instance."""
    global _wave_exit_system
    
    if _wave_exit_system is None:
        _wave_exit_system = MomentumWaveExit()
    
    return _wave_exit_system
