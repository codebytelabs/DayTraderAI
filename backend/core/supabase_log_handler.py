"""
Custom logging handler that persists logs to Supabase.
"""
import logging
from datetime import datetime
from typing import Optional


class SupabaseLogHandler(logging.Handler):
    """
    Custom logging handler that writes logs to Supabase database.
    Only logs INFO level and above to avoid spam.
    """
    
    def __init__(self, supabase_client, source: str = "backend"):
        super().__init__()
        self.supabase_client = supabase_client
        self.source = source
        self.setLevel(logging.INFO)  # Only log INFO and above
        
    def emit(self, record: logging.LogRecord):
        """
        Emit a log record to Supabase.
        """
        try:
            # Skip if no supabase client
            if not self.supabase_client:
                return
            
            # Map Python log levels to our log levels
            level_map = {
                logging.DEBUG: "info",
                logging.INFO: "info",
                logging.WARNING: "warn",
                logging.ERROR: "error",
                logging.CRITICAL: "error"
            }
            
            level = level_map.get(record.levelno, "info")
            message = self.format(record)
            
            # Extract component from logger name (e.g., "trading.engine" -> "trading")
            component = record.name.split('.')[0] if '.' in record.name else record.name
            
            # Insert log into Supabase
            self.supabase_client.insert_log({
                "level": level,
                "message": message,
                "component": component,
                "source": self.source,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception:
            # Silently fail - don't want logging to crash the app
            pass
