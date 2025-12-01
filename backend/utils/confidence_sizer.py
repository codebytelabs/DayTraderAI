#!/usr/bin/env python3
"""
Confidence-Based Position Sizer

Scales position sizes based on confidence level from momentum scoring.
Higher confidence = larger position (more conviction).

Confidence Tiers:
- 90+: 15% max (high conviction)
- 80-89: 12% max
- 70-79: 10% max
- 60-69: 8% max
- <60: Skip trade

Volume Bonus: +2% if volume confirmed (up to 15% max)
"""

import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PositionSizeResult:
    """Result of position size calculation."""
    shares: int = 0
    dollar_amount: float = 0.0
    percent_of_equity: float = 0.0
    confidence_tier: str = "low"
    volume_bonus_applied: bool = False
    skip_trade: bool = False
    skip_reason: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if this is a valid position to take."""
        return not self.skip_trade and self.shares > 0


class ConfidenceBasedSizer:
    """
    Dynamic position sizing based on confidence score.
    Higher confidence = larger position.
    
    This replaces fixed position sizing with adaptive sizing
    that scales with conviction level.
    """
    
    # Confidence tier thresholds and max position sizes
    TIERS = {
        'ultra_high': {'min_confidence': 90, 'max_pct': 0.15, 'label': 'ultra_high'},
        'high': {'min_confidence': 80, 'max_pct': 0.12, 'label': 'high'},
        'medium': {'min_confidence': 70, 'max_pct': 0.10, 'label': 'medium'},
        'low': {'min_confidence': 60, 'max_pct': 0.08, 'label': 'low'},
    }
    
    # Volume bonus
    VOLUME_BONUS_PCT = 0.02  # +2% for confirmed volume
    MAX_POSITION_PCT = 0.15  # Never exceed 15%
    
    # Skip thresholds
    MIN_CONFIDENCE = 60
    MIN_ADX = 20
    
    def __init__(self):
        logger.info("✅ ConfidenceBasedSizer initialized")
    
    def calculate_position_size(
        self,
        confidence: float,
        equity: float,
        price: float,
        volume_confirmed: bool = False,
        adx: float = 25.0
    ) -> PositionSizeResult:
        """
        Calculate position size based on confidence.
        
        Args:
            confidence: Confidence score (0-100)
            equity: Total account equity
            price: Stock price
            volume_confirmed: Whether volume is 150%+ of average
            adx: ADX value for trend strength
            
        Returns:
            PositionSizeResult with shares, dollar amount, and tier info
        """
        result = PositionSizeResult()
        
        # Check if we should skip the trade
        should_skip, skip_reason = self.should_skip_trade(confidence, adx)
        if should_skip:
            result.skip_trade = True
            result.skip_reason = skip_reason
            logger.info(f"⏭️ Skipping trade: {skip_reason}")
            return result
        
        # Determine confidence tier
        tier = self._get_confidence_tier(confidence)
        result.confidence_tier = tier['label']
        
        # Calculate base position percentage
        base_pct = tier['max_pct']
        
        # Apply volume bonus if confirmed
        if volume_confirmed:
            base_pct += self.VOLUME_BONUS_PCT
            result.volume_bonus_applied = True
            logger.debug(f"Volume bonus applied: +{self.VOLUME_BONUS_PCT*100}%")
        
        # Cap at maximum
        final_pct = min(base_pct, self.MAX_POSITION_PCT)
        result.percent_of_equity = final_pct
        
        # Calculate dollar amount and shares
        result.dollar_amount = equity * final_pct
        result.shares = int(result.dollar_amount / price) if price > 0 else 0
        
        # Recalculate actual dollar amount based on whole shares
        result.dollar_amount = result.shares * price
        result.percent_of_equity = result.dollar_amount / equity if equity > 0 else 0
        
        logger.info(f"📊 Position size: {result.shares} shares (${result.dollar_amount:.2f}, "
                   f"{result.percent_of_equity*100:.1f}% of equity, tier={result.confidence_tier})")
        
        return result

    def should_skip_trade(self, confidence: float, adx: float) -> tuple[bool, Optional[str]]:
        """
        Determine if trade should be skipped.
        
        Skip if:
        - Confidence < 60 (low conviction)
        - ADX < 20 (choppy market, no clear trend)
        
        Args:
            confidence: Confidence score (0-100)
            adx: ADX value
            
        Returns:
            Tuple of (should_skip, reason)
        """
        if confidence < self.MIN_CONFIDENCE:
            return True, f"Low confidence: {confidence:.0f} (need ≥{self.MIN_CONFIDENCE})"
        
        if adx < self.MIN_ADX:
            return True, f"Choppy market: ADX={adx:.1f} (need ≥{self.MIN_ADX})"
        
        return False, None
    
    def _get_confidence_tier(self, confidence: float) -> dict:
        """
        Get the confidence tier for a given confidence score.
        
        Args:
            confidence: Confidence score (0-100)
            
        Returns:
            Tier dictionary with min_confidence, max_pct, and label
        """
        if confidence >= 90:
            return self.TIERS['ultra_high']
        elif confidence >= 80:
            return self.TIERS['high']
        elif confidence >= 70:
            return self.TIERS['medium']
        else:
            return self.TIERS['low']
    
    def get_position_pct_for_confidence(self, confidence: float, volume_confirmed: bool = False) -> float:
        """
        Get the position percentage for a given confidence score.
        
        This is a simpler method that just returns the percentage
        without calculating shares.
        
        Args:
            confidence: Confidence score (0-100)
            volume_confirmed: Whether volume is confirmed
            
        Returns:
            Position percentage (0.0 to 0.15)
        """
        if confidence < self.MIN_CONFIDENCE:
            return 0.0
        
        tier = self._get_confidence_tier(confidence)
        base_pct = tier['max_pct']
        
        if volume_confirmed:
            base_pct += self.VOLUME_BONUS_PCT
        
        return min(base_pct, self.MAX_POSITION_PCT)
    
    def adjust_for_consecutive_losses(self, result: PositionSizeResult, consecutive_losses: int) -> PositionSizeResult:
        """
        Reduce position size after consecutive losses.
        
        After 3 consecutive losses, reduce position sizes by 50%
        for the next 3 trades.
        
        Args:
            result: Original position size result
            consecutive_losses: Number of consecutive losses
            
        Returns:
            Adjusted position size result
        """
        if consecutive_losses >= 3:
            # Reduce by 50%
            result.shares = result.shares // 2
            result.dollar_amount = result.dollar_amount / 2
            result.percent_of_equity = result.percent_of_equity / 2
            logger.warning(f"⚠️ Position reduced 50% due to {consecutive_losses} consecutive losses")
        
        return result
