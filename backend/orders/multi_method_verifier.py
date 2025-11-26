#!/usr/bin/env python3
"""
Multi-Method Verifier

Implements multiple independent methods to verify order fills.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import logging
from typing import Any
from datetime import datetime

from .fill_verification import FillVerification, VerificationMethod, MethodResult


class MultiMethodVerifier:
    """
    Multi-method fill verification system
    
    This class implements four independent verification methods to detect
    order fills. Using multiple methods provides redundancy and ensures
    fills are never missed due to API inconsistencies.
    """
    
    def __init__(self):
        """Initialize multi-method verifier"""
        self.logger = logging.getLogger(__name__)
        self.logger.debug("MultiMethodVerifier initialized")
    
    def verify_fill(self, order: Any) -> FillVerification:
        """
        Verify fill using multiple independent methods
        
        This method runs all four verification methods and aggregates
        their results. ANY method confirming the fill = order is filled.
        
        Args:
            order: Order object from broker API
            
        Returns:
            FillVerification with consensus result
        """
        verification = FillVerification(is_filled=False)
        
        # Method 1: Status field check
        status_result = self._check_status_field(order)
        verification.add_method_result(
            VerificationMethod.STATUS_FIELD,
            status_result['confirmed'],
            status_result['confidence'],
            status_result['details'],
            status_result['value']
        )
        
        # Method 2: Quantity match check
        quantity_result = self._check_quantity_match(order)
        verification.add_method_result(
            VerificationMethod.QUANTITY_MATCH,
            quantity_result['confirmed'],
            quantity_result['confidence'],
            quantity_result['details'],
            quantity_result['value']
        )
        
        # Method 3: Fill price check
        price_result = self._check_fill_price(order)
        verification.add_method_result(
            VerificationMethod.FILL_PRICE,
            price_result['confirmed'],
            price_result['confidence'],
            price_result['details'],
            price_result['value']
        )
        
        # Method 4: Timestamp check
        timestamp_result = self._check_timestamps(order)
        verification.add_method_result(
            VerificationMethod.TIMESTAMP_CHECK,
            timestamp_result['confirmed'],
            timestamp_result['confidence'],
            timestamp_result['details'],
            timestamp_result['value']
        )
        
        # Extract fill details if filled
        if verification.is_filled:
            self._extract_fill_details(order, verification)
        
        self.logger.debug(
            f"Verification complete: {verification.is_filled} "
            f"(methods: {verification.methods_confirmed})"
        )
        
        return verification
    
    def _check_status_field(self, order: Any) -> dict:
        """
        Method 1: Check order.status == 'filled'
        
        This is the most reliable method as it directly checks the
        broker's status field.
        
        Args:
            order: Order object
            
        Returns:
            Dict with confirmed, confidence, details, value
        """
        try:
            status = self._extract_status(order)
            
            # ENHANCED: Check for filled status (handle ALL variations)
            filled_statuses = ['filled', 'fill', 'executed', 'complete', 'completed']
            is_filled = status.lower() in filled_statuses
            
            return {
                'confirmed': is_filled,
                'confidence': 1.0 if is_filled else 0.0,
                'details': f"Status field: {status}",
                'value': status
            }
            
        except Exception as e:
            self.logger.warning(f"Status field check failed: {e}")
            return {
                'confirmed': False,
                'confidence': 0.0,
                'details': f"Error: {str(e)}",
                'value': None
            }
    
    def _check_quantity_match(self, order: Any) -> dict:
        """
        Method 2: Check filled_qty >= requested_qty
        
        If the filled quantity matches or exceeds the requested quantity,
        the order must be filled.
        
        Args:
            order: Order object
            
        Returns:
            Dict with confirmed, confidence, details, value
        """
        try:
            if not hasattr(order, 'filled_qty') or not hasattr(order, 'qty'):
                return {
                    'confirmed': False,
                    'confidence': 0.0,
                    'details': "Missing quantity fields",
                    'value': None
                }
            
            filled_qty = float(order.filled_qty or 0)
            total_qty = float(order.qty or 0)
            
            # Check if fully filled
            is_filled = filled_qty > 0 and filled_qty >= total_qty
            
            # Confidence based on how close to full fill
            if is_filled:
                confidence = 1.0
            elif filled_qty > 0:
                confidence = 0.5  # Partial fill
            else:
                confidence = 0.0
            
            return {
                'confirmed': is_filled,
                'confidence': confidence,
                'details': f"Filled {filled_qty}/{total_qty} shares",
                'value': filled_qty
            }
            
        except Exception as e:
            self.logger.warning(f"Quantity match check failed: {e}")
            return {
                'confirmed': False,
                'confidence': 0.0,
                'details': f"Error: {str(e)}",
                'value': None
            }
    
    def _check_fill_price(self, order: Any) -> dict:
        """
        Method 3: Check filled_avg_price > 0
        
        If a fill price exists and is positive, the order must have filled.
        
        Args:
            order: Order object
            
        Returns:
            Dict with confirmed, confidence, details, value
        """
        try:
            if not hasattr(order, 'filled_avg_price'):
                return {
                    'confirmed': False,
                    'confidence': 0.0,
                    'details': "Missing filled_avg_price field",
                    'value': None
                }
            
            fill_price = order.filled_avg_price
            
            if fill_price is None:
                return {
                    'confirmed': False,
                    'confidence': 0.0,
                    'details': "Fill price is None",
                    'value': None
                }
            
            fill_price = float(fill_price)
            is_filled = fill_price > 0
            
            return {
                'confirmed': is_filled,
                'confidence': 0.9 if is_filled else 0.0,
                'details': f"Fill price: ${fill_price:.2f}",
                'value': fill_price
            }
            
        except Exception as e:
            self.logger.warning(f"Fill price check failed: {e}")
            return {
                'confirmed': False,
                'confidence': 0.0,
                'details': f"Error: {str(e)}",
                'value': None
            }
    
    def _check_timestamps(self, order: Any) -> dict:
        """
        Method 4: Check filled_at timestamp exists
        
        If a filled_at timestamp exists, the order has been filled.
        
        Args:
            order: Order object
            
        Returns:
            Dict with confirmed, confidence, details, value
        """
        try:
            if not hasattr(order, 'filled_at'):
                return {
                    'confirmed': False,
                    'confidence': 0.0,
                    'details': "Missing filled_at field",
                    'value': None
                }
            
            filled_at = order.filled_at
            
            if filled_at is None:
                return {
                    'confirmed': False,
                    'confidence': 0.0,
                    'details': "Filled timestamp is None",
                    'value': None
                }
            
            # Timestamp exists
            is_filled = True
            
            return {
                'confirmed': is_filled,
                'confidence': 0.8,
                'details': f"Filled at: {filled_at}",
                'value': filled_at
            }
            
        except Exception as e:
            self.logger.warning(f"Timestamp check failed: {e}")
            return {
                'confirmed': False,
                'confidence': 0.0,
                'details': f"Error: {str(e)}",
                'value': None
            }
    
    def _extract_status(self, order: Any) -> str:
        """
        Extract status from order object
        
        Handles both enum and string status values.
        
        Args:
            order: Order object
            
        Returns:
            Status string
        """
        if not hasattr(order, 'status'):
            return "unknown"
        
        status = order.status
        
        # Handle enum
        if hasattr(status, 'value'):
            return status.value
        elif hasattr(status, 'name'):
            return status.name
        else:
            return str(status).lower()
    
    def _extract_fill_details(self, order: Any, verification: FillVerification):
        """
        Extract fill details from order
        
        Args:
            order: Order object
            verification: Verification object to update
        """
        # Extract fill price
        if hasattr(order, 'filled_avg_price') and order.filled_avg_price:
            try:
                verification.fill_price = float(order.filled_avg_price)
            except (ValueError, TypeError):
                pass
        
        # Extract fill quantity
        if hasattr(order, 'filled_qty') and order.filled_qty:
            try:
                verification.fill_quantity = int(order.filled_qty)
            except (ValueError, TypeError):
                pass
        
        # Extract fill timestamp
        if hasattr(order, 'filled_at') and order.filled_at:
            verification.fill_timestamp = order.filled_at
        
        # Calculate confidence score
        confirmed_count = len(verification.methods_confirmed)
        if confirmed_count == 1:
            verification.confidence_score = 0.7
        elif confirmed_count == 2:
            verification.confidence_score = 0.85
        elif confirmed_count == 3:
            verification.confidence_score = 0.95
        else:
            verification.confidence_score = 1.0
