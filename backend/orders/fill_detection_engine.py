#!/usr/bin/env python3
"""
Fill Detection Engine

Core orchestration component for robust order fill detection.
Requirements: 1.1, 1.2, 1.3, 4.1, 4.2, 4.5, 5.1, 5.2
"""

import time
import logging
from datetime import datetime
from typing import Optional, Any

from .fill_detection_config import FillDetectionConfig
from .fill_result import FillResult, FillStatus, DetectionMethod
from .fill_verification import FillVerification
from .multi_method_verifier import MultiMethodVerifier
from .error_recovery_manager import ErrorRecoveryManager
from .ultimate_fill_validator import UltimateFillValidator


class FillDetectionEngine:
    """
    Core engine for robust order fill detection
    
    This class orchestrates the entire fill detection process with fault tolerance,
    multi-method verification, error recovery, and comprehensive logging.
    """
    
    def __init__(self, alpaca_client, config: Optional[FillDetectionConfig] = None):
        """
        Initialize fill detection engine
        
        Args:
            alpaca_client: Alpaca trading client
            config: Fill detection configuration
        """
        self.alpaca = alpaca_client
        self.config = config or FillDetectionConfig()
        
        # Initialize components
        self.verifier = MultiMethodVerifier()
        self.error_recovery = ErrorRecoveryManager(
            max_retries=self.config.max_retries,
            backoff_base=self.config.retry_backoff_base
        )
        self.ultimate_validator = UltimateFillValidator(alpaca_client)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, self.config.log_level))
        
        self.logger.info(f"🔥 FillDetectionEngine initialized with config: timeout={self.config.timeout_seconds}s")
    
    def monitor_order_fill(self, order_id: str, timeout_seconds: Optional[int] = None) -> FillResult:
        """
        Monitor order until filled, rejected, or timeout
        
        This is the main entry point for fill detection. It orchestrates the entire
        process including monitoring, verification, error recovery, and final checks.
        
        Args:
            order_id: Order ID to monitor
            timeout_seconds: Override default timeout
            
        Returns:
            FillResult with status and details
        """
        # Use provided timeout or config default
        timeout = timeout_seconds or self.config.timeout_seconds
        
        # Initialize result
        result = FillResult(
            filled=False,
            status=FillStatus.TIMEOUT,
            checks_performed=0,
            api_calls_made=0,
            retries_attempted=0
        )
        
        start_time = time.time()
        deadline = start_time + timeout
        
        self.logger.info(
            f"🔥 BULLETPROOF FILL DETECTOR: {order_id} (timeout: {timeout}s)"
        )
        
        try:
            # Primary monitoring loop
            fill_result = self._primary_monitor_loop(order_id, deadline, result)
            
            if fill_result:
                # Fill detected during monitoring
                fill_result.elapsed_time = time.time() - start_time
                self.logger.info(
                    f"🎉 ORDER FILLED! {order_id} @ ${fill_result.fill_price:.2f} "
                    f"after {fill_result.elapsed_time:.1f}s (method: {fill_result.detection_method.value if fill_result.detection_method else 'unknown'})"
                )
                return fill_result
            
            # No fill detected, handle timeout
            timeout_result = self._handle_timeout(order_id, result)
            timeout_result.elapsed_time = time.time() - start_time
            
            if timeout_result.filled:
                self.logger.info(
                    f"🎉 LAST SECOND FILL! {order_id} @ ${timeout_result.fill_price:.2f} "
                    f"detected during timeout handling"
                )
            else:
                self.logger.warning(
                    f"⏱️  BULLETPROOF TIMEOUT: {order_id} after {timeout}s "
                    f"({timeout_result.checks_performed} checks)"
                )
            
            return timeout_result
            
        except Exception as e:
            # Unexpected error
            result.elapsed_time = time.time() - start_time
            result.set_error(f"Unexpected error: {str(e)}", str(e))
            
            self.logger.error(
                f"❌ Unexpected error in fill detection for {order_id}: {e}",
                exc_info=True
            )
            
            return result
    
    def _primary_monitor_loop(self, order_id: str, deadline: float, result: FillResult) -> Optional[FillResult]:
        """
        Main monitoring loop with multi-method verification
        
        Args:
            order_id: Order ID to monitor
            deadline: Deadline timestamp
            result: Result object to update
            
        Returns:
            FillResult if filled, None if timeout
        """
        iteration = 0
        last_status = None
        start_time = deadline - self.config.timeout_seconds
        
        self.logger.debug(f"🔍 Starting primary monitor loop for {order_id}")
        
        while time.time() < deadline:
            iteration += 1
            elapsed = time.time() - start_time
            
            # Calculate adaptive polling interval
            poll_interval = self.config.get_adaptive_interval(iteration - 1)
            
            try:
                # Get order status with retry logic
                order = self._get_order_with_retry(order_id, result)
                if not order:
                    # Error getting order, but continue monitoring
                    self.logger.warning(
                        f"⚠️  Could not fetch order {order_id} on check #{iteration}, continuing..."
                    )
                    time.sleep(poll_interval)
                    continue
                
                result.checks_performed += 1
                
                # Get current status
                current_status = self._extract_order_status(order)
                
                # Log status changes
                if current_status != last_status:
                    if self.config.log_status_changes:
                        self.logger.info(
                            f"🔄 Status change: {last_status or 'unknown'} → {current_status} "
                            f"(check #{iteration}, {elapsed:.1f}s)"
                        )
                    
                    result.add_status_change(current_status, datetime.now(), 
                                           f"Check #{iteration}, elapsed {elapsed:.1f}s")
                    last_status = current_status
                
                # BULLETPROOF FILL DETECTION - Multiple methods
                fill_detected, detection_method = self._bulletproof_fill_check(order)
                
                if fill_detected:
                    # Fill detected!
                    self.logger.info(
                        f"🎉 FILL DETECTED by {detection_method.value}! "
                        f"Order {order_id} after {elapsed:.1f}s (check #{iteration})"
                    )
                    
                    fill_result = self._create_fill_result(order, result)
                    fill_result.detection_method = detection_method
                    fill_result.add_detection_method(detection_method)
                    
                    return fill_result
                
                # Check for partial fills
                if self._is_partial_fill(order):
                    filled_qty = self._get_filled_quantity(order)
                    total_qty = self._get_total_quantity(order)
                    
                    self.logger.warning(
                        f"⚠️  Partial fill detected: {filled_qty}/{total_qty} shares "
                        f"for {order_id} after {elapsed:.1f}s"
                    )
                    
                    result.set_partial_fill(filled_qty, total_qty)
                    return result
                
                # Check for rejected/canceled orders
                if self._is_order_rejected(order):
                    self.logger.warning(
                        f"⚠️  Order {current_status}: {order_id} after {elapsed:.1f}s"
                    )
                    
                    result.filled = False
                    result.status = FillStatus.REJECTED
                    result.reason = f"Order {current_status}"
                    result.last_known_status = current_status
                    return result
                
                # Still pending - log progress periodically
                if iteration % 10 == 0:  # Log every 10 checks
                    self.logger.info(
                        f"⏳ Still waiting... Status: {current_status} "
                        f"(check #{iteration}, {elapsed:.1f}s)"
                    )
                
            except Exception as e:
                self.logger.error(
                    f"❌ Error in monitoring loop (check #{iteration}): {e}"
                )
                result.retries_attempted += 1
                # Continue monitoring even on errors
            
            # Wait before next check
            time.sleep(poll_interval)
        
        # Timeout reached
        return None
    
    def _handle_timeout(self, order_id: str, result: FillResult) -> FillResult:
        """
        Handle timeout with final verification and cancel logic
        
        Args:
            order_id: Order ID
            result: Current result object
            
        Returns:
            Updated FillResult
        """
        self.logger.info(f"⏱️  Timeout reached for {order_id}, performing final verification...")
        
        if not self.config.enable_final_verification:
            result.set_timeout("Timeout without final verification")
            return result
        
        try:
            # FINAL CHECK - Maybe it filled right at the end
            final_order = self._get_order_with_retry(order_id, result)
            if final_order:
                fill_detected, detection_method = self._bulletproof_fill_check(final_order)
                if fill_detected:
                    # Last second fill!
                    fill_result = self._create_fill_result(final_order, result)
                    fill_result.detection_method = DetectionMethod.FINAL_VERIFICATION
                    return fill_result
            
            # Try to cancel the order
            self.logger.info(f"🚫 Attempting to cancel {order_id}...")
            
            try:
                self.alpaca.cancel_order(order_id)
                result.api_calls_made += 1
                
                # Verify cancellation
                time.sleep(0.5)  # Brief wait
                canceled_order = self._get_order_with_retry(order_id, result)
                
                if canceled_order and self._is_order_canceled(canceled_order):
                    result.set_timeout("Order successfully canceled")
                    self.logger.info(f"✅ Order {order_id} successfully canceled")
                else:
                    result.set_timeout("Order cancellation status unclear")
                    self.logger.warning(f"⚠️  Order {order_id} cancellation status unclear")
                
            except Exception as cancel_error:
                # Cancel failed - might be already filled!
                cancel_error_str = str(cancel_error).lower()
                
                # ENHANCED RACE CONDITION DETECTION - catch all variations
                filled_indicators = [
                    'already in "filled" state',
                    "already in 'filled' state",
                    'already in \\"filled\\" state',
                    "already in \\'filled\\' state",
                    "already filled",
                    "filled state",
                    "order is filled",
                    "cannot cancel filled order",
                    "order already executed",
                    "already executed",
                    "42210000"  # Alpaca error code for already filled
                ]
                
                race_detected = any(indicator in cancel_error_str for indicator in filled_indicators)
                
                if race_detected:
                    # RACE CONDITION DETECTED!
                    self.logger.info(f"🎉 CANCEL RACE DETECTED! {order_id} was already filled")
                    self.logger.info(f"   Cancel error: {cancel_error_str}")
                    
                    # IMMEDIATE VERIFICATION - Don't rely on another API call
                    race_order = self._get_order_with_retry(order_id, result)
                    if race_order:
                        fill_detected, detection_method = self._bulletproof_fill_check(race_order)
                        if fill_detected:
                            self.logger.info(f"🎉 RACE CONDITION CONFIRMED! Fill detected by {detection_method.value if detection_method else 'unknown'}")
                            fill_result = self._create_fill_result(race_order, result)
                            fill_result.detection_method = DetectionMethod.CANCEL_RACE_DETECTION
                            fill_result.add_detection_method(DetectionMethod.CANCEL_RACE_DETECTION)
                            return fill_result
                        else:
                            self.logger.warning(f"⚠️  Cancel race detected but fill verification failed - checking again...")
                            # Try one more time with a brief delay
                            time.sleep(0.2)
                            final_race_order = self._get_order_with_retry(order_id, result)
                            if final_race_order:
                                final_fill_detected, final_method = self._bulletproof_fill_check(final_race_order)
                                if final_fill_detected:
                                    self.logger.info(f"🎉 DELAYED RACE CONFIRMATION! Fill detected by {final_method.value if final_method else 'unknown'}")
                                    fill_result = self._create_fill_result(final_race_order, result)
                                    fill_result.detection_method = DetectionMethod.CANCEL_RACE_DETECTION
                                    return fill_result
                
                result.set_timeout(f"Cancel failed: {cancel_error_str}")
                self.logger.warning(f"⚠️  Failed to cancel {order_id}: {cancel_error}")
            
        except Exception as e:
            result.set_error(f"Final verification failed: {str(e)}", str(e))
            self.logger.error(f"❌ Final verification failed for {order_id}: {e}")
        
        # ULTIMATE SAFETY NET - Last chance to find the fill
        if not result.filled:
            self.logger.info(f"🛡️  Activating ULTIMATE FILL VALIDATOR for {order_id}")
            ultimate_result = self.ultimate_validator.ultimate_fill_check(order_id, result)
            if ultimate_result.filled:
                self.logger.info(f"🎉 ULTIMATE VALIDATOR SAVED THE DAY! Fill found for {order_id}")
                return ultimate_result
        
        return result
    
    def _get_order_with_retry(self, order_id: str, result: FillResult) -> Optional[Any]:
        """
        Get order with retry logic using ErrorRecoveryManager
        
        Args:
            order_id: Order ID
            result: Result object to update
            
        Returns:
            Order object or None
        """
        def get_order_operation():
            result.api_calls_made += 1
            return self.alpaca.get_order(order_id)
        
        success, order = self.error_recovery.execute_with_retry(
            get_order_operation,
            operation_name=f"get_order({order_id})"
        )
        
        if not success:
            result.retries_attempted += self.config.max_retries
            return None
        
        return order
    
    def _extract_order_status(self, order) -> str:
        """Extract status from order object"""
        if hasattr(order, 'status'):
            if hasattr(order.status, 'value'):
                return order.status.value
            elif hasattr(order.status, 'name'):
                return order.status.name
            else:
                return str(order.status).lower()
        return "unknown"
    
    def _bulletproof_fill_check(self, order) -> tuple[bool, Optional[DetectionMethod]]:
        """
        Multi-method fill detection using MultiMethodVerifier
        
        Returns:
            (is_filled, detection_method)
        """
        if not self.config.enable_multi_method_verification:
            # Fallback to simple status check
            status = self._extract_order_status(order)
            if status.lower() in ['filled', 'fill']:
                return True, DetectionMethod.STATUS_FIELD
            return False, None
        
        # Use multi-method verifier
        verification = self.verifier.verify_fill(order)
        
        if verification.is_filled:
            # Determine primary detection method
            if 'status_field' in verification.methods_confirmed:
                primary_method = DetectionMethod.STATUS_FIELD
            elif 'quantity_match' in verification.methods_confirmed:
                primary_method = DetectionMethod.QUANTITY_MATCH
            elif 'fill_price' in verification.methods_confirmed:
                primary_method = DetectionMethod.FILL_PRICE
            elif 'timestamp_check' in verification.methods_confirmed:
                primary_method = DetectionMethod.TIMESTAMP_CHECK
            else:
                primary_method = DetectionMethod.STATUS_FIELD
            
            if self.config.log_verification_details:
                self.logger.debug(
                    f"Fill confirmed by {len(verification.methods_confirmed)} methods: "
                    f"{verification.methods_confirmed} (confidence: {verification.confidence_score:.2f})"
                )
            
            return True, primary_method
        
        return False, None
    
    def _is_partial_fill(self, order) -> bool:
        """Check if order is partially filled"""
        if hasattr(order, 'filled_qty') and hasattr(order, 'qty'):
            filled_qty = float(order.filled_qty or 0)
            total_qty = float(order.qty or 0)
            return 0 < filled_qty < total_qty
        return False
    
    def _is_order_rejected(self, order) -> bool:
        """Check if order is rejected/canceled"""
        status = self._extract_order_status(order)
        return status.lower() in ['canceled', 'cancelled', 'rejected', 'expired']
    
    def _is_order_canceled(self, order) -> bool:
        """Check if order is canceled"""
        status = self._extract_order_status(order)
        return status.lower() in ['canceled', 'cancelled']
    
    def _get_filled_quantity(self, order) -> int:
        """Get filled quantity from order"""
        if hasattr(order, 'filled_qty'):
            return int(order.filled_qty or 0)
        return 0
    
    def _get_total_quantity(self, order) -> int:
        """Get total quantity from order"""
        if hasattr(order, 'qty'):
            return int(order.qty or 0)
        return 0
    
    def _create_fill_result(self, order, base_result: FillResult) -> FillResult:
        """Create fill result from order"""
        # Extract fill details
        fill_price = None
        if hasattr(order, 'filled_avg_price') and order.filled_avg_price:
            fill_price = float(order.filled_avg_price)
        
        fill_quantity = self._get_filled_quantity(order)
        
        # Create new result based on base result
        result = FillResult(
            filled=True,
            status=FillStatus.FILLED,
            fill_price=fill_price,
            fill_quantity=fill_quantity,
            fill_timestamp=datetime.now(),
            checks_performed=base_result.checks_performed,
            api_calls_made=base_result.api_calls_made,
            retries_attempted=base_result.retries_attempted,
            status_history=base_result.status_history
        )
        
        return result
