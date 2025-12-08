"""
Multi-Timeframe Confidence Calculator.

Calculates weighted confidence score from all timeframes.

Requirements: 5.1, 5.2, 5.3
"""

import logging
from typing import Dict

from trading.mtf.models import MTFFeatures, TrendBias, MTFConfig

logger = logging.getLogger(__name__)


class MTFConfidenceCalculator:
    """Calculates multi-timeframe confidence score.
    
    Requirements:
    - 5.1: Weight timeframes as 15-min (40%), 5-min (35%), 1-min (25%)
    - 5.2: Increase 15-min weight to 50% when ADX > 25
    - 5.3: Add 20-point alignment bonus when all timeframes align
    """
    
    DEFAULT_WEIGHTS = {
        '15min': 0.40,
        '5min': 0.35,
        '1min': 0.25,
    }
    
    # ADX threshold for strong trend
    STRONG_TREND_ADX = 25
    
    # Weight for 15-min when trend is strong
    STRONG_TREND_15MIN_WEIGHT = 0.50
    
    # Alignment bonus
    FULL_ALIGNMENT_BONUS = 20
    
    def __init__(self, config: MTFConfig = None):
        """Initialize the confidence calculator."""
        self.config = config or MTFConfig()

    def get_effective_weights(self, features: MTFFeatures) -> Dict[str, float]:
        """Get effective weights, adjusting for strong trends.
        
        Requirement 5.2: Increase 15-min weight to 50% when ADX > 25.
        
        Args:
            features: MTFFeatures containing ADX values
            
        Returns:
            Dict of timeframe weights
        """
        # Start with configured or default weights
        weights = self.config.get_weights().copy()
        
        # Check if 15-min trend is strong
        if features.tf_15min.adx > self.STRONG_TREND_ADX:
            # Increase 15-min weight to 50%
            old_15min = weights.get('15min', 0.40)
            weights['15min'] = self.STRONG_TREND_15MIN_WEIGHT
            
            # Redistribute the difference to other timeframes proportionally
            diff = self.STRONG_TREND_15MIN_WEIGHT - old_15min
            remaining = 1.0 - old_15min
            
            if remaining > 0:
                for tf in ['5min', '1min']:
                    if tf in weights:
                        weights[tf] = weights[tf] * (1 - diff / remaining)
            
            logger.debug(
                f"Strong 15-min trend (ADX={features.tf_15min.adx:.1f}), "
                f"increased 15-min weight to {self.STRONG_TREND_15MIN_WEIGHT}"
            )
        
        return weights
    
    def calculate_confidence(
        self,
        features: MTFFeatures,
        signal: str,
        trend_bias: TrendBias,
        momentum_score: int,
        volume_score: int,
    ) -> float:
        """Calculate weighted MTF confidence score.
        
        Requirement 5.1: Weight timeframes as 15-min (40%), 5-min (35%), 1-min (25%).
        
        Args:
            features: MTFFeatures containing all timeframe data
            signal: Signal direction ('buy' or 'sell')
            trend_bias: TrendBias from trend analyzer
            momentum_score: Score from momentum analyzer
            volume_score: Score from volume analyzer
            
        Returns:
            Confidence score (0-100)
        """
        weights = self.get_effective_weights(features)
        
        # Base confidence from each timeframe
        base_confidence = 50.0  # Start at neutral
        
        # Add trend alignment contribution
        if trend_bias.direction.value == signal.lower() or trend_bias.direction.value == 'neutral':
            base_confidence += 15.0
        
        # Add daily alignment bonus
        if trend_bias.daily_aligned:
            base_confidence += 15.0
        
        # Add momentum score
        base_confidence += momentum_score
        
        # Add volume score
        base_confidence += volume_score
        
        # Clamp to 0-100
        confidence = max(0.0, min(100.0, base_confidence))
        
        logger.debug(
            f"MTF confidence: {confidence:.1f} "
            f"(base=50, trend={15 if trend_bias.direction.value != 'neutral' else 0}, "
            f"daily={15 if trend_bias.daily_aligned else 0}, "
            f"momentum={momentum_score}, volume={volume_score})"
        )
        
        return confidence
    
    def apply_alignment_bonus(
        self,
        base_confidence: float,
        all_aligned: bool,
    ) -> float:
        """Apply bonus for full timeframe alignment.
        
        Requirement 5.3: Add 20-point alignment bonus when all timeframes align.
        
        Args:
            base_confidence: Base confidence score
            all_aligned: True if all timeframes are aligned
            
        Returns:
            Adjusted confidence score
        """
        if all_aligned:
            adjusted = base_confidence + self.FULL_ALIGNMENT_BONUS
            logger.debug(f"Full alignment bonus: +{self.FULL_ALIGNMENT_BONUS} points")
            return min(100.0, adjusted)
        return base_confidence
