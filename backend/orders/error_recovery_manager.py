#!/usr/bin/env python3
"""
Error Recovery Manager

Handles API errors and network issues gracefully with retry logic.
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""

import time
import logging
import random
from typing import Callable, Tuple, Any, Optional
from enum import Enum


class ErrorType(Enum):
    """Classification of error types"""
    TRANSIENT = "transient"  # Retry with backoff
    PERMANENT = "permanent"  # Fail immediately
    AMBIGUOUS = "ambiguous"  # Continue monitoring


class ErrorRecoveryManager:
    """
    Error recovery manager with intelligent retry logic
    
    This class handles API errors gracefully by classifying them and
    applying appropriate recovery strategies (retry, fail, or continue).
    """
    
    def __init__(self, max_retries: int = 3, backoff_base: float = 0.5):
        """
        Initialize error recovery manager
        
        Args:
            max_retries: Maximum number of retry attempts
            backoff_base: Base delay for exponential backoff
        """
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.logger = logging.getLogger(__name__)
        
        self.logger.debug(
            f"ErrorRecoveryManager initialized: max_retries={max_retries}, "
            f"backoff_base={backoff_base}s"
        )
    
    def execute_with_retry(
        self, 
        operation: Callable, 
        operation_name: str = "operation",
        max_retries: Optional[int] = None
    ) -> Tuple[bool, Any]:
        """
        Execute operation with exponential backoff retry
        
        Args:
            operation: Callable to execute
            operation_name: Name for logging
            max_retries: Override default max retries
            
        Returns:
            (success, result) tuple
        """
        retries = max_retries if max_retries is not None else self.max_retries
        
        for attempt in range(retries + 1):
            try:
                result = operation()
                
                if attempt > 0:
                    self.logger.info(
                        f"✅ {operation_name} succeeded after {attempt} retries"
                    )
                
                return True, result
                
            except Exception as e:
                error_type = self._classify_error(e)
                
                if error_type == ErrorType.PERMANENT:
                    # Permanent error - fail immediately
                    self.logger.error(
                        f"❌ {operation_name} failed with permanent error: {e}"
                    )
                    return False, None
                
                if attempt < retries:
                    # Transient or ambiguous error - retry
                    delay = self._calculate_backoff(attempt + 1, error_type)
                    
                    self.logger.warning(
                        f"⚠️  {operation_name} failed (attempt {attempt + 1}/{retries + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    time.sleep(delay)
                else:
                    # Max retries reached
                    self.logger.error(
                        f"❌ {operation_name} failed after {retries} retries: {e}"
                    )
                    return False, None
        
        return False, None
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """
        Classify error type for recovery strategy
        
        Args:
            error: Exception to classify
            
        Returns:
            ErrorType classification
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # Permanent errors - fail immediately
        permanent_indicators = [
            'invalid order id',
            'order not found',
            'already canceled',
            'insufficient permissions',
            'invalid parameter',
            'forbidden',
            'unauthorized',
            'authentication failed'
        ]
        
        for indicator in permanent_indicators:
            if indicator in error_str:
                return ErrorType.PERMANENT
        
        # Transient errors - retry with backoff
        transient_indicators = [
            'timeout',
            'connection',
            'network',
            'temporary',
            'unavailable',
            'rate limit',
            'too many requests',
            '429',
            '503',
            '504',
            'gateway'
        ]
        
        for indicator in transient_indicators:
            if indicator in error_str or indicator in error_type_name:
                return ErrorType.TRANSIENT
        
        # Ambiguous errors - continue monitoring
        return ErrorType.AMBIGUOUS
    
    def _calculate_backoff(self, attempt: int, error_type: ErrorType) -> float:
        """
        Calculate exponential backoff delay with jitter
        
        Args:
            attempt: Retry attempt number (1-based)
            error_type: Type of error
            
        Returns:
            Delay in seconds
        """
        # Base exponential backoff
        delay = self.backoff_base * (2 ** (attempt - 1))
        
        # Rate limit errors get longer delays
        if error_type == ErrorType.TRANSIENT:
            delay *= 2
        
        # Add jitter (±20%) to prevent thundering herd
        jitter = delay * 0.2 * (2 * random.random() - 1)
        delay += jitter
        
        # Cap at 30 seconds
        return min(delay, 30.0)
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if error should trigger retry
        
        Args:
            error: Exception to check
            
        Returns:
            True if retryable
        """
        error_type = self._classify_error(error)
        return error_type in [ErrorType.TRANSIENT, ErrorType.AMBIGUOUS]
    
    def should_continue_monitoring(self, error: Exception) -> bool:
        """
        Determine if monitoring should continue after error
        
        Args:
            error: Exception that occurred
            
        Returns:
            True if monitoring should continue
        """
        error_type = self._classify_error(error)
        
        # Continue monitoring for transient and ambiguous errors
        # Only stop for permanent errors
        return error_type != ErrorType.PERMANENT
    
    def get_error_description(self, error: Exception) -> str:
        """
        Get human-readable error description
        
        Args:
            error: Exception to describe
            
        Returns:
            Error description string
        """
        error_type = self._classify_error(error)
        
        descriptions = {
            ErrorType.TRANSIENT: "Temporary error (will retry)",
            ErrorType.PERMANENT: "Permanent error (cannot retry)",
            ErrorType.AMBIGUOUS: "Unknown error (will continue monitoring)"
        }
        
        return f"{descriptions[error_type]}: {str(error)}"
