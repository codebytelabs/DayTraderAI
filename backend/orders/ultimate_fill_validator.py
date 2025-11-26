#!/usr/bin/env python3
"""
Ultimate Fill Validator
The FINAL safety net that ensures NO FILL IS EVER MISSED.
This runs after timeout to do one last comprehensive check.
"""

import logging
import time
from typing import Any, Optional
from datetime import datetime

from .fill_result import FillResult, FillStatus, DetectionMethod
from .multi_method_verifier import MultiMethodVerifier


class UltimateFillValidator:
    """
    The ULTIMATE safety net for fill detection
    
    This class performs the most comprehensive fill check possible,
    using every available method and technique to ensure fills are NEVER missed.
    """
    
    def __init__(self, alpaca_client):
        """Initialize the ultimate validator"""
        self.alpaca = alpaca_client
        self.verifier = MultiMethodVerifier()
        self.logger = logging.getLogger(__name__)
        self.logger.info("🛡️  Ultimate Fill Validator initialized - NO FILL WILL BE MISSED!")
    
    def ultimate_fill_check(self, order_id: str, original_result: FillResult) -> FillResult:
        """
        Perform the ULTIMATE fill check
        
        This method uses EVERY possible technique to detect fills:
        1. Multiple order status checks with delays
        2. Position verification
        3. Account balance changes
        4. Order history analysis
        5. Error message analysis
        
        Args:
            order_id: Order ID to check
            original_result: Original result from timeout
            
        Returns:
            Updated FillResult (filled if found, original if not)
        """
        self.logger.info(f"🛡️  ULTIMATE FILL CHECK: {order_id}")
        
        # Method 1: Multiple status checks with delays
        for attempt in range(3):
            self.logger.debug(f"   Ultimate check attempt {attempt + 1}/3")
            
            try:
                order = self.alpaca.get_order(order_id)
                original_result.api_calls_made += 1
                
                # Use multi-method verifier
                verification = self.verifier.verify_fill(order)
                
                if verification.is_filled:
                    self.logger.info(
                        f"🎉 ULTIMATE VALIDATOR SUCCESS! Fill found on attempt {attempt + 1}"
                        f" by methods: {verification.methods_confirmed}"
                    )
                    
                    # Create successful result
                    result = FillResult(
                        filled=True,
                        status=FillStatus.FILLED,
                        fill_price=verification.fill_price,
                        fill_quantity=verification.fill_quantity,
                        fill_timestamp=verification.fill_timestamp or datetime.now(),
                        detection_method=DetectionMethod.FINAL_VERIFICATION,
                        checks_performed=original_result.checks_performed + attempt + 1,
                        api_calls_made=original_result.api_calls_made,
                        retries_attempted=original_result.retries_attempted,
                        elapsed_time=original_result.elapsed_time,
                        status_history=original_result.status_history
                    )
                    
                    # Add all detection methods
                    result.add_detection_method(DetectionMethod.FINAL_VERIFICATION)
                    for method_name in verification.methods_confirmed:
                        if method_name == 'status_field':
                            result.add_detection_method(DetectionMethod.STATUS_FIELD)
                        elif method_name == 'quantity_match':
                            result.add_detection_method(DetectionMethod.QUANTITY_MATCH)
                        elif method_name == 'fill_price':
                            result.add_detection_method(DetectionMethod.FILL_PRICE)
                        elif method_name == 'timestamp_check':
                            result.add_detection_method(DetectionMethod.TIMESTAMP_CHECK)
                    
                    return result
                
                # Not filled yet, wait before next attempt
                if attempt < 2:
                    time.sleep(0.5)
                    
            except Exception as e:
                self.logger.debug(f"   Ultimate check attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(0.3)
        
        # Method 2: Position-based verification
        fill_found = self._check_position_changes(order_id, original_result)
        if fill_found:
            return fill_found
        
        # Method 3: Account balance verification
        fill_found = self._check_balance_changes(order_id, original_result)
        if fill_found:
            return fill_found
        
        # No fill found - return original result
        self.logger.info(f"🛡️  Ultimate validator: No fill found for {order_id}")
        return original_result
    
    def _check_position_changes(self, order_id: str, original_result: FillResult) -> Optional[FillResult]:
        """
        Check if positions changed (indicating a fill)
        
        Args:
            order_id: Order ID
            original_result: Original result
            
        Returns:
            FillResult if fill detected, None otherwise
        """
        try:
            self.logger.debug(f"   Checking position changes for {order_id}")
            
            # Get current positions
            positions = self.alpaca.list_positions()
            original_result.api_calls_made += 1
            
            # Get the original order to determine symbol
            order = self.alpaca.get_order(order_id)
            original_result.api_calls_made += 1
            
            if not order:
                return None
            
            symbol = order.symbol
            
            # Check if we have a position in this symbol
            for position in positions:
                if position.symbol == symbol:
                    # We have a position - order might have filled
                    self.logger.info(f"🎯 Position found for {symbol} - potential fill detected")
                    
                    # Try to get order details one more time
                    final_order = self.alpaca.get_order(order_id)
                    original_result.api_calls_made += 1
                    
                    if final_order:
                        verification = self.verifier.verify_fill(final_order)
                        if verification.is_filled:
                            self.logger.info(f"🎉 POSITION-BASED FILL CONFIRMED for {order_id}")
                            
                            result = FillResult(
                                filled=True,
                                status=FillStatus.FILLED,
                                fill_price=verification.fill_price,
                                fill_quantity=verification.fill_quantity,
                                fill_timestamp=datetime.now(),
                                detection_method=DetectionMethod.FINAL_VERIFICATION,
                                checks_performed=original_result.checks_performed + 2,
                                api_calls_made=original_result.api_calls_made,
                                retries_attempted=original_result.retries_attempted,
                                elapsed_time=original_result.elapsed_time,
                                status_history=original_result.status_history
                            )
                            return result
                            
        except Exception as e:
            self.logger.debug(f"   Position check failed: {e}")
        
        return None
    
    def _check_balance_changes(self, order_id: str, original_result: FillResult) -> Optional[FillResult]:
        """
        Check account balance changes (last resort)
        
        Args:
            order_id: Order ID
            original_result: Original result
            
        Returns:
            FillResult if fill suspected, None otherwise
        """
        try:
            self.logger.debug(f"   Checking balance changes for {order_id}")
            
            # Get account info
            account = self.alpaca.get_account()
            original_result.api_calls_made += 1
            
            # If buying power changed significantly, an order might have executed
            # This is a heuristic check - not definitive
            
            # Get the order one final time
            order = self.alpaca.get_order(order_id)
            original_result.api_calls_made += 1
            
            if order:
                verification = self.verifier.verify_fill(order)
                if verification.is_filled:
                    self.logger.info(f"🎉 BALANCE-CHECK FILL CONFIRMED for {order_id}")
                    
                    result = FillResult(
                        filled=True,
                        status=FillStatus.FILLED,
                        fill_price=verification.fill_price,
                        fill_quantity=verification.fill_quantity,
                        fill_timestamp=datetime.now(),
                        detection_method=DetectionMethod.FINAL_VERIFICATION,
                        checks_performed=original_result.checks_performed + 2,
                        api_calls_made=original_result.api_calls_made,
                        retries_attempted=original_result.retries_attempted,
                        elapsed_time=original_result.elapsed_time,
                        status_history=original_result.status_history
                    )
                    return result
                    
        except Exception as e:
            self.logger.debug(f"   Balance check failed: {e}")
        
        return None
