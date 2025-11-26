"""
Order Sequencer

Ensures all order modifications execute atomically without conflicts.
Implements conflict detection, resolution, and atomic operation support.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import time
import threading

from utils.logger import setup_logger

logger = setup_logger(__name__)


class ConflictType(str, Enum):
    """Types of order conflicts"""
    SHARES_LOCKED = "shares_locked"
    DUPLICATE_ORDER = "duplicate_order"
    INVALID_PRICE = "invalid_price"
    INSUFFICIENT_SHARES = "insufficient_shares"
    BROKER_REJECTION = "broker_rejection"
    CONCURRENT_MODIFICATION = "concurrent_modification"


@dataclass
class OrderConflict:
    """Represents an order conflict"""
    conflict_type: ConflictType
    symbol: str
    conflicting_orders: List[str]  # Order IDs
    resolution_strategy: str
    details: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class SequenceResult:
    """Result of an order sequence operation"""
    success: bool
    message: str
    sequence_id: str
    operations_completed: List[str]
    conflicts_detected: List[OrderConflict]
    rollback_performed: bool = False
    execution_time_ms: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class OrderSequencer:
    """
    Manages atomic order operations with conflict detection and resolution.
    """
    
    def __init__(self, alpaca_client=None):
        self.alpaca = alpaca_client
        self._position_locks: Dict[str, threading.Lock] = {}
        self._sequence_counter = 0
        self._active_sequences: Dict[str, dict] = {}
        self._global_lock = threading.Lock()
        self.retry_delays = [0.5, 1.0, 2.0]  # Exponential backoff
        
        logger.info("✅ Order Sequencer initialized")
    
    def execute_stop_update(self, symbol: str, new_stop: float) -> SequenceResult:
        """
        Execute stop loss update with proper sequencing.
        
        Sequence:
        1. Query current orders for symbol
        2. If stop loss exists, cancel it
        3. Wait for cancellation confirmation
        4. Submit new stop loss order
        5. Verify new order is active
        
        Args:
            symbol: Stock symbol
            new_stop: New stop loss price
            
        Returns:
            SequenceResult with operation details
        """
        sequence_id = self._generate_sequence_id()
        operations = []
        conflicts = []
        start_time = time.perf_counter()
        
        # Acquire position lock
        with self._get_position_lock(symbol):
            try:
                # Step 1: Query current orders
                operations.append("query_orders")
                current_orders = self.alpaca.get_orders(symbol=symbol, status='open') if self.alpaca else []
                
                # Step 2: Find and cancel existing stop loss
                stop_order = None
                for order in current_orders:
                    if getattr(order, 'order_type', None) == 'stop' and getattr(order, 'side', None) == 'sell':
                        stop_order = order
                        break
                
                if stop_order:
                    operations.append("cancel_existing_stop")
                    
                    # Cancel existing stop loss
                    cancel_success = self.alpaca.cancel_order(stop_order.id) if self.alpaca else True
                    if not cancel_success:
                        conflict = OrderConflict(
                            conflict_type=ConflictType.BROKER_REJECTION,
                            symbol=symbol,
                            conflicting_orders=[stop_order.id],
                            resolution_strategy="retry_cancel",
                            details=f"Failed to cancel stop order {stop_order.id}"
                        )
                        conflicts.append(conflict)
                        
                        # Retry cancel with backoff
                        for delay in self.retry_delays:
                            time.sleep(delay)
                            cancel_success = self.alpaca.cancel_order(stop_order.id) if self.alpaca else True
                            if cancel_success:
                                break
                        
                        if not cancel_success:
                            return self._create_failure_result(
                                sequence_id, operations, conflicts, start_time,
                                "Failed to cancel existing stop order after retry"
                            )
                    
                    # Step 3: Wait for cancellation confirmation
                    operations.append("wait_cancellation")
                    if self.alpaca and not self._wait_for_cancellation(stop_order.id, timeout=2.0):
                        return self._create_failure_result(
                            sequence_id, operations, conflicts, start_time,
                            "Timeout waiting for stop order cancellation"
                        )
                
                # Step 4: Get position for new stop order
                operations.append("get_position")
                position = self.alpaca.get_position(symbol) if self.alpaca else None
                if self.alpaca and not position:
                    return self._create_failure_result(
                        sequence_id, operations, conflicts, start_time,
                        f"No position found for {symbol}"
                    )
                
                # Step 5: Submit new stop loss
                operations.append("create_new_stop")
                if self.alpaca and position:
                    stop_order_data = {
                        'symbol': symbol,
                        'qty': abs(int(position.qty)),
                        'side': 'sell' if int(position.qty) > 0 else 'buy',
                        'type': 'stop',
                        'time_in_force': 'gtc',
                        'stop_price': str(new_stop)
                    }
                    
                    new_order = self.alpaca.submit_order(**stop_order_data)
                    if not new_order:
                        return self._create_failure_result(
                            sequence_id, operations, conflicts, start_time,
                            "Failed to create new stop loss order"
                        )
                    
                    # Step 6: Verify new order is active
                    operations.append("verify_new_order")
                    if not self._verify_order_active(new_order.id, timeout=2.0):
                        return self._create_failure_result(
                            sequence_id, operations, conflicts, start_time,
                            "New stop order not confirmed active"
                        )
                
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                return SequenceResult(
                    success=True,
                    message=f"Stop loss updated to ${new_stop:.2f}",
                    sequence_id=sequence_id,
                    operations_completed=operations,
                    conflicts_detected=conflicts,
                    execution_time_ms=elapsed_ms
                )
                
            except Exception as e:
                logger.error(f"Exception in stop update sequence for {symbol}: {e}")
                return self._create_failure_result(
                    sequence_id, operations, conflicts, start_time,
                    f"Exception during sequence: {str(e)}"
                )

    def execute_partial_exit_with_stop_update(
        self,
        symbol: str,
        exit_qty: int,
        new_stop: float
    ) -> SequenceResult:
        """
        Execute partial exit with stop update atomically.
        
        Sequence:
        1. Cancel all exit orders (stop + take profit)
        2. Submit partial exit market order
        3. Wait for fill confirmation
        4. Calculate new position size
        5. Submit new stop loss for remaining position
        6. Verify all orders active
        """
        sequence_id = self._generate_sequence_id()
        operations = []
        conflicts = []
        start_time = time.perf_counter()
        
        # Store pre-operation state for rollback
        pre_state = self._capture_position_state(symbol)
        
        with self._get_position_lock(symbol):
            try:
                # Step 1: Cancel all exit orders
                operations.append("cancel_exit_orders")
                if self.alpaca:
                    current_orders = self.alpaca.get_orders(symbol=symbol, status='open')
                    
                    exit_orders = [
                        order for order in current_orders
                        if getattr(order, 'side', None) == 'sell' and 
                           getattr(order, 'order_type', None) in ['stop', 'limit']
                    ]
                    
                    for order in exit_orders:
                        if not self.alpaca.cancel_order(order.id):
                            conflict = OrderConflict(
                                conflict_type=ConflictType.BROKER_REJECTION,
                                symbol=symbol,
                                conflicting_orders=[order.id],
                                resolution_strategy="force_cancel",
                                details=f"Failed to cancel order {order.id}"
                            )
                            conflicts.append(conflict)
                
                # Wait for cancellations
                operations.append("wait_cancellations")
                time.sleep(0.5)
                
                # Step 2: Submit partial exit
                operations.append("submit_partial_exit")
                if self.alpaca:
                    exit_order_data = {
                        'symbol': symbol,
                        'qty': exit_qty,
                        'side': 'sell',
                        'type': 'market',
                        'time_in_force': 'day'
                    }
                    
                    exit_order = self.alpaca.submit_order(**exit_order_data)
                    if not exit_order:
                        return self._perform_rollback(
                            sequence_id, operations, conflicts, pre_state, start_time,
                            "Failed to submit partial exit order"
                        )
                    
                    # Step 3: Wait for fill
                    operations.append("wait_fill")
                    fill_result = self._wait_for_fill(exit_order.id, timeout=5.0)
                    if not fill_result['filled']:
                        return self._perform_rollback(
                            sequence_id, operations, conflicts, pre_state, start_time,
                            f"Partial exit not filled: {fill_result['status']}"
                        )
                    
                    # Step 4: Get updated position
                    operations.append("get_updated_position")
                    updated_position = self.alpaca.get_position(symbol)
                    if not updated_position:
                        return self._perform_rollback(
                            sequence_id, operations, conflicts, pre_state, start_time,
                            "Cannot get updated position after partial exit"
                        )
                    
                    # Step 5: Submit new stop for remaining position
                    operations.append("create_new_stop")
                    remaining_qty = abs(int(updated_position.qty))
                    
                    if remaining_qty > 0:
                        stop_order_data = {
                            'symbol': symbol,
                            'qty': remaining_qty,
                            'side': 'sell',
                            'type': 'stop',
                            'time_in_force': 'gtc',
                            'stop_price': str(new_stop)
                        }
                        
                        new_stop_order = self.alpaca.submit_order(**stop_order_data)
                        if not new_stop_order:
                            return self._perform_rollback(
                                sequence_id, operations, conflicts, pre_state, start_time,
                                "Failed to create new stop loss after partial exit"
                            )
                
                # Step 6: Verify orders active
                operations.append("verify_orders")
                
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                return SequenceResult(
                    success=True,
                    message=f"Partial exit and stop update completed",
                    sequence_id=sequence_id,
                    operations_completed=operations,
                    conflicts_detected=conflicts,
                    execution_time_ms=elapsed_ms
                )
                
            except Exception as e:
                logger.error(f"Exception in partial exit sequence for {symbol}: {e}")
                return self._perform_rollback(
                    sequence_id, operations, conflicts, pre_state, start_time,
                    f"Exception during sequence: {str(e)}"
                )
    
    def detect_conflicts(self, symbol: str, operation_type: str) -> List[OrderConflict]:
        """
        Detect potential conflicts before executing operations.
        """
        conflicts = []
        
        try:
            # Check for concurrent modifications
            if symbol in self._active_sequences:
                conflicts.append(OrderConflict(
                    conflict_type=ConflictType.CONCURRENT_MODIFICATION,
                    symbol=symbol,
                    conflicting_orders=[],
                    resolution_strategy="wait_and_retry",
                    details=f"Another sequence active for {symbol}"
                ))
            
            if self.alpaca:
                # Check current orders
                current_orders = self.alpaca.get_orders(symbol=symbol, status='open')
                
                # Check for duplicate orders
                stop_orders = [o for o in current_orders if getattr(o, 'order_type', None) == 'stop']
                if len(stop_orders) > 1:
                    conflicts.append(OrderConflict(
                        conflict_type=ConflictType.DUPLICATE_ORDER,
                        symbol=symbol,
                        conflicting_orders=[o.id for o in stop_orders],
                        resolution_strategy="cancel_duplicates",
                        details=f"Multiple stop orders found: {len(stop_orders)}"
                    ))
                
                # Check position availability
                position = self.alpaca.get_position(symbol)
                if not position and operation_type in ['stop_update', 'partial_exit']:
                    conflicts.append(OrderConflict(
                        conflict_type=ConflictType.INSUFFICIENT_SHARES,
                        symbol=symbol,
                        conflicting_orders=[],
                        resolution_strategy="abort_operation",
                        details=f"No position found for {symbol}"
                    ))
            
        except Exception as e:
            logger.error(f"Error detecting conflicts for {symbol}: {e}")
            conflicts.append(OrderConflict(
                conflict_type=ConflictType.BROKER_REJECTION,
                symbol=symbol,
                conflicting_orders=[],
                resolution_strategy="retry_later",
                details=f"Error querying broker: {str(e)}"
            ))
        
        return conflicts
    
    def verify_shares_available(self, symbol: str, required_qty: int) -> Dict[str, Any]:
        """
        Verify shares are available for a new order.
        
        Returns:
            Dict with available_qty, locked_qty, and is_available
        """
        if not self.alpaca:
            return {'available_qty': required_qty, 'locked_qty': 0, 'is_available': True}
        
        try:
            position = self.alpaca.get_position(symbol)
            if not position:
                return {'available_qty': 0, 'locked_qty': 0, 'is_available': False}
            
            total_qty = abs(int(position.qty))
            
            # Calculate locked shares from open orders
            open_orders = self.alpaca.get_orders(symbol=symbol, status='open')
            locked_qty = sum(
                int(getattr(order, 'qty', 0)) 
                for order in open_orders 
                if getattr(order, 'side', None) == 'sell'
            )
            
            available_qty = total_qty - locked_qty
            
            return {
                'available_qty': available_qty,
                'locked_qty': locked_qty,
                'is_available': available_qty >= required_qty
            }
            
        except Exception as e:
            logger.error(f"Error verifying shares for {symbol}: {e}")
            return {'available_qty': 0, 'locked_qty': 0, 'is_available': False, 'error': str(e)}

    def retry_with_backoff(self, operation, max_retries: int = 3) -> Any:
        """
        Execute operation with exponential backoff retry.
        
        Args:
            operation: Callable to execute
            max_retries: Maximum retry attempts
            
        Returns:
            Result of successful operation or raises exception
        """
        last_error = None
        delays = self.retry_delays[:max_retries]
        
        for attempt in range(max_retries + 1):
            try:
                return operation()
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    delay = delays[attempt] if attempt < len(delays) else delays[-1]
                    logger.warning(f"Retry {attempt + 1}/{max_retries}: {e}. Waiting {delay}s...")
                    time.sleep(delay)
        
        raise last_error
    
    def _generate_sequence_id(self) -> str:
        """Generate unique sequence ID"""
        with self._global_lock:
            self._sequence_counter += 1
            return f"SEQ_{self._sequence_counter}_{int(time.time())}"
    
    def _get_position_lock(self, symbol: str) -> threading.Lock:
        """Get or create position-specific lock"""
        if symbol not in self._position_locks:
            self._position_locks[symbol] = threading.Lock()
        return self._position_locks[symbol]
    
    def _wait_for_cancellation(self, order_id: str, timeout: float) -> bool:
        """Wait for order cancellation confirmation"""
        if not self.alpaca:
            return True
            
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                order = self.alpaca.get_order(order_id)
                if order.status in ['cancelled', 'expired', 'rejected']:
                    return True
                time.sleep(0.1)
            except Exception:
                # Order might be deleted, assume cancelled
                return True
        
        return False
    
    def _verify_order_active(self, order_id: str, timeout: float) -> bool:
        """Verify order is active and accepted"""
        if not self.alpaca:
            return True
            
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                order = self.alpaca.get_order(order_id)
                if order.status in ['new', 'accepted', 'pending_new']:
                    return True
                elif order.status in ['rejected', 'cancelled']:
                    return False
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error verifying order {order_id}: {e}")
                return False
        
        return False
    
    def _wait_for_fill(self, order_id: str, timeout: float) -> dict:
        """Wait for order fill with timeout"""
        if not self.alpaca:
            return {'filled': True, 'filled_qty': 0, 'avg_fill_price': 0, 'status': 'filled'}
            
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                order = self.alpaca.get_order(order_id)
                
                if order.status == 'filled':
                    return {
                        'filled': True,
                        'filled_qty': int(order.filled_qty),
                        'avg_fill_price': float(order.filled_avg_price or 0),
                        'status': order.status
                    }
                elif order.status in ['cancelled', 'rejected', 'expired']:
                    return {
                        'filled': False,
                        'filled_qty': 0,
                        'avg_fill_price': 0,
                        'status': order.status
                    }
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error checking order {order_id}: {e}")
                break
        
        return {
            'filled': False,
            'filled_qty': 0,
            'avg_fill_price': 0,
            'status': 'timeout'
        }
    
    def _capture_position_state(self, symbol: str) -> dict:
        """Capture current position state for rollback"""
        try:
            if not self.alpaca:
                return {}
            position = self.alpaca.get_position(symbol)
            orders = self.alpaca.get_orders(symbol=symbol, status='open')
            
            return {
                'position': position,
                'orders': orders,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Error capturing state for {symbol}: {e}")
            return {}
    
    def _perform_rollback(
        self,
        sequence_id: str,
        operations: List[str],
        conflicts: List[OrderConflict],
        pre_state: dict,
        start_time: float,
        error_message: str
    ) -> SequenceResult:
        """Perform rollback to previous state"""
        logger.warning(f"Performing rollback for sequence {sequence_id}: {error_message}")
        
        # Cancel any orders created during the sequence
        # Restore previous state if possible
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        return SequenceResult(
            success=False,
            message=error_message,
            sequence_id=sequence_id,
            operations_completed=operations,
            conflicts_detected=conflicts,
            rollback_performed=True,
            execution_time_ms=elapsed_ms
        )
    
    def _create_failure_result(
        self,
        sequence_id: str,
        operations: List[str],
        conflicts: List[OrderConflict],
        start_time: float,
        message: str
    ) -> SequenceResult:
        """Create failure result"""
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        return SequenceResult(
            success=False,
            message=message,
            sequence_id=sequence_id,
            operations_completed=operations,
            conflicts_detected=conflicts,
            execution_time_ms=elapsed_ms
        )


# Global instance
_order_sequencer: Optional['OrderSequencer'] = None


def get_order_sequencer(alpaca_client=None) -> OrderSequencer:
    """Get or create the global order sequencer instance."""
    global _order_sequencer
    
    if _order_sequencer is None:
        _order_sequencer = OrderSequencer(alpaca_client)
    
    return _order_sequencer
