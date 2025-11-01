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
    """
    
    def __init__(
        self,
        alpaca_client: AlpacaClient,
        supabase_client: SupabaseClient
    ):
        self.alpaca = alpaca_client
        self.supabase = supabase_client
    
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
            
            logger.debug(f"Updated prices for {len(positions)} positions")
            
        except Exception as e:
            logger.error(f"Failed to update position prices: {e}")
    
    def check_stops_and_targets(self) -> List[str]:
        """
        Check if any positions hit stop loss or take profit.
        Returns list of symbols that need to be closed.
        """
        symbols_to_close = []
        
        try:
            positions = trading_state.get_all_positions()
            
            for position in positions:
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
    
    def close_position(self, symbol: str, reason: str = "Manual close"):
        """
        Close a position and record the trade.
        """
        try:
            position = trading_state.get_position(symbol)
            if not position:
                logger.warning(f"No position found for {symbol}")
                return False
            
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
                
                # Remove from state
                trading_state.remove_position(symbol)
                self.supabase.delete_position(symbol)
                
                logger.info(f"Position closed: {symbol} - P/L: ${position.unrealized_pl:.2f}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to close position {symbol}: {e}")
            return False
