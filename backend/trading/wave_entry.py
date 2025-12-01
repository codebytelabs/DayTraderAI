#!/usr/bin/env python3
"""
Wave Entry Engine - Optimize entry timing for momentum waves

This engine helps catch waves early rather than chasing extended moves.
It classifies crossovers, calculates entry bonuses, and checks timeframe alignment.

Key concepts:
- Fresh crossover (0.05-0.3%): Ideal entry, wave just starting
- Developing crossover (0.3-1.0%): Acceptable, wave in progress
- Extended crossover (>1.0%): Risky, wave may be ending
"""

import logging
from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CrossoverType(Enum):
    """EMA crossover classification."""
    FRESH = "fresh"           # 0.05-0.3% - ideal entry
    DEVELOPING = "developing"  # 0.3-1.0% - acceptable
    EXTENDED = "extended"      # >1.0% - reduce confidence


class EntryQuality(Enum):
    """Overall entry quality classification."""
    IDEAL = "ideal"
    ACCEPTABLE = "acceptable"
    POOR = "poor"


@dataclass
class EntryAnalysis:
    """Result of entry timing analysis."""
    crossover_type: CrossoverType
    entry_quality: EntryQuality
    confidence_adjustment: int  # Points to add/subtract from confidence
    vwap_bonus: int  # Bonus for VWAP proximity
    timeframe_bonus: int  # Bonus for multi-TF alignment
    should_enter: bool
    reason: str


class WaveEntryEngine:
    """
    Entry timing optimization for momentum waves.
    Catches waves early, avoids chasing extended moves.
    """
    
    # Crossover thresholds (EMA9 - EMA21 as percentage)
    FRESH_MIN = 0.05
    FRESH_MAX = 0.3
    DEVELOPING_MAX = 1.0
    
    # Penalties and bonuses
    EXTENDED_PENALTY = 15  # -15 points for extended moves
    VWAP_BONUS = 5         # +5 points for VWAP proximity
    TIMEFRAME_BONUS = 10   # +10 points for multi-TF alignment
    
    # VWAP proximity threshold
    VWAP_PROXIMITY_PCT = 0.5  # Within 0.5% of VWAP
    
    # ADX threshold
    MIN_ADX = 20
    
    def __init__(self):
        logger.info("✅ WaveEntryEngine initialized")
    
    def analyze_entry(self, features: Dict) -> EntryAnalysis:
        """
        Analyze entry timing for a potential trade.
        
        Args:
            features: Dictionary with technical indicators
            
        Returns:
            EntryAnalysis with classification and adjustments
        """
        ema_diff = features.get('ema_diff', 0.0)
        vwap_distance = features.get('vwap_distance', 1.0)
        adx = features.get('adx', 0.0)
        multi_tf_aligned = features.get('multi_tf_aligned', False)
        
        # Classify crossover
        crossover_type = self.classify_crossover(ema_diff)
        
        # Calculate adjustments
        confidence_adjustment = 0
        
        # Extended penalty
        if crossover_type == CrossoverType.EXTENDED:
            confidence_adjustment -= self.EXTENDED_PENALTY
        
        # VWAP bonus
        vwap_bonus = self.calculate_entry_bonus(vwap_distance)
        confidence_adjustment += vwap_bonus
        
        # Timeframe bonus
        timeframe_bonus = self.TIMEFRAME_BONUS if multi_tf_aligned else 0
        confidence_adjustment += timeframe_bonus
        
        # Determine entry quality
        entry_quality = self._determine_entry_quality(crossover_type, vwap_bonus > 0, multi_tf_aligned)
        
        # Should we enter?
        should_enter, reason = self._should_enter(crossover_type, adx, entry_quality)
        
        return EntryAnalysis(
            crossover_type=crossover_type,
            entry_quality=entry_quality,
            confidence_adjustment=confidence_adjustment,
            vwap_bonus=vwap_bonus,
            timeframe_bonus=timeframe_bonus,
            should_enter=should_enter,
            reason=reason
        )
    
    def classify_crossover(self, ema_diff: float) -> CrossoverType:
        """
        Classify EMA crossover type.
        
        - 0.05-0.3%: FRESH (ideal entry)
        - 0.3-1.0%: DEVELOPING (acceptable)
        - >1.0%: EXTENDED (reduce confidence)
        
        Args:
            ema_diff: EMA9 - EMA21 as percentage
            
        Returns:
            CrossoverType enum
        """
        ema_diff_abs = abs(ema_diff)
        
        if self.FRESH_MIN <= ema_diff_abs <= self.FRESH_MAX:
            return CrossoverType.FRESH
        elif ema_diff_abs <= self.DEVELOPING_MAX:
            return CrossoverType.DEVELOPING
        else:
            return CrossoverType.EXTENDED
    
    def calculate_entry_bonus(self, vwap_distance: float) -> int:
        """
        Calculate entry point bonus based on VWAP proximity.
        
        Within 0.5% of VWAP: +5 points (good entry point)
        
        Args:
            vwap_distance: Distance from VWAP as percentage
            
        Returns:
            Bonus points (0 or 5)
        """
        if abs(vwap_distance) <= self.VWAP_PROXIMITY_PCT:
            return self.VWAP_BONUS
        return 0

    def check_timeframe_alignment(self, features: Dict) -> bool:
        """
        Check if multiple timeframes show aligned momentum.
        
        Returns True if 5-min and 1-hour both show same direction.
        
        Args:
            features: Dictionary with timeframe data
            
        Returns:
            True if timeframes are aligned
        """
        # Check for explicit multi-TF alignment flag
        if 'multi_tf_aligned' in features:
            return features['multi_tf_aligned']
        
        # Check individual timeframe directions
        tf_5min = features.get('direction_5min', None)
        tf_1hour = features.get('direction_1hour', None)
        
        if tf_5min is not None and tf_1hour is not None:
            return tf_5min == tf_1hour
        
        # Default to False if we don't have the data
        return False
    
    def _determine_entry_quality(
        self, 
        crossover_type: CrossoverType, 
        near_vwap: bool, 
        multi_tf_aligned: bool
    ) -> EntryQuality:
        """
        Determine overall entry quality.
        
        Args:
            crossover_type: Type of EMA crossover
            near_vwap: Whether price is near VWAP
            multi_tf_aligned: Whether timeframes are aligned
            
        Returns:
            EntryQuality enum
        """
        # Fresh crossover with VWAP and TF alignment = IDEAL
        if crossover_type == CrossoverType.FRESH and near_vwap and multi_tf_aligned:
            return EntryQuality.IDEAL
        
        # Fresh crossover with at least one bonus = IDEAL
        if crossover_type == CrossoverType.FRESH and (near_vwap or multi_tf_aligned):
            return EntryQuality.IDEAL
        
        # Fresh crossover alone = ACCEPTABLE
        if crossover_type == CrossoverType.FRESH:
            return EntryQuality.ACCEPTABLE
        
        # Developing with bonuses = ACCEPTABLE
        if crossover_type == CrossoverType.DEVELOPING and (near_vwap or multi_tf_aligned):
            return EntryQuality.ACCEPTABLE
        
        # Developing alone = ACCEPTABLE (but borderline)
        if crossover_type == CrossoverType.DEVELOPING:
            return EntryQuality.ACCEPTABLE
        
        # Extended = POOR
        return EntryQuality.POOR
    
    def _should_enter(
        self, 
        crossover_type: CrossoverType, 
        adx: float, 
        entry_quality: EntryQuality
    ) -> Tuple[bool, str]:
        """
        Determine if we should enter the trade.
        
        Args:
            crossover_type: Type of EMA crossover
            adx: ADX value
            entry_quality: Overall entry quality
            
        Returns:
            Tuple of (should_enter, reason)
        """
        # Skip if ADX too low (choppy market)
        if adx < self.MIN_ADX:
            return False, f"Choppy market: ADX={adx:.1f} (need ≥{self.MIN_ADX})"
        
        # Skip if extended move
        if crossover_type == CrossoverType.EXTENDED:
            return False, "Extended move - wave may be ending"
        
        # Enter on fresh or developing crossovers
        if crossover_type == CrossoverType.FRESH:
            return True, f"Fresh crossover - ideal entry ({entry_quality.value})"
        
        if crossover_type == CrossoverType.DEVELOPING:
            return True, f"Developing crossover - acceptable entry ({entry_quality.value})"
        
        return False, "Unknown crossover type"
    
    def get_confidence_adjustment(self, features: Dict) -> int:
        """
        Get the total confidence adjustment for entry timing.
        
        This is a convenience method that returns just the adjustment.
        
        Args:
            features: Dictionary with technical indicators
            
        Returns:
            Total confidence adjustment (can be negative)
        """
        analysis = self.analyze_entry(features)
        return analysis.confidence_adjustment
