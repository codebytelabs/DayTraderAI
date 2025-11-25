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
            
            # Fetch existing positions from DB to preserve stop losses if features missing
            db_positions = {}
            try:
                db_result = self.supabase.get_positions()
                if db_result:
                    db_positions = {p['symbol']: p for p in db_result}
            except Exception as e:
                logger.error(f"Failed to fetch DB positions for sync: {e}")

            for alpaca_pos in alpaca_positions:
                symbol = alpaca_pos.symbol
                alpaca_symbols.add(symbol)
                
                # Get features for stop/target calculation
                features = trading_state.get_features(symbol)
                stop_loss = 0
                take_profit = 0
                
                # Try to get from DB first (preserve existing protection)
                if symbol in db_positions:
                    stop_loss = db_positions[symbol].get('stop_loss', 0)
                    take_profit = db_positions[symbol].get('take_profit', 0)
                
                if features:
                    # Recalculate stops based on current ATR
                    from config import settings
                    atr = features.get('atr', 0)
                    entry_price = float(alpaca_pos.avg_entry_price)
                    
                    # Only recalculate if ATR is valid
                    if atr > 0:
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
    
    def cleanup_tiny_positions(self, min_value: float = 1000.0):
        """
        Close positions that are too small to be meaningful.
        This frees up position slots for better opportunities.
        
        Args:
            min_value: Minimum position value in dollars (default $1000)
        """
        try:
            positions = self.alpaca.get_positions()
            if not positions:
                return 0
            
            closed_count = 0
            for position in positions:
                symbol = position.symbol
                market_value = abs(float(position.market_value))
                
                if market_value < min_value:
                    logger.info(f"🧹 Closing tiny position {symbol}: ${market_value:.2f} < ${min_value:.0f} minimum")
                    
                    try:
                        # Cancel any existing orders first
                        open_orders = self.alpaca.get_orders(status='open')
                        for order in open_orders:
                            if order.symbol == symbol:
                                self.alpaca.cancel_order(order.id)
                        
                        # Close the position
                        self.alpaca.close_position(symbol)
                        
                        # Clean up state
                        trading_state.remove_position(symbol)
                        self.supabase.delete_position(symbol)
                        
                        closed_count += 1
                        logger.info(f"✅ Closed tiny position {symbol}")
                        
                    except Exception as e:
                        logger.error(f"Failed to close tiny position {symbol}: {e}")
            
            if closed_count > 0:
                logger.info(f"🧹 Cleaned up {closed_count} tiny positions (< ${min_value:.0f})")
            
            return closed_count
            
        except Exception as e:
            logger.error(f"Error cleaning up tiny positions: {e}")
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
                
                # CRITICAL FIX: Update the ACTUAL Alpaca order
                try:
                    # Find the active stop order
                    open_orders = self.alpaca.get_orders(status='open')
                    stop_order = None
                    
                    for order in open_orders:
                        if (order.symbol == position.symbol and 
                            order.type.value in ['stop', 'trailing_stop'] and
                            order.status.value in ['new', 'accepted', 'pending_new', 'held']):
                            stop_order = order
                            break
                    
                    if stop_order:
                        logger.info(f"🔄 Updating Alpaca order {stop_order.id} to new stop ${new_stop:.2f}")
                        self.alpaca.replace_order(
                            order_id=stop_order.id,
                            stop_price=round(new_stop, 2)
                        )
                    else:
                        logger.warning(f"⚠️  Could not find active stop order for {position.symbol} to update")
                        
                except Exception as e:
                    logger.error(f"Failed to update Alpaca order for {position.symbol}: {e}")
            
        except Exception as e:
            logger.error(f"Error updating trailing stop for {position.symbol}: {e}")
    
    def check_stops_and_targets(self) -> List[str]:
        """
        ONLY check stops/targets if NO bracket orders exist.
        Let bracket orders handle exits - they're more reliable!
        
        CRITICAL FIX: Never interfere with bracket orders - they execute at intended prices.
        """
        symbols_to_close = []
        
        try:
            positions = trading_state.get_all_positions()
            
            # Get OPEN orders to detect active bracket legs
            # FIXED: Use status='open' to get all active orders including bracket legs
            open_orders = self.alpaca.get_orders(status='open')
            
            # Build comprehensive set of symbols with ANY active orders
            symbols_with_orders = set()
            for order in open_orders:
                # Any open order means this symbol has protection
                symbols_with_orders.add(order.symbol)
                logger.debug(f"   Found active order for {order.symbol}: {order.id} ({order.order_type}, {order.status})")
            
            logger.debug(f"🛡️  Symbols with active orders (skipping manual checks): {symbols_with_orders}")
            
            for position in positions:
                # CRITICAL: Skip if ANY orders exist for this symbol
                if position.symbol in symbols_with_orders:
                    logger.debug(f"✓ {position.symbol} has active orders - letting brackets handle exit")
                    continue
                
                # Only check manually if NO orders exist (backup safety net)
                logger.warning(f"⚠️  {position.symbol} has NO orders - manual check activated")
                
                current_price = position.current_price
                
                # Check stop loss (use LIMIT order, not market!)
                if position.side == 'buy':
                    if current_price <= position.stop_loss:
                        logger.error(f"🚨 EMERGENCY STOP: {position.symbol} @ ${current_price:.2f}")
                        symbols_to_close.append((position.symbol, 'emergency_stop'))
                    elif current_price >= position.take_profit:
                        logger.info(f"✅ TAKE PROFIT: {position.symbol} @ ${current_price:.2f}")
                        symbols_to_close.append((position.symbol, 'take_profit'))
                else:  # sell/short
                    if current_price >= position.stop_loss:
                        logger.error(f"🚨 EMERGENCY STOP: {position.symbol} @ ${current_price:.2f}")
                        symbols_to_close.append((position.symbol, 'emergency_stop'))
                    elif current_price <= position.take_profit:
                        logger.info(f"✅ TAKE PROFIT: {position.symbol} @ ${current_price:.2f}")
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
        Close position intelligently:
        - If reason is 'take_profit' or 'stop_loss': DON'T cancel brackets, let them execute
        - If reason is 'emergency' or 'manual': Cancel brackets and close immediately
        
        CRITICAL FIX: Don't interfere with bracket exits - they execute at intended prices!
        """
        try:
            position = trading_state.get_position(symbol)
            if not position:
                logger.warning(f"No position found in local state for {symbol}")
                return False
            
            logger.info(f"🎯 Closing {symbol}: {reason}")
            
            # CRITICAL: Don't interfere with bracket exits!
            if reason in ['take_profit', 'stop_loss']:
                logger.info(f"✓ {symbol} exiting via bracket order - not interfering")
                return True
            
            # CRITICAL: Check if position has active bracket orders before emergency stop
            # If brackets exist, they will handle the exit - don't interfere!
            if reason == 'emergency_stop':
                open_orders = self.alpaca.get_orders(status='open')
                symbol_orders = [o for o in open_orders if o.symbol == symbol]
                if symbol_orders:
                    logger.info(f"✓ {symbol} has {len(symbol_orders)} active orders - brackets will handle exit, skipping emergency stop")
                    return True
            
            # CRITICAL: NEVER cancel bracket orders unless it's a true emergency
            # Only cancel for emergency/manual closes, and even then preserve brackets
            if reason in ['emergency_stop', 'manual_close', 'risk_limit']:
                # Cancel non-bracket orders only
                self._cancel_all_symbol_orders(symbol, preserve_brackets=True)
            
            # Step 2: Verify position still exists and get fresh data
            try:
                alpaca_position = self.alpaca.get_position(symbol)
                if not alpaca_position or int(alpaca_position.qty) == 0:
                    logger.info(f"Position {symbol} already closed or doesn't exist")
                    self._cleanup_position_state(symbol, position, reason)
                    return True
            except Exception as e:
                if "position does not exist" in str(e).lower():
                    logger.info(f"Position {symbol} not found in Alpaca, cleaning up state")
                    self._cleanup_position_state(symbol, position, reason)
                    return True
                logger.error(f"Error checking position {symbol}: {e}")
                return False
            
            # Step 3: Close via Alpaca with retry logic
            success = self._close_position_with_retry(symbol, position)
            
            if success:
                self._cleanup_position_state(symbol, position, reason)
                return True
            else:
                logger.warning(f"Close failed for {symbol}, attempting force cleanup")
                return self._force_cleanup_position(symbol, position, reason)
            
        except Exception as e:
            logger.error(f"Failed to close position {symbol}: {e}")
            # Clean up state if position doesn't exist
            if "position not found" in str(e).lower() or "does not exist" in str(e).lower():
                logger.info(f"Cleaning up orphaned position {symbol} from local state")
                self._cleanup_position_state(symbol, position, reason)
                return True
            return False
    
    def _cancel_all_symbol_orders(self, symbol: str, preserve_brackets: bool = False):
        """
        Cancel all open orders for a symbol to prevent 'insufficient qty' errors
        
        Args:
            symbol: Symbol to cancel orders for
            preserve_brackets: If True, DON'T cancel bracket order legs (stop/limit orders)
        """
        try:
            open_orders = self.alpaca.get_orders(status='open')
            cancelled_count = 0
            skipped_brackets = 0
            
            for order in open_orders:
                if order.symbol == symbol:
                    # Check if this is a bracket order leg
                    is_bracket_leg = (
                        order.type.value in ['stop', 'limit', 'trailing_stop'] and
                        order.side.value in ['sell', 'buy']
                    )
                    
                    # CRITICAL: Preserve bracket legs if requested
                    if preserve_brackets and is_bracket_leg:
                        skipped_brackets += 1
                        logger.info(f"✓ Preserving bracket order {order.id} for {symbol}")
                        continue
                    
                    try:
                        self.alpaca.cancel_order(order.id)
                        cancelled_count += 1
                        logger.info(f"Cancelled order {order.id} for {symbol}")
                    except Exception as e:
                        logger.warning(f"Could not cancel order {order.id}: {e}")
            
            if cancelled_count > 0:
                logger.info(f"✅ Cancelled {cancelled_count} orders for {symbol}")
            if skipped_brackets > 0:
                logger.info(f"✓ Preserved {skipped_brackets} bracket orders for {symbol}")
            
            if cancelled_count > 0:
                # Brief pause to let cancellations process
                import time
                time.sleep(0.5)
                
        except Exception as e:
            logger.warning(f"Error cancelling orders for {symbol}: {e}")
    
    def _close_position_with_retry(self, symbol: str, position: Position, max_retries: int = 2) -> bool:
        """Close position with retry logic for API errors"""
        for attempt in range(max_retries):
            try:
                success = self.alpaca.close_position(symbol)
                if success:
                    logger.info(f"✅ Successfully closed {symbol}")
                    return True
                    
            except Exception as e:
                error_msg = str(e).lower()
                
                if "insufficient qty available" in error_msg:
                    logger.warning(f"Attempt {attempt + 1}/{max_retries}: Quantity held in orders for {symbol}")
                    
                    if attempt < max_retries - 1:
                        # Cancel non-bracket orders and retry
                        # CRITICAL: Preserve brackets even during retries
                        self._cancel_all_symbol_orders(symbol, preserve_brackets=True)
                        import time
                        time.sleep(1)
                        continue
                    else:
                        logger.error(f"Failed to close {symbol} after {max_retries} attempts")
                        return False
                        
                elif "position does not exist" in error_msg:
                    logger.info(f"Position {symbol} already closed")
                    return True
                    
                else:
                    logger.error(f"Error closing {symbol}: {e}")
                    return False
        
        return False
    
    def _cleanup_position_state(self, symbol: str, position: Position, reason: str):
        """Clean up position from state and database, record trade"""
        try:
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
            
            # Remove from state
            trading_state.remove_position(symbol)
            self.supabase.delete_position(symbol)
            
            # Clean up tracking
            if self.trailing_stop_manager:
                self.trailing_stop_manager.remove_trailing_stop(symbol)
            
            if self.profit_taker:
                self.profit_taker.remove_partial_profit(symbol)
            
            if self.cooldown_manager:
                self.cooldown_manager.record_trade_result(
                    symbol=symbol,
                    pnl=position.unrealized_pl,
                    reason=reason
                )
            
            logger.info(f"✓ Position closed: {symbol} - P/L: ${position.unrealized_pl:.2f} ({reason})")
            
        except Exception as e:
            logger.error(f"Error cleaning up position state for {symbol}: {e}")
    
    def _force_cleanup_position(self, symbol: str, position: Position, reason: str) -> bool:
        """Force cleanup when position is stuck or can't be closed normally"""
        try:
            logger.warning(f"🔧 Force cleaning up stuck position: {symbol}")
            
            # FIRST: Check if position actually still exists in Alpaca
            try:
                alpaca_positions = self.alpaca.get_positions()
                alpaca_symbols = {p.symbol for p in alpaca_positions}
                
                if symbol in alpaca_symbols:
                    # Position still exists - check if it has bracket orders
                    open_orders = self.alpaca.get_orders(status='open')
                    symbol_orders = [o for o in open_orders if o.symbol == symbol]
                    
                    if symbol_orders:
                        # Has active orders - DON'T clean up, let brackets handle it
                        logger.warning(f"⚠️  {symbol} has {len(symbol_orders)} active orders - NOT cleaning up, letting brackets handle exit")
                        return False
                    else:
                        # No orders but position exists - try to cancel and close
                        self._cancel_all_symbol_orders(symbol, preserve_brackets=False)
                        try:
                            self.alpaca.close_position(symbol)
                            logger.info(f"✅ Successfully closed {symbol} after order cleanup")
                        except Exception as close_err:
                            logger.error(f"Still can't close {symbol}: {close_err}")
                            return False
                else:
                    # Position doesn't exist in Alpaca - safe to clean up state
                    logger.info(f"✅ {symbol} already closed in Alpaca - cleaning up local state")
            except Exception as check_err:
                logger.error(f"Error checking Alpaca state for {symbol}: {check_err}")
                return False
            
            # Only clean up state if position is actually closed
            self._cleanup_position_state(symbol, position, reason)
            
            logger.info(f"✅ Force cleanup completed for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Force cleanup failed for {symbol}: {e}")
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
            
            # Log the check result for debugging
            if position.symbol == 'SPY':
                logger.info(f"🔍 SPY Partial Profit Check: {result}")

            # If should take partial profits (and not in shadow mode)
            if result.get('should_take') and not result.get('shadow_mode'):
                logger.info(f"✅ Triggering partial profit execution for {position.symbol}")
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
            
            # CRITICAL: Check if remaining position would be too small
            # For a $141K portfolio, minimum meaningful position is ~$1000 (0.7%)
            remaining_qty = position.qty - shares_to_sell
            remaining_value = remaining_qty * position.current_price
            min_position_value = 1000  # $1000 minimum remaining position
            
            if remaining_value < min_position_value:
                # Close entire position instead of leaving tiny remainder
                logger.info(f"🎯 Closing FULL position {symbol}: remaining ${remaining_value:.0f} < ${min_position_value} minimum")
                shares_to_sell = position.qty  # Sell all shares
            else:
                logger.info(f"🎯 Taking partial profits for {symbol}: {shares_to_sell}/{position.qty} shares at +{profit_r:.2f}R (remaining: ${remaining_value:.0f})")
            
            # CRITICAL FIX: Cancel existing orders to free up shares
            # Otherwise we get "insufficient qty available" errors
            self._cancel_all_symbol_orders(symbol, preserve_brackets=False)
            
            # Submit partial close order
            try:
                if position.side == 'buy':
                    # Close partial long position
                    order = self.alpaca.submit_market_order(
                        symbol=symbol,
                        qty=shares_to_sell,
                        side='sell',
                        client_order_id=f"partial_profit_{symbol}_{int(datetime.now().timestamp())}"
                    )
                else:
                    # Close partial short position
                    order = self.alpaca.submit_market_order(
                        symbol=symbol,
                        qty=shares_to_sell,
                        side='buy',
                        client_order_id=f"partial_profit_{symbol}_{int(datetime.now().timestamp())}"
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
                    final_remaining_qty = position.qty - shares_to_sell
                    
                    if final_remaining_qty <= 0:
                        # Full position closed - remove from state
                        trading_state.remove_position(symbol)
                        self.supabase.delete_position(symbol)
                        logger.info(f"✓ Full position closed for {symbol}: {shares_to_sell} shares sold (was too small to keep remainder)")
                    else:
                        # Partial close - update position
                        position.qty = final_remaining_qty
                        trading_state.update_position(position)
                        
                        # Update database with full position data to avoid constraint violations
                        self.supabase.upsert_position({
                            'symbol': symbol,
                            'qty': final_remaining_qty,
                            'side': position.side,
                            'avg_entry_price': position.avg_entry_price,
                            'current_price': position.current_price,
                            'unrealized_pl': position.unrealized_pl,
                            'unrealized_pl_pct': position.unrealized_pl_pct,
                            'market_value': position.market_value,
                            'stop_loss': position.stop_loss,
                            'take_profit': position.take_profit,
                            'entry_time': position.entry_time.isoformat(),
                            'updated_at': datetime.utcnow().isoformat()
                        })
                        
                        logger.info(f"✓ Partial profits taken for {symbol}: {shares_to_sell} shares sold, {final_remaining_qty} remaining")
                    
                    # Calculate PnL for the partial trade
                    if position.side == 'buy':
                        pnl = (position.current_price - position.avg_entry_price) * shares_to_sell
                    else:
                        pnl = (position.avg_entry_price - position.current_price) * shares_to_sell
                    
                    cost_basis = position.avg_entry_price * shares_to_sell
                    pnl_pct = (pnl / cost_basis) * 100 if cost_basis else 0
                    
                    # Log trade for analysis with complete schema
                    self.supabase.insert_trade({
                        'symbol': symbol,
                        'side': 'sell' if position.side == 'buy' else 'buy',
                        'qty': shares_to_sell,
                        'entry_price': position.avg_entry_price,
                        'exit_price': position.current_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'entry_time': position.entry_time.isoformat(),  # ✅ FIX: Added missing field
                        'exit_time': datetime.utcnow().isoformat(),      # ✅ FIX: Added missing field
                        'strategy': 'ema',       # Shortened to fit varchar(10)
                        'reason': 'part_prof'    # Shortened from 'partial_profit' (15 chars) to fit varchar(10)
                    })
                    
                else:
                    logger.error(f"Failed to submit partial profit order for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error submitting partial profit order for {symbol}: {e}")
                
        except Exception as e:
            logger.error(f"Error executing partial profit taking for {position.symbol}: {e}")

    def check_and_fix_held_orders(self):
        """
        Check for HELD stop loss orders and fix them automatically.
        This prevents the ONDS issue where stop losses don't protect positions.
        
        NOTE: Bracket order legs are HELD by design until parent fills - don't touch them!
        """
        try:
            # Get all positions
            positions = trading_state.get_all_positions()
            if not positions:
                return
            
            # Get all orders
            all_orders = self.alpaca.get_orders(status='all')
            
            # Build set of bracket order IDs to exclude
            bracket_order_ids = set()
            for order in all_orders:
                # If this is a bracket parent or has legs, add all related IDs
                # CRITICAL: Check both string and enum values for order_class
                if hasattr(order, 'order_class') and order.order_class:
                    order_class_str = str(order.order_class).lower()
                    if 'bracket' in order_class_str:
                        bracket_order_ids.add(order.id)
                        if hasattr(order, 'legs') and order.legs:
                            for leg in order.legs:
                                bracket_order_ids.add(leg.id)
            
            for position in positions:
                symbol = position.symbol
                
                # Find HELD stop loss orders for this symbol (excluding bracket orders)
                held_stops = [
                    order for order in all_orders
                    if (order.symbol == symbol and 
                        order.type.value in ['stop', 'trailing_stop'] and 
                        order.status.value == 'held' and
                        order.id not in bracket_order_ids)  # CRITICAL: Don't touch bracket legs!
                ]
                
                if held_stops:
                    logger.error(f"🚨 HELD stop loss detected for {symbol}!")
                    
                    for held_order in held_stops:
                        # Cancel HELD order
                        try:
                            self.alpaca.cancel_order(held_order.id)
                            logger.info(f"✅ Canceled HELD order: {held_order.id}")
                        except Exception as e:
                            logger.error(f"Failed to cancel HELD order: {e}")
                            continue
                        
                        # Create new emergency stop
                        current_price = position.current_price
                        entry_price = position.avg_entry_price
                        
                        # Use 1.5% below current as emergency stop
                        emergency_stop = current_price * 0.985
                        
                        # Don't set stop above entry for losing positions
                        if emergency_stop > entry_price:
                            emergency_stop = entry_price * 0.99
                        
                        try:
                            from alpaca.trading.requests import StopOrderRequest
                            from alpaca.trading.enums import OrderSide, TimeInForce
                            
                            stop_request = StopOrderRequest(
                                symbol=symbol,
                                qty=position.qty,
                                side=OrderSide.SELL if position.side == 'buy' else OrderSide.BUY,
                                time_in_force=TimeInForce.GTC,
                                stop_price=round(emergency_stop, 2)
                            )
                            
                            new_stop = self.alpaca.submit_order_request(stop_request)
                            logger.info(f"✅ Created new stop loss for {symbol} at ${emergency_stop:.2f}")
                            
                            # Update position with new stop
                            position.stop_loss = emergency_stop
                            trading_state.update_position(position)
                            
                        except Exception as e:
                            logger.error(f"Failed to create new stop loss for {symbol}: {e}")
                
        except Exception as e:
            logger.error(f"Error checking for HELD orders: {e}")
    
    def verify_position_protection(self):
        """
        Verify all positions have active stop loss AND take profit protection.
        Auto-recreate missing orders.
        """
        try:
            positions = trading_state.get_all_positions()
            if not positions:
                return
            
            all_orders = self.alpaca.get_orders(status='all')
            unprotected_stops = []
            missing_take_profits = []
            
            for position in positions:
                symbol = position.symbol
                
                # Check for active stop loss
                has_active_stop = False
                has_take_profit = False
                
                for order in all_orders:
                    if order.symbol != symbol:
                        continue
                    
                    # Check stop loss
                    if (order.type.value in ['stop', 'trailing_stop'] and 
                        order.status.value in ['new', 'accepted', 'pending_new', 'held']):
                        has_active_stop = True
                    
                    # Check take profit
                    if (order.type.value == 'limit' and 
                        order.side.value == 'sell' and
                        order.status.value in ['new', 'accepted', 'pending_new']):
                        has_take_profit = True
                
                if not has_active_stop:
                    unprotected_stops.append(symbol)
                    logger.error(f"🚨 NO ACTIVE STOP LOSS for {symbol}! P/L: ${position.unrealized_pl:.2f}")
                
                if not has_take_profit:
                    missing_take_profits.append(symbol)
                    # CRITICAL FIX: Don't try to recreate if shares are already held by stop-loss
                    if has_active_stop:
                        logger.info(f"ℹ️  {symbol} has stop-loss but no take-profit (shares held) - skipping recreation to avoid deadlock")
                    else:
                        logger.warning(f"⚠️  NO TAKE-PROFIT for {symbol} - recreating...")
                        self._recreate_take_profit(position)
            
            if unprotected_stops:
                logger.error(f"⚠️  {len(unprotected_stops)} positions without stop loss: {', '.join(unprotected_stops)}")
                # Auto-fix unprotected positions
                self.check_and_fix_held_orders()
            
        except Exception as e:
            logger.error(f"Error verifying position protection: {e}")
    
    def _recreate_take_profit(self, position):
        """
        Recreate missing take-profit order for a position.
        Uses 2.5% above entry for 2.5:1 R/R ratio.
        
        CRITICAL: If shares are held by stop-loss, cancel it and recreate both orders.
        Alpaca won't allow multiple sell orders for the same shares.
        """
        try:
            from alpaca.trading.requests import LimitOrderRequest, StopOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce
            
            symbol = position.symbol
            qty = position.qty
            entry = position.avg_entry_price
            current = position.current_price
            
            # Calculate take-profit and stop-loss based on position side
            if position.side == 'buy':
                # LONG: profit above entry, stop below entry
                take_profit_price = entry * 1.025  # 2.5% above
                stop_loss_price = entry * 0.985    # 1.5% below
                
                # Don't create take-profit if price already exceeded it
                if current >= take_profit_price:
                    logger.info(f"⚠️  {symbol} already past take-profit level (${current:.2f} >= ${take_profit_price:.2f}) - skipping")
                    return
                
                # Don't create if position is losing significantly
                if current < entry * 0.99:
                    logger.info(f"⚠️  {symbol} is losing position - only stop-loss needed")
                    return
            else:
                # SHORT: profit below entry, stop above entry
                take_profit_price = entry * 0.975  # 2.5% below
                stop_loss_price = entry * 1.015    # 1.5% above
                
                # Don't create take-profit if price already exceeded it
                if current <= take_profit_price:
                    logger.info(f"⚠️  {symbol} already past take-profit level (${current:.2f} <= ${take_profit_price:.2f}) - skipping")
                    return
                
                # Don't create if position is losing significantly
                if current > entry * 1.01:
                    logger.info(f"⚠️  {symbol} is losing position - only stop-loss needed")
                    return
            
            # CRITICAL: Check if shares are held by existing orders
            all_orders = self.alpaca.get_orders(status='open')
            has_existing_orders = False
            
            # Determine expected exit side for this position
            expected_exit_side = 'sell' if position.side == 'buy' else 'buy'
            
            for order in all_orders:
                if (order.symbol == symbol and 
                    order.side.value == expected_exit_side and
                    order.status.value in ['new', 'accepted', 'pending_new', 'held']):
                    has_existing_orders = True
                    break
            
            if has_existing_orders:
                logger.info(f"ℹ️  {symbol} already has exit orders (shares held) - skipping recreation to avoid 'insufficient qty' error")
                return
            
            logger.info(f"✅ No conflicting orders for {symbol} - safe to create take-profit")
            
            # Determine correct exit side based on position side
            # For LONG positions: exit with SELL
            # For SHORT positions: exit with BUY
            exit_side = OrderSide.SELL if position.side == 'buy' else OrderSide.BUY
            
            # Create ONLY take-profit (stop-loss should already exist)
            take_profit_request = LimitOrderRequest(
                symbol=symbol,
                qty=abs(qty),  # Use absolute value for short positions
                side=exit_side,
                time_in_force=TimeInForce.GTC,
                limit_price=round(take_profit_price, 2)
            )
            
            tp_order = self.alpaca.submit_order_request(take_profit_request)
            logger.info(f"✅ Created take-profit for {symbol}: ${take_profit_price:.2f}")
            
            # Update position with both prices
            position.stop_loss = stop_loss_price
            position.take_profit = take_profit_price
            trading_state.update_position(position)
            
        except Exception as e:
            logger.error(f"Failed to recreate bracket for {symbol}: {e}")
