import logging
import asyncio
from typing import Any
from streaming.broadcaster import StreamingBroadcaster

class WebSocketLogHandler(logging.Handler):
    """
    Custom logging handler that pushes log records to the StreamingBroadcaster.
    """
    def __init__(self, broadcaster: StreamingBroadcaster):
        super().__init__()
        self.broadcaster = broadcaster
        self.loop = asyncio.get_running_loop() if asyncio.get_event_loop().is_running() else None

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            log_entry = {
                "type": "log",
                "payload": {
                    "timestamp": record.created, # Unix timestamp
                    "level": record.levelname,
                    "message": msg,
                    "source": record.name
                }
            }
            
            # We need to schedule the async enqueue on the event loop
            # If we are in the loop, we can create a task.
            # If we are in a thread, we need run_coroutine_threadsafe.
            
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
                
            if loop and loop.is_running():
                loop.create_task(self.broadcaster.enqueue(log_entry))
            elif self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcaster.enqueue(log_entry), self.loop)
                
        except Exception:
            self.handleError(record)
