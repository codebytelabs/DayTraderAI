"""
Central stream manager that coordinates all real-time data streams.
Handles connection lifecycle, health monitoring, and reconnection logic.
"""

from typing import Dict, Optional, List
from datetime import datetime
from .stock_stream import StockStreamManager
from utils.logger import setup_logger
import asyncio
from config import settings

logger = setup_logger(__name__)


class StreamManager:
    """Coordinates all real-time data streams."""
    
    def __init__(self):
        self.stock_stream: Optional[StockStreamManager] = None
        self.is_running = False
        self._tasks: List[asyncio.Task] = []
        self._symbols: List[str] = []
        self._reconnect_attempts = 0
        self._last_reconnect: Optional[datetime] = None
        self._reconnect_delay = settings.stream_reconnect_delay
        
        logger.info("Stream manager initialized")
    
    async def start(self, symbols: List[str]):
        """
        Start all data streams.
        
        Args:
            symbols: List of symbols to stream
        """
        if self.is_running:
            logger.warning("Streams already running")
            return
        
        self._symbols = symbols

        try:
            self.stock_stream = StockStreamManager()
            self.stock_stream.subscribe(symbols, data_types=['quotes', 'trades', 'bars'])

            stream_task = asyncio.create_task(self._run_with_reconnect())
            self._tasks.append(stream_task)

            self.is_running = True
            logger.info(f"✅ Streams started for {len(symbols)} symbols")

        except Exception as e:
            logger.error(f"Failed to start streams: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop all data streams."""
        if not self.is_running:
            return
        
        try:
            logger.info("Stopping all streams...")
            
            # Stop stock stream
            if self.stock_stream:
                await self.stock_stream.stop()
            
            # Cancel all tasks
            for task in self._tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete
            if self._tasks:
                await asyncio.gather(*self._tasks, return_exceptions=True)
            
            self._tasks.clear()
            self.is_running = False
            
            logger.info("All streams stopped")
            
        except Exception as e:
            logger.error(f"Error stopping streams: {e}")
    
    def get_status(self) -> Dict:
        """Get status of all streams."""
        return {
            "running": self.is_running,
            "reconnect_attempts": self._reconnect_attempts,
            "last_reconnect": self._last_reconnect.isoformat() if self._last_reconnect else None,
            "stock_stream": self.stock_stream.get_status() if self.stock_stream else None
        }
    
    def register_quote_handler(self, handler):
        """Register handler for quote updates."""
        if self.stock_stream:
            self.stock_stream.on_quote(handler)
    
    def register_trade_handler(self, handler):
        """Register handler for trade updates."""
        if self.stock_stream:
            self.stock_stream.on_trade(handler)
    
    def register_bar_handler(self, handler):
        """Register handler for bar updates."""
        if self.stock_stream:
            self.stock_stream.on_bar(handler)

    async def _run_with_reconnect(self):
        while self.is_running and self.stock_stream:
            try:
                await self.stock_stream.start()
                break
            except Exception as exc:
                self._reconnect_attempts += 1
                self._last_reconnect = datetime.utcnow()
                logger.error(
                    "Streaming connection failed (%s). Attempt %s. Reconnecting in %ss",
                    exc,
                    self._reconnect_attempts,
                    self._reconnect_delay,
                )
                await asyncio.sleep(self._reconnect_delay)
                # Recreate stream instance for clean reconnect
                self.stock_stream = StockStreamManager()
                try:
                    self.stock_stream.subscribe(self._symbols, data_types=['quotes', 'trades', 'bars'])
                except Exception as sub_exc:
                    logger.error("Resubscribe failed during reconnect: %s", sub_exc)
        logger.info("Streaming loop exited")


# Global stream manager instance
stream_manager = StreamManager()
