from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock


@dataclass
class Position:
    symbol: str
    qty: int
    side: str
    avg_entry_price: float
    current_price: float
    unrealized_pl: float
    unrealized_pl_pct: float
    market_value: float
    stop_loss: float
    take_profit: float
    entry_time: datetime


@dataclass
class Order:
    order_id: str
    client_order_id: str
    symbol: str
    qty: int
    side: str
    type: str
    status: str
    filled_qty: int
    filled_avg_price: Optional[float]
    submitted_at: datetime


@dataclass
class TradingMetrics:
    equity: float
    cash: float
    buying_power: float
    daily_pl: float
    daily_pl_pct: float
    total_pl: float
    win_rate: float
    profit_factor: float
    wins: int
    losses: int
    total_trades: int
    open_positions: int
    max_positions: int
    circuit_breaker_triggered: bool


class TradingState:
    """
    Thread-safe shared state for the trading system.
    All components read/write through this.
    """
    
    def __init__(self):
        self._lock = Lock()
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.metrics = TradingMetrics(
            equity=0,
            cash=0,
            buying_power=0,
            daily_pl=0,
            daily_pl_pct=0,
            total_pl=0,
            win_rate=0,
            profit_factor=0,
            wins=0,
            losses=0,
            total_trades=0,
            open_positions=0,
            max_positions=5,
            circuit_breaker_triggered=False
        )
        self.features: Dict[str, Dict] = {}  # symbol -> features
        self.is_trading_enabled = True
        self.last_update = datetime.utcnow()
    
    def update_position(self, position: Position):
        """Update or add position."""
        with self._lock:
            self.positions[position.symbol] = position
            self.metrics.open_positions = len(self.positions)
    
    def remove_position(self, symbol: str):
        """Remove position (when closed)."""
        with self._lock:
            if symbol in self.positions:
                del self.positions[symbol]
                self.metrics.open_positions = len(self.positions)
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol."""
        with self._lock:
            return self.positions.get(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """Get all positions."""
        with self._lock:
            return list(self.positions.values())
    
    def update_order(self, order: Order):
        """Update or add order."""
        with self._lock:
            self.orders[order.order_id] = order
    
    def remove_order(self, order_id: str):
        """Remove order."""
        with self._lock:
            if order_id in self.orders:
                del self.orders[order_id]
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        with self._lock:
            return self.orders.get(order_id)
    
    def get_all_orders(self) -> List[Order]:
        """Get all orders."""
        with self._lock:
            return list(self.orders.values())
    
    def update_metrics(self, **kwargs):
        """Update metrics."""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.metrics, key):
                    setattr(self.metrics, key, value)
            self.last_update = datetime.utcnow()
    
    def get_metrics(self) -> TradingMetrics:
        """Get current metrics."""
        with self._lock:
            return self.metrics
    
    def update_features(self, symbol: str, features: Dict):
        """Update features for symbol."""
        with self._lock:
            self.features[symbol] = features
    
    def get_features(self, symbol: str) -> Optional[Dict]:
        """Get features for symbol."""
        with self._lock:
            return self.features.get(symbol)
    
    def enable_trading(self):
        """Enable trading."""
        with self._lock:
            self.is_trading_enabled = True
    
    def disable_trading(self):
        """Disable trading (emergency stop)."""
        with self._lock:
            self.is_trading_enabled = False
    
    def is_trading_allowed(self) -> bool:
        """Check if trading is allowed."""
        with self._lock:
            return self.is_trading_enabled and not self.metrics.circuit_breaker_triggered


# Global state instance
trading_state = TradingState()
