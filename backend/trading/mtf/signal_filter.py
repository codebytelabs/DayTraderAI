"""
Multi-Timeframe Signal Filter.

Orchestrates all MTF analyzers and makes final signal decisions.

Requirements: 5.4, 5.5, 5.6, 7.2, 7.3, 7.4
"""

import logging
from typing import Optional, Dict
import pandas as pd

from trading.mtf.models import (
    MTFFeatures,
    MTFSignalResult,
    MTFConfig,
    SRLevels,
    TrendBias,
)
from trading.mtf.trend_analyzer import TrendAnalyzer
from trading.mtf.momentum_analyzer import MomentumAnalyzer
from trading.mtf.sr_analyzer import SupportResistanceAnalyzer
from trading.mtf.volume_analyzer import VolumeAnalyzer
from trading.mtf.confidence_calculator import MTFConfidenceCalculator

logger = logging.getLogger(__name__)


class MTFSignalFilter:
    """Filters signals using multi-timeframe analysis.
    
    Requirements:
    - 5.4: Reject signals when MTF confidence < 60
    - 5.5: Allow increased position sizing up to 1.5x when confidence > 80
    - 5.6: Reduce position size to 0.7x when confidence 60-70
    - 7.2: Wait for alignment when 5-min conflicts with 15-min
    - 7.3: Reduce position by 40% when >1 timeframe has ADX < 20
    - 7.4: Allow full position when all timeframes have ADX > 25
    """
    
    # Confidence thresholds
    MIN_CONFIDENCE = 60
    HIGH_CONFIDENCE = 80
    MID_CONFIDENCE = 70
    
    # ADX thresholds
    RANGING_ADX = 20
    TRENDING_ADX = 25
    
    # Position size multipliers
    LOW_CONFIDENCE_MULTIPLIER = 0.7
    HIGH_CONFIDENCE_MULTIPLIER = 1.5
    RANGING_MARKET_REDUCTION = 0.40
    
    def __init__(self, config: MTFConfig = None):
        """Initialize the signal filter with all analyzers."""
        self.config = config or MTFConfig()
        self.trend_analyzer = TrendAnalyzer()
        self.momentum_analyzer = MomentumAnalyzer()
        self.sr_analyzer = SupportResistanceAnalyzer()
        self.volume_analyzer = VolumeAnalyzer()
        self.confidence_calculator = MTFConfidenceCalculator(self.config)

    def evaluate_signal(
        self,
        symbol: str,
        signal: str,
        features: MTFFeatures,
        df_15min: Optional[pd.DataFrame] = None,
    ) -> MTFSignalResult:
        """Evaluate a signal against multi-timeframe analysis.
        
        Args:
            symbol: Stock symbol
            signal: Signal direction ('buy' or 'sell')
            features: MTFFeatures for the symbol
            df_15min: Optional 15-min DataFrame for S/R calculation
            
        Returns:
            MTFSignalResult with all analysis results
        """
        # Check if MTF is disabled
        if self.config.should_bypass():
            return self._create_bypass_result(symbol, signal, features)
        
        # Analyze trend
        trend_bias, trend_aligned, rejection_reason, trend_bonus = \
            self.trend_analyzer.analyze_trend(features, signal)
        
        # If trend not aligned, reject immediately
        if not trend_aligned:
            return self._create_rejected_result(
                symbol, signal, features, trend_bias, rejection_reason
            )
        
        # Analyze momentum
        rsi_aligned, rsi_count, macd_aligned, momentum_score = \
            self.momentum_analyzer.analyze_momentum(features, signal)
        
        # Analyze volume
        volume_confirmed = self.volume_analyzer.check_volume_confirmation(features)
        volume_score = self.volume_analyzer.get_volume_score(features, signal)
        
        # Get S/R levels
        sr_levels = self.sr_analyzer.get_nearest_levels(
            features.tf_1min.close, features, df_15min
        )
        
        # Calculate confidence
        base_confidence = self.confidence_calculator.calculate_confidence(
            features, signal, trend_bias, momentum_score, volume_score
        )
        
        # Apply alignment bonus
        all_aligned = rsi_count == 3 and macd_aligned and trend_aligned
        mtf_confidence = self.confidence_calculator.apply_alignment_bonus(
            base_confidence, all_aligned
        )
        
        # Determine if signal should be rejected
        should_reject, reject_reason = self.should_reject(mtf_confidence, trend_aligned)
        
        # Calculate position size multiplier
        position_multiplier = self._calculate_position_multiplier(
            mtf_confidence, features, signal, sr_levels
        )
        
        return MTFSignalResult(
            symbol=symbol,
            signal=signal,
            mtf_confidence=mtf_confidence,
            trend_bias=trend_bias,
            trend_aligned=trend_aligned,
            momentum_aligned=rsi_aligned and macd_aligned,
            rsi_alignment_count=rsi_count,
            macd_aligned=macd_aligned,
            volume_confirmed=volume_confirmed,
            sr_levels=sr_levels,
            position_size_multiplier=position_multiplier,
            rejection_reason=reject_reason,
        )
    
    def should_reject(
        self,
        mtf_confidence: float,
        trend_aligned: bool,
    ) -> tuple:
        """Determine if signal should be rejected.
        
        Requirement 5.4: Reject when confidence < 60.
        
        Args:
            mtf_confidence: Calculated confidence score
            trend_aligned: Whether trend is aligned
            
        Returns:
            Tuple of (should_reject, rejection_reason)
        """
        if not trend_aligned:
            return True, "Signal contradicts higher timeframe trend"
        
        if mtf_confidence < self.MIN_CONFIDENCE:
            return True, f"MTF confidence too low: {mtf_confidence:.1f} < {self.MIN_CONFIDENCE}"
        
        return False, None
    
    def _calculate_position_multiplier(
        self,
        confidence: float,
        features: MTFFeatures,
        signal: str,
        sr_levels: SRLevels,
    ) -> float:
        """Calculate position size multiplier based on all factors.
        
        Requirements 5.4, 5.5, 5.6, 7.3, 7.4:
        - Below 60: 0.0 (rejected)
        - 60-70: 0.7x
        - 70-80: 1.0x
        - Above 80: 1.5x
        - ADX adjustments for ranging/trending markets
        - S/R proximity adjustments
        """
        # Base multiplier from confidence
        if confidence < self.MIN_CONFIDENCE:
            return 0.0
        elif confidence < self.MID_CONFIDENCE:
            multiplier = self.LOW_CONFIDENCE_MULTIPLIER
        elif confidence < self.HIGH_CONFIDENCE:
            multiplier = 1.0
        else:
            multiplier = self.HIGH_CONFIDENCE_MULTIPLIER
        
        # ADX-based adjustment
        adx_multiplier = self._get_adx_multiplier(features)
        multiplier *= adx_multiplier
        
        # S/R proximity adjustment
        sr_multiplier = self.sr_analyzer.get_position_size_multiplier(
            features.tf_1min.close, signal, sr_levels
        )
        multiplier *= sr_multiplier
        
        return multiplier
    
    def _get_adx_multiplier(self, features: MTFFeatures) -> float:
        """Get position multiplier based on ADX across timeframes.
        
        Requirements 7.3, 7.4:
        - Reduce by 40% when >1 timeframe has ADX < 20
        - Full size when all timeframes have ADX > 25
        """
        adx_values = [
            features.tf_1min.adx,
            features.tf_5min.adx,
            features.tf_15min.adx,
        ]
        
        # Count ranging timeframes (ADX < 20)
        ranging_count = sum(1 for adx in adx_values if adx < self.RANGING_ADX)
        
        # Count trending timeframes (ADX > 25)
        trending_count = sum(1 for adx in adx_values if adx > self.TRENDING_ADX)
        
        if ranging_count > 1:
            logger.debug(f"Ranging market ({ranging_count} TFs with ADX < 20), reducing size by 40%")
            return 1.0 - self.RANGING_MARKET_REDUCTION
        
        if trending_count == 3:
            logger.debug("All timeframes trending (ADX > 25), full position size")
            return 1.0
        
        return 1.0
    
    def _create_bypass_result(
        self,
        symbol: str,
        signal: str,
        features: MTFFeatures,
    ) -> MTFSignalResult:
        """Create result when MTF is bypassed."""
        return MTFSignalResult(
            symbol=symbol,
            signal=signal,
            mtf_confidence=100.0,
            trend_bias=TrendBias.from_ema_values(100, 100),
            trend_aligned=True,
            momentum_aligned=True,
            rsi_alignment_count=3,
            macd_aligned=True,
            volume_confirmed=True,
            sr_levels=SRLevels(
                nearest_support=features.tf_1min.close * 0.98,
                nearest_resistance=features.tf_1min.close * 1.02,
                daily_high=features.tf_daily.high,
                daily_low=features.tf_daily.low,
                daily_close=features.tf_daily.close,
            ),
            position_size_multiplier=1.0,
            rejection_reason=None,
        )
    
    def _create_rejected_result(
        self,
        symbol: str,
        signal: str,
        features: MTFFeatures,
        trend_bias: TrendBias,
        rejection_reason: str,
    ) -> MTFSignalResult:
        """Create result for rejected signal."""
        return MTFSignalResult(
            symbol=symbol,
            signal=signal,
            mtf_confidence=0.0,
            trend_bias=trend_bias,
            trend_aligned=False,
            momentum_aligned=False,
            rsi_alignment_count=0,
            macd_aligned=False,
            volume_confirmed=False,
            sr_levels=SRLevels(
                nearest_support=features.tf_1min.close * 0.98,
                nearest_resistance=features.tf_1min.close * 1.02,
                daily_high=features.tf_daily.high,
                daily_low=features.tf_daily.low,
                daily_close=features.tf_daily.close,
            ),
            position_size_multiplier=0.0,
            rejection_reason=rejection_reason,
        )
