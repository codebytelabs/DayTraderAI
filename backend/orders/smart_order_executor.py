"""
Smart Order Executor - Industry Standard Implementation
Handles limit orders with dynamic SL/TP calculation based on actual fill price
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OrderConfig:
    """Configuration for smart order execution"""
    max_slippage_pct: float = 0.001  # 0.10% max acceptable slippage
    limit_buffer_regular: float = 0.0005  # 0.05% buffer for regular hours
    limit_buffer_extended: float = 0.0002  # 0.02% buffer for extended hours
    fill_timeout_seconds: int = 30  # Wait 30s for regular hours
    fill_timeout_extended: int = 90  # Wait 90s for extended hours (slower fills)
    min_rr_ratio: float = 2.0  # Minimum 1:2 risk/reward
    enable_extended_hours: bool = False  # Disable extended hours by default
    
    # Fill detection configuration
    fill_initial_poll_interval: float = 0.5  # Start checking every 0.5s
    fill_max_poll_interval: float = 2.0  # Max 2s between checks
    fill_max_retries: int = 3  # Retry API calls up to 3 times
    fill_enable_final_verification: bool = True  # Always do final check
    fill_enable_multi_method: bool = True  # Use all 4 verification methods


@dataclass
class OrderResult:
    """Result of order execution"""
    success: bool
    filled_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    slippage_pct: Optional[float] = None
    rr_ratio: Optional[float] = None
    reason: Optional[str] = None
    order_id: Optional[str] = None


class SmartOrderExecutor:
    """
    Industry-standard order executor with:
    - Limit orders (not market)
    - Dynamic SL/TP based on actual fill
    - Slippage protection
    - R/R validation
    - Extended hours handling
    - BULLETPROOF fill detection
    """
    
    def __init__(self, alpaca_client, config: Optional[OrderConfig] = None):
        self.alpaca = alpaca_client
        self.config = config or OrderConfig()
        
        # Initialize bulletproof fill detection engine
        from .fill_detection_engine import FillDetectionEngine
        from .fill_detection_config import FillDetectionConfig
        
        fill_config = FillDetectionConfig(
            timeout_seconds=self.config.fill_timeout_seconds,
            initial_poll_interval=self.config.fill_initial_poll_interval,
            max_poll_interval=self.config.fill_max_poll_interval,
            max_retries=self.config.fill_max_retries,
            enable_final_verification=self.config.fill_enable_final_verification,
            enable_multi_method_verification=self.config.fill_enable_multi_method
        )
        
        self.fill_detector = FillDetectionEngine(alpaca_client, fill_config)
        
        logger.info("✅ Smart Order Executor initialized (industry standard + BULLETPROOF fill detection)")

    
    def execute_trade(
        self,
        symbol: str,
        side: str,  # 'buy' or 'sell'
        quantity: int,
        signal_price: float,
        risk_amount: float,
        rr_ratio: float = 2.0
    ) -> OrderResult:
        """
        Execute trade with industry-standard flow:
        1. Submit limit order
        2. Wait for full fill
        3. Get actual fill price
        4. Dynamically calculate SL/TP
        5. Validate R/R ratio
        6. Submit bracket orders
        
        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            quantity: Number of shares
            signal_price: Original signal price
            risk_amount: Dollar risk per share
            rr_ratio: Target risk/reward ratio (default 2.0)
            
        Returns:
            OrderResult with execution details
        """
        
        # Step 1: Check if we should trade (extended hours check)
        if not self._should_trade_now():
            return OrderResult(
                success=False,
                reason="Extended hours trading disabled"
            )
        
        # Step 2: Calculate limit price with buffer
        limit_price = self._calculate_limit_price(signal_price, side)
        
        logger.info(
            f"📝 Submitting limit order: {side.upper()} {quantity} {symbol} "
            f"@ ${limit_price:.2f} (signal: ${signal_price:.2f})"
        )
        
        # Step 3: Submit limit order
        try:
            order = self._submit_limit_order(symbol, side, quantity, limit_price)
            if not order:
                return OrderResult(success=False, reason="Order submission failed")
            
            order_id = order.id
            logger.info(f"✓ Limit order submitted: {order_id}")
            
        except Exception as e:
            logger.error(f"❌ Order submission failed: {e}")
            return OrderResult(success=False, reason=f"Submission error: {e}")

        
        # Step 4: Wait for full fill (with timeout)
        # Use longer timeout for extended hours
        timeout = self._get_fill_timeout()
        filled_price = self._wait_for_fill(order_id, timeout=timeout)
        
        if filled_price is None:
            # CRITICAL: Final check - query order status directly before giving up
            logger.warning(f"⚠️  Fill detection timed out, doing final order status check...")
            final_price = self._final_fill_check(order_id)
            if final_price:
                logger.info(f"✅ Final check found fill @ ${final_price:.2f}")
                filled_price = final_price
            else:
                logger.warning(f"⚠️  Order {order_id} not filled within {timeout}s, attempting cancel...")
                cancel_result = self._cancel_order(order_id)
                
                # ALWAYS do a final fill check after cancel attempt
                # This catches the race condition where order fills during cancel
                import time
                time.sleep(0.5)  # Brief wait for order status to update
                final_price = self._final_fill_check(order_id)
                if final_price:
                    logger.info(f"✅ Order filled (detected after cancel attempt) @ ${final_price:.2f}")
                    filled_price = final_price
                elif not cancel_result:
                    # Cancel failed - try one more time
                    time.sleep(0.3)
                    final_price = self._final_fill_check(order_id)
                    if final_price:
                        logger.info(f"✅ Order filled (final retry) @ ${final_price:.2f}")
                        filled_price = final_price
                
                if filled_price is None:
                    return OrderResult(success=False, reason="Fill timeout")
        
        logger.info(f"✓ Order filled: {quantity} {symbol} @ ${filled_price:.2f}")
        
        # Step 5: Calculate slippage
        slippage_pct = abs(filled_price - signal_price) / signal_price
        
        if slippage_pct > self.config.max_slippage_pct:
            logger.error(
                f"❌ Excessive slippage: {slippage_pct*100:.2f}% "
                f"(max: {self.config.max_slippage_pct*100:.2f}%) - Canceling trade"
            )
            # Close position immediately
            self._close_position(symbol, quantity, side)
            return OrderResult(
                success=False,
                filled_price=filled_price,
                slippage_pct=slippage_pct,
                reason=f"Slippage {slippage_pct*100:.2f}% exceeds max {self.config.max_slippage_pct*100:.2f}%"
            )
        
        logger.info(f"✓ Slippage acceptable: {slippage_pct*100:.3f}%")
        
        # Step 6: Dynamically calculate SL/TP based on ACTUAL FILL PRICE
        stop_loss, take_profit = self._calculate_dynamic_exits(
            filled_price, side, risk_amount, rr_ratio
        )
        
        # Step 7: Validate R/R ratio after slippage
        actual_risk = abs(filled_price - stop_loss)
        actual_reward = abs(take_profit - filled_price)
        actual_rr = actual_reward / actual_risk if actual_risk > 0 else 0
        
        if actual_rr < self.config.min_rr_ratio:
            logger.error(
                f"❌ R/R ratio too low: 1:{actual_rr:.2f} "
                f"(min: 1:{self.config.min_rr_ratio:.1f}) - Canceling trade"
            )
            self._close_position(symbol, quantity, side)
            return OrderResult(
                success=False,
                filled_price=filled_price,
                slippage_pct=slippage_pct,
                rr_ratio=actual_rr,
                reason=f"R/R {actual_rr:.2f} below minimum {self.config.min_rr_ratio}"
            )
        
        logger.info(
            f"✓ R/R validated: 1:{actual_rr:.2f} "
            f"(Risk: ${actual_risk:.2f}, Reward: ${actual_reward:.2f})"
        )

        
        # Step 8: Submit bracket orders (OCO)
        try:
            bracket_result = self._submit_bracket_orders(
                symbol, quantity, stop_loss, take_profit
            )
            
            if not bracket_result:
                logger.error("❌ Bracket order submission failed")
                return OrderResult(
                    success=False,
                    filled_price=filled_price,
                    reason="Bracket submission failed"
                )
            
            logger.info(
                f"✅ Trade complete: {side.upper()} {quantity} {symbol} @ ${filled_price:.2f} | "
                f"SL: ${stop_loss:.2f} | TP: ${take_profit:.2f} | "
                f"R/R: 1:{actual_rr:.2f} | Slippage: {slippage_pct*100:.3f}%"
            )
            
            return OrderResult(
                success=True,
                filled_price=filled_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                slippage_pct=slippage_pct,
                rr_ratio=actual_rr,
                order_id=order_id
            )
            
        except Exception as e:
            logger.error(f"❌ Bracket order error: {e}")
            return OrderResult(
                success=False,
                filled_price=filled_price,
                reason=f"Bracket error: {e}"
            )
    
    def _should_trade_now(self) -> bool:
        """Check if we should trade based on market hours"""
        if self.config.enable_extended_hours:
            return True
        
        # CRITICAL FIX: Use ET timezone, not local machine time
        import pytz
        now = datetime.now(tz=pytz.timezone('US/Eastern')).time()
        market_open = time(9, 30)  # 9:30 AM ET
        market_close = time(16, 0)  # 4:00 PM ET
        
        is_regular_hours = market_open <= now <= market_close
        
        if not is_regular_hours:
            logger.debug("Extended hours trading disabled")
        
        return is_regular_hours
    
    def _is_extended_hours(self) -> bool:
        """Check if we're in extended hours trading"""
        import pytz
        now = datetime.now(tz=pytz.timezone('US/Eastern')).time()
        market_open = time(9, 30)
        market_close = time(16, 0)
        return not (market_open <= now <= market_close)
    
    def _get_fill_timeout(self) -> int:
        """Get appropriate fill timeout based on market hours"""
        if self._is_extended_hours():
            logger.info(f"📊 Extended hours - using {self.config.fill_timeout_extended}s timeout")
            return self.config.fill_timeout_extended
        return self.config.fill_timeout_seconds
    
    def _final_fill_check(self, order_id: str) -> Optional[float]:
        """
        Final direct check of order status before giving up.
        This catches fills that happened but weren't detected by the monitoring loop.
        CRITICAL: This is the last line of defense against missed fills.
        """
        try:
            order = self.alpaca.get_order(order_id)
            if not order:
                logger.warning(f"Final fill check: Could not fetch order {order_id}")
                return None
            
            # Log the raw status for debugging
            raw_status = getattr(order, 'status', 'unknown')
            logger.info(f"Final fill check for {order_id}: status={raw_status}")
            
            # Check status - handle all variations
            status = str(raw_status).lower()
            filled_indicators = ['filled', 'fill', 'executed', 'complete']
            
            if any(indicator in status for indicator in filled_indicators):
                # Order was filled! Get the fill price
                fill_price = None
                
                # Try filled_avg_price first (most accurate)
                if hasattr(order, 'filled_avg_price') and order.filled_avg_price:
                    fill_price = float(order.filled_avg_price)
                    logger.info(f"Final fill check: Found fill @ ${fill_price:.2f} (filled_avg_price)")
                # Fallback to limit_price
                elif hasattr(order, 'limit_price') and order.limit_price:
                    fill_price = float(order.limit_price)
                    logger.info(f"Final fill check: Found fill @ ${fill_price:.2f} (limit_price)")
                # Last resort - try to get any price
                elif hasattr(order, 'filled_qty') and float(order.filled_qty or 0) > 0:
                    # Order has filled quantity, use limit price as estimate
                    if hasattr(order, 'limit_price') and order.limit_price:
                        fill_price = float(order.limit_price)
                        logger.info(f"Final fill check: Found fill @ ${fill_price:.2f} (estimated from limit)")
                
                return fill_price
            
            logger.info(f"Final fill check: Order {order_id} not filled (status: {status})")
            return None
            
        except Exception as e:
            logger.warning(f"Final fill check failed for {order_id}: {e}")
            return None

    
    def _calculate_limit_price(self, signal_price: float, side: str) -> float:
        """Calculate limit price with appropriate buffer"""
        # CRITICAL FIX: Use ET timezone, not local machine time
        import pytz
        now = datetime.now(tz=pytz.timezone('US/Eastern')).time()
        market_open = time(9, 30)
        market_close = time(16, 0)
        is_regular_hours = market_open <= now <= market_close
        
        # Use tighter buffer for extended hours
        buffer = (
            self.config.limit_buffer_regular 
            if is_regular_hours 
            else self.config.limit_buffer_extended
        )
        
        if side == 'buy':
            # Buy: Add buffer (willing to pay slightly more)
            return signal_price * (1 + buffer)
        else:
            # Sell: Subtract buffer (willing to accept slightly less)
            return signal_price * (1 - buffer)
    
    def _submit_limit_order(self, symbol: str, side: str, quantity: int, limit_price: float):
        """Submit limit order to broker"""
        try:
            from alpaca.trading.requests import LimitOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce
            import time
            
            order_side = OrderSide.BUY if side == 'buy' else OrderSide.SELL
            
            request = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                time_in_force=TimeInForce.DAY,
                limit_price=round(limit_price, 2)
            )
            
            return self.alpaca.submit_order_request(request)
        except Exception as e:
            logger.error(f"Failed to submit limit order: {e}")
            return None
    
    def _wait_for_fill(self, order_id: str, timeout: int) -> Optional[float]:
        """
        Wait for order to be fully filled using BULLETPROOF fill detection
        Returns actual fill price or None if timeout/partial fill
        
        This method now uses the FillDetectionEngine which provides:
        - Multi-method verification (4 independent checks)
        - Graceful error recovery with retry logic
        - Final verification check at timeout
        - Cancel-race condition detection
        - Comprehensive logging
        """
        logger.info(f"🔥 BULLETPROOF FILL DETECTOR: {order_id} (timeout: {timeout}s)")
        
        # Use the bulletproof fill detection engine
        result = self.fill_detector.monitor_order_fill(order_id, timeout)
        
        # Check result
        if result.filled:
            logger.info(
                f"✅ Order filled: {order_id} @ ${result.fill_price:.2f} "
                f"(detected by {result.detection_method.value if result.detection_method else 'unknown'}, "
                f"{result.checks_performed} checks, {result.elapsed_time:.1f}s)"
            )
            return result.fill_price
        
        # Not filled - log reason
        logger.warning(
            f"⚠️  Order not filled: {order_id} - {result.reason} "
            f"({result.checks_performed} checks, {result.elapsed_time:.1f}s)"
        )
        
        return None

    def _calculate_dynamic_exits(
        self, 
        filled_price: float, 
        side: str, 
        risk_amount: float, 
        rr_ratio: float
    ) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit based on ACTUAL FILL PRICE
        This is the industry standard approach
        """
        if side == 'buy':
            stop_loss = filled_price - risk_amount
            take_profit = filled_price + (risk_amount * rr_ratio)
        else:  # sell/short
            stop_loss = filled_price + risk_amount
            take_profit = filled_price - (risk_amount * rr_ratio)
        return stop_loss, take_profit
    
    def _cancel_order(self, order_id: str) -> bool:
        """
        Cancel pending order.
        Returns True if cancelled, False if failed or already filled.
        """
        logger.info(f"Canceling order: {order_id}")
        try:
            result = self.alpaca.cancel_order(order_id)
            return result if result is not None else True
        except Exception as e:
            error_str = str(e).lower()
            # Check if order was already filled (not a real error)
            if 'filled' in error_str or 'already' in error_str:
                logger.info(f"Order {order_id} already filled (cancel not needed)")
                return False  # Return False to trigger final fill check
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    def _close_position(self, symbol: str, quantity: int, original_side: str) -> bool:
        """Close position immediately (opposite side)"""
        close_side = 'sell' if original_side == 'buy' else 'buy'
        logger.info(f"Closing position: {close_side.upper()} {quantity} {symbol}")
        try:
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce
            
            order_side = OrderSide.SELL if close_side == 'sell' else OrderSide.BUY
            
            request = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.alpaca.submit_order_request(request)
            return order is not None
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return False
    
    def _submit_bracket_orders(
        self, 
        symbol: str, 
        quantity: int, 
        stop_loss: float, 
        take_profit: float
    ) -> bool:
        """Submit OCO bracket orders (stop loss + take profit)"""
        logger.info(
            f"Submitting bracket: {symbol} SL=${stop_loss:.2f} TP=${take_profit:.2f}"
        )
        try:
            from alpaca.trading.requests import LimitOrderRequest, StopOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
            
            # Submit stop loss order
            stop_request = StopOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=OrderSide.SELL,  # Assuming long position
                time_in_force=TimeInForce.GTC,
                stop_price=round(stop_loss, 2)
            )
            
            # Submit take profit order
            tp_request = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=OrderSide.SELL,  # Assuming long position
                time_in_force=TimeInForce.GTC,
                limit_price=round(take_profit, 2)
            )
            
            # Note: Alpaca's OCO orders require special handling
            # For now, submit as separate orders
            # TODO: Implement proper OCO bracket
            stop_order = self.alpaca.submit_order_request(stop_request)
            tp_order = self.alpaca.submit_order_request(tp_request)
            
            return stop_order is not None and tp_order is not None
        except Exception as e:
            logger.error(f"Failed to submit bracket orders: {e}")
            return False


# Global instance
smart_executor = None  # Will be initialized by OrderManager


def execute_smart_trade(
    symbol: str,
    side: str,
    quantity: int,
    signal_price: float,
    risk_amount: float,
    rr_ratio: float = 2.0
) -> OrderResult:
    """
    Execute trade using industry-standard smart order execution
    """
    if smart_executor is None:
        raise RuntimeError("Smart executor not initialized")
    
    return smart_executor.execute_trade(
        symbol, side, quantity, signal_price, risk_amount, rr_ratio
    )
