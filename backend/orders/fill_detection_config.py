#!/usr/bin/env python3
"""
Fill Detection Configuration

Defines configuration parameters for the robust order execution system.
Requirements: 6.1, 6.2, 6.3, 6.4
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FillDetectionConfig:
    """
    Configuration for fill detection system
    
    This class defines all configurable parameters for the robust order
    execution system, allowing optimization for different market conditions
    and order types.
    
    OPTIMIZED Dec 2025: Faster polling for quicker fill detection
    """
    
    # Timeout settings - REDUCED for faster response
    timeout_seconds: int = 30
    """Maximum time to wait for order fill before timeout (30s is plenty for liquid stocks)"""
    
    # Polling settings - FASTER for quicker detection
    initial_poll_interval: float = 0.2
    """Initial polling interval in seconds (very fast detection)"""
    
    max_poll_interval: float = 1.0
    """Maximum polling interval in seconds (still responsive)"""
    
    poll_interval_increase: float = 0.05
    """Amount to increase polling interval each iteration (slower ramp)"""
    
    # Retry settings
    max_retries: int = 3
    """Maximum number of retries for transient errors"""
    
    retry_backoff_base: float = 0.5
    """Base delay for exponential backoff in seconds"""
    
    # Feature flags
    enable_final_verification: bool = True
    """Enable final verification check at timeout"""
    
    enable_adaptive_polling: bool = True
    """Enable adaptive polling intervals"""
    
    enable_multi_method_verification: bool = True
    """Enable multiple verification methods"""
    
    enable_state_consistency_check: bool = True
    """Enable broker/bot state consistency validation"""
    
    # Logging settings
    log_level: str = "INFO"
    """Logging level for fill detection"""
    
    log_status_changes: bool = True
    """Log all status changes"""
    
    log_verification_details: bool = True
    """Log details of verification methods"""
    
    def __post_init__(self):
        """Validate configuration parameters"""
        self._validate_timeout()
        self._validate_polling()
        self._validate_retry()
        self._validate_logging()
    
    def _validate_timeout(self):
        """Validate timeout settings"""
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.timeout_seconds > 300:  # 5 minutes max
            raise ValueError("timeout_seconds cannot exceed 300 seconds")
    
    def _validate_polling(self):
        """Validate polling settings"""
        if self.initial_poll_interval <= 0:
            raise ValueError("initial_poll_interval must be positive")
        if self.max_poll_interval <= 0:
            raise ValueError("max_poll_interval must be positive")
        if self.initial_poll_interval > self.max_poll_interval:
            raise ValueError("initial_poll_interval cannot exceed max_poll_interval")
        if self.poll_interval_increase < 0:
            raise ValueError("poll_interval_increase cannot be negative")
    
    def _validate_retry(self):
        """Validate retry settings"""
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.max_retries > 10:
            raise ValueError("max_retries cannot exceed 10")
        if self.retry_backoff_base <= 0:
            raise ValueError("retry_backoff_base must be positive")
    
    def _validate_logging(self):
        """Validate logging settings"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if self.log_level not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
    
    def get_adaptive_interval(self, iteration: int) -> float:
        """
        Calculate adaptive polling interval for given iteration
        
        Args:
            iteration: Current iteration number (0-based)
            
        Returns:
            Polling interval in seconds
        """
        if not self.enable_adaptive_polling:
            return self.initial_poll_interval
        
        interval = self.initial_poll_interval + (iteration * self.poll_interval_increase)
        return min(interval, self.max_poll_interval)
    
    def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay for retry attempt
        
        Args:
            attempt: Retry attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        return self.retry_backoff_base * (2 ** (attempt - 1))
