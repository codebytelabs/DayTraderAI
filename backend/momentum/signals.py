# Data models for momentum signals

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class MomentumSignal:
    """Result of momentum validation"""
    
    # Decision
    extend: bool
    
    # Indicator values
    adx: float = 0.0
    volume_ratio: float = 0.0
    trend_strength: float = 0.0
    rsi: Optional[float] = None
    
    # Metadata
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    symbol: str = ""
    current_profit_r: float = 0.0
    
    # Validation flags
    adx_pass: bool = False
    volume_pass: bool = False
    trend_pass: bool = False
    data_fresh: bool = True
    
    @property
    def consensus_score(self) -> float:
        """Calculate consensus score (0-1)"""
        total = 3
        if self.rsi is not None:
            total = 4
        
        passing = sum([
            self.adx_pass,
            self.volume_pass,
            self.trend_pass,
            bool(self.rsi and self.rsi > 60) if self.rsi is not None else False
        ])
        
        return passing / total
    
    def log_signal(self):
        """Log the momentum signal"""
        decision = "🎯 EXTEND TARGET" if self.extend else "⏹️ KEEP STANDARD"
        
        logger.info(f"📊 Momentum Signal - {self.symbol} | {decision}")
        logger.info(f"   Profit: +{self.current_profit_r:.2f}R")
        logger.info(f"   ADX: {self.adx:.1f} {'✅' if self.adx_pass else '❌'}")
        logger.info(f"   Volume: {self.volume_ratio:.2f}x {'✅' if self.volume_pass else '❌'}")
        logger.info(f"   Trend: {self.trend_strength:.2f} {'✅' if self.trend_pass else '❌'}")
        if self.rsi is not None:
            logger.info(f"   RSI: {self.rsi:.1f}")
        logger.info(f"   Reason: {self.reason}")

@dataclass
class PositionEnhancement:
    """Enhanced position model with momentum tracking"""
    
    symbol: str
    entry_price: float
    quantity: int
    initial_stop: float
    initial_target: float
    
    brackets_adjusted: bool = False
    target_extended: bool = False
    momentum_signal: Optional[MomentumSignal] = None
    adjustment_timestamp: Optional[datetime] = None
