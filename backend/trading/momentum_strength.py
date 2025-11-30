"""
Momentum Strength Calculator - Calculates composite momentum strength for regime confirmation.

Based on professional intraday trading research:
- Combines ADX, volume ratio, and trend strength into a single 0-1 score
- Used to confirm or override simple regime-based position sizing
- Strong momentum in extreme greed = ride the wave (1.2x)
- Weak momentum in extreme greed = protect against reversal (0.7x)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple, Optional
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from momentum.indicators import ADXCalculator, VolumeAnalyzer, TrendStrengthCalculator

logger = logging.getLogger(__name__)


@dataclass
class MomentumStrengthResult:
    """Result of momentum strength calculation"""
    
    # Composite score (0.0 to 1.0)
    score: float
    
    # Individual indicator values
    adx: float
    volume_ratio: float
    trend_strength: float
    
    # Confirmation flags
    adx_confirmed: bool
    volume_confirmed: bool
    trend_confirmed: bool
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    data_fresh: bool = True
    
    @property
    def confirmed_count(self) -> int:
        """Number of confirmed indicators"""
        return sum([self.adx_confirmed, self.volume_confirmed, self.trend_confirmed])
    
    @property
    def is_strong(self) -> bool:
        """Momentum is strong (>0.8)"""
        return self.score > 0.8
    
    @property
    def is_weak(self) -> bool:
        """Momentum is weak (<0.5)"""
        return self.score < 0.5
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging/API"""
        return {
            "score": round(self.score, 3),
            "adx": round(self.adx, 1),
            "adx_confirmed": self.adx_confirmed,
            "volume_ratio": round(self.volume_ratio, 2),
            "volume_confirmed": self.volume_confirmed,
            "trend_strength": round(self.trend_strength, 3),
            "trend_confirmed": self.trend_confirmed,
            "confirmed_count": self.confirmed_count,
            "is_strong": self.is_strong,
            "is_weak": self.is_weak,
            "data_fresh": self.data_fresh,
        }


class MomentumStrengthCalculator:
    """
    Calculates composite momentum strength score (0-1).
    
    Combines three indicators with equal weighting:
    1. ADX (trend strength) - threshold 25
    2. Volume ratio (vs average) - threshold 1.5x
    3. Trend strength (composite) - threshold 0.7
    
    Each indicator contributes 1/3 to the final score.
    """
    
    # Thresholds for "confirmed" status
    ADX_THRESHOLD = 25.0
    VOLUME_THRESHOLD = 1.5
    TREND_THRESHOLD = 0.7
    
    # Validation bounds
    ADX_MIN = 0.0
    ADX_MAX = 100.0
    ADX_DEFAULT = 25.0
    
    VOLUME_MIN = 0.0
    VOLUME_MAX = 10.0
    VOLUME_DEFAULT = 1.0
    
    TREND_MIN = 0.0
    TREND_MAX = 1.0
    TREND_DEFAULT = 0.5
    
    def __init__(self, adx_period: int = 14, volume_lookback: int = 20):
        """
        Initialize calculator with indicator instances.
        
        Args:
            adx_period: Period for ADX calculation (default 14)
            volume_lookback: Lookback period for volume average (default 20)
        """
        self.adx_calculator = ADXCalculator(period=adx_period)
        self.volume_analyzer = VolumeAnalyzer(lookback_period=volume_lookback)
        self.trend_calculator = TrendStrengthCalculator()
        
        logger.info(f"MomentumStrengthCalculator initialized: ADX period={adx_period}, volume lookback={volume_lookback}")
    
    def calculate_strength(
        self,
        high: List[float],
        low: List[float],
        close: List[float],
        volume: List[float]
    ) -> MomentumStrengthResult:
        """
        Calculate composite momentum strength from price/volume data.
        
        Args:
            high: List of high prices
            low: List of low prices
            close: List of close prices
            volume: List of volume values
            
        Returns:
            MomentumStrengthResult with score (0-1) and component details
        """
        try:
            # Calculate individual indicators
            raw_adx = self.adx_calculator.calculate(high, low, close)
            raw_volume_ratio = self.volume_analyzer.calculate_volume_ratio(volume)
            raw_trend = self.trend_calculator.calculate(close, high, low)
            
            # Validate and sanitize inputs
            adx, volume_ratio, trend_strength = self.validate_inputs(
                raw_adx, raw_volume_ratio, raw_trend
            )
            
            # Check confirmation status
            adx_confirmed = adx >= self.ADX_THRESHOLD
            volume_confirmed = volume_ratio >= self.VOLUME_THRESHOLD
            trend_confirmed = trend_strength >= self.TREND_THRESHOLD
            
            # Calculate composite score (equal weighting)
            # Normalize each component to 0-1 range, then average
            adx_score = self._normalize_adx(adx)
            volume_score = self._normalize_volume(volume_ratio)
            trend_score = trend_strength  # Already 0-1
            
            # Equal weighting: 1/3 each
            composite_score = (adx_score + volume_score + trend_score) / 3.0
            
            # Ensure bounds
            composite_score = max(0.0, min(1.0, composite_score))
            
            result = MomentumStrengthResult(
                score=composite_score,
                adx=adx,
                volume_ratio=volume_ratio,
                trend_strength=trend_strength,
                adx_confirmed=adx_confirmed,
                volume_confirmed=volume_confirmed,
                trend_confirmed=trend_confirmed,
                data_fresh=True
            )
            
            logger.debug(
                f"Momentum strength: {composite_score:.3f} "
                f"(ADX={adx:.1f}{'✓' if adx_confirmed else ''}, "
                f"Vol={volume_ratio:.2f}x{'✓' if volume_confirmed else ''}, "
                f"Trend={trend_strength:.3f}{'✓' if trend_confirmed else ''})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating momentum strength: {e}")
            # Return neutral result on error
            return MomentumStrengthResult(
                score=0.5,
                adx=self.ADX_DEFAULT,
                volume_ratio=self.VOLUME_DEFAULT,
                trend_strength=self.TREND_DEFAULT,
                adx_confirmed=False,
                volume_confirmed=False,
                trend_confirmed=False,
                data_fresh=False
            )
    
    def calculate_strength_from_values(
        self,
        adx: float,
        volume_ratio: float,
        trend_strength: float
    ) -> MomentumStrengthResult:
        """
        Calculate momentum strength from pre-computed indicator values.
        Useful for testing and when indicators are already available.
        
        Args:
            adx: ADX value
            volume_ratio: Volume ratio (current/average)
            trend_strength: Trend strength score (0-1)
            
        Returns:
            MomentumStrengthResult with score and component details
        """
        # Validate and sanitize inputs
        adx, volume_ratio, trend_strength = self.validate_inputs(
            adx, volume_ratio, trend_strength
        )
        
        # Check confirmation status
        adx_confirmed = adx >= self.ADX_THRESHOLD
        volume_confirmed = volume_ratio >= self.VOLUME_THRESHOLD
        trend_confirmed = trend_strength >= self.TREND_THRESHOLD
        
        # Calculate composite score
        adx_score = self._normalize_adx(adx)
        volume_score = self._normalize_volume(volume_ratio)
        trend_score = trend_strength
        
        composite_score = (adx_score + volume_score + trend_score) / 3.0
        composite_score = max(0.0, min(1.0, composite_score))
        
        return MomentumStrengthResult(
            score=composite_score,
            adx=adx,
            volume_ratio=volume_ratio,
            trend_strength=trend_strength,
            adx_confirmed=adx_confirmed,
            volume_confirmed=volume_confirmed,
            trend_confirmed=trend_confirmed,
            data_fresh=True
        )
    
    def validate_inputs(
        self,
        adx: float,
        volume_ratio: float,
        trend_strength: float
    ) -> Tuple[float, float, float]:
        """
        Validate and sanitize indicator values.
        Invalid values are replaced with defaults.
        
        Args:
            adx: Raw ADX value
            volume_ratio: Raw volume ratio
            trend_strength: Raw trend strength
            
        Returns:
            Tuple of (sanitized_adx, sanitized_volume, sanitized_trend)
        """
        # Validate ADX
        if adx < self.ADX_MIN or adx > self.ADX_MAX:
            logger.warning(f"Invalid ADX value {adx}, using default {self.ADX_DEFAULT}")
            adx = self.ADX_DEFAULT
        
        # Validate volume ratio
        if volume_ratio < self.VOLUME_MIN or volume_ratio > self.VOLUME_MAX:
            logger.warning(f"Invalid volume ratio {volume_ratio}, using default {self.VOLUME_DEFAULT}")
            volume_ratio = self.VOLUME_DEFAULT
        
        # Validate trend strength (clamp to bounds)
        if trend_strength < self.TREND_MIN:
            logger.warning(f"Trend strength {trend_strength} below min, clamping to {self.TREND_MIN}")
            trend_strength = self.TREND_MIN
        elif trend_strength > self.TREND_MAX:
            logger.warning(f"Trend strength {trend_strength} above max, clamping to {self.TREND_MAX}")
            trend_strength = self.TREND_MAX
        
        return adx, volume_ratio, trend_strength
    
    def _normalize_adx(self, adx: float) -> float:
        """
        Normalize ADX to 0-1 range.
        ADX of 0 = 0, ADX of 50+ = 1 (very strong trend)
        """
        # ADX typically ranges 0-50 for practical purposes
        # Above 50 is extremely strong
        normalized = adx / 50.0
        return max(0.0, min(1.0, normalized))
    
    def _normalize_volume(self, volume_ratio: float) -> float:
        """
        Normalize volume ratio to 0-1 range.
        Ratio of 0.5 = 0, Ratio of 2.5+ = 1
        """
        # Volume ratio typically ranges 0.5 to 2.5 for meaningful signals
        # Below 0.5 is very low, above 2.5 is very high
        if volume_ratio <= 0.5:
            return 0.0
        elif volume_ratio >= 2.5:
            return 1.0
        else:
            # Linear interpolation from 0.5-2.5 to 0-1
            return (volume_ratio - 0.5) / 2.0
