# Momentum-based bracket adjustment system

__version__ = "1.0.0"

from .config import MomentumConfig
from .signals import MomentumSignal
from .validator import MomentumSignalValidator
from .engine import BracketAdjustmentEngine

__all__ = [
    'MomentumConfig',
    'MomentumSignal',
    'MomentumSignalValidator',
    'BracketAdjustmentEngine'
]
