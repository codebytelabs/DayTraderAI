#!/usr/bin/env python3
"""
Fill Verification Data Model

Defines the result structure for multi-method verification operations.
Requirements: 2.1, 2.5
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Any
from enum import Enum


class VerificationMethod(Enum):
    """Available verification methods"""
    STATUS_FIELD = "status_field"
    QUANTITY_MATCH = "quantity_match"
    FILL_PRICE = "fill_price"
    TIMESTAMP_CHECK = "timestamp_check"


@dataclass
class MethodResult:
    """Result from a single verification method"""
    method: VerificationMethod
    confirmed: bool
    confidence: float  # 0.0 to 1.0
    details: Optional[str] = None
    value_found: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FillVerification:
    """
    Result of multi-method verification
    
    This class aggregates results from multiple independent verification
    methods to provide a consensus on whether an order has been filled.
    """
    
    # Core verification result
    is_filled: bool
    """Consensus result: is the order filled?"""
    
    # Method results
    method_results: List[MethodResult] = field(default_factory=list)
    """Results from individual verification methods"""
    
    methods_confirmed: List[str] = field(default_factory=list)
    """Names of methods that confirmed the fill"""
    
    # Fill details (if available)
    fill_price: Optional[float] = None
    """Fill price (from most reliable method)"""
    
    fill_quantity: Optional[int] = None
    """Fill quantity (from most reliable method)"""
    
    fill_timestamp: Optional[datetime] = None
    """Fill timestamp (from most reliable method)"""
    
    # Confidence metrics
    confidence_score: float = 0.0
    """Overall confidence score (0.0-1.0)"""
    
    def add_method_result(self, method: VerificationMethod, confirmed: bool, 
                         confidence: float, details: Optional[str] = None, 
                         value_found: Optional[Any] = None):
        """Add result from a verification method"""
        result = MethodResult(
            method=method,
            confirmed=confirmed,
            confidence=confidence,
            details=details,
            value_found=value_found
        )
        
        self.method_results.append(result)
        
        if confirmed:
            self.methods_confirmed.append(method.value)
            self.is_filled = True  # ANY method confirming = filled
