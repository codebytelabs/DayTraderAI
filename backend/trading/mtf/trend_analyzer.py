"""
Multi-Timeframe Trend Analyzer.

Determines trend direction from higher timeframes and checks signal alignment.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
"""

import logging
from typing import Optional, Tuple

from trading.mtf.models import (
    MTFFeatures,
    TrendBias,
    TrendDirection,
    TimeframeFeatures,
)

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyzes trend across timeframes.
    
    Uses 15-minute EMA(50) vs EMA(200) relationship to determine trend bias.
    Checks if signals align with higher timeframe trends.
    
    Requirements:
    - 2.1: Determine trend direction using EMA(50) and EMA(200) relationship
    - 2.2: Classify as bullish when EMA(50) > EMA(200) by more than 0.1%
    - 2.3: Classify as bearish when EMA(50) < EMA(200) by more than 0.1%
    - 2.4: Classify as neutral when EMAs are within 0.1% of each other
    - 2.5: Reject signals that contradict 15-minute trend bias
    - 2.6: Increase confidence by 15 points when daily trend aligns
    """
    
    # Threshold for trend classification (0.1%)
    TREND_THRESHOLD_PCT = 0.1
    
    # Confidence bonus for daily alignment
    DAILY_ALIGNMENT_BONUS = 15
    
    def __init__(self):
        """Initialize the trend analyzer."""
        pass
    
    def get_trend_bias(self, features: MTFFeatures) -> TrendBias:
        """Determine overall trend bias from 15-min and daily timeframes.
        
        Requirements 2.1, 2.2, 2.3, 2.4:
        - Uses 15-minute EMA(50) vs EMA(200) for primary trend
        - Classifies as bullish/bearish/neutral based on 0.1% threshold
        
        Args:
            features: MTFFeatures containing all timeframe data
            
        Returns:
            TrendBias with direction, strength, and daily alignment
        """
        # Get 15-minute features for primary trend
        tf_15min = features.tf_15min
        
        # Get daily trend direction for alignment check
        daily_direction = self._get_timeframe_trend_direction(features.tf_daily)
        
        # Create trend bias from 15-minute EMAs
        trend_bias = TrendBias.from_ema_values(
            ema_50=tf_15min.ema_50,
            ema_200=tf_15min.ema_200,
            daily_direction=daily_direction,
        )
        
        logger.debug(
            f"Trend bias for {features.symbol}: {trend_bias.direction.value}, "
            f"strength={trend_bias.strength:.1f}, daily_aligned={trend_bias.daily_aligned}"
        )
        
        return trend_bias
    
    def _get_timeframe_trend_direction(
        self, 
        tf_features: TimeframeFeatures
    ) -> TrendDirection:
        """Get trend direction for a single timeframe.
        
        Args:
            tf_features: Features for a single timeframe
            
        Returns:
            TrendDirection based on EMA relationship
        """
        if tf_features.ema_200 == 0:
            return TrendDirection.NEUTRAL
        
        ema_diff_pct = ((tf_features.ema_50 - tf_features.ema_200) / tf_features.ema_200) * 100
        
        if ema_diff_pct > self.TREND_THRESHOLD_PCT:
            return TrendDirection.BULLISH
        elif ema_diff_pct < -self.TREND_THRESHOLD_PCT:
            return TrendDirection.BEARISH
        else:
            return TrendDirection.NEUTRAL
    
    def check_trend_alignment(
        self, 
        signal: str, 
        trend_bias: TrendBias
    ) -> Tuple[bool, Optional[str]]:
        """Check if signal aligns with higher timeframe trend.
        
        Requirement 2.5: Reject signals that contradict 15-minute trend bias.
        
        Args:
            signal: Signal direction ('buy' or 'sell')
            trend_bias: TrendBias from get_trend_bias()
            
        Returns:
            Tuple of (is_aligned, rejection_reason)
            - is_aligned: True if signal aligns with trend
            - rejection_reason: String explaining rejection, or None if aligned
        """
        signal_lower = signal.lower()
        
        # Buy signals should align with bullish or neutral trend
        if signal_lower == 'buy':
            if trend_bias.direction == TrendDirection.BEARISH:
                reason = (
                    f"Buy signal rejected: 15-min trend is bearish "
                    f"(EMA diff: {trend_bias.ema_diff_pct:.2f}%)"
                )
                logger.info(reason)
                return False, reason
        
        # Sell signals should align with bearish or neutral trend
        elif signal_lower == 'sell':
            if trend_bias.direction == TrendDirection.BULLISH:
                reason = (
                    f"Sell signal rejected: 15-min trend is bullish "
                    f"(EMA diff: {trend_bias.ema_diff_pct:.2f}%)"
                )
                logger.info(reason)
                return False, reason
        
        return True, None
    
    def get_daily_alignment_bonus(self, trend_bias: TrendBias) -> int:
        """Get confidence bonus for daily trend alignment.
        
        Requirement 2.6: Increase confidence by 15 points when daily aligns.
        
        Args:
            trend_bias: TrendBias with daily_aligned flag
            
        Returns:
            Confidence bonus (15 if aligned, 0 otherwise)
        """
        if trend_bias.daily_aligned:
            logger.debug(f"Daily trend alignment bonus: +{self.DAILY_ALIGNMENT_BONUS}")
            return self.DAILY_ALIGNMENT_BONUS
        return 0
    
    def analyze_trend(
        self, 
        features: MTFFeatures, 
        signal: str
    ) -> Tuple[TrendBias, bool, Optional[str], int]:
        """Complete trend analysis for a signal.
        
        Combines all trend analysis steps:
        1. Get trend bias from 15-min and daily
        2. Check signal alignment
        3. Calculate daily alignment bonus
        
        Args:
            features: MTFFeatures for the symbol
            signal: Signal direction ('buy' or 'sell')
            
        Returns:
            Tuple of (trend_bias, is_aligned, rejection_reason, confidence_bonus)
        """
        # Get trend bias
        trend_bias = self.get_trend_bias(features)
        
        # Check alignment
        is_aligned, rejection_reason = self.check_trend_alignment(signal, trend_bias)
        
        # Calculate bonus
        confidence_bonus = self.get_daily_alignment_bonus(trend_bias) if is_aligned else 0
        
        return trend_bias, is_aligned, rejection_reason, confidence_bonus
