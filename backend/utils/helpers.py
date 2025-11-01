import hashlib
from datetime import datetime
from typing import Optional


def generate_order_id(
    symbol: str,
    side: str,
    qty: int,
    price: Optional[float] = None,
    timestamp: Optional[datetime] = None
) -> str:
    """
    Generate deterministic order ID for idempotency.
    Same inputs always produce same ID, preventing duplicate orders.
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    # Floor to minute for retry window
    ts_bucket = timestamp.replace(second=0, microsecond=0).isoformat()
    
    # Use price hint or 0 if market order
    price_hint = f"{price:.4f}" if price else "0.0000"
    
    payload = f"{symbol}|{side}|{qty}|{price_hint}|{ts_bucket}"
    return hashlib.sha256(payload.encode()).hexdigest()[:24]


def calculate_position_size(
    equity: float,
    risk_pct: float,
    entry_price: float,
    stop_price: float
) -> int:
    """
    Calculate position size based on risk percentage.
    Risk = (entry - stop) * qty
    """
    if entry_price <= 0 or stop_price <= 0:
        return 0
    
    risk_per_share = abs(entry_price - stop_price)
    if risk_per_share == 0:
        return 0
    
    risk_amount = equity * risk_pct
    qty = int(risk_amount / risk_per_share)
    
    return max(0, qty)


def calculate_atr_stop(
    entry_price: float,
    atr: float,
    multiplier: float,
    side: str
) -> float:
    """Calculate ATR-based stop loss."""
    if side.lower() == "buy":
        return entry_price - (atr * multiplier)
    else:
        return entry_price + (atr * multiplier)


def calculate_atr_target(
    entry_price: float,
    atr: float,
    multiplier: float,
    side: str
) -> float:
    """Calculate ATR-based take profit."""
    if side.lower() == "buy":
        return entry_price + (atr * multiplier)
    else:
        return entry_price - (atr * multiplier)
