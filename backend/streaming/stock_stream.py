"""
Real-time stock data streaming using Alpaca WebSocket API.
Replaces polling with push-based updates for lower latency.
"""

from alpaca.data.live import StockDataStream
from alpaca.data.models import Bar, Quote, Trade
from typing import Callable, List, Optional
from config import settings
from utils.logger import setup_logger
import asyncio

logger = setup_logger(__name__)


class StockStreamManager:
    """Manages real-time stock data streams from Alpaca."""
    
    def __init__(self):
        self.stream = StockDataStream(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            raw_data=False
        )
        self.is_running = False
        self.subscribed_symbols: List[str] = []
        
        # Callbacks for different data types
        self.quote_callbacks: List[Callable] = []
        self.trade_callbacks: List[Callable] = []
        self.bar_callbacks: List[Callable] = []
        
        logger.info("Stock stream manager initialized")
    
    def on_quote(self, callback: Callable[[Quote], None]):
        """Register callback for quote updates."""
        self.quote_callbacks.append(callback)
        
    def on_trade(self, callback: Callable[[Trade], None]):
        """Register callback for trade updates."""
        self.trade_callbacks.append(callback)
        
    def on_bar(self, callback: Callable[[Bar], None]):
        """Register callback for bar updates."""
        self.bar_callbacks.append(callback)
    
    async def _handle_quote(self, quote: Quote):
        """Handle incoming quote data."""
        try:
            for callback in self.quote_callbacks:
                await callback(quote)
        except Exception as e:
            logger.error(f"Error handling quote: {e}")
    
    async def _handle_trade(self, trade: Trade):
        """Handle incoming trade data."""
        try:
            for callback in self.trade_callbacks:
                await callback(trade)
        except Exception as e:
            logger.error(f"Error handling trade: {e}")
    
    async def _handle_bar(self, bar: Bar):
        """Handle incoming bar data."""
        try:
            for callback in self.bar_callbacks:
                await callback(bar)
        except Exception as e:
            logger.error(f"Error handling bar: {e}")
    
    def subscribe(self, symbols: List[str], data_types: Optional[List[str]] = None):
        """
        Subscribe to real-time data for symbols.
        
        Args:
            symbols: List of symbols to subscribe to
            data_types: List of data types ('quotes', 'trades', 'bars'). Default: all
        """
        if data_types is None:
            data_types = ['quotes', 'trades', 'bars']
        
        try:
            # Register handlers
            if 'quotes' in data_types:
                self.stream.subscribe_quotes(self._handle_quote, *symbols)
                logger.info(f"Subscribed to quotes for {len(symbols)} symbols")
            
            if 'trades' in data_types:
                self.stream.subscribe_trades(self._handle_trade, *symbols)
                logger.info(f"Subscribed to trades for {len(symbols)} symbols")
            
            if 'bars' in data_types:
                self.stream.subscribe_bars(self._handle_bar, *symbols)
                logger.info(f"Subscribed to bars for {len(symbols)} symbols")
            
            self.subscribed_symbols.extend(symbols)
            
        except Exception as e:
            logger.error(f"Failed to subscribe to symbols: {e}")
            raise
    
    def unsubscribe(self, symbols: List[str], data_types: Optional[List[str]] = None):
        """
        Unsubscribe from real-time data for symbols.
        
        Args:
            symbols: List of symbols to unsubscribe from
            data_types: List of data types to unsubscribe from. Default: all
        """
        if data_types is None:
            data_types = ['quotes', 'trades', 'bars']
        
        try:
            if 'quotes' in data_types:
                self.stream.unsubscribe_quotes(*symbols)
            
            if 'trades' in data_types:
                self.stream.unsubscribe_trades(*symbols)
            
            if 'bars' in data_types:
                self.stream.unsubscribe_bars(*symbols)
            
            for symbol in symbols:
                if symbol in self.subscribed_symbols:
                    self.subscribed_symbols.remove(symbol)
            
            logger.info(f"Unsubscribed from {len(symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from symbols: {e}")
    
    async def start(self):
        """Start the WebSocket stream."""
        if self.is_running:
            logger.warning("Stream already running")
            return
        
        try:
            self.is_running = True
            logger.info("🌊 Starting stock data stream...")
            await self.stream._run_forever()
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop the WebSocket stream."""
        if not self.is_running:
            return
        
        try:
            logger.info("Stopping stock data stream...")
            await self.stream.stop_ws()
            self.is_running = False
            logger.info("Stock data stream stopped")
            
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
    
    def get_status(self) -> dict:
        """Get stream status."""
        return {
            "running": self.is_running,
            "subscribed_symbols": self.subscribed_symbols,
            "quote_callbacks": len(self.quote_callbacks),
            "trade_callbacks": len(self.trade_callbacks),
            "bar_callbacks": len(self.bar_callbacks)
        }
