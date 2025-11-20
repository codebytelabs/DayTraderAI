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
    fill_timeout_seconds: int = 60  # Wait 60s for full fill
    min_rr_ratio: float = 2.0  # Minimum 1:2 risk/reward
    enable_extended_hours: bool = False  # Disable extended hours by default


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
    """
    
    def __init__(self, alpaca_client, config: Optional[OrderConfig] = None):
        self.alpaca = alpaca_client
        self.config = config or OrderConfig()
        logger.info("✅ Smart Order Executor initialized (industry standard)")

    
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
        filled_price = self._wait_for_fill(order_id, timeout=self.config.fill_timeout_seconds)
        
        if filled_price is None:
            logger.warning(f"⚠️  Order {order_id} not filled within {self.config.fill_timeout_seconds}s, canceling")
            self._cancel_order(order_id)
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
        Wait for order to be fully filled
        Returns actual fill price or None if timeout/partial fill
        """
        import time
        
        logger.debug(f"Waiting for fill: {order_id} (timeout: {timeout}s)")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                order = self.alpaca.get_order(order_id)
                
                # Check if filled
                if order.status == 'filled':
                    filled_price = float(order.filled_avg_price)
                    logger.info(f"✅ Order filled: {order_id} @ ${filled_price:.2f}")
                    return filled_price
                
                # Check if partially filled (reject)
                if order.filled_qty and order.filled_qty < order.qty:
                    logger.warning(f"⚠️  Partial fill detected: {order_id}")
                    return None
                
                # Check if canceled or rejected
                if order.status in ['canceled', 'rejected', 'expired']:
                    logger.warning(f"⚠️  Order {order.status}: {order_id}")
                    return None
                
                # Wait before next check
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error checking order status: {e}")
                return None
        
        logger.warning(f"⏱️  Order fill timeout: {order_id}")
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
        """Cancel pending order"""
        logger.info(f"Canceling order: {order_id}")
        try:
            return self.alpaca.cancel_order(order_id)
        except Exception as e:
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
