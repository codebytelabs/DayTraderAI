"""
Bracket order implementation for automatic take-profit and stop-loss.
A bracket order consists of:
1. Entry order (market or limit)
2. Take profit order (limit)
3. Stop loss order (stop)
"""

from alpaca.trading.requests import (
    MarketOrderRequest, 
    LimitOrderRequest,
    StopOrderRequest,
    TrailingStopOrderRequest
)
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from typing import Optional, Dict
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BracketOrderBuilder:
    """Builder for creating bracket orders with TP and SL."""
    
    @staticmethod
    def create_market_bracket(
        symbol: str,
        qty: float,
        side: OrderSide,
        take_profit_price: float,
        stop_loss_price: float,
        client_order_id: Optional[str] = None
    ) -> MarketOrderRequest:
        """
        Create a market bracket order.
        
        Args:
            symbol: Stock symbol
            qty: Quantity to trade
            side: BUY or SELL
            take_profit_price: Take profit limit price
            stop_loss_price: Stop loss price
            client_order_id: Optional custom order ID
            
        Returns:
            MarketOrderRequest with bracket parameters
        """
        try:
            order = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.BRACKET,
                take_profit={"limit_price": take_profit_price},
                stop_loss={"stop_price": stop_loss_price},
                client_order_id=client_order_id
            )
            
            logger.info(
                f"Created bracket order: {side} {qty} {symbol} "
                f"TP=${take_profit_price:.2f} SL=${stop_loss_price:.2f}"
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to create bracket order: {e}")
            raise
    
    @staticmethod
    def create_limit_bracket(
        symbol: str,
        qty: float,
        side: OrderSide,
        limit_price: float,
        take_profit_price: float,
        stop_loss_price: float,
        client_order_id: Optional[str] = None
    ) -> LimitOrderRequest:
        """
        Create a limit bracket order.
        
        Args:
            symbol: Stock symbol
            qty: Quantity to trade
            side: BUY or SELL
            limit_price: Entry limit price
            take_profit_price: Take profit limit price
            stop_loss_price: Stop loss price
            client_order_id: Optional custom order ID
            
        Returns:
            LimitOrderRequest with bracket parameters
        """
        try:
            order = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price,
                order_class=OrderClass.BRACKET,
                take_profit={"limit_price": take_profit_price},
                stop_loss={"stop_price": stop_loss_price},
                client_order_id=client_order_id
            )
            
            logger.info(
                f"Created limit bracket order: {side} {qty} {symbol} "
                f"@${limit_price:.2f} TP=${take_profit_price:.2f} SL=${stop_loss_price:.2f}"
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to create limit bracket order: {e}")
            raise
    
    @staticmethod
    def create_trailing_stop_bracket(
        symbol: str,
        qty: float,
        side: OrderSide,
        trail_percent: float,
        take_profit_price: float,
        client_order_id: Optional[str] = None
    ) -> MarketOrderRequest:
        """
        Create a bracket order with trailing stop loss.
        
        Args:
            symbol: Stock symbol
            qty: Quantity to trade
            side: BUY or SELL
            trail_percent: Trailing stop percentage (e.g., 2.0 for 2%)
            take_profit_price: Take profit limit price
            client_order_id: Optional custom order ID
            
        Returns:
            MarketOrderRequest with trailing stop bracket
        """
        try:
            order = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.BRACKET,
                take_profit={"limit_price": take_profit_price},
                stop_loss={"trail_percent": trail_percent},
                client_order_id=client_order_id
            )
            
            logger.info(
                f"Created trailing bracket order: {side} {qty} {symbol} "
                f"Trail={trail_percent}% TP=${take_profit_price:.2f}"
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to create trailing bracket order: {e}")
            raise
    
    @staticmethod
    def calculate_bracket_prices(
        entry_price: float,
        side: OrderSide,
        take_profit_pct: float = 2.0,
        stop_loss_pct: float = 1.0
    ) -> Dict[str, float]:
        """
        Calculate take profit and stop loss prices based on percentages.
        
        Args:
            entry_price: Entry price
            side: BUY or SELL
            take_profit_pct: Take profit percentage (default 2%)
            stop_loss_pct: Stop loss percentage (default 1%)
            
        Returns:
            Dict with 'take_profit' and 'stop_loss' prices
        """
        if side == OrderSide.BUY:
            # Long position
            take_profit = entry_price * (1 + take_profit_pct / 100)
            stop_loss = entry_price * (1 - stop_loss_pct / 100)
        else:
            # Short position
            take_profit = entry_price * (1 - take_profit_pct / 100)
            stop_loss = entry_price * (1 + stop_loss_pct / 100)
        
        return {
            "take_profit": round(take_profit, 2),
            "stop_loss": round(stop_loss, 2)
        }
