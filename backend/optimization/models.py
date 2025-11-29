"""
Data models for parameter optimization system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime


@dataclass
class PerformanceMetrics:
    """Performance metrics from backtesting or live trading."""
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    total_return: float
    max_drawdown: float
    
    def to_dict(self) -> Dict:
        return {
            "sharpe_ratio": self.sharpe_ratio,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "total_trades": self.total_trades,
            "total_return": self.total_return,
            "max_drawdown": self.max_drawdown,
        }


@dataclass
class OptimizationResult:
    """Result from parameter optimization."""
    best_parameters: Dict[str, float]
    best_fitness: float
    metrics: PerformanceMetrics
    iterations_run: int
    convergence_history: List[float] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "best_parameters": self.best_parameters,
            "best_fitness": self.best_fitness,
            "metrics": self.metrics.to_dict(),
            "iterations_run": self.iterations_run,
            "convergence_history": self.convergence_history,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ValidationResult:
    """Result from walk-forward validation."""
    in_sample_metrics: PerformanceMetrics
    out_sample_metrics: PerformanceMetrics
    overfitting_detected: bool
    degradation_percent: float
    
    def to_dict(self) -> Dict:
        return {
            "in_sample_metrics": self.in_sample_metrics.to_dict(),
            "out_sample_metrics": self.out_sample_metrics.to_dict(),
            "overfitting_detected": self.overfitting_detected,
            "degradation_percent": self.degradation_percent,
        }


@dataclass
class VerificationResult:
    """Result from comparing pre/post optimization performance."""
    pre_metrics: PerformanceMetrics
    post_metrics: PerformanceMetrics
    win_rate_improvement: float
    profit_factor_improvement: float
    sharpe_improvement: float
    
    def to_dict(self) -> Dict:
        return {
            "pre_metrics": self.pre_metrics.to_dict(),
            "post_metrics": self.post_metrics.to_dict(),
            "win_rate_improvement": self.win_rate_improvement,
            "profit_factor_improvement": self.profit_factor_improvement,
            "sharpe_improvement": self.sharpe_improvement,
        }


# Parameter spaces with valid bounds
# Format: parameter_name -> (min_value, max_value)

REGIME_PARAMETERS: Dict[str, Tuple[float, float]] = {
    # Extreme Fear regime
    "extreme_fear_profit_target_r": (2.5, 5.0),
    "extreme_fear_trailing_stop_r": (1.0, 2.0),
    "extreme_fear_partial_profit_1_r": (2.0, 4.0),
    "extreme_fear_partial_profit_2_r": (3.5, 6.0),
    # Fear regime
    "fear_profit_target_r": (2.0, 4.0),
    "fear_trailing_stop_r": (0.75, 1.5),
    "fear_partial_profit_1_r": (1.5, 3.0),
    "fear_partial_profit_2_r": (2.5, 5.0),
    # Neutral regime
    "neutral_profit_target_r": (1.5, 3.0),
    "neutral_trailing_stop_r": (0.5, 1.0),
    "neutral_partial_profit_1_r": (1.0, 2.5),
    "neutral_partial_profit_2_r": (2.0, 4.0),
    # Greed regime
    "greed_profit_target_r": (1.5, 3.5),
    "greed_trailing_stop_r": (0.75, 1.5),
    "greed_partial_profit_1_r": (1.0, 2.5),
    "greed_partial_profit_2_r": (2.0, 4.5),
    # Extreme Greed regime
    "extreme_greed_profit_target_r": (2.0, 4.0),
    "extreme_greed_trailing_stop_r": (1.0, 2.0),
    "extreme_greed_partial_profit_1_r": (1.5, 3.0),
    "extreme_greed_partial_profit_2_r": (3.0, 5.5),
}

MOMENTUM_PARAMETERS: Dict[str, Tuple[float, float]] = {
    "adx_threshold": (20.0, 35.0),
    "volume_threshold": (1.2, 2.0),
    "trend_threshold": (0.6, 0.8),
    "atr_trailing_multiplier": (1.5, 3.0),
    "evaluation_profit_r": (0.5, 1.0),
}

CONFIDENCE_PARAMETERS: Dict[str, Tuple[float, float]] = {
    "base_long_threshold": (0.45, 0.60),
    "base_short_threshold": (0.50, 0.65),
}

# Combined parameter space for full optimization
ALL_PARAMETERS: Dict[str, Tuple[float, float]] = {
    **REGIME_PARAMETERS,
    **MOMENTUM_PARAMETERS,
    **CONFIDENCE_PARAMETERS,
}


def validate_parameters(parameters: Dict[str, float], bounds: Dict[str, Tuple[float, float]]) -> bool:
    """
    Validate that all parameters are within their defined bounds.
    
    Args:
        parameters: Dictionary of parameter name -> value
        bounds: Dictionary of parameter name -> (min, max)
        
    Returns:
        True if all parameters are valid, False otherwise
    """
    for name, value in parameters.items():
        if name not in bounds:
            continue  # Skip unknown parameters
        min_val, max_val = bounds[name]
        if not (min_val <= value <= max_val):
            return False
    return True


def clamp_parameters(parameters: Dict[str, float], bounds: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
    """
    Clamp all parameters to their valid bounds.
    
    Args:
        parameters: Dictionary of parameter name -> value
        bounds: Dictionary of parameter name -> (min, max)
        
    Returns:
        Dictionary with all values clamped to valid ranges
    """
    result = {}
    for name, value in parameters.items():
        if name in bounds:
            min_val, max_val = bounds[name]
            result[name] = max(min_val, min(max_val, value))
        else:
            result[name] = value
    return result
