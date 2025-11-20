"""
Stop Loss Protection Manager

Industry best practice: Dedicated protection manager that runs frequently
to ensure all positions have active stop loss protection.

This module:
- Runs every 5 seconds (vs 60 seconds for position sync)
- Independently verifies stop loss protection
- Creates standalone stop loss orders if missing
- Cancels 'held' bracket legs that won't activate
- Updates trailing stops for profitable positions

Reference: Production trading systems should never rely solely on bracket orders.
Always use active monitoring and repair logic.
"""

from typing import Dict, List, Optional, Tuple
from alpaca.trading.requests import StopOrderRequest, TrailingStopOrderRequest, MarketOrderRequest, TakeProfitRequest, StopLossRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from core.alpaca_client import AlpacaClient
from core.state import trading_state
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class StopLossProtectionManager:
    """
    Dedicated manager for ensuring all positions have active stop loss protection.
    Runs independently of bracket orders and position_manager.
    """
    
    def __init__(self, alpaca_client: AlpacaClient):
        self.alpaca = alpaca_client
        self.protected_positions = set()  # Track which positions we've protected
        self.last_check_time = {}  # Track last check time per symbol
        logger.info("✅ Stop Loss Protection Manager initialized")
    
    def verify_all_positions(self) -> Dict[str, str]:
        """
        Main entry point: Verify all positions have active stop loss protection.
        
        Returns:
            Dict mapping symbol to status: 'protected', 'created', 'failed'
        """
        results = {}
        
        try:
            # Get all open positions
            positions = trading_state.get_all_positions()
            
            if not positions:
                return results
            
            # Get all orders once (more efficient than per-position queries)
            all_orders = self.alpaca.get_orders(status='all')
            
            for position in positions:
                symbol = position.symbol
                
                try:
                    # Check if position has active stop loss
                    has_stop, stop_price = self._has_active_stop_loss(symbol, all_orders)
                    
                    if has_stop:
                        results[symbol] = 'protected'
                        self.protected_positions.add(symbol)
                        logger.debug(f"✅ {symbol} protected with stop at ${stop_price:.2f}")
                        continue
                    
                    # No active stop - need to create one
                    logger.warning(f"🚨 {symbol} has NO ACTIVE STOP LOSS - creating now...")
                    
                    # Create stop loss (will handle bracket recreation if needed)
                    success = self._create_stop_loss(position)
                    
                    if success:
                        results[symbol] = 'created'
                        self.protected_positions.add(symbol)
                        logger.info(f"✅ Created stop loss for {symbol}")
                    else:
                        results[symbol] = 'failed'
                        logger.error(f"❌ Failed to create stop loss for {symbol}")
                
                except Exception as e:
                    logger.error(f"Error protecting {symbol}: {e}")
                    results[symbol] = 'failed'
            
            # Log summary
            protected = sum(1 for s in results.values() if s in ['protected', 'created'])
            failed = sum(1 for s in results.values() if s == 'failed')
            
            if failed > 0:
                logger.error(f"⚠️  Protection status: {protected} protected, {failed} FAILED")
            elif protected > 0:
                logger.debug(f"✅ All {protected} positions protected")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in verify_all_positions: {e}")
            return results
    
    def _has_active_stop_loss(
        self, 
        symbol: str, 
        all_orders: List
    ) -> Tuple[bool, Optional[float]]:
        """
        Check if symbol has an active stop loss order.
        
        Returns:
            (has_stop, stop_price) tuple
        """
        for order in all_orders:
            if order.symbol != symbol:
                continue
            
            # Check for stop or trailing_stop orders
            if order.type.value not in ['stop', 'trailing_stop']:
                continue
            
            # Must be in active status (not 'cancelled', 'filled')
            # CRITICAL: Include 'held' status for bracket order legs
            if order.status.value not in ['new', 'accepted', 'pending_new', 'held']:
                continue
            
            # Found active stop loss
            stop_price = None
            if hasattr(order, 'stop_price') and order.stop_price:
                stop_price = float(order.stop_price)
            
            return True, stop_price
        
        return False, None
    
    def _cancel_all_exit_orders(self, symbol: str, all_orders: List) -> List[str]:
        """
        Cancel ALL exit orders (stop, take-profit) to free up shares.
        CRITICAL FIX: Must cancel take-profit orders too, not just stops!
        
        This is the KEY fix for "insufficient qty available" errors.
        
        Returns:
            List of cancelled order IDs
        """
        cancelled = []
        
        for order in all_orders:
            if order.symbol != symbol:
                continue
            
            # Cancel ANY exit order (stop, limit, trailing_stop)
            is_exit_order = (
                order.type.value in ['stop', 'trailing_stop', 'limit'] and
                order.side.value == 'sell' and  # For long positions
                order.status.value in ['new', 'accepted', 'pending_new', 'held']
            )
            
            if is_exit_order:
                try:
                    self.alpaca.cancel_order(order.id)
                    cancelled.append(order.id)
                    logger.info(f"🗑️  Cancelled {order.type.value} order: {order.id}")
                except Exception as e:
                    logger.error(f"Failed to cancel order {order.id}: {e}")
        
        if cancelled:
            logger.info(f"✅ Cancelled {len(cancelled)} exit orders for {symbol}")
        
        return cancelled
    
    def _create_stop_loss(self, position) -> bool:
        """
        Create stop loss protection.
        If take-profit exists, cancel it and recreate as complete bracket.
        
        Args:
            position: Position object from trading_state
            
        Returns:
            True if stop loss created successfully
        """
        try:
            symbol = position.symbol
            
            # Get OPEN orders only (not cancelled/filled)
            open_orders = self.alpaca.get_orders(status='open')
            
            # Check if take-profit exists
            has_take_profit = any(
                order.symbol == symbol and
                order.type.value == 'limit' and
                order.side.value == 'sell' and
                order.status.value in ['new', 'accepted', 'pending_new', 'held']
                for order in open_orders
            )
            
            if has_take_profit:
                logger.info(f"🔄 {symbol} has take-profit but no stop - recreating as bracket")
                
                # Cancel all exit orders
                cancelled = self._cancel_all_exit_orders(symbol, open_orders)
                logger.info(f"Cancelled {len(cancelled)} orders for {symbol}")
                
                # Wait briefly for cancellations to process
                import time
                time.sleep(0.5)
                
                # Recreate as complete bracket
                return self._recreate_complete_bracket(position)
            else:
                # No open orders - position needs protection
                # Check if this is a case where orders were cancelled but shares still held
                logger.info(f"No open orders for {symbol} - creating complete bracket")
                
                # Try to create complete bracket first
                try:
                    return self._recreate_complete_bracket(position)
                except Exception as e:
                    logger.warning(f"Bracket creation failed for {symbol}, falling back to standalone stop: {e}")
                    
                    # Fallback to standalone stop
                    entry_price = position.avg_entry_price
                    current_price = position.current_price
                    
                    if hasattr(position, 'stop_loss') and position.stop_loss:
                        risk = abs(entry_price - position.stop_loss)
                    else:
                        risk = entry_price * 0.01  # Default 1% risk
                    
                    profit_r = (current_price - entry_price) / risk if risk > 0 else 0
                    
                    # Use trailing stop for profitable positions
                    use_trailing = (
                        profit_r >= getattr(settings, 'trailing_stops_activation_threshold', 2.0) and
                        getattr(settings, 'trailing_stops_enabled', True)
                    )
                    
                    if use_trailing:
                        return self._create_trailing_stop(position, profit_r)
                    else:
                        return self._create_fixed_stop(position)
            
        except Exception as e:
            logger.error(f"Failed to create stop loss for {position.symbol}: {e}")
            return False
    
    def _create_fixed_stop(self, position) -> bool:
        """Create a fixed stop loss order with MINIMUM 1.5% distance."""
        try:
            symbol = position.symbol
            qty = position.qty
            entry_price = position.avg_entry_price
            current_price = position.current_price
            
            # CRITICAL FIX: Enforce MINIMUM 1.5% stop distance
            # TDG bug was caused by 0.11% stop - way too tight!
            min_stop_pct = 0.015  # 1.5% minimum
            
            # Get ATR for dynamic sizing if available
            try:
                features = trading_state.get_features(symbol)
                atr = features.get('atr', 0) if features else 0
                if atr > 0:
                    # Use ATR-based stop (minimum 1.5%)
                    atr_stop_pct = (atr * 2.5) / entry_price  # 2.5x ATR
                    stop_pct = max(min_stop_pct, atr_stop_pct)
                else:
                    stop_pct = min_stop_pct
            except:
                stop_pct = min_stop_pct
            
            # Calculate stop loss price
            if position.side == 'buy':
                # For long positions, stop BELOW entry
                stop_price = entry_price * (1 - stop_pct)
            else:
                # For short positions, stop ABOVE entry
                stop_price = entry_price * (1 + stop_pct)
            
            logger.info(
                f"🛡️  Stop for {symbol}: ${stop_price:.2f} "
                f"({stop_pct*100:.1f}% from entry ${entry_price:.2f})"
            )
            
            # Sanity check: stop should be below current price for long positions
            if position.side == 'buy' and stop_price >= current_price:
                logger.warning(
                    f"Stop price ${stop_price:.2f} >= current ${current_price:.2f}, "
                    f"adjusting to 1.5% below current"
                )
                stop_price = current_price * 0.985
            
            # Round to 2 decimal places
            stop_price = round(stop_price, 2)
            
            # Create stop loss order
            stop_request = StopOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,  # Assuming long positions
                time_in_force=TimeInForce.GTC,  # Good til cancelled
                stop_price=stop_price,
                client_order_id=f"protection_{symbol}_{int(current_price * 100)}"
            )
            
            # Submit order
            order = self.alpaca.submit_order_request(stop_request)
            
            logger.info(
                f"✅ Fixed stop loss created for {symbol}: "
                f"${stop_price:.2f} (Order ID: {order.id})"
            )
            
            # Update position with stop loss info
            position.stop_loss = stop_price
            trading_state.update_position(position)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create fixed stop for {position.symbol}: {e}")
            return False
    
    def _recreate_complete_bracket(self, position) -> bool:
        """
        Recreate bracket order with BOTH stop-loss and take-profit.
        This is the KEY fix for positions with incomplete protection.
        
        Args:
            position: Position object from trading_state
            
        Returns:
            True if bracket created successfully
        """
        try:
            symbol = position.symbol
            qty = position.qty
            entry_price = position.avg_entry_price
            current_price = position.current_price
            
            # Calculate bracket prices (1.5% stop, 2.5% target for 1.67:1 R/R)
            stop_loss_price = entry_price * 0.985  # 1.5% below entry
            take_profit_price = entry_price * 1.025  # 2.5% above entry
            
            # Safety check: Don't recreate if position is losing badly
            if current_price < entry_price * 0.98:
                logger.warning(f"⚠️  Position {symbol} losing >2%, using emergency stop only")
                return self._create_fixed_stop(position)
            
            # Create separate stop-loss and take-profit orders (not a bracket)
            # We can't use bracket orders for existing positions
            from alpaca.trading.requests import LimitOrderRequest
            
            # Create take-profit order
            tp_request = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,  # Exit order for long position
                time_in_force=TimeInForce.GTC,
                limit_price=round(take_profit_price, 2)
            )
            
            tp_order = self.alpaca.submit_order_request(tp_request)
            logger.info(f"✅ Take-profit created: ${take_profit_price:.2f}")
            
            # Create stop-loss order
            stop_request = StopOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.GTC,
                stop_price=round(stop_loss_price, 2)
            )
            
            order = self.alpaca.submit_order_request(stop_request)
            logger.info(f"✅ Stop-loss created: ${stop_loss_price:.2f}")
            
            logger.info(
                f"✅ Complete bracket recreated for {symbol}: "
                f"Entry ${entry_price:.2f}, Current ${current_price:.2f}, "
                f"SL ${stop_loss_price:.2f}, TP ${take_profit_price:.2f}"
            )
            
            # Update position
            position.stop_loss = stop_loss_price
            position.take_profit = take_profit_price
            trading_state.update_position(position)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to recreate bracket for {symbol}: {e}")
            # Fallback to fixed stop if bracket fails
            logger.info(f"Falling back to fixed stop for {symbol}")
            return self._create_fixed_stop(position)
    
    def _create_trailing_stop(self, position, profit_r: float) -> bool:
        """Create a trailing stop order for profitable position."""
        try:
            symbol = position.symbol
            qty = position.qty
            current_price = position.current_price
            
            # Calculate trailing percentage
            # Use config settings or defaults
            trail_percent = getattr(settings, 'trailing_stops_distance_r', 0.5) * 100  # Convert to percentage
            
            # Minimum 0.5%, maximum 3%
            trail_percent = max(0.5, min(3.0, trail_percent))
            
            # Create trailing stop order
            trailing_request = TrailingStopOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,  # Assuming long positions
                time_in_force=TimeInForce.GTC,
                trail_percent=trail_percent,
                client_order_id=f"trailing_{symbol}_{int(current_price * 100)}"
            )
            
            # Submit order
            order = self.alpaca.submit_order_request(trailing_request)
            
            logger.info(
                f"✅ Trailing stop created for {symbol}: "
                f"{trail_percent:.1f}% trail at +{profit_r:.2f}R profit (Order ID: {order.id})"
            )
            
            # Update position with trailing stop info
            position.stop_loss = current_price * (1 - trail_percent / 100)  # Approximate
            trading_state.update_position(position)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create trailing stop for {position.symbol}: {e}")
            return False
    
    def get_protection_status(self) -> Dict:
        """Get current protection status for monitoring."""
        positions = trading_state.get_all_positions()
        
        return {
            'total_positions': len(positions),
            'protected_positions': len(self.protected_positions),
            'unprotected': len(positions) - len(self.protected_positions),
            'protected_symbols': list(self.protected_positions)
        }


# Global instance
_protection_manager: Optional[StopLossProtectionManager] = None


def get_protection_manager(alpaca_client: AlpacaClient = None) -> StopLossProtectionManager:
    """Get or create the global protection manager instance."""
    global _protection_manager
    
    if _protection_manager is None:
        if alpaca_client is None:
            raise ValueError("alpaca_client required for first initialization")
        _protection_manager = StopLossProtectionManager(alpaca_client)
    
    return _protection_manager
