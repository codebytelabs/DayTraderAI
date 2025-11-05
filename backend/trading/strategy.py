from typing import Optional, Dict
from config import settings
from core.state import trading_state
from data.features import FeatureEngine
from trading.order_manager import OrderManager
from utils.helpers import calculate_position_size, calculate_atr_stop, calculate_atr_target
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EMAStrategy:
    """
    EMA Crossover Strategy with ATR-based stops and targets.
    Entry: EMA(9) crosses EMA(21)
    Exit: Stop loss or take profit based on ATR
    """
    
    def __init__(self, order_manager: OrderManager):
        self.order_manager = order_manager
        self.ema_short = settings.ema_short
        self.ema_long = settings.ema_long
        self.stop_mult = settings.stop_loss_atr_mult
        self.target_mult = settings.take_profit_atr_mult
    
    def evaluate(self, symbol: str, features: Dict) -> Optional[str]:
        """
        Evaluate strategy for a symbol.
        Returns signal: 'buy', 'sell', or None
        """
        if not features:
            return None
        
        # Check if we already have a position
        existing_position = trading_state.get_position(symbol)
        if existing_position:
            # Don't generate new signals if we have a position
            return None
        
        # Detect crossover
        signal = FeatureEngine.detect_ema_crossover(features)
        
        if signal:
            logger.info(f"Signal detected for {symbol}: {signal.upper()}")
        
        return signal
    
    def execute_signal(self, symbol: str, signal: str, features: Dict) -> bool:
        """
        Execute trading signal with proper position sizing.
        Returns True if order submitted successfully.
        """
        try:
            # Get account info for position sizing
            metrics = trading_state.get_metrics()
            equity = metrics.equity
            
            if equity <= 0:
                logger.error("Invalid equity for position sizing")
                return False
            
            # Calculate position size based on risk
            price = features['price']
            atr = features['atr']
            
            stop_price = calculate_atr_stop(price, atr, self.stop_mult, signal)
            target_price = calculate_atr_target(price, atr, self.target_mult, signal)
            
            # Enforce minimum stop distance
            stop_distance = abs(price - stop_price)
            min_stop_distance = price * settings.min_stop_distance_pct
            
            if stop_distance < min_stop_distance:
                logger.warning(
                    f"Stop distance too small for {symbol}: ${stop_distance:.2f} < ${min_stop_distance:.2f} "
                    f"(min {settings.min_stop_distance_pct*100}%). Adjusting..."
                )
                # Adjust stop to meet minimum distance
                if signal == 'buy':
                    stop_price = price - min_stop_distance
                else:
                    stop_price = price + min_stop_distance
            
            qty = calculate_position_size(
                equity=equity,
                risk_pct=settings.risk_per_trade_pct,
                entry_price=price,
                stop_price=stop_price
            )
            
            if qty <= 0:
                logger.warning(f"Position size too small for {symbol}")
                return False
            
            # Cap position size at max position value
            max_position_value = equity * settings.max_position_pct
            position_value = qty * price
            
            if position_value > max_position_value:
                # Reduce quantity to fit within max position size
                qty = int(max_position_value / price)
                logger.warning(
                    f"Position size capped for {symbol}: {int(position_value/price)} shares → {qty} shares "
                    f"(${position_value:,.2f} → ${qty * price:,.2f}, max {settings.max_position_pct*100}% of equity)"
                )
                
                if qty <= 0:
                    logger.warning(f"Position size too small after capping for {symbol}")
                    return False
            
            # Submit order
            reason = f"EMA({self.ema_short}/{self.ema_long}) {signal.upper()} crossover"
            order = self.order_manager.submit_order(
                symbol=symbol,
                side=signal,
                qty=qty,
                reason=reason,
                price=price,
                take_profit_price=target_price,
                stop_loss_price=stop_price,
            )
            
            if order:
                logger.info(
                    f"Order submitted: {signal.upper()} {qty} {symbol} @ ~${price:.2f} "
                    f"(Stop: ${stop_price:.2f}, Target: ${target_price:.2f})"
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to execute signal for {symbol}: {e}")
            return False
    
    def check_exit(self, symbol: str, features: Dict) -> Optional[str]:
        """
        Check if we should exit a position.
        Returns 'stop_loss', 'take_profit', or None
        """
        position = trading_state.get_position(symbol)
        if not position:
            return None
        
        current_price = features['price']
        
        # Check stop loss
        if position.side == 'buy':
            if current_price <= position.stop_loss:
                return 'stop_loss'
            if current_price >= position.take_profit:
                return 'take_profit'
        else:  # sell/short
            if current_price >= position.stop_loss:
                return 'stop_loss'
            if current_price <= position.take_profit:
                return 'take_profit'
        
        return None
    
    def execute_exit(self, symbol: str, reason: str) -> bool:
        """Execute exit order."""
        try:
            position = trading_state.get_position(symbol)
            if not position:
                return False
            
            # Determine exit side (opposite of entry)
            exit_side = 'sell' if position.side == 'buy' else 'buy'
            
            order = self.order_manager.submit_order(
                symbol=symbol,
                side=exit_side,
                qty=position.qty,
                reason=reason
            )
            
            if order:
                logger.info(f"Exit order submitted: {symbol} ({reason})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to execute exit for {symbol}: {e}")
            return False
