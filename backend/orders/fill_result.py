#!/usr/bin/env python3
"""
Fill Result Data Model

Defines the result structure for fill detection operations.
Requirements: 1.3, 5.4
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class FillStatus(Enum):
    """Status of fill detection operation"""
    FILLED = "filled"
    TIMEOUT = "timeout"
    REJECTED = "rejected"
    CANCELED = "canceled"
    PARTIAL = "partial"
    ERROR = "error"


class DetectionMethod(Enum):
    """Method used to detect the fill"""
    STATUS_FIELD = "status_field"
    QUANTITY_MATCH = "quantity_match"
    FILL_PRICE = "fill_price"
    TIMESTAMP_CHECK = "timestamp_check"
    FINAL_VERIFICATION = "final_verification"
    CANCEL_RACE_DETECTION = "cancel_race_detection"


@dataclass
class FillResult:
    """
    Result of fill detection operation
    
    Contains all information about the fill detection attempt,
    including success/failure status, timing, and diagnostic data.
    """
    
    # Core result data
    filled: bool
    """Whether the order was successfully filled"""
    
    status: FillStatus
    """Status of the fill detection operation"""
    
    # Fill details (if filled)
    fill_price: Optional[float] = None
    """Actual fill price"""
    
    fill_quantity: Optional[int] = None
    """Actual fill quantity"""
    
    fill_timestamp: Optional[datetime] = None
    """Timestamp when order was filled"""
    
    # Detection metadata
    detection_method: Optional[DetectionMethod] = None
    """Primary method that detected the fill"""
    
    detection_methods_used: List[DetectionMethod] = field(default_factory=list)
    """All methods that confirmed the fill"""
    
    # Performance metrics
    checks_performed: int = 0
    """Number of status checks performed"""
    
    elapsed_time: float = 0.0
    """Total time elapsed during detection (seconds)"""
    
    api_calls_made: int = 0
    """Number of API calls made"""
    
    retries_attempted: int = 0
    """Number of retry attempts made"""
    
    # Diagnostic information
    reason: Optional[str] = None
    """Reason for failure (if not filled)"""
    
    error_details: Optional[str] = None
    """Detailed error information"""
    
    last_known_status: Optional[str] = None
    """Last known order status"""
    
    status_history: List[Dict[str, Any]] = field(default_factory=list)
    """History of status changes"""
    
    def add_detection_method(self, method: DetectionMethod):
        """Add a detection method that confirmed the fill"""
        if method not in self.detection_methods_used:
            self.detection_methods_used.append(method)
        
        # Set primary detection method if not set
        if self.detection_method is None:
            self.detection_method = method
    
    def add_status_change(self, status: str, timestamp: datetime, details: Optional[str] = None):
        """Add a status change to the history"""
        self.status_history.append({
            'status': status,
            'timestamp': timestamp,
            'details': details
        })
        self.last_known_status = status
    
    def set_error(self, error: str, details: Optional[str] = None):
        """Set error information"""
        self.filled = False
        self.status = FillStatus.ERROR
        self.reason = error
        self.error_details = details
    
    def set_timeout(self, reason: Optional[str] = None):
        """Set timeout status"""
        self.filled = False
        self.status = FillStatus.TIMEOUT
        self.reason = reason or "Order fill timeout"
    
    def set_filled(self, price: float, quantity: int, timestamp: Optional[datetime] = None):
        """Set filled status with details"""
        self.filled = True
        self.status = FillStatus.FILLED
        self.fill_price = price
        self.fill_quantity = quantity
        self.fill_timestamp = timestamp or datetime.now()
    
    def set_partial_fill(self, filled_qty: int, total_qty: int):
        """Set partial fill status"""
        self.filled = False
        self.status = FillStatus.PARTIAL
        self.fill_quantity = filled_qty
        self.reason = f"Partial fill: {filled_qty}/{total_qty} shares"
