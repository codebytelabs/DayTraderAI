"""
Parameter Optimization Module

Uses scikit-opt (PSO/GA) with walk-forward validation to optimize trading parameters.
Prevents overfitting through proper train/validation splits and Sharpe ratio fitness.
"""

from .models import (
    OptimizationResult,
    ValidationResult,
    PerformanceMetrics,
    REGIME_PARAMETERS,
    MOMENTUM_PARAMETERS,
)
from .optimizer import ParameterOptimizer
from .validator import WalkForwardValidator
from .fitness import FitnessCalculator
from .logger import ResultsLogger
from .integration import OptimizationIntegration, run_integrated_optimization

__all__ = [
    "OptimizationResult",
    "ValidationResult",
    "PerformanceMetrics",
    "REGIME_PARAMETERS",
    "MOMENTUM_PARAMETERS",
    "ParameterOptimizer",
    "WalkForwardValidator",
    "FitnessCalculator",
    "ResultsLogger",
    "OptimizationIntegration",
    "run_integrated_optimization",
]
