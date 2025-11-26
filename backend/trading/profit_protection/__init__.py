"""
Intelligent Profit Protection System

This module provides dynamic trailing stops, R-multiple based profit taking,
and intelligent order conflict resolution to ensure profits are systematically
protected and locked in.
"""

from .position_state_tracker import PositionStateTracker, get_position_tracker
from .intelligent_stop_manager import IntelligentStopManager, get_stop_manager
from .profit_taking_engine import ProfitTakingEngine, get_profit_engine
from .profit_protection_manager import ProfitProtectionManager, get_profit_protection_manager
from .order_sequencer import OrderSequencer, get_order_sequencer, ConflictType, OrderConflict, SequenceResult
from .error_handler import (
    ErrorHandler, get_error_handler, ErrorContext, RecoveryAction,
    ErrorSeverity, ErrorCategory, CircuitBreaker, SystemState,
    RetryableError, ConflictError, StateError
)
from .models import (
    PositionState, ProtectionState, ProtectionStateEnum,
    ShareAllocation, PartialProfit
)

__all__ = [
    'PositionStateTracker',
    'get_position_tracker',
    'IntelligentStopManager',
    'get_stop_manager',
    'ProfitTakingEngine',
    'get_profit_engine',
    'ProfitProtectionManager',
    'get_profit_protection_manager',
    'OrderSequencer',
    'get_order_sequencer',
    'ConflictType',
    'OrderConflict',
    'SequenceResult',
    'ErrorHandler',
    'get_error_handler',
    'ErrorContext',
    'RecoveryAction',
    'ErrorSeverity',
    'ErrorCategory',
    'CircuitBreaker',
    'SystemState',
    'RetryableError',
    'ConflictError',
    'StateError',
    'PositionState',
    'ProtectionState',
    'ProtectionStateEnum',
    'ShareAllocation',
    'PartialProfit',
]
