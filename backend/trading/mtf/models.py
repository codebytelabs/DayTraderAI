"""
Multi-Timeframe Analysis Data Models.

Defines dataclasses for MTF features, trend bias, support/resistance levels,
signal results, and configuration.

Requirements: 9.1, 9.2, 9.3, 9.4
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class TrendDirection(Enum):
    """Trend direction classification."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class TimeframeFeatures:
    """Features calculated for a single timeframe.
    
    Contains all technical indicators computed for one timeframe (1-min, 5-min, 15-min, or daily).
    """
    timeframe: str
    ema_short: float  # EMA(9)
    ema_long: float   # EMA(21)
    ema_50: float     # EMA(50) - for trend analysis
    ema_200: float    # EMA(200) - for trend analysis
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    adx: float
    volume: float
    volume_avg: float
    volume_ratio: float
    high: float
    low: float
    close: float
    
    def is_valid(self) -> bool:
        """Check if all required features have valid values."""
        return all([
            self.ema_short > 0,
            self.ema_long > 0,
            0 <= self.rsi <= 100,
            self.adx >= 0,
            self.volume >= 0,
            self.close > 0,
        ])



@dataclass
class MTFFeatures:
    """Features aggregated across all timeframes.
    
    Contains TimeframeFeatures for each analyzed timeframe.
    """
    symbol: str
    tf_1min: TimeframeFeatures
    tf_5min: TimeframeFeatures
    tf_15min: TimeframeFeatures
    tf_daily: TimeframeFeatures
    timestamp: datetime
    
    def get_timeframe(self, tf: str) -> Optional[TimeframeFeatures]:
        """Get features for a specific timeframe."""
        mapping = {
            '1min': self.tf_1min,
            '5min': self.tf_5min,
            '15min': self.tf_15min,
            'daily': self.tf_daily,
        }
        return mapping.get(tf)
    
    def all_valid(self) -> bool:
        """Check if all timeframes have valid features."""
        return all([
            self.tf_1min.is_valid(),
            self.tf_5min.is_valid(),
            self.tf_15min.is_valid(),
            self.tf_daily.is_valid(),
        ])


@dataclass
class TrendBias:
    """Trend bias determined from higher timeframes.
    
    Based on 15-minute EMA(50) vs EMA(200) relationship.
    """
    direction: TrendDirection
    strength: float  # 0-100 scale
    daily_aligned: bool  # True if daily trend matches 15-min trend
    ema_diff_pct: float  # Percentage difference between EMA(50) and EMA(200)
    
    @classmethod
    def from_ema_values(cls, ema_50: float, ema_200: float, daily_direction: Optional[TrendDirection] = None) -> 'TrendBias':
        """Create TrendBias from EMA values.
        
        Classification rules (Requirements 2.2, 2.3, 2.4):
        - Bullish: EMA(50) > EMA(200) by more than 0.1%
        - Bearish: EMA(50) < EMA(200) by more than 0.1%
        - Neutral: EMAs within 0.1% of each other
        """
        if ema_200 == 0:
            return cls(
                direction=TrendDirection.NEUTRAL,
                strength=0.0,
                daily_aligned=False,
                ema_diff_pct=0.0,
            )
        
        ema_diff_pct = ((ema_50 - ema_200) / ema_200) * 100
        
        # Classification threshold: 0.1%
        threshold = 0.1
        
        if ema_diff_pct > threshold:
            direction = TrendDirection.BULLISH
            strength = min(100.0, abs(ema_diff_pct) * 20)  # Scale to 0-100
        elif ema_diff_pct < -threshold:
            direction = TrendDirection.BEARISH
            strength = min(100.0, abs(ema_diff_pct) * 20)
        else:
            direction = TrendDirection.NEUTRAL
            strength = 0.0
        
        daily_aligned = daily_direction == direction if daily_direction else False
        
        return cls(
            direction=direction,
            strength=strength,
            daily_aligned=daily_aligned,
            ema_diff_pct=ema_diff_pct,
        )


@dataclass
class SRLevels:
    """Support and resistance levels from higher timeframes."""
    nearest_support: float
    nearest_resistance: float
    daily_high: float
    daily_low: float
    daily_close: float
    swing_highs: List[float] = field(default_factory=list)
    swing_lows: List[float] = field(default_factory=list)
    
    def is_near_resistance(self, price: float, threshold_pct: float = 0.3) -> bool:
        """Check if price is within threshold of nearest resistance."""
        if self.nearest_resistance <= 0:
            return False
        distance_pct = abs(price - self.nearest_resistance) / self.nearest_resistance * 100
        return distance_pct <= threshold_pct
    
    def is_near_support(self, price: float, threshold_pct: float = 0.3) -> bool:
        """Check if price is within threshold of nearest support."""
        if self.nearest_support <= 0:
            return False
        distance_pct = abs(price - self.nearest_support) / self.nearest_support * 100
        return distance_pct <= threshold_pct



@dataclass
class MTFSignalResult:
    """Result of multi-timeframe signal evaluation.
    
    Contains all analysis results and the final decision on whether to take the trade.
    """
    symbol: str
    signal: str  # 'buy' or 'sell'
    mtf_confidence: float  # 0-100 scale
    trend_bias: TrendBias
    trend_aligned: bool
    momentum_aligned: bool
    rsi_alignment_count: int  # Number of timeframes with aligned RSI
    macd_aligned: bool
    volume_confirmed: bool
    sr_levels: SRLevels
    position_size_multiplier: float  # 0.7x, 1.0x, or 1.5x based on confidence
    rejection_reason: Optional[str] = None
    
    @property
    def should_trade(self) -> bool:
        """Determine if the signal should be traded."""
        return self.rejection_reason is None and self.mtf_confidence >= 60.0
    
    def get_position_size_multiplier(self) -> float:
        """Get position size multiplier based on confidence.
        
        Requirements 5.4, 5.5, 5.6:
        - Below 60: Rejected (0.0x)
        - 60-70: 0.7x normal
        - 70-80: 1.0x normal
        - Above 80: 1.5x normal
        """
        if self.mtf_confidence < 60:
            return 0.0
        elif self.mtf_confidence < 70:
            return 0.7
        elif self.mtf_confidence < 80:
            return 1.0
        else:
            return 1.5


@dataclass
class MTFConfig:
    """Configuration for MTF analysis.
    
    Requirements 9.1, 9.2, 9.3, 9.4:
    - ENABLE_MTF_ANALYSIS: Enable/disable MTF checks
    - weights: Custom timeframe weights
    - min_confidence: Minimum confidence threshold
    - strict_mode: Require all timeframes to align
    """
    enabled: bool = True
    strict_mode: bool = False
    min_confidence: float = 60.0
    weights: Dict[str, float] = field(default_factory=dict)
    
    # Default weights (Requirements 5.1)
    DEFAULT_WEIGHTS: Dict[str, float] = field(
        default_factory=lambda: {'15min': 0.40, '5min': 0.35, '1min': 0.25},
        repr=False,
    )
    
    def __post_init__(self):
        """Initialize with default weights if not provided."""
        if not self.weights:
            self.weights = dict(self.DEFAULT_WEIGHTS)
    
    def get_weights(self) -> Dict[str, float]:
        """Get the effective weights (custom or default).
        
        Requirement 9.2: Custom weights override defaults.
        """
        if self.weights:
            return self.weights
        return dict(self.DEFAULT_WEIGHTS)
    
    def validate_weights(self) -> bool:
        """Validate that weights sum to approximately 1.0."""
        total = sum(self.get_weights().values())
        return 0.99 <= total <= 1.01
    
    @classmethod
    def from_settings(cls, settings) -> 'MTFConfig':
        """Create MTFConfig from application settings.
        
        Requirement 9.1: Configuration from settings.
        """
        enabled = getattr(settings, 'ENABLE_MTF_ANALYSIS', True)
        strict_mode = getattr(settings, 'MTF_STRICT_MODE', False)
        min_confidence = getattr(settings, 'MTF_MIN_CONFIDENCE', 60.0)
        
        # Parse custom weights if provided
        weights = {}
        custom_weights = getattr(settings, 'MTF_WEIGHTS', None)
        if custom_weights:
            if isinstance(custom_weights, dict):
                weights = custom_weights
            elif isinstance(custom_weights, str):
                # Parse string format: "15min:0.40,5min:0.35,1min:0.25"
                try:
                    for pair in custom_weights.split(','):
                        tf, weight = pair.strip().split(':')
                        weights[tf.strip()] = float(weight.strip())
                except (ValueError, AttributeError):
                    weights = {}
        
        return cls(
            enabled=enabled,
            strict_mode=strict_mode,
            min_confidence=min_confidence,
            weights=weights,
        )
    
    def should_bypass(self) -> bool:
        """Check if MTF analysis should be bypassed.
        
        Requirement 9.1: When ENABLE_MTF_ANALYSIS=False, bypass all checks.
        """
        return not self.enabled
