from typing import List, Optional
from datetime import datetime
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from core.state import trading_state, Position
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PositionManager:
    """
    Manages positions: syncing, monitoring, updating.
    Includes trailing stops (Sprint 5) and partial profits (Sprint 6) integration.
    """
    
    def __init__(
        self,
        alpaca_client: AlpacaClient,
        supabase_client: SupabaseClient,
        trailing_stop_manager=None,
        profit_taker=None,
        cooldown_manager=None
    ):
        self.alpaca = alpaca_client
        self.supabase = supabase_client
        self.trailing_stop_manager = trailing_stop_manager
        self.profit_taker = profit_taker
        self.cooldown_manager = cooldown_manager
        
        # Initialize trailing stops if not provided
        if self.trailing_stop_manager is None:
            from trading.trailing_stops import TrailingStopManager
            self.trailing_stop_manager = TrailingStopManager(supabase_client)
            logger.info("Trailing Stop Manager auto-initialized in Position Manager")
        
        # Initialize profit taker if not provided (Sprint 6)
        if self.profit_taker is None:
            from trading.profit_taker import ProfitTaker
            self.profit_taker = ProfitTaker(supabase_client)
            logger.info("Profit Taker auto-initialized in Position Manager")
        
        # Initialize cooldown manager if not provided (Sprint 6)
        if self.cooldown_manager is None:
            from trading.symbol_cooldown import SymbolCooldownManager
            self.cooldown_manager = SymbolCooldownManager(supabase_client)
            logger.info("Symbol Cooldown Manager auto-initialized in Position Manager")
    
    def sync_positions(self):
        """
        Sync positions from Alpaca to state and database.
        Call this on startup and periodically.
        """
        try:
            alpaca_positions = self.alpaca.get_positions()
            
            # Clear current state
            current_symbols = set(trading_state.positions.keys())
            alpaca_symbols = set()
            
            for alpaca_pos in alpaca_positions:
                symbol = alpaca_pos.symbol
                alpaca_symbols.add(symbol)
                
                # Get features for stop/target calculation
                features = trading_state.get_features(symbol)
                stop_loss = 0
                take_profit = 0
                
                if features:
                    # Recalculate stops based on current ATR
                    from config import settings
                    atr = features.get('atr', 0)
                    entry_price = float(alpaca_pos.avg_entry_price)
                    
                    if int(alpaca_pos.qty) > 0:  # Long position
                        stop_loss = entry_price - (atr * settings.stop_loss_atr_mult)
                        take_profit = entry_price + (atr * settings.take_profit_atr_mult)
                    else:  # Short position
                        stop_loss = entry_price + (atr * settings.stop_loss_atr_mult)
                        take_profit = entry_price - (atr * settings.take_profit_atr_mult)
                
                # Create Position object
                position = Position(
                    symbol=symbol,
                    qty=abs(int(alpaca_pos.qty)),
                    side='buy' if int(alpaca_pos.qty) > 0 else 'sell',
                    avg_entry_price=float(alpaca_pos.avg_entry_price),
                    current_price=float(alpaca_pos.current_price),
                    unrealized_pl=float(alpaca_pos.unrealized_pl),
                    unrealized_pl_pct=float(alpaca_pos.unrealized_plpc) * 100,
                    market_value=float(alpaca_pos.market_value),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    entry_time=datetime.utcnow()
                )
                
                # Update state
                trading_state.update_position(position)
                
                # Update database
                self.supabase.upsert_position({
                    'symbol': position.symbol,
                    'qty': position.qty,
                    'side': position.side,
                    'avg_entry_price': position.avg_entry_price,
                    'current_price': position.current_price,
                    'unrealized_pl': position.unrealized_pl,
                    'unrealized_pl_pct': position.unrealized_pl_pct,
                    'market_value': position.market_value,
                    'stop_loss': position.stop_loss,
                    'take_profit': position.take_profit,
                    'entry_time': position.entry_time.isoformat()
                })
            
            # Remove positions that no longer exist in Alpaca
            for symbol in current_symbols - alpaca_symbols:
                trading_state.remove_position(symbol)
                self.supabase.delete_position(symbol)
            
            logger.info(f"Synced {len(alpaca_positions)} positions from Alpaca")
            return len(alpaca_positions)
            
        except Exception as e:
            logger.error(f"Failed to sync positions: {e}")
            return 0
    
    def update_position_prices(self):
        """
        Update current prices for all positions.
        Call this frequently (every few seconds).
        Also updates trailing stops if enabled.
        """
        try:
            positions = trading_state.get_all_positions()
            if not positions:
                return
            
            symbols = [p.symbol for p in positions]
            latest_bars = self.alpaca.get_latest_bars(symbols)
            
            if not latest_bars:
                return
            
            for position in positions:
                if position.symbol in latest_bars:
                    bar = latest_bars[position.symbol]
                    current_price = float(bar.close)
                    
                    # Calculate P/L
                    if position.side == 'buy':
                        unrealized_pl = (current_price - position.avg_entry_price) * position.qty
                    else:
                        unrealized_pl = (position.avg_entry_price - current_price) * position.qty
                    
                    unrealized_pl_pct = (unrealized_pl / (position.avg_entry_price * position.qty)) * 100
                    
                    # Update position
                    position.current_price = current_price
                    position.unrealized_pl = unrealized_pl
                    position.unrealized_pl_pct = unrealized_pl_pct
                    position.market_value = current_price * position.qty
                    
                    trading_state.update_position(position)
                    
                    # Sprint 6: Check for partial profits
                    self._check_partial_profits_for_position(position)
                    
                    # Sprint 5: Update trailing stops
                    self._update_trailing_stop_for_position(position)
            
            logger.debug(f"Updated prices for {len(positions)} positions")
            
        except Exception as e:
            logger.error(f"Failed to update position prices: {e}")
    
    def _update_trailing_stop_for_position(self, position: Position):
        """
        Update trailing stop for a single position (Sprint 5)
        
        Args:
            position: Position object
        """
        try:
            if not self.trailing_stop_manager:
                return
            
            # Get ATR for this symbol if available
            features = trading_state.get_features(position.symbol)
            atr = features.get('atr', None) if features else None
            
            # Update trailing stop
            result = self.trailing_stop_manager.update_trailing_stop(
                symbol=position.symbol,
                entry_price=position.avg_entry_price,
                current_price=position.current_price,
                current_stop=position.stop_loss,
                side='long' if position.side == 'buy' else 'short',
                atr=atr
            )
            
            # If trailing stop was updated (and not in shadow mode), update the position
            if result.get('updated') and not result.get('shadow_mode'):
                new_stop = result['new_stop']
                
                # Update position stop loss
                position.stop_loss = new_stop
                trading_state.update_position(position)
                
                # Update database with full position data to avoid constraint violations
                self.supabase.upsert_position({
                    'symbol': position.symbol,
                    'qty': position.qty,
                    'side': position.side,
                    'avg_entry_price': position.avg_entry_price,
                    'current_price': position.current_price,
                    'unrealized_pl': position.unrealized_pl,
                    'unrealized_pl_pct': position.unrealized_pl_pct,
                    'market_value': position.market_value,
                    'stop_loss': new_stop,
                    'take_profit': position.take_profit,
                    'entry_time': position.entry_time.isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                })
                
                logger.info(f"✓ Position {position.symbol} stop loss updated to ${new_stop:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating trailing stop for {position.symbol}: {e}")
    
    def check_stops_and_targets(self) -> List[str]:
        """
        Check if any positions hit stop loss or take profit.
        Returns list of symbols that need to be closed.
        
        NOTE: If bracket orders are active, they will handle exits automatically.
        This method only triggers manual closes for positions without bracket orders.
        """
        symbols_to_close = []
        
        try:
            positions = trading_state.get_all_positions()
            
            # Get all open orders to check for bracket orders
            open_orders = self.alpaca.get_orders(status='open')
            symbols_with_brackets = set()
            
            for order in open_orders:
                # Check if this is a bracket order (has order_class='bracket' or has legs)
                is_bracket = (
                    (hasattr(order, 'order_class') and order.order_class == 'bracket') or
                    (hasattr(order, 'legs') and order.legs)
                )
                if is_bracket:
                    symbols_with_brackets.add(order.symbol)
            
            if symbols_with_brackets:
                logger.debug(f"Symbols with bracket orders: {symbols_with_brackets}")
            
            for position in positions:
                # Skip positions with active bracket orders - they'll exit automatically
                if position.symbol in symbols_with_brackets:
                    logger.debug(f"Skipping {position.symbol} - has active bracket orders")
                    continue
                
                current_price = position.current_price
                
                # Check stop loss
                if position.side == 'buy':
                    if current_price <= position.stop_loss:
                        logger.warning(f"STOP LOSS HIT: {position.symbol} @ ${current_price:.2f}")
                        symbols_to_close.append((position.symbol, 'stop_loss'))
                    elif current_price >= position.take_profit:
                        logger.info(f"TAKE PROFIT HIT: {position.symbol} @ ${current_price:.2f}")
                        symbols_to_close.append((position.symbol, 'take_profit'))
                else:  # sell/short
                    if current_price >= position.stop_loss:
                        logger.warning(f"STOP LOSS HIT: {position.symbol} @ ${current_price:.2f}")
                        symbols_to_close.append((position.symbol, 'stop_loss'))
                    elif current_price <= position.take_profit:
                        logger.info(f"TAKE PROFIT HIT: {position.symbol} @ ${current_price:.2f}")
                        symbols_to_close.append((position.symbol, 'take_profit'))
            
            return symbols_to_close
            
        except Exception as e:
            logger.error(f"Failed to check stops/targets: {e}")
            return []
    
    def has_bracket_orders(self, symbol: str) -> bool:
        """
        Check if a position has active bracket orders.
        """
        try:
            open_orders = self.alpaca.get_orders(status='open')
            for order in open_orders:
                if order.symbol == symbol and hasattr(order, 'legs') and order.legs:
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to check bracket orders for {symbol}: {e}")
            return False
    
    def close_position(self, symbol: str, reason: str = "Manual close"):
        """
        Close a position and record the trade.
        If bracket orders exist, cancels them first.
        If position not found in Alpaca, cleans up local state.
        """
        try:
            position = trading_state.get_position(symbol)
            if not position:
                logger.warning(f"No position found in local state for {symbol}")
                return False
            
            # Check for bracket orders and cancel them first
            if self.has_bracket_orders(symbol):
                logger.info(f"Canceling bracket orders for {symbol} before closing")
                open_orders = self.alpaca.get_orders(status='open')
                for order in open_orders:
                    if order.symbol == symbol:
                        self.alpaca.cancel_order(order.id)
            
            # Close via Alpaca
            success = self.alpaca.close_position(symbol)
            
            if success:
                # Record trade in database
                self.supabase.insert_trade({
                    'symbol': symbol,
                    'side': position.side,
                    'qty': position.qty,
                    'entry_price': position.avg_entry_price,
                    'exit_price': position.current_price,
                    'pnl': position.unrealized_pl,
                    'pnl_pct': position.unrealized_pl_pct,
                    'entry_time': position.entry_time.isoformat(),
                    'exit_time': datetime.utcnow().isoformat(),
                    'strategy': 'EMA_Crossover',
                    'reason': reason
                })
                
                # Update metrics
                metrics = trading_state.get_metrics()
                if position.unrealized_pl > 0:
                    trading_state.update_metrics(
                        wins=metrics.wins + 1,
                        total_trades=metrics.total_trades + 1
                    )
                else:
                    trading_state.update_metrics(
                        losses=metrics.losses + 1,
                        total_trades=metrics.total_trades + 1
                    )
                
                # Remove from state (whether closed manually or already closed by bracket)
                trading_state.remove_position(symbol)
                self.supabase.delete_position(symbol)
                
                # Sprint 5: Clean up trailing stop tracking
                if self.trailing_stop_manager:
                    self.trailing_stop_manager.remove_trailing_stop(symbol)
                
                # Sprint 6: Clean up partial profit tracking
                if self.profit_taker:
                    self.profit_taker.remove_partial_profit(symbol)
                
                # Sprint 6: Record trade result for cooldown tracking
                if self.cooldown_manager:
                    self.cooldown_manager.record_trade_result(
                        symbol=symbol,
                        pnl=position.unrealized_pl,
                        reason=reason
                    )
                
                logger.info(f"✓ Position closed: {symbol} - P/L: ${position.unrealized_pl:.2f} ({reason})")
                return True
            else:
                # If close failed but position not found, clean up state anyway
                logger.warning(f"Close failed for {symbol}, cleaning up local state")
                trading_state.remove_position(symbol)
                self.supabase.delete_position(symbol)
                return False
            
        except Exception as e:
            logger.error(f"Failed to close position {symbol}: {e}")
            # Clean up state if position doesn't exist
            if "position not found" in str(e).lower():
                logger.info(f"Cleaning up orphaned position {symbol} from local state")
                trading_state.remove_position(symbol)
                self.supabase.delete_position(symbol)
            return False

    def _check_partial_profits_for_position(self, position: Position):
        """
        Check and execute partial profits for a single position (Sprint 6)
        
        Args:
            position: Position object
        """
        try:
            if not self.profit_taker:
                return
            
            # Check if should take partial profits
            result = self.profit_taker.should_take_partial_profits(
                symbol=position.symbol,
                entry_price=position.avg_entry_price,
                current_price=position.current_price,
                stop_loss=position.stop_loss,
                side='long' if position.side == 'buy' else 'short'
            )
            
            # If should take partial profits (and not in shadow mode)
            if result.get('should_take') and not result.get('shadow_mode'):
                self._execute_partial_profit_taking(position, result)
            
        except Exception as e:
            logger.error(f"Error checking partial profits for {position.symbol}: {e}")
    
    def _execute_partial_profit_taking(self, position: Position, result: dict):
        """
        Execute partial profit taking for a position
        
        Args:
            position: Position object
            result: Partial profit decision result
        """
        try:
            from typing import Dict, Any
            
            symbol = position.symbol
            percentage = result['percentage']
            profit_r = result['profit_r']
            
            # Calculate shares to sell (50% by default)
            shares_to_sell = int(position.qty * percentage)
            if shares_to_sell <= 0:
                logger.warning(f"Cannot take partial profits for {symbol}: shares_to_sell = {shares_to_sell}")
                return
            
            logger.info(f"🎯 Taking partial profits for {symbol}: {shares_to_sell}/{position.qty} shares at +{profit_r:.2f}R")
            
            # Submit partial close order
            try:
                if position.side == 'buy':
                    # Close partial long position
                    order = self.alpaca.submit_order(
                        symbol=symbol,
                        qty=shares_to_sell,
                        side='sell',
                        type='market',
                        time_in_force='day'
                    )
                else:
                    # Close partial short position
                    order = self.alpaca.submit_order(
                        symbol=symbol,
                        qty=shares_to_sell,
                        side='buy',
                        type='market',
                        time_in_force='day'
                    )
                
                if order:
                    # Record partial profit taking
                    self.profit_taker.record_partial_profit(
                        symbol=symbol,
                        shares_sold=shares_to_sell,
                        price=position.current_price,
                        profit_r=profit_r,
                        profit_amount=result['profit_amount']
                    )
                    
                    # Update position quantity
                    remaining_qty = position.qty - shares_to_sell
                    position.qty = remaining_qty
                    trading_state.update_position(position)
                    
                    # Update database with full position data to avoid constraint violations
                    self.supabase.upsert_position({
                        'symbol': symbol,
                        'qty': remaining_qty,
                        'side': position.side,
                        'avg_entry_price': position.avg_entry_price,
                        'current_price': position.current_price,
                        'unrealized_pl': position.unrealized_pl,
                        'unrealized_pl_pct': position.unrealized_pl_pct,
                        'market_value': position.market_value,
                        'stop_loss': position.stop_loss,
                        'take_profit': position.take_profit,
                        'entry_time': position.entry_time.isoformat(),
                        'partial_profits_taken': True,
                        'updated_at': datetime.utcnow().isoformat()
                    })
                    
                    logger.info(f"✓ Partial profits taken for {symbol}: {shares_to_sell} shares sold, {remaining_qty} remaining")
                    
                    # Log trade for analysis
                    self.supabase.insert_trade({
                        'symbol': symbol,
                        'side': 'sell' if position.side == 'buy' else 'buy',
                        'qty': shares_to_sell,
                        'price': position.current_price,
                        'exit_type': 'partial_profit',
                        'profit_r': profit_r,
                        'profit_amount': result['profit_amount'],
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                else:
                    logger.error(f"Failed to submit partial profit order for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error submitting partial profit order for {symbol}: {e}")
                
        except Exception as e:
            logger.error(f"Error executing partial profit taking for {position.symbol}: {e}")
