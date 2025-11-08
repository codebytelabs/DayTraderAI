from supabase import create_client, Client
from typing import Dict, List, Optional, Any
from datetime import datetime
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
        logger.info("Supabase client initialized")
    
    # Trades
    def insert_trade(self, trade_data: Dict[str, Any]):
        """Insert completed trade."""
        try:
            result = self.client.table("trades").insert(trade_data).execute()
            logger.info(f"Trade inserted: {trade_data.get('symbol')}")
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to insert trade: {e}")
            return None
    
    def get_trades(self, limit: int = 100):
        """Get recent trades."""
        try:
            result = self.client.table("trades")\
                .select("*")\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get trades: {e}")
            return []
    
    # Positions
    def upsert_position(self, position_data: Dict[str, Any]):
        """Insert or update position."""
        try:
            result = self.client.table("positions")\
                .upsert(position_data, on_conflict="symbol")\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to upsert position: {e}")
            return None
    
    def delete_position(self, symbol: str):
        """Delete position (when closed)."""
        try:
            self.client.table("positions")\
                .delete()\
                .eq("symbol", symbol)\
                .execute()
            logger.info(f"Position deleted: {symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete position: {e}")
            return False
    
    def get_positions(self):
        """Get all current positions."""
        try:
            result = self.client.table("positions").select("*").execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    # Orders
    def insert_order(self, order_data: Dict[str, Any]):
        """Insert order."""
        try:
            result = self.client.table("orders").insert(order_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to insert order: {e}")
            return None
    
    def update_order(self, order_id: str, updates: Dict[str, Any]):
        """Update order status."""
        try:
            result = self.client.table("orders")\
                .update(updates)\
                .eq("order_id", order_id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update order: {e}")
            return None
    
    def get_orders(self, status: Optional[str] = None, limit: int = 100):
        """Get orders, optionally filtered by status."""
        try:
            query = self.client.table("orders").select("*")
            if status:
                query = query.eq("status", status)
            result = query.order("submitted_at", desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            return []
    
    def order_exists(self, client_order_id: str) -> bool:
        """Check if order with this ID already exists."""
        try:
            result = self.client.table("orders")\
                .select("order_id")\
                .eq("client_order_id", client_order_id)\
                .execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to check order existence: {e}")
            return False
    
    # Market Data
    def insert_bars(self, bars_data: List[Dict[str, Any]]):
        """Insert market data bars."""
        try:
            result = self.client.table("market_data").insert(bars_data).execute()
            return len(result.data) if result.data else 0
        except Exception as e:
            logger.error(f"Failed to insert bars: {e}")
            return 0
    
    def get_latest_bar(self, symbol: str):
        """Get latest bar for symbol."""
        try:
            result = self.client.table("market_data")\
                .select("*")\
                .eq("symbol", symbol)\
                .order("timestamp", desc=True)\
                .limit(1)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get latest bar: {e}")
            return None
    
    # Features
    def upsert_features(self, features_data: Dict[str, Any]):
        """Insert or update computed features with retry logic."""
        import time
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                result = self.client.table("features")\
                    .upsert(features_data, on_conflict="symbol")\
                    .execute()
                return result.data[0] if result.data else None
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Features upsert attempt {attempt + 1} failed, retrying in {2**attempt}s: {e}")
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to upsert features after {max_retries} attempts: {e}")
                    return None
    
    def get_features(self, symbol: str):
        """Get features for symbol."""
        try:
            result = self.client.table("features")\
                .select("*")\
                .eq("symbol", symbol)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get features: {e}")
            return None
    
    # Metrics
    def insert_metrics(self, metrics_data: Dict[str, Any]):
        """Insert performance metrics."""
        try:
            result = self.client.table("metrics").insert(metrics_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to insert metrics: {e}")
            return None
    
    def get_latest_metrics(self):
        """Get latest performance metrics."""
        try:
            result = self.client.table("metrics")\
                .select("*")\
                .order("timestamp", desc=True)\
                .limit(1)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return None
    
    # Advisories
    def insert_advisory(self, advisory_data: Dict[str, Any]):
        """Insert LLM advisory."""
        try:
            result = self.client.table("advisories").insert(advisory_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to insert advisory: {e}")
            return None
    
    def get_advisories(self, limit: int = 50):
        """Get recent advisories."""
        try:
            result = self.client.table("advisories")\
                .select("*")\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get advisories: {e}")
            return []

    # Logs
    def insert_log(self, log_data: Dict[str, Any]):
        """Insert system log."""
        try:
            result = self.client.table("logs").insert(log_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            # Silently fail - don't want logging to crash the app
            pass
    
    def get_logs(self, limit: int = 100):
        """Get recent logs."""
        try:
            result = self.client.table("logs")\
                .select("*")\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return []


# Global instance
_supabase_client = None


def get_client():
    """Get the global Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client.client
