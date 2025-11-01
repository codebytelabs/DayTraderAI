from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestBarRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AlpacaClient:
    def __init__(self):
        self.trading_client = TradingClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            paper=True  # Always start with paper trading
        )
        self.data_client = StockHistoricalDataClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key
        )
        logger.info("Alpaca client initialized (PAPER TRADING)")
    
    def get_account(self):
        """Get account information."""
        try:
            return self.trading_client.get_account()
        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            raise
    
    def get_positions(self):
        """Get all open positions."""
        try:
            return self.trading_client.get_all_positions()
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    def get_position(self, symbol: str):
        """Get position for specific symbol."""
        try:
            return self.trading_client.get_open_position(symbol)
        except Exception as e:
            logger.debug(f"No position for {symbol}: {e}")
            return None
    
    def get_orders(self, status: Optional[str] = None):
        """Get orders, optionally filtered by status."""
        try:
            request = GetOrdersRequest(
                status=OrderStatus[status.upper()] if status else None
            )
            return self.trading_client.get_orders(filter=request)
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            return []
    
    def submit_market_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        client_order_id: str
    ):
        """Submit market order with deterministic ID."""
        try:
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            
            request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY,
                client_order_id=client_order_id
            )
            
            order = self.trading_client.submit_order(request)
            logger.info(f"Order submitted: {side} {qty} {symbol} (ID: {client_order_id})")
            return order
            
        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            raise
    
    def cancel_order(self, order_id: str):
        """Cancel an order."""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f"Order canceled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def close_position(self, symbol: str):
        """Close position for symbol."""
        try:
            self.trading_client.close_position(symbol)
            logger.info(f"Position closed: {symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to close position {symbol}: {e}")
            return False
    
    def close_all_positions(self):
        """Emergency: close all positions."""
        try:
            self.trading_client.close_all_positions(cancel_orders=True)
            logger.warning("ALL POSITIONS CLOSED (EMERGENCY)")
            return True
        except Exception as e:
            logger.error(f"Failed to close all positions: {e}")
            return False
    
    def get_bars(
        self,
        symbols: List[str],
        timeframe: TimeFrame = TimeFrame.Minute,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None
    ):
        """Get historical bars."""
        try:
            if start is None:
                start = datetime.now() - timedelta(days=30)
            if end is None:
                end = datetime.now()
            
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit
            )
            
            bars = self.data_client.get_stock_bars(request)
            return bars.df if hasattr(bars, 'df') else bars
            
        except Exception as e:
            logger.error(f"Failed to get bars: {e}")
            return None
    
    def get_latest_bars(self, symbols: List[str]):
        """Get latest bar for symbols."""
        try:
            request = StockLatestBarRequest(symbol_or_symbols=symbols)
            bars = self.data_client.get_stock_latest_bar(request)
            return bars
        except Exception as e:
            logger.error(f"Failed to get latest bars: {e}")
            return None
    
    def is_market_open(self) -> bool:
        """Check if market is currently open."""
        try:
            clock = self.trading_client.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f"Failed to check market status: {e}")
            return False
