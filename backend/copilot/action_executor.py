"""
Action executor for copilot commands.

Executes trading actions based on classified intents from ActionClassifier.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import settings
from core.alpaca_client import AlpacaClient
from core.state import trading_state
from data.market_data import MarketDataManager
from news.news_client import NewsClient
from trading.position_manager import PositionManager
from trading.risk_manager import RiskManager
from trading.trading_engine import TradingEngine
from utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ExecutionResult:
    """Result of an executed action."""
    
    success: bool
    action: str
    details: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    error: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None


class ActionExecutor:
    """Executes trading actions based on classified intents."""
    
    def __init__(
        self,
        alpaca_client: AlpacaClient,
        trading_engine: Optional[TradingEngine],
        position_manager: PositionManager,
        risk_manager: RiskManager,
        market_data_manager: MarketDataManager,
        news_client: Optional[NewsClient] = None,
    ):
        self._alpaca = alpaca_client
        self._engine = trading_engine
        self._positions = position_manager
        self._risk = risk_manager
        self._market_data = market_data_manager
        self._news = news_client
        logger.info("ActionExecutor initialized")
    
    async def execute(self, intent: "ActionIntent", context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the action specified in the intent.
        
        Args:
            intent: Classified action intent with parameters
            context: Current trading context
            
        Returns:
            ExecutionResult with success status and details
        """
        if not intent.action:
            return ExecutionResult(
                success=False,
                action="unknown",
                error="No action specified in intent",
                message="Could not determine what action to execute"
            )
        
        # Route to specific action handler
        action_handlers = {
            "check_market_status": self._check_market_status,
            "get_position_details": self._get_position_details,
            "get_account_summary": self._get_account_summary,
            "close_position": self._close_position,
            "close_all_positions": self._close_all_positions,
            "cancel_order": self._cancel_order,
            "cancel_all_orders": self._cancel_all_orders,
            "modify_stop_loss": self._modify_stop_loss,
            "modify_take_profit": self._modify_take_profit,
        }
        
        handler = action_handlers.get(intent.action)
        if not handler:
            return ExecutionResult(
                success=False,
                action=intent.action,
                error=f"Unknown action: {intent.action}",
                message=f"I don't know how to execute '{intent.action}'"
            )
        
        try:
            result = await handler(intent.parameters, context)
            return result
        except Exception as e:
            logger.error(f"Error executing {intent.action}: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                action=intent.action,
                error=str(e),
                message=f"Failed to execute {intent.action}: {str(e)}"
            )
    
    async def _check_market_status(
        self, 
        parameters: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Check if market is currently open."""
        try:
            clock = await asyncio.to_thread(self._alpaca.trading_client.get_clock)
            
            is_open = clock.is_open
            next_open = clock.next_open.isoformat() if clock.next_open else "Unknown"
            next_close = clock.next_close.isoformat() if clock.next_close else "Unknown"
            timestamp = clock.timestamp.isoformat() if clock.timestamp else datetime.utcnow().isoformat()
            
            status_text = "open" if is_open else "closed"
            
            message = f"Market is currently {status_text}."
            if not is_open:
                message += f"\nNext open: {next_open}"
            else:
                message += f"\nCloses at: {next_close}"
            
            return ExecutionResult(
                success=True,
                action="check_market_status",
                details={
                    "is_open": is_open,
                    "next_open": next_open,
                    "next_close": next_close,
                    "timestamp": timestamp,
                },
                message=message
            )
        except Exception as e:
            logger.error(f"Failed to check market status: {e}")
            return ExecutionResult(
                success=False,
                action="check_market_status",
                error=str(e),
                message="Failed to check market status"
            )
    
    async def _get_position_details(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Get detailed information about a specific position."""
        symbol = parameters.get("symbol")
        if not symbol:
            return ExecutionResult(
                success=False,
                action="get_position_details",
                error="No symbol specified",
                message="Please specify which position you want to see"
            )
        
        try:
            position = trading_state.get_position(symbol)
            if not position:
                return ExecutionResult(
                    success=False,
                    action="get_position_details",
                    error=f"No position found for {symbol}",
                    message=f"You don't have an open position in {symbol}"
                )
            
            # Get latest market data
            latest_bars = await asyncio.to_thread(self._alpaca.get_latest_bars, [symbol])
            current_price = float(latest_bars[symbol].close) if latest_bars and symbol in latest_bars else position.current_price
            
            # Get recent news if available
            news_items = []
            if self._news:
                try:
                    articles = await asyncio.to_thread(
                        self._news.get_news,
                        symbols=[symbol],
                        limit=3
                    )
                    news_items = [
                        {
                            "headline": article.get("headline"),
                            "url": article.get("url"),
                            "created_at": article.get("created_at")
                        }
                        for article in articles[:3]
                    ]
                except Exception as e:
                    logger.warning(f"Failed to fetch news for {symbol}: {e}")
            
            # Calculate exposure
            account = context.get("account", {})
            equity = account.get("equity", 0)
            exposure_pct = (abs(position.market_value) / equity * 100) if equity else 0
            
            details = {
                "symbol": position.symbol,
                "qty": position.qty,
                "side": position.side,
                "avg_entry_price": position.avg_entry_price,
                "current_price": current_price,
                "unrealized_pl": position.unrealized_pl,
                "unrealized_pl_pct": position.unrealized_pl_pct,
                "market_value": position.market_value,
                "stop_loss": position.stop_loss,
                "take_profit": position.take_profit,
                "exposure_pct": exposure_pct,
                "entry_time": position.entry_time.isoformat(),
                "news": news_items
            }
            
            pl_sign = "+" if position.unrealized_pl >= 0 else ""
            message = (
                f"{symbol} Position:\n"
                f"- Side: {position.side.upper()}\n"
                f"- Quantity: {position.qty} shares\n"
                f"- Entry: ${position.avg_entry_price:.2f}\n"
                f"- Current: ${current_price:.2f}\n"
                f"- P/L: {pl_sign}${position.unrealized_pl:.2f} ({pl_sign}{position.unrealized_pl_pct:.2f}%)\n"
                f"- Stop Loss: ${position.stop_loss:.2f}\n"
                f"- Take Profit: ${position.take_profit:.2f}\n"
                f"- Exposure: {exposure_pct:.1f}% of equity"
            )
            
            return ExecutionResult(
                success=True,
                action="get_position_details",
                details=details,
                message=message
            )
        except Exception as e:
            logger.error(f"Failed to get position details for {symbol}: {e}")
            return ExecutionResult(
                success=False,
                action="get_position_details",
                error=str(e),
                message=f"Failed to get details for {symbol}"
            )
    
    async def _get_account_summary(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Get account summary with key metrics."""
        try:
            account = context.get("account", {})
            positions = context.get("positions", [])
            performance = context.get("performance", {})
            risk = context.get("risk", {})
            
            equity = account.get("equity", 0)
            cash = account.get("cash", 0)
            buying_power = account.get("buying_power", 0)
            daily_pl = account.get("daily_pl", 0)
            daily_pl_pct = account.get("daily_pl_pct", 0)
            
            open_positions = len(positions)
            max_positions = risk.get("max_positions", 0)
            
            win_rate = performance.get("win_rate", 0) * 100
            profit_factor = performance.get("profit_factor", 0)
            
            circuit_breaker = account.get("circuit_breaker_triggered", False)
            
            pl_sign = "+" if daily_pl >= 0 else ""
            
            message = (
                f"Account Summary:\n"
                f"- Equity: ${equity:,.2f}\n"
                f"- Cash: ${cash:,.2f}\n"
                f"- Buying Power: ${buying_power:,.2f}\n"
                f"- Daily P/L: {pl_sign}${daily_pl:,.2f} ({pl_sign}{daily_pl_pct:.2f}%)\n"
                f"- Open Positions: {open_positions}/{max_positions}\n"
                f"- Win Rate: {win_rate:.1f}%\n"
                f"- Profit Factor: {profit_factor:.2f}\n"
                f"- Circuit Breaker: {'ACTIVE ⚠️' if circuit_breaker else 'Clear ✓'}"
            )
            
            details = {
                "equity": equity,
                "cash": cash,
                "buying_power": buying_power,
                "daily_pl": daily_pl,
                "daily_pl_pct": daily_pl_pct,
                "open_positions": open_positions,
                "max_positions": max_positions,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "circuit_breaker": circuit_breaker,
                "positions": positions[:5]  # Top 5 positions
            }
            
            return ExecutionResult(
                success=True,
                action="get_account_summary",
                details=details,
                message=message
            )
        except Exception as e:
            logger.error(f"Failed to get account summary: {e}")
            return ExecutionResult(
                success=False,
                action="get_account_summary",
                error=str(e),
                message="Failed to get account summary"
            )
    
    async def _close_position(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Close a specific position."""
        symbol = parameters.get("symbol")
        if not symbol:
            return ExecutionResult(
                success=False,
                action="close_position",
                error="No symbol specified",
                message="Please specify which position to close"
            )
        
        try:
            # Check circuit breaker
            if self._risk.check_circuit_breaker():
                return ExecutionResult(
                    success=False,
                    action="close_position",
                    error="Circuit breaker active",
                    message="Cannot close position: circuit breaker is active"
                )
            
            # Get position before closing
            position = trading_state.get_position(symbol)
            if not position:
                return ExecutionResult(
                    success=False,
                    action="close_position",
                    error=f"No position found for {symbol}",
                    message=f"You don't have an open position in {symbol}"
                )
            
            before_state = {
                "symbol": position.symbol,
                "qty": position.qty,
                "side": position.side,
                "avg_entry_price": position.avg_entry_price,
                "current_price": position.current_price,
                "unrealized_pl": position.unrealized_pl,
                "unrealized_pl_pct": position.unrealized_pl_pct,
            }
            
            # Close position
            success = await asyncio.to_thread(
                self._positions.close_position,
                symbol,
                "copilot_command"
            )
            
            if success:
                pl_sign = "+" if before_state["unrealized_pl"] >= 0 else ""
                message = (
                    f"✅ Closed {symbol} position\n"
                    f"- Quantity: {before_state['qty']} shares\n"
                    f"- Entry: ${before_state['avg_entry_price']:.2f}\n"
                    f"- Exit: ${before_state['current_price']:.2f}\n"
                    f"- Realized P/L: {pl_sign}${before_state['unrealized_pl']:.2f} "
                    f"({pl_sign}{before_state['unrealized_pl_pct']:.2f}%)"
                )
                
                return ExecutionResult(
                    success=True,
                    action="close_position",
                    details={
                        "symbol": symbol,
                        "realized_pl": before_state["unrealized_pl"],
                        "realized_pl_pct": before_state["unrealized_pl_pct"],
                        "exit_price": before_state["current_price"],
                        "qty": before_state["qty"],
                    },
                    message=message,
                    before_state=before_state
                )
            else:
                return ExecutionResult(
                    success=False,
                    action="close_position",
                    error="Failed to close position",
                    message=f"Failed to close {symbol} position. Check logs for details."
                )
        except Exception as e:
            logger.error(f"Failed to close position {symbol}: {e}")
            return ExecutionResult(
                success=False,
                action="close_position",
                error=str(e),
                message=f"Error closing {symbol}: {str(e)}"
            )
    
    async def _close_all_positions(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Close all open positions."""
        try:
            # Check circuit breaker
            if self._risk.check_circuit_breaker():
                return ExecutionResult(
                    success=False,
                    action="close_all_positions",
                    error="Circuit breaker active",
                    message="Cannot close positions: circuit breaker is active"
                )
            
            positions = trading_state.get_all_positions()
            if not positions:
                return ExecutionResult(
                    success=True,
                    action="close_all_positions",
                    message="No open positions to close"
                )
            
            # Store before state
            before_state = {
                "count": len(positions),
                "positions": [
                    {
                        "symbol": p.symbol,
                        "qty": p.qty,
                        "unrealized_pl": p.unrealized_pl
                    }
                    for p in positions
                ]
            }
            
            # Close all positions
            closed_count = 0
            failed_symbols = []
            total_pl = 0.0
            
            for position in positions:
                try:
                    success = await asyncio.to_thread(
                        self._positions.close_position,
                        position.symbol,
                        "copilot_close_all"
                    )
                    if success:
                        closed_count += 1
                        total_pl += position.unrealized_pl
                    else:
                        failed_symbols.append(position.symbol)
                except Exception as e:
                    logger.error(f"Failed to close {position.symbol}: {e}")
                    failed_symbols.append(position.symbol)
            
            pl_sign = "+" if total_pl >= 0 else ""
            message = f"✅ Closed {closed_count}/{len(positions)} positions\n"
            message += f"Total Realized P/L: {pl_sign}${total_pl:.2f}"
            
            if failed_symbols:
                message += f"\n⚠️ Failed to close: {', '.join(failed_symbols)}"
            
            return ExecutionResult(
                success=closed_count > 0,
                action="close_all_positions",
                details={
                    "closed_count": closed_count,
                    "total_positions": len(positions),
                    "total_pl": total_pl,
                    "failed_symbols": failed_symbols
                },
                message=message,
                before_state=before_state
            )
        except Exception as e:
            logger.error(f"Failed to close all positions: {e}")
            return ExecutionResult(
                success=False,
                action="close_all_positions",
                error=str(e),
                message=f"Error closing all positions: {str(e)}"
            )
    
    async def _cancel_order(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Cancel a specific order."""
        symbol = parameters.get("symbol")
        
        try:
            # Get open orders
            orders = await asyncio.to_thread(self._alpaca.get_orders, "open")
            
            if not orders:
                return ExecutionResult(
                    success=False,
                    action="cancel_order",
                    message="No open orders to cancel"
                )
            
            # Filter by symbol if specified
            if symbol:
                orders = [o for o in orders if o.symbol == symbol]
                if not orders:
                    return ExecutionResult(
                        success=False,
                        action="cancel_order",
                        message=f"No open orders found for {symbol}"
                    )
            
            # If multiple orders, cancel the most recent
            order = orders[0]
            order_id = order.id
            
            success = await asyncio.to_thread(self._alpaca.cancel_order, order_id)
            
            if success:
                message = (
                    f"✅ Cancelled order\n"
                    f"- Symbol: {order.symbol}\n"
                    f"- Side: {order.side.value}\n"
                    f"- Quantity: {order.qty}\n"
                    f"- Order ID: {order_id}"
                )
                
                return ExecutionResult(
                    success=True,
                    action="cancel_order",
                    details={
                        "order_id": order_id,
                        "symbol": order.symbol,
                        "side": order.side.value,
                        "qty": order.qty
                    },
                    message=message
                )
            else:
                return ExecutionResult(
                    success=False,
                    action="cancel_order",
                    error="Failed to cancel order",
                    message=f"Failed to cancel order {order_id}"
                )
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return ExecutionResult(
                success=False,
                action="cancel_order",
                error=str(e),
                message=f"Error cancelling order: {str(e)}"
            )
    
    async def _cancel_all_orders(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Cancel all open orders."""
        try:
            orders = await asyncio.to_thread(self._alpaca.get_orders, "open")
            
            if not orders:
                return ExecutionResult(
                    success=True,
                    action="cancel_all_orders",
                    message="No open orders to cancel"
                )
            
            cancelled_count = 0
            failed_count = 0
            
            for order in orders:
                try:
                    success = await asyncio.to_thread(self._alpaca.cancel_order, order.id)
                    if success:
                        cancelled_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Failed to cancel order {order.id}: {e}")
                    failed_count += 1
            
            message = f"✅ Cancelled {cancelled_count}/{len(orders)} orders"
            if failed_count > 0:
                message += f"\n⚠️ Failed to cancel {failed_count} orders"
            
            return ExecutionResult(
                success=cancelled_count > 0,
                action="cancel_all_orders",
                details={
                    "cancelled_count": cancelled_count,
                    "total_orders": len(orders),
                    "failed_count": failed_count
                },
                message=message
            )
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return ExecutionResult(
                success=False,
                action="cancel_all_orders",
                error=str(e),
                message=f"Error cancelling orders: {str(e)}"
            )
    
    async def _modify_stop_loss(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Modify stop-loss level for a position."""
        symbol = parameters.get("symbol")
        new_stop = parameters.get("stop_loss")
        
        if not symbol or new_stop is None:
            return ExecutionResult(
                success=False,
                action="modify_stop_loss",
                error="Missing symbol or stop-loss price",
                message="Please specify both symbol and new stop-loss price"
            )
        
        try:
            position = trading_state.get_position(symbol)
            if not position:
                return ExecutionResult(
                    success=False,
                    action="modify_stop_loss",
                    error=f"No position found for {symbol}",
                    message=f"You don't have an open position in {symbol}"
                )
            
            # Validate stop-loss level
            current_price = position.current_price
            
            if position.side == "buy":
                # For long positions, stop must be below current price
                if new_stop >= current_price:
                    return ExecutionResult(
                        success=False,
                        action="modify_stop_loss",
                        error="Invalid stop-loss level",
                        message=f"Stop-loss must be below current price ${current_price:.2f} for long positions"
                    )
                
                # Check minimum distance (e.g., 1% or 1 ATR)
                features = self._market_data.get_latest_features(symbol)
                if features:
                    atr = features.get("atr", 0)
                    min_distance = max(current_price * 0.01, atr * 0.5)  # 1% or 0.5 ATR
                    if (current_price - new_stop) < min_distance:
                        return ExecutionResult(
                            success=False,
                            action="modify_stop_loss",
                            error="Stop-loss too close to current price",
                            message=f"Stop-loss must be at least ${min_distance:.2f} below current price"
                        )
            else:
                # For short positions, stop must be above current price
                if new_stop <= current_price:
                    return ExecutionResult(
                        success=False,
                        action="modify_stop_loss",
                        error="Invalid stop-loss level",
                        message=f"Stop-loss must be above current price ${current_price:.2f} for short positions"
                    )
                
                # Check minimum distance
                features = self._market_data.get_latest_features(symbol)
                if features:
                    atr = features.get("atr", 0)
                    min_distance = max(current_price * 0.01, atr * 0.5)
                    if (new_stop - current_price) < min_distance:
                        return ExecutionResult(
                            success=False,
                            action="modify_stop_loss",
                            error="Stop-loss too close to current price",
                            message=f"Stop-loss must be at least ${min_distance:.2f} above current price"
                        )
            
            # Store before state
            before_state = {
                "symbol": symbol,
                "old_stop_loss": position.stop_loss,
                "current_price": current_price
            }
            
            # Update stop-loss
            position.stop_loss = new_stop
            trading_state.update_position(position)
            
            message = (
                f"✅ Updated stop-loss for {symbol}\n"
                f"- Old Stop: ${before_state['old_stop_loss']:.2f}\n"
                f"- New Stop: ${new_stop:.2f}\n"
                f"- Current Price: ${current_price:.2f}"
            )
            
            return ExecutionResult(
                success=True,
                action="modify_stop_loss",
                details={
                    "symbol": symbol,
                    "old_stop_loss": before_state["old_stop_loss"],
                    "new_stop_loss": new_stop,
                    "current_price": current_price
                },
                message=message,
                before_state=before_state,
                after_state={"stop_loss": new_stop}
            )
        except Exception as e:
            logger.error(f"Failed to modify stop-loss for {symbol}: {e}")
            return ExecutionResult(
                success=False,
                action="modify_stop_loss",
                error=str(e),
                message=f"Error modifying stop-loss: {str(e)}"
            )
    
    async def _modify_take_profit(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Modify take-profit level for a position."""
        symbol = parameters.get("symbol")
        new_tp = parameters.get("take_profit")
        
        if not symbol or new_tp is None:
            return ExecutionResult(
                success=False,
                action="modify_take_profit",
                error="Missing symbol or take-profit price",
                message="Please specify both symbol and new take-profit price"
            )
        
        try:
            position = trading_state.get_position(symbol)
            if not position:
                return ExecutionResult(
                    success=False,
                    action="modify_take_profit",
                    error=f"No position found for {symbol}",
                    message=f"You don't have an open position in {symbol}"
                )
            
            # Validate take-profit level
            current_price = position.current_price
            
            if position.side == "buy":
                # For long positions, TP must be above current price
                if new_tp <= current_price:
                    return ExecutionResult(
                        success=False,
                        action="modify_take_profit",
                        error="Invalid take-profit level",
                        message=f"Take-profit must be above current price ${current_price:.2f} for long positions"
                    )
            else:
                # For short positions, TP must be below current price
                if new_tp >= current_price:
                    return ExecutionResult(
                        success=False,
                        action="modify_take_profit",
                        error="Invalid take-profit level",
                        message=f"Take-profit must be below current price ${current_price:.2f} for short positions"
                    )
            
            # Store before state
            before_state = {
                "symbol": symbol,
                "old_take_profit": position.take_profit,
                "current_price": current_price
            }
            
            # Update take-profit
            position.take_profit = new_tp
            trading_state.update_position(position)
            
            message = (
                f"✅ Updated take-profit for {symbol}\n"
                f"- Old Target: ${before_state['old_take_profit']:.2f}\n"
                f"- New Target: ${new_tp:.2f}\n"
                f"- Current Price: ${current_price:.2f}"
            )
            
            return ExecutionResult(
                success=True,
                action="modify_take_profit",
                details={
                    "symbol": symbol,
                    "old_take_profit": before_state["old_take_profit"],
                    "new_take_profit": new_tp,
                    "current_price": current_price
                },
                message=message,
                before_state=before_state,
                after_state={"take_profit": new_tp}
            )
        except Exception as e:
            logger.error(f"Failed to modify take-profit for {symbol}: {e}")
            return ExecutionResult(
                success=False,
                action="modify_take_profit",
                error=str(e),
                message=f"Error modifying take-profit: {str(e)}"
            )
