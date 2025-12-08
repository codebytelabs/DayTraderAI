"""
Multi-Timeframe Momentum Analyzer.

Confirms momentum alignment across timeframes using RSI and MACD.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""

import logging
from typing import Tuple

from trading.mtf.models import MTFFeatures

logger = logging.getLogger(__name__)


class MomentumAnalyzer:
    """Analyzes momentum across timeframes.
    
    Uses RSI and MACD to confirm momentum alignment before entry.
    
    Requirements:
    - 3.1: Require RSI > 50 on at least 2 of 3 timeframes for buys
    - 3.2: Require RSI < 50 on at least 2 of 3 timeframes for sells
    - 3.3: Add bullish momentum when MACD histogram positive on 5-min and 15-min
    - 3.4: Add bearish momentum when MACD histogram negative on 5-min and 15-min
    - 3.5: Reduce confidence by 20 points when momentum conflicts
    - 3.6: Increase confidence by 25 points when all timeframes align
    """
    
    # RSI threshold for momentum direction
    RSI_THRESHOLD = 50
    
    # Minimum timeframes required for RSI alignment
    MIN_RSI_ALIGNMENT = 2
    
    # Confidence adjustments
    FULL_ALIGNMENT_BONUS = 25
    CONFLICT_PENALTY = 20
    
    def __init__(self):
        """Initialize the momentum analyzer."""
        pass
    
    def check_rsi_alignment(
        self, 
        features: MTFFeatures, 
        signal: str
    ) -> Tuple[bool, int]:
        """Check RSI alignment across timeframes.
        
        Requirements 3.1, 3.2:
        - Buy: RSI > 50 on at least 2 of 3 timeframes
        - Sell: RSI < 50 on at least 2 of 3 timeframes
        
        Args:
            features: MTFFeatures containing all timeframe data
            signal: Signal direction ('buy' or 'sell')
            
        Returns:
            Tuple of (is_aligned, alignment_count)
        """
        signal_lower = signal.lower()
        
        # Get RSI values from 1-min, 5-min, 15-min
        rsi_values = [
            features.tf_1min.rsi,
            features.tf_5min.rsi,
            features.tf_15min.rsi,
        ]
        
        if signal_lower == 'buy':
            # Count timeframes with RSI > 50
            aligned_count = sum(1 for rsi in rsi_values if rsi > self.RSI_THRESHOLD)
        else:  # sell
            # Count timeframes with RSI < 50
            aligned_count = sum(1 for rsi in rsi_values if rsi < self.RSI_THRESHOLD)
        
        is_aligned = aligned_count >= self.MIN_RSI_ALIGNMENT
        
        logger.debug(
            f"RSI alignment for {signal}: {aligned_count}/3 timeframes aligned "
            f"(RSI values: 1min={rsi_values[0]:.1f}, 5min={rsi_values[1]:.1f}, 15min={rsi_values[2]:.1f})"
        )
        
        return is_aligned, aligned_count
    
    def check_macd_alignment(
        self, 
        features: MTFFeatures, 
        signal: str
    ) -> bool:
        """Check MACD alignment on 5-min and 15-min timeframes.
        
        Requirements 3.3, 3.4:
        - Bullish: MACD histogram positive on both 5-min and 15-min
        - Bearish: MACD histogram negative on both 5-min and 15-min
        
        Args:
            features: MTFFeatures containing all timeframe data
            signal: Signal direction ('buy' or 'sell')
            
        Returns:
            True if MACD is aligned with signal direction
        """
        signal_lower = signal.lower()
        
        macd_5min = features.tf_5min.macd_histogram
        macd_15min = features.tf_15min.macd_histogram
        
        if signal_lower == 'buy':
            # Both should be positive for bullish confirmation
            is_aligned = macd_5min > 0 and macd_15min > 0
        else:  # sell
            # Both should be negative for bearish confirmation
            is_aligned = macd_5min < 0 and macd_15min < 0
        
        logger.debug(
            f"MACD alignment for {signal}: {'aligned' if is_aligned else 'not aligned'} "
            f"(5min={macd_5min:.4f}, 15min={macd_15min:.4f})"
        )
        
        return is_aligned
    
    def get_momentum_score(
        self, 
        features: MTFFeatures, 
        signal: str
    ) -> int:
        """Calculate momentum alignment score with bonuses/penalties.
        
        Requirements 3.5, 3.6:
        - +25 points when all three timeframes show aligned momentum
        - -20 points when momentum indicators conflict
        
        Args:
            features: MTFFeatures containing all timeframe data
            signal: Signal direction ('buy' or 'sell')
            
        Returns:
            Momentum score adjustment (positive or negative)
        """
        signal_lower = signal.lower()
        
        # Check RSI alignment
        rsi_aligned, rsi_count = self.check_rsi_alignment(features, signal)
        
        # Check MACD alignment
        macd_aligned = self.check_macd_alignment(features, signal)
        
        # Check if all timeframes are fully aligned
        all_aligned = rsi_count == 3 and macd_aligned
        
        # Check for conflicts
        has_conflict = self._has_momentum_conflict(features, signal)
        
        # Calculate score
        score = 0
        
        if all_aligned:
            score = self.FULL_ALIGNMENT_BONUS
            logger.debug(f"Full momentum alignment: +{self.FULL_ALIGNMENT_BONUS} points")
        elif has_conflict:
            score = -self.CONFLICT_PENALTY
            logger.debug(f"Momentum conflict: -{self.CONFLICT_PENALTY} points")
        
        return score
    
    def _has_momentum_conflict(
        self, 
        features: MTFFeatures, 
        signal: str
    ) -> bool:
        """Check if there's a momentum conflict across timeframes.
        
        A conflict exists when:
        - RSI shows opposite direction on majority of timeframes
        - MACD shows opposite direction on 5-min and 15-min
        
        Args:
            features: MTFFeatures containing all timeframe data
            signal: Signal direction ('buy' or 'sell')
            
        Returns:
            True if there's a momentum conflict
        """
        signal_lower = signal.lower()
        
        # Get RSI values
        rsi_values = [
            features.tf_1min.rsi,
            features.tf_5min.rsi,
            features.tf_15min.rsi,
        ]
        
        # Get MACD values
        macd_5min = features.tf_5min.macd_histogram
        macd_15min = features.tf_15min.macd_histogram
        
        if signal_lower == 'buy':
            # Conflict if majority RSI < 50 AND both MACD negative
            rsi_bearish_count = sum(1 for rsi in rsi_values if rsi < self.RSI_THRESHOLD)
            macd_bearish = macd_5min < 0 and macd_15min < 0
            return rsi_bearish_count >= 2 and macd_bearish
        else:  # sell
            # Conflict if majority RSI > 50 AND both MACD positive
            rsi_bullish_count = sum(1 for rsi in rsi_values if rsi > self.RSI_THRESHOLD)
            macd_bullish = macd_5min > 0 and macd_15min > 0
            return rsi_bullish_count >= 2 and macd_bullish
    
    def analyze_momentum(
        self, 
        features: MTFFeatures, 
        signal: str
    ) -> Tuple[bool, int, bool, int]:
        """Complete momentum analysis for a signal.
        
        Args:
            features: MTFFeatures for the symbol
            signal: Signal direction ('buy' or 'sell')
            
        Returns:
            Tuple of (rsi_aligned, rsi_count, macd_aligned, momentum_score)
        """
        rsi_aligned, rsi_count = self.check_rsi_alignment(features, signal)
        macd_aligned = self.check_macd_alignment(features, signal)
        momentum_score = self.get_momentum_score(features, signal)
        
        return rsi_aligned, rsi_count, macd_aligned, momentum_score
