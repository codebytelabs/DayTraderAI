from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    GetOrdersRequest,
    GetPortfolioHistoryRequest,
    ReplaceOrderRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus, QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestBarRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed
from datetime import datetime, timedelta, timezone
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
    
    def get_orders(self, status: Optional[str] = None, symbols: Optional[List[str]] = None):
        """Get orders, optionally filtered by status and symbols."""
        try:
            if status:
                # Map string status to QueryOrderStatus enum (used for filtering)
                status_map = {
                    'open': QueryOrderStatus.OPEN,
                    'closed': QueryOrderStatus.CLOSED,
                    'all': QueryOrderStatus.ALL,
                }
                status_enum = status_map.get(status.lower())
                if not status_enum:
                    logger.warning(f"Unknown order status: {status}, fetching all orders")
                    status_enum = QueryOrderStatus.ALL
            else:
                status_enum = QueryOrderStatus.ALL
            
            request = GetOrdersRequest(status=status_enum, symbols=symbols)
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

    def submit_order_request(self, request: BaseOrderRequest):
        """Submit a pre-built order request (e.g., bracket orders)."""
        try:
            order = self.trading_client.submit_order(request)
            side = getattr(request, "side", None)
            qty = getattr(request, "qty", None)
            symbol = getattr(request, "symbol", None)
            logger.info(
                "Order submitted: %s %s %s (Class=%s)",
                getattr(side, "value", side),
                qty,
                symbol,
                getattr(request, "order_class", None),
            )
            return order
        except Exception as e:
            logger.error(f"Failed to submit order request: {e}")
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
    
    def cancel_order_with_error(self, order_id: str) -> tuple:
        """
        Cancel an order and return both success status and error message.
        CRITICAL: Used to detect "already filled" race conditions.
        
        Returns:
            Tuple of (success: bool, error_message: str or None)
        """
        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f"Order canceled: {order_id}")
            return True, None
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to cancel order {order_id}: {error_msg}")
            return False, error_msg
            
    def replace_order(
        self,
        order_id: str,
        qty: Optional[int] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        trail: Optional[float] = None,
        client_order_id: Optional[str] = None
    ):
        """
        Replace an existing order with updated parameters.
        Useful for trailing stops and adjusting brackets.
        """
        try:
            # Build request object
            # Only include fields that are not None
            req_data = {}
            if qty is not None:
                req_data['qty'] = qty
            if limit_price is not None:
                req_data['limit_price'] = limit_price
            if stop_price is not None:
                req_data['stop_price'] = stop_price
            if trail is not None:
                req_data['trail'] = trail
            if client_order_id is not None:
                req_data['client_order_id'] = client_order_id
                
            request = ReplaceOrderRequest(**req_data)
            
            order = self.trading_client.replace_order_by_id(
                order_id=order_id,
                order_data=request
            )
            
            logger.info(f"Order {order_id} replaced successfully")
            return order
            
        except Exception as e:
            logger.error(f"Failed to replace order {order_id}: {e}")
            return None
    
    def close_position(self, symbol: str):
        """Close position for symbol."""
        try:
            self.trading_client.close_position(symbol)
            logger.info(f"Position closed: {symbol}")
            return True
        except Exception as e:
            error_msg = str(e)
            # If position not found, it's already closed - return True to clean up state
            if "position not found" in error_msg.lower() or "40410000" in error_msg:
                logger.info(f"Position {symbol} already closed (not found in Alpaca)")
                return True
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
        """Get historical bars using IEX feed (free for paper trading)."""
        try:
            if start is None:
                start = datetime.now(timezone.utc) - timedelta(days=30)
            if end is None:
                end = datetime.now(timezone.utc)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit,
                feed=DataFeed.IEX  # Use IEX feed for paper trading (free)
            )
            
            bars = self.data_client.get_stock_bars(request)
            return bars.df if hasattr(bars, 'df') else bars
            
        except Exception as e:
            logger.error(f"Failed to get bars: {e}")
            return None
    
    def get_latest_bars(self, symbols: List[str]):
        """Get latest bar for symbols using IEX feed (free)."""
        try:
            request = StockLatestBarRequest(
                symbol_or_symbols=symbols,
                feed=DataFeed.IEX  # Use IEX feed for paper trading (free)
            )
            bars = self.data_client.get_stock_latest_bar(request)
            return bars
        except Exception as e:
            logger.error(f"Failed to get latest bars: {e}")
            return None
    
    def get_bars_for_symbol(
        self,
        symbol: str,
        timeframe: TimeFrame = TimeFrame.Minute,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None
    ):
        """
        Get bars for a single symbol, returning a clean DataFrame.
        Handles multi-index extraction automatically.
        
        This is a convenience method that wraps get_bars() and handles
        the multi-index DataFrame structure that Alpaca returns.
        """
        try:
            import pandas as pd
            
            bars = self.get_bars(
                symbols=[symbol],
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit
            )
            
            if bars is None:
                return None
            
            # Extract symbol level if multi-indexed
            if isinstance(bars, pd.DataFrame) and isinstance(bars.index, pd.MultiIndex):
                if symbol in bars.index.get_level_values(0):
                    return bars.loc[symbol]
                else:
                    logger.warning(f"Symbol {symbol} not found in multi-indexed bars")
                    return None
            else:
                return bars
                
        except Exception as e:
            logger.error(f"Failed to get bars for {symbol}: {e}")
            return None
    
    def get_latest_trade_price(self, symbol: str) -> Optional[float]:
        """
        Get the most recent trade price for a symbol.
        This is the ACTUAL current market price, not historical bar data.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Latest trade price, or None if unavailable
        """
        try:
            from alpaca.data.requests import StockLatestTradeRequest
            
            request = StockLatestTradeRequest(
                symbol_or_symbols=symbol,
                feed=DataFeed.IEX
            )
            trades = self.data_client.get_stock_latest_trade(request)
            
            if trades and symbol in trades:
                price = float(trades[symbol].price)
                logger.debug(f"📍 Real-time price for {symbol}: ${price:.2f}")
                return price
            return None
        except Exception as e:
            logger.warning(f"Failed to get latest trade for {symbol}: {e}")
            return None
    
    def get_latest_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get the latest bid/ask quote for a symbol.
        Useful for checking spread before placing orders.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            dict: {'bid': float, 'ask': float, 'spread': float, 'mid': float}
        """
        try:
            from alpaca.data.requests import StockLatestQuoteRequest
            
            request = StockLatestQuoteRequest(
                symbol_or_symbols=symbol,
                feed=DataFeed.IEX
            )
            quotes = self.data_client.get_stock_latest_quote(request)
            
            if quotes and symbol in quotes:
                quote = quotes[symbol]
                bid = float(quote.bid_price)
                ask = float(quote.ask_price)
                spread = ask - bid
                mid = (bid + ask) / 2
                logger.debug(f"📍 Quote for {symbol}: Bid ${bid:.2f} | Ask ${ask:.2f} | Spread ${spread:.2f}")
                return {
                    'bid': bid,
                    'ask': ask,
                    'spread': spread,
                    'mid': mid
                }
            return None
        except Exception as e:
            logger.warning(f"Failed to get latest quote for {symbol}: {e}")
            return None
    
    def is_market_open(self) -> bool:
        """Check if market is currently open."""
        try:
            clock = self.trading_client.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f"Failed to check market status: {e}")
            return False
    
    def get_clock(self):
        """Get market clock information."""
        try:
            return self.trading_client.get_clock()
        except Exception as e:
            logger.error(f"Failed to get clock: {e}")
            raise
    
    def get_portfolio_history(
        self,
        timeframe: str = "1D",
        period: str = None
    ) -> Optional[List[Dict]]:
        """
        Fetch portfolio equity history from Alpaca.
        
        Args:
            timeframe: Button clicked in UI - "1D", "1W", "1M", "3M", "1Y", "ALL"
            period: Not used, kept for compatibility
        
        Returns:
            List of portfolio history data points with timestamp and equity
        """
        try:
            # Map UI timeframe to Alpaca API parameters
            if timeframe == "1D":
                api_period = "1D"
                api_timeframe = "5Min"
            elif timeframe == "1W":
                api_period = "1W"
                api_timeframe = "1H"
            elif timeframe == "1M":
                api_period = "1M"
                api_timeframe = "1D"
            elif timeframe == "3M":
                api_period = "3M"
                api_timeframe = "1D"
            elif timeframe == "1Y":
                api_period = "1A"  # Alpaca uses "1A" for 1 year
                api_timeframe = "1D"
            else:  # "ALL" or any other value
                api_period = "all"  # Get all available history
                api_timeframe = "1D"
            
            request = GetPortfolioHistoryRequest(
                period=api_period,
                timeframe=api_timeframe,
                extended_hours=False
            )
            
            # Fetch portfolio history from Alpaca
            portfolio_history = self.trading_client.get_portfolio_history(history_filter=request)
            
            if not portfolio_history:
                logger.warning("No portfolio history returned from Alpaca")
                return None
            
            # Transform to list of dicts
            result = []
            timestamps = portfolio_history.timestamp
            equity_values = portfolio_history.equity
            
            for i in range(len(timestamps)):
                result.append({
                    'timestamp': timestamps[i],  # Already in seconds
                    'equity': equity_values[i]
                })
            
            logger.info(f"Fetched {len(result)} portfolio history points (period={api_period}, timeframe={api_timeframe})")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get portfolio history: {e}")
            return None
