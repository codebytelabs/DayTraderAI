"""
Adaptive Parameters Module
Sprint 3: Dynamic parameter adjustment based on performance

Provides real-time parameter optimization:
- Dynamic stop loss adjustment
- Dynamic take profit adjustment
- Position sizing optimization
- Entry criteria refinement
- Real-time parameter updates
"""

from .parameter_optimizer import ParameterOptimizer
from .stop_loss_adjuster import StopLossAdjuster
from .take_profit_adjuster import TakeProfitAdjuster
from .position_sizer import AdaptivePositionSizer
from .entry_refiner import EntryRefiner

__all__ = [
    'ParameterOptimizer',
    'StopLossAdjuster',
    'TakeProfitAdjuster',
    'AdaptivePositionSizer',
    'EntryRefiner'
]

__version__ = '1.0.0'
