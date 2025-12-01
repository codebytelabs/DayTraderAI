#!/usr/bin/env python3
"""
Momentum Wave Rider Data Models

Data classes for the momentum scanner system including:
- MomentumCandidate: Stock candidate with momentum scores and resistance analysis
- PositionSize: Position sizing result with confidence tiers
- ProfitAction: Profit protection action recommendations
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class CrossoverType(Enum):
    """EMA crossover classification."""
    FRESH = "fresh"           # 0.05-0.3% - ideal entry
    DEVELOPING = "developing"  # 0.3-1.0% - acceptable
    EXTENDED = "extended"      # >1.0% - reduce confidence


class EntryQuality(Enum):
    """Entry point quality classification."""
    IDEAL = "ideal"
    ACCEPTABLE = "acceptable"
    POOR = "poor"


class UpsideQuality(Enum):
    """Upside potential classification - room to run."""
    EXCELLENT = "excellent"  # >5% to resistance
    GOOD = "good"            # 3-5% to resistance
    SOME = "some"            # 2-3% to resistance
    LIMITED = "limited"      # 1-2% to resistance
    POOR = "poor"            # <1% to resistance


@dataclass
class MomentumCandidate:
    """
    Momentum candidate with full scoring and resistance analysis.
    
    This is the core data model for the momentum wave rider system.
    It includes both momentum indicators AND upside potential analysis
    to ensure we only trade stocks with room to run.
    """
    # Basic info
    symbol: str
    price: float
    volume_ratio: float  # Current volume / 20-period average
    
    # Overall scores
    momentum_score: int = 0  # 0-100 total score
    confidence: int = 0      # 0-100 (score with bonuses/penalties)
    
    # Component scores (0-25, 0-20, 0-20, 0-25, 0-10 = 100 max)
    volume_score: int = 0     # 0-25 pts
    trend_strength_score: int = 0  # 0-20 pts (ADX/RSI)
    breakout_score: int = 0   # 0-20 pts
    upside_score: int = 0     # 0-25 pts (NEW - room to run)
    trend_score: int = 0      # 0-10 pts
    
    # Technical indicators
    adx: float = 0.0
    rsi: float = 50.0
    ema_diff: float = 0.0     # EMA9 - EMA21 as percentage
    vwap_distance: float = 0.0  # Distance from VWAP as percentage
    
    # Resistance analysis (NEW - prevents chasing tops)
    resistance_level: float = 0.0   # Next major resistance
    support_level: float = 0.0      # Recent support
    distance_to_resistance: float = 0.0  # Percentage to resistance
    risk_reward_ratio: float = 0.0  # Potential reward / risk
    
    # Classification
    crossover_type: str = "developing"  # 'fresh', 'developing', 'extended'
    entry_quality: str = "acceptable"   # 'ideal', 'acceptable', 'poor'
    upside_quality: str = "some"        # 'excellent', 'good', 'some', 'limited', 'poor'
    
    # Direction
    direction: str = "long"  # 'long' or 'short'
    
    def __post_init__(self):
        """Validate and clamp scores to valid ranges."""
        self.momentum_score = max(0, min(100, self.momentum_score))
        self.confidence = max(0, min(100, self.confidence))
        self.volume_score = max(0, min(25, self.volume_score))
        self.trend_strength_score = max(0, min(20, self.trend_strength_score))
        self.breakout_score = max(0, min(20, self.breakout_score))
        self.upside_score = max(0, min(25, self.upside_score))
        self.trend_score = max(0, min(10, self.trend_score))


@dataclass
class PositionSize:
    """
    Position sizing result based on confidence level.
    
    Confidence Tiers:
    - 90+: 15% max (high conviction)
    - 80-89: 12% max
    - 70-79: 10% max
    - 60-69: 8% max
    - <60: Skip trade
    """
    shares: int = 0
    dollar_amount: float = 0.0
    percent_of_equity: float = 0.0
    confidence_tier: str = "low"  # 'high', 'medium', 'low'
    volume_bonus_applied: bool = False
    skip_trade: bool = False
    skip_reason: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if this is a valid position to take."""
        return not self.skip_trade and self.shares > 0


@dataclass
class ProfitAction:
    """
    Profit protection action recommendation.
    
    Actions:
    - hold: Keep position as-is
    - partial_profit: Take partial profit (e.g., 50% at 2R)
    - tighten_stop: Tighten trailing stop
    - exit: Exit the position entirely
    """
    action: str = "hold"  # 'hold', 'partial_profit', 'tighten_stop', 'exit'
    r_multiple: float = 0.0
    new_stop_price: Optional[float] = None
    shares_to_sell: Optional[int] = None
    reason: str = ""
    
    @property
    def requires_action(self) -> bool:
        """Check if this action requires trading."""
        return self.action != "hold"


@dataclass
class MomentumScore:
    """
    Detailed momentum score breakdown.
    
    Total possible: 100 points
    - Volume: 0-25 pts
    - Momentum (ADX/RSI): 0-20 pts
    - Breakout: 0-20 pts
    - Upside Potential: 0-25 pts
    - Trend: 0-10 pts
    - Penalties: up to -35 pts
    """
    total_score: int = 0
    
    # Component scores
    volume_score: int = 0
    momentum_score: int = 0
    breakout_score: int = 0
    upside_score: int = 0
    trend_score: int = 0
    
    # Penalties applied
    overbought_penalty: int = 0      # -20 if RSI > 75 or < 25
    extended_penalty: int = 0        # -15 if EMA diff > 1%
    insufficient_room_penalty: int = 0  # -15 if upside < 1%
    
    # Bonuses applied
    rr_bonus: int = 0  # +5 if R/R > 3:1, +3 if R/R > 2:1
    vwap_bonus: int = 0  # +5 if within 0.5% of VWAP
    timeframe_bonus: int = 0  # +10 if multi-TF aligned
    
    def calculate_total(self) -> int:
        """Calculate total score from components."""
        base = (
            self.volume_score + 
            self.momentum_score + 
            self.breakout_score + 
            self.upside_score + 
            self.trend_score
        )
        penalties = (
            self.overbought_penalty + 
            self.extended_penalty + 
            self.insufficient_room_penalty
        )
        bonuses = self.rr_bonus + self.vwap_bonus + self.timeframe_bonus
        
        self.total_score = max(0, min(100, base - penalties + bonuses))
        return self.total_score
