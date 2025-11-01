from typing import Optional
from datetime import datetime
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from core.state import trading_state, Order
from trading.risk_manager import RiskManager
from utils.helpers import generate_order_id
from utils.logger import setup_logger

logger = setup_logger(__name__)


class OrderManager:
    """
    Handles order submission with idempotency and tracking.
    All orders go through RiskManager first.
    """
    
    def __init__(
        self,
        alpaca_client: AlpacaClient,
        supabase_client: SupabaseClient,
        risk_manager: RiskManager
    ):
        self.alpaca = alpaca_client
        self.supabase = supabase_client
        self.risk_manager = risk_manager
    
    def submit_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        reason: str = "",
        price: Optional[float] = None
    ) -> Optional[Order]:
        """
        Submit order with full risk checks and idempotency.
        Returns Order object if successful, None if rejected.
        """
        
        # 1. Generate deterministic order ID
        client_order_id = generate_order_id(symbol, side, qty, price)
        
        # 2. Check if we already submitted this order
        if self.supabase.order_exists(client_order_id):
            logger.warning(f"Order already exists: {client_order_id}")
            # Fetch and return existing order
            orders = self.supabase.get_orders()
            for order_data in orders:
                if order_data.get('client_order_id') == client_order_id:
                    return self._order_from_dict(order_data)
            return None
        
        # 3. Risk check
        approved, reason_text = self.risk_manager.check_order(symbol, side, qty, price)
        if not approved:
            logger.warning(f"Order REJECTED: {reason_text}")
            # Log rejection
            self._log_rejection(symbol, side, qty, reason_text)
            return None
        
        # 4. Submit to Alpaca
        try:
            alpaca_order = self.alpaca.submit_market_order(
                symbol=symbol,
                qty=qty,
                side=side,
                client_order_id=client_order_id
            )
            
            # 5. Create Order object
            order = Order(
                order_id=alpaca_order.id,
                client_order_id=client_order_id,
                symbol=symbol,
                qty=qty,
                side=side.lower(),
                type='market',
                status=alpaca_order.status.value,
                filled_qty=int(alpaca_order.filled_qty) if alpaca_order.filled_qty else 0,
                filled_avg_price=float(alpaca_order.filled_avg_price) if alpaca_order.filled_avg_price else None,
                submitted_at=alpaca_order.submitted_at
            )
            
            # 6. Store in state and DB
            trading_state.update_order(order)
            
            self.supabase.insert_order({
                'order_id': order.order_id,
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'qty': order.qty,
                'side': order.side,
                'type': order.type,
                'status': order.status,
                'filled_qty': order.filled_qty,
                'filled_avg_price': order.filled_avg_price,
                'submitted_at': order.submitted_at.isoformat(),
                'reason': reason
            })
            
            logger.info(f"Order submitted successfully: {side} {qty} {symbol} (Reason: {reason})")
            return order
            
        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            success = self.alpaca.cancel_order(order_id)
            if success:
                # Update in state and DB
                order = trading_state.get_order(order_id)
                if order:
                    order.status = 'canceled'
                    trading_state.update_order(order)
                
                self.supabase.update_order(order_id, {'status': 'canceled'})
                logger.info(f"Order canceled: {order_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    def update_order_status(self, order_id: str, status: str, filled_qty: int = 0, filled_avg_price: Optional[float] = None):
        """Update order status (called by monitoring loop)."""
        order = trading_state.get_order(order_id)
        if order:
            order.status = status
            order.filled_qty = filled_qty
            if filled_avg_price:
                order.filled_avg_price = filled_avg_price
            
            trading_state.update_order(order)
            
            # Update in DB
            updates = {
                'status': status,
                'filled_qty': filled_qty
            }
            if filled_avg_price:
                updates['filled_avg_price'] = filled_avg_price
            
            self.supabase.update_order(order_id, updates)
    
    def _order_from_dict(self, data: dict) -> Order:
        """Convert dict to Order object."""
        return Order(
            order_id=data['order_id'],
            client_order_id=data['client_order_id'],
            symbol=data['symbol'],
            qty=data['qty'],
            side=data['side'],
            type=data['type'],
            status=data['status'],
            filled_qty=data['filled_qty'],
            filled_avg_price=data.get('filled_avg_price'),
            submitted_at=datetime.fromisoformat(data['submitted_at'])
        )
    
    def _log_rejection(self, symbol: str, side: str, qty: int, reason: str):
        """Log rejected order to DB for analysis."""
        try:
            self.supabase.client.table("order_rejections").insert({
                'symbol': symbol,
                'side': side,
                'qty': qty,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log rejection: {e}")
