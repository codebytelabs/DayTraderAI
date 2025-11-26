"""
Error Handler

Provides comprehensive error handling, recovery mechanisms, and alerting
for the Intelligent Profit Protection System.
"""

from typing import Optional, Dict, List, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import time
import traceback

from utils.logger import setup_logger

logger = setup_logger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories"""
    BROKER_API = "broker_api"
    NETWORK = "network"
    DATA_VALIDATION = "data_validation"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    TIMEOUT = "timeout"


class SystemState(str, Enum):
    """System operational states"""
    NORMAL = "normal"
    RECOVERY = "recovery"
    ERROR = "error"


# Custom exception classes
class RetryableError(Exception):
    """Error that can be retried"""
    pass


class ConflictError(Exception):
    """Order conflict error"""
    pass


class StateError(Exception):
    """State inconsistency error"""
    pass


@dataclass
class ErrorContext:
    """Context information for an error"""
    operation: str
    symbol: Optional[str]
    parameters: Dict[str, Any]
    timestamp: datetime
    stack_trace: str
    retry_count: int = 0


@dataclass
class RecoveryAction:
    """Recovery action to take for an error"""
    action_type: str  # retry, fallback, alert, abort
    parameters: Dict[str, Any]
    delay_seconds: float = 0.0
    max_attempts: int = 3


class CircuitBreaker:
    """Circuit breaker for preventing cascading failures"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker"""
        if self.last_failure_time is None:
            return True
        
        return (datetime.utcnow() - self.last_failure_time).total_seconds() > self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        self.state = "closed"
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.error(f"Circuit breaker OPENED after {self.failure_count} failures")


class OperationQueue:
    """Queue for offline operations"""
    
    def __init__(self, max_size: int = 1000):
        self.queue: List[Dict] = []
        self.max_size = max_size
    
    def enqueue(self, operation: Dict) -> bool:
        """Add operation to queue"""
        if len(self.queue) >= self.max_size:
            logger.warning("Operation queue full, dropping oldest operation")
            self.queue.pop(0)
        
        operation['queued_at'] = datetime.utcnow()
        self.queue.append(operation)
        return True
    
    def dequeue(self) -> Optional[Dict]:
        """Remove and return oldest operation"""
        if self.queue:
            return self.queue.pop(0)
        return None
    
    def size(self) -> int:
        """Get queue size"""
        return len(self.queue)
    
    def clear(self):
        """Clear all queued operations"""
        self.queue.clear()


class ErrorHandler:
    """
    Comprehensive error handling and recovery system.
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_history: List[Dict] = []
        self.recovery_strategies: Dict[str, RecoveryAction] = self._init_recovery_strategies()
        self.retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff
        self.system_state = SystemState.NORMAL
        self.operation_queue = OperationQueue()
        self.alert_callbacks: List[Callable] = []
        
        logger.info("✅ Error Handler initialized")
    
    def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        custom_recovery: Optional[RecoveryAction] = None
    ) -> RecoveryAction:
        """
        Handle an error with appropriate recovery strategy.
        """
        # Classify the error
        category = self._classify_error(error)
        severity = self._assess_severity(error, context)
        
        # Log the error
        self._log_error(error, context, category, severity)
        
        # Record in history
        self._record_error(error, context, category, severity)
        
        # Determine recovery action
        if custom_recovery:
            recovery_action = custom_recovery
        else:
            recovery_action = self._determine_recovery_action(error, context, category, severity)
        
        # Execute recovery if immediate
        if recovery_action.action_type == "immediate_retry":
            return self._execute_immediate_retry(context, recovery_action)
        elif recovery_action.action_type == "alert":
            self._send_alert(error, context, severity)
        
        return recovery_action
    
    def execute_with_retry(
        self,
        operation: Callable,
        context: ErrorContext,
        max_retries: int = 3,
        custom_delays: Optional[List[float]] = None
    ) -> Any:
        """
        Execute operation with retry logic and exponential backoff.
        """
        delays = custom_delays or self.retry_delays[:max_retries]
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Use circuit breaker for the operation
                circuit_breaker = self._get_circuit_breaker(context.operation)
                result = circuit_breaker.call(operation)
                
                if attempt > 0:
                    logger.info(f"Operation {context.operation} succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_error = e
                context.retry_count = attempt
                
                if attempt < max_retries:
                    delay = delays[attempt] if attempt < len(delays) else delays[-1]
                    
                    logger.warning(
                        f"Operation {context.operation} failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Operation {context.operation} failed after {max_retries + 1} attempts: {str(e)}"
                    )
        
        # All retries exhausted - alert operator
        self._handle_exhausted_retries(last_error, context)
        raise last_error
    
    def is_recoverable_error(self, error: Exception) -> bool:
        """Determine if an error is recoverable."""
        error_str = str(error).lower()
        
        # Network/timeout errors are usually recoverable
        recoverable_patterns = [
            'timeout', 'connection', 'network', 'temporary',
            'rate limit', 'throttle', 'busy', 'unavailable',
            'socket', 'dns', 'ssl'
        ]
        
        for pattern in recoverable_patterns:
            if pattern in error_str:
                return True
        
        # HTTP status codes that are recoverable
        if hasattr(error, 'status_code'):
            recoverable_codes = [429, 500, 502, 503, 504]
            if error.status_code in recoverable_codes:
                return True
        
        return False
    
    def enter_recovery_mode(self, reason: str):
        """Enter recovery mode - reject new positions"""
        self.system_state = SystemState.RECOVERY
        logger.warning(f"🔄 Entering RECOVERY mode: {reason}")
    
    def exit_recovery_mode(self):
        """Exit recovery mode after validation"""
        self.system_state = SystemState.NORMAL
        logger.info("✅ Exiting RECOVERY mode - system normal")
    
    def is_in_recovery_mode(self) -> bool:
        """Check if system is in recovery mode"""
        return self.system_state == SystemState.RECOVERY
    
    def queue_offline_operation(self, operation: Dict) -> bool:
        """Queue operation for later execution when offline"""
        return self.operation_queue.enqueue(operation)
    
    def process_queued_operations(self, executor: Callable) -> int:
        """Process all queued operations"""
        processed = 0
        while True:
            operation = self.operation_queue.dequeue()
            if operation is None:
                break
            try:
                executor(operation)
                processed += 1
            except Exception as e:
                logger.error(f"Failed to process queued operation: {e}")
                # Re-queue failed operation
                self.operation_queue.enqueue(operation)
                break
        return processed
    
    def register_alert_callback(self, callback: Callable):
        """Register callback for alerts"""
        self.alert_callbacks.append(callback)

    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_errors = [
            error for error in self.error_history
            if error['timestamp'] > cutoff_time
        ]
        
        if not recent_errors:
            return {
                'total_errors': 0,
                'by_category': {},
                'by_severity': {},
                'by_operation': {},
                'recovery_success_rate': 0.0
            }
        
        # Count by category
        by_category = {}
        for error in recent_errors:
            category = error['category']
            by_category[category] = by_category.get(category, 0) + 1
        
        # Count by severity
        by_severity = {}
        for error in recent_errors:
            severity = error['severity']
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Count by operation
        by_operation = {}
        for error in recent_errors:
            operation = error['operation']
            by_operation[operation] = by_operation.get(operation, 0) + 1
        
        # Calculate recovery success rate
        recovered_errors = sum(1 for error in recent_errors if error.get('recovered', False))
        recovery_rate = (recovered_errors / len(recent_errors)) * 100 if recent_errors else 0
        
        return {
            'total_errors': len(recent_errors),
            'by_category': by_category,
            'by_severity': by_severity,
            'by_operation': by_operation,
            'recovery_success_rate': recovery_rate
        }
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """Classify error into appropriate category"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        if 'timeout' in error_str or 'timeout' in error_type:
            return ErrorCategory.TIMEOUT
        elif any(term in error_str for term in ['connection', 'network', 'socket', 'dns']):
            return ErrorCategory.NETWORK
        elif any(term in error_str for term in ['api', 'broker', 'alpaca', 'rate limit']):
            return ErrorCategory.BROKER_API
        elif any(term in error_str for term in ['validation', 'invalid', 'format']):
            return ErrorCategory.DATA_VALIDATION
        elif any(term in error_str for term in ['memory', 'disk', 'cpu', 'system']):
            return ErrorCategory.SYSTEM
        else:
            return ErrorCategory.BUSINESS_LOGIC
    
    def _assess_severity(self, error: Exception, context: ErrorContext) -> ErrorSeverity:
        """Assess the severity of an error"""
        error_str = str(error).lower()
        
        # Critical errors
        if any(term in error_str for term in ['critical', 'fatal', 'corruption']):
            return ErrorSeverity.CRITICAL
        
        # High severity for profit protection operations
        if context.operation in ['stop_update', 'partial_exit', 'profit_taking']:
            return ErrorSeverity.HIGH
        
        # High severity for repeated failures
        if context.retry_count >= 2:
            return ErrorSeverity.HIGH
        
        # Medium severity for broker API errors
        if 'api' in error_str or 'broker' in error_str:
            return ErrorSeverity.MEDIUM
        
        return ErrorSeverity.LOW
    
    def _determine_recovery_action(
        self,
        error: Exception,
        context: ErrorContext,
        category: ErrorCategory,
        severity: ErrorSeverity
    ) -> RecoveryAction:
        """Determine appropriate recovery action"""
        
        # Check if we have a predefined strategy
        strategy_key = f"{category}_{severity}"
        if strategy_key in self.recovery_strategies:
            return self.recovery_strategies[strategy_key]
        
        # Default strategies based on category
        if category == ErrorCategory.TIMEOUT:
            return RecoveryAction(
                action_type="retry",
                parameters={"max_attempts": 3, "exponential_backoff": True},
                delay_seconds=2.0
            )
        elif category == ErrorCategory.NETWORK:
            return RecoveryAction(
                action_type="retry",
                parameters={"max_attempts": 5, "exponential_backoff": True},
                delay_seconds=1.0
            )
        elif category == ErrorCategory.BROKER_API:
            if severity == ErrorSeverity.CRITICAL:
                return RecoveryAction(
                    action_type="alert",
                    parameters={"immediate": True, "escalate": True}
                )
            else:
                return RecoveryAction(
                    action_type="retry",
                    parameters={"max_attempts": 2, "exponential_backoff": True},
                    delay_seconds=5.0
                )
        else:
            return RecoveryAction(
                action_type="alert",
                parameters={"log_only": True}
            )
    
    def _init_recovery_strategies(self) -> Dict[str, RecoveryAction]:
        """Initialize predefined recovery strategies"""
        return {
            f"{ErrorCategory.TIMEOUT}_{ErrorSeverity.LOW}": RecoveryAction(
                action_type="retry",
                parameters={"max_attempts": 3},
                delay_seconds=1.0
            ),
            f"{ErrorCategory.BROKER_API}_{ErrorSeverity.CRITICAL}": RecoveryAction(
                action_type="alert",
                parameters={"immediate": True, "escalate": True}
            ),
            f"{ErrorCategory.NETWORK}_{ErrorSeverity.HIGH}": RecoveryAction(
                action_type="fallback",
                parameters={"use_cached_data": True}
            )
        }
    
    def _get_circuit_breaker(self, operation: str) -> CircuitBreaker:
        """Get or create circuit breaker for operation"""
        if operation not in self.circuit_breakers:
            self.circuit_breakers[operation] = CircuitBreaker()
        return self.circuit_breakers[operation]
    
    def _log_error(
        self,
        error: Exception,
        context: ErrorContext,
        category: ErrorCategory,
        severity: ErrorSeverity
    ):
        """Log error with appropriate level"""
        message = (
            f"Error in {context.operation}: {str(error)} "
            f"[Category: {category}, Severity: {severity}, Symbol: {context.symbol}]"
        )
        
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(message)
        elif severity == ErrorSeverity.HIGH:
            logger.error(message)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(message)
        else:
            logger.info(message)
    
    def _record_error(
        self,
        error: Exception,
        context: ErrorContext,
        category: ErrorCategory,
        severity: ErrorSeverity
    ):
        """Record error in history"""
        error_record = {
            'timestamp': context.timestamp,
            'operation': context.operation,
            'symbol': context.symbol,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'category': category,
            'severity': severity,
            'retry_count': context.retry_count,
            'stack_trace': context.stack_trace
        }
        
        self.error_history.append(error_record)
        
        # Keep only last 1000 errors
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def _execute_immediate_retry(
        self,
        context: ErrorContext,
        recovery_action: RecoveryAction
    ) -> RecoveryAction:
        """Execute immediate retry if specified"""
        if recovery_action.delay_seconds > 0:
            time.sleep(recovery_action.delay_seconds)
        
        return recovery_action
    
    def _send_alert(
        self,
        error: Exception,
        context: ErrorContext,
        severity: ErrorSeverity
    ):
        """Send alert for critical errors"""
        alert_message = (
            f"ALERT: {severity} error in profit protection system\n"
            f"Operation: {context.operation}\n"
            f"Symbol: {context.symbol}\n"
            f"Error: {str(error)}\n"
            f"Time: {context.timestamp}"
        )
        
        # Log the alert
        logger.critical(f"🚨 {alert_message}")
        
        # Call registered alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_message, severity, context)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def _handle_exhausted_retries(
        self,
        error: Exception,
        context: ErrorContext
    ):
        """Handle case when all retries are exhausted"""
        alert_message = (
            f"EXHAUSTED RETRIES: Operation {context.operation} failed after all retry attempts\n"
            f"Symbol: {context.symbol}\n"
            f"Final error: {str(error)}"
        )
        
        logger.critical(f"🚨 {alert_message}")
        
        # Mark as unrecovered in history
        if self.error_history:
            self.error_history[-1]['recovered'] = False
        
        # Send alert to all callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_message, ErrorSeverity.CRITICAL, context)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")


# Global instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get or create the global error handler instance."""
    global _error_handler
    
    if _error_handler is None:
        _error_handler = ErrorHandler()
    
    return _error_handler
