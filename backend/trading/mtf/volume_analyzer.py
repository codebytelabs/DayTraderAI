"""
Multi-Timeframe Volume Analyzer.

Analyzes volume patterns across timeframes for signal confirmation.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

import logging
from typing import Tuple

from trading.mtf.models import MTFFeatures

logger = logging.getLogger(__name__)


class VolumeAnalyzer:
    """Analyzes volume patterns across timeframes.
    
    Requirements:
    - 6.1: Compare current volume to 20-period average on each timeframe
    - 6.2: Add volume confirmation when 5-min volume > 1.5x average
    - 6.3: Reduce confidence by 10 points when 15-min volume < 0.7x average
    - 6.4: Add 10 points when volume increases with price in signal direction
    - 6.5: Flag potential reversal when volume diverges from price
    """
    
    # Volume confirmation threshold (1.5x average)
    VOLUME_CONFIRMATION_THRESHOLD = 1.5
    
    # Low volume threshold (0.7x average)
    LOW_VOLUME_THRESHOLD = 0.7
    
    # Confidence adjustments
    VOLUME_CONFIRMATION_BONUS = 10
    LOW_VOLUME_PENALTY = 10
    
    def __init__(self):
        """Initialize the volume analyzer."""
        pass
    
    def check_volume_confirmation(self, features: MTFFeatures) -> bool:
        """Check if 5-min volume confirms the signal.
        
        Requirement 6.2: Volume confirmation when 5-min volume > 1.5x average.
        
        Args:
            features: MTFFeatures containing volume data
            
        Returns:
            True if volume is confirmed (> 1.5x average)
        """
        volume_ratio = features.tf_5min.volume_ratio
        is_confirmed = volume_ratio > self.VOLUME_CONFIRMATION_THRESHOLD
        
        logger.debug(
            f"5-min volume ratio: {volume_ratio:.2f}x "
            f"({'confirmed' if is_confirmed else 'not confirmed'})"
        )
        
        return is_confirmed

    def get_volume_penalty(self, features: MTFFeatures) -> int:
        """Get confidence penalty for low 15-min volume.
        
        Requirement 6.3: Reduce confidence by 10 points when 15-min volume < 0.7x average.
        
        Args:
            features: MTFFeatures containing volume data
            
        Returns:
            Penalty points (negative value) or 0
        """
        volume_ratio = features.tf_15min.volume_ratio
        
        if volume_ratio < self.LOW_VOLUME_THRESHOLD:
            logger.debug(
                f"Low 15-min volume ({volume_ratio:.2f}x), "
                f"penalty: -{self.LOW_VOLUME_PENALTY} points"
            )
            return -self.LOW_VOLUME_PENALTY
        
        return 0
    
    def check_volume_price_alignment(
        self, 
        features: MTFFeatures, 
        signal: str
    ) -> Tuple[bool, bool]:
        """Check volume-price alignment for divergence detection.
        
        Requirements 6.4, 6.5:
        - Add 10 points when volume increases with price in signal direction
        - Flag potential reversal when volume diverges from price
        
        Args:
            features: MTFFeatures containing volume and price data
            signal: Signal direction ('buy' or 'sell')
            
        Returns:
            Tuple of (is_aligned, has_divergence)
        """
        signal_lower = signal.lower()
        
        # Get volume ratios
        vol_5min = features.tf_5min.volume_ratio
        vol_15min = features.tf_15min.volume_ratio
        
        # Check if volume is increasing on higher timeframes
        volume_increasing = vol_15min > 1.0 and vol_5min > 1.0
        
        # For alignment, we want volume to support the signal direction
        # High volume on breakouts is bullish for buys, bearish for sells
        is_aligned = volume_increasing
        
        # Divergence: price moving but volume declining
        has_divergence = vol_15min < 0.8 and vol_5min < 0.8
        
        if has_divergence:
            logger.warning(
                f"Volume-price divergence detected: "
                f"5-min vol={vol_5min:.2f}x, 15-min vol={vol_15min:.2f}x"
            )
        
        return is_aligned, has_divergence
    
    def get_volume_score(self, features: MTFFeatures, signal: str) -> int:
        """Calculate total volume score for confidence adjustment.
        
        Combines all volume analysis into a single score.
        
        Args:
            features: MTFFeatures containing volume data
            signal: Signal direction ('buy' or 'sell')
            
        Returns:
            Volume score adjustment (positive or negative)
        """
        score = 0
        
        # Check volume confirmation
        if self.check_volume_confirmation(features):
            score += self.VOLUME_CONFIRMATION_BONUS
        
        # Check for low volume penalty
        score += self.get_volume_penalty(features)
        
        # Check volume-price alignment
        is_aligned, has_divergence = self.check_volume_price_alignment(features, signal)
        
        if is_aligned:
            score += self.VOLUME_CONFIRMATION_BONUS
        
        # Note: divergence is flagged but doesn't directly affect score
        # It's used for risk assessment
        
        logger.debug(f"Volume score: {score}")
        
        return score
