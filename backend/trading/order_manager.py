from typing import Optional
from datetime import datetime
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from core.state import trading_state, Order
from trading.risk_manager import RiskManager
from utils.helpers import generate_order_id
from utils.logger import setup_logger
from orders.bracket_orders import BracketOrderBuilder
from alpaca.trading.enums import OrderSide as AlpacaOrderSide
from config import settings

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
        price: Optional[float] = None,
        take_profit_price: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
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
        order_side_enum = AlpacaOrderSide.BUY if side.lower() == "buy" else AlpacaOrderSide.SELL

        bracket_prices = None
        if take_profit_price is not None and stop_loss_price is not None:
            bracket_prices = {
                "take_profit": float(take_profit_price),
                "stop_loss": float(stop_loss_price),
            }
        elif settings.bracket_orders_enabled and price:
            bracket_prices = BracketOrderBuilder.calculate_bracket_prices(
                price,
                order_side_enum,
                settings.default_take_profit_pct,
                settings.default_stop_loss_pct,
            )

        use_bracket = settings.bracket_orders_enabled and bracket_prices is not None

        try:
            if use_bracket:
                request = BracketOrderBuilder.create_market_bracket(
                    symbol=symbol,
                    qty=qty,
                    side=order_side_enum,
                    take_profit_price=bracket_prices["take_profit"],
                    stop_loss_price=bracket_prices["stop_loss"],
                    client_order_id=client_order_id,
                )
                alpaca_order = self.alpaca.submit_order_request(request)
            else:
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
                'order_id': str(order.order_id),  # Convert UUID to string
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
            
            if use_bracket:
                logger.info(
                    "Bracket order submitted: %s %s %s TP=%s SL=%s (Reason: %s)",
                    side,
                    qty,
                    symbol,
                    bracket_prices["take_profit"],
                    bracket_prices["stop_loss"],
                    reason,
                )
            else:
                logger.info(f"Order submitted successfully: {side} {qty} {symbol} (Reason: {reason})")
            return order
            
        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            return None
    
    def submit_options_order(
        self,
        option_symbol: str,
        contracts: int,
        premium: float,
        option_type: str,
        underlying_symbol: str,
        reason: str = "options_strategy"
    ) -> Optional[Order]:
        """
        Submit an options order.
        
        Args:
            option_symbol: Full options symbol
            contracts: Number of contracts
            premium: Premium price per share
            option_type: 'call' or 'put'
            underlying_symbol: Underlying stock symbol
            reason: Reason for the trade
            
        Returns:
            Order object if successful, None if rejected
        """
        try:
            # Generate order ID
            client_order_id = generate_order_id(option_symbol, 'buy', contracts, premium)
            
            # Check if already submitted
            if trading_state.get_order(client_order_id):
                logger.warning(f"Options order already exists: {client_order_id}")
                return trading_state.get_order(client_order_id)
            
            # Risk check for options
            total_cost = premium * contracts * 100  # Each contract = 100 shares
            
            if not self.risk_manager.check_options_trade(
                symbol=underlying_symbol,
                cost=total_cost,
                contracts=contracts
            ):
                logger.warning(f"Options order rejected by risk manager: {option_symbol}")
                return None
            
            # Submit options order to Alpaca
            # Note: Options orders are typically limit orders at the premium price
            order = self.alpaca.submit_order(
                symbol=option_symbol,
                qty=contracts,
                side='buy',
                type='limit',
                limit_price=premium,
                time_in_force='day',
                client_order_id=client_order_id
            )
            
            if not order:
                logger.error(f"Failed to submit options order: {option_symbol}")
                return None
            
            # Create Order object
            order_obj = Order(
                order_id=order.id,
                client_order_id=client_order_id,
                symbol=option_symbol,
                qty=contracts,
                side='buy',
                type='limit',
                status=order.status,
                submitted_at=order.submitted_at.isoformat() if order.submitted_at else datetime.now().isoformat(),
                filled_qty=order.filled_qty or 0,
                filled_avg_price=float(order.filled_avg_price) if order.filled_avg_price else None
            )
            
            # Store in state and DB
            trading_state.add_order(order_obj)
            
            self.supabase.insert_order({
                'order_id': order_obj.order_id,
                'client_order_id': client_order_id,
                'symbol': option_symbol,
                'underlying_symbol': underlying_symbol,
                'qty': contracts,
                'side': 'buy',
                'type': 'limit',
                'status': order_obj.status,
                'submitted_at': order_obj.submitted_at,
                'reason': reason,
                'option_type': option_type,
                'premium': premium,
                'is_option': True
            })
            
            logger.info(
                f"✅ Options order submitted: BUY {contracts} contracts of {option_symbol} "
                f"({option_type.upper()}) @ ${premium} (Reason: {reason})"
            )
            
            return order_obj
            
        except Exception as e:
            logger.error(f"Failed to submit options order: {e}", exc_info=True)
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
