# Configuration for momentum detection system

from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class MomentumConfig:
    """Configuration for momentum detection system"""
    
    # Feature flag
    enabled: bool = False
    
    # Indicator thresholds
    adx_threshold: float = 25.0
    adx_period: int = 14
    volume_threshold: float = 1.5
    volume_lookback: int = 20
    trend_threshold: float = 0.7
    include_rsi: bool = False
    
    # Bracket adjustment parameters
    extended_target_r: float = 3.0
    progressive_stop_r: float = 0.5
    use_atr_trailing: bool = True
    atr_trailing_multiplier: float = 2.0
    
    # Risk management
    max_api_retries: int = 3
    data_freshness_seconds: int = 60
    
    # Evaluation trigger
    evaluation_profit_r: float = 0.75
    
    def __post_init__(self):
        """Validate configuration values"""
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration parameters"""
        errors = []
        
        if not (20.0 <= self.adx_threshold <= 35.0):
            errors.append(f"ADX threshold {self.adx_threshold} must be between 20-35")
        
        if not (1.2 <= self.volume_threshold <= 2.0):
            errors.append(f"Volume threshold {self.volume_threshold} must be between 1.2-2.0")
        
        if not (0.6 <= self.trend_threshold <= 0.8):
            errors.append(f"Trend threshold {self.trend_threshold} must be between 0.6-0.8")
        
        if errors:
            error_msg = "Configuration validation errors: " + "; ".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("✅ Momentum configuration validated")
    
    @classmethod
    def default_conservative(cls) -> 'MomentumConfig':
        """Conservative configuration"""
        return cls(
            enabled=False,
            adx_threshold=30.0,
            volume_threshold=1.8,
            trend_threshold=0.75,
            extended_target_r=3.0,
            progressive_stop_r=0.5
        )
    
    def log_config(self):
        """Log current configuration"""
        logger.info(f"📊 Momentum System Configuration:")
        logger.info(f"   Enabled: {self.enabled}")
        logger.info(f"   ADX Threshold: {self.adx_threshold}")
        logger.info(f"   Volume Threshold: {self.volume_threshold}x")
        logger.info(f"   Trend Threshold: {self.trend_threshold}")
        logger.info(f"   Extended Target: +{self.extended_target_r}R")
        logger.info(f"   Progressive Stop: +{self.progressive_stop_r}R")
