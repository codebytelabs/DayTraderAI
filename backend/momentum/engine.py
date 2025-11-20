# Bracket adjustment engine - handles Alpaca API calls to modify orders
# Implements the core logic for extending targets and moving stops

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time

from .config import MomentumConfig
from .signals import MomentumSignal, PositionEnhancement
from .validator import MomentumSignalValidator
from .indicators import ATRCalculator

logger = logging.getLogger(__name__)

class BracketAdjustmentEngine:
    """
    Handles bracket order adjustments based on momentum signals.
    Manages Alpaca API calls to modify stop loss and take profit orders.
    """
    
    def __init__(
        self,
        alpaca_client,
        config: MomentumConfig,
        validator: Optional[MomentumSignalValidator] = None
    ):
        self.alpaca = alpaca_client
        self.config = config
        self.validator = validator or MomentumSignalValidator(config)
        self.atr_calculator = ATRCalculator(period=14)
        
        # Track adjusted positions
        self.adjusted_positions: Dict[str, PositionEnhancement] = {}
        
        logger.info("✅ Bracket Adjustment Engine initialized")
    
    def evaluate_and_adjust(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        stop_loss: float,
        take_profit: float,
        quantity: int,
        side: str,
        market_data: Dict
    ) -> Optional[MomentumSignal]:
        """
        Evaluate momentum and adjust brackets if conditions are met.
        
        Args:
            symbol: Stock symbol
            entry_price: Entry price
            current_price: Current market price
            stop_loss: Current stop loss price
            take_profit: Current take profit price
            quantity: Position size
            side: 'long' or 'short'
            market_data: Dict with 'high', 'low', 'close', 'volume' lists
            
        Returns:
            MomentumSignal if evaluated, None if skipped
        """
        try:
            # Check if already adjusted
            if symbol in self.adjusted_positions:
                logger.debug(f"Position {symbol} already adjusted, skipping")
                return None
            
            # Calculate current profit in R
            risk = abs(entry_price - stop_loss)
            if risk == 0:
                logger.warning(f"Zero risk for {symbol}, cannot evaluate")
                return None
            
            profit = current_price - entry_price if side == 'long' else entry_price - current_price
            profit_r = profit / risk
            
            # Check if ready for evaluation
            if profit_r < self.config.evaluation_profit_r:
                logger.debug(f"{symbol} at +{profit_r:.2f}R, waiting for +{self.config.evaluation_profit_r}R")
                return None
            
            logger.info(f"📊 Evaluating momentum for {symbol} at +{profit_r:.2f}R")
            
            # Validate momentum
            signal = self.validator.validate_momentum(
                symbol=symbol,
                high=market_data['high'],
                low=market_data['low'],
                close=market_data['close'],
                volume=market_data['volume'],
                current_profit_r=profit_r
            )
            
            # If momentum is strong, adjust brackets
            if signal.extend:
                success = self._adjust_brackets(
                    symbol=symbol,
                    entry_price=entry_price,
                    current_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    quantity=quantity,
                    side=side,
                    signal=signal,
                    market_data=market_data
                )
                
                if success:
                    # Track adjusted position
                    position = PositionEnhancement(
                        symbol=symbol,
                        entry_price=entry_price,
                        quantity=quantity,
                        initial_stop=stop_loss,
                        initial_target=take_profit
                    )
                    
                    self.adjusted_positions[symbol] = position
                    logger.info(f"✅ Brackets adjusted for {symbol}")
                else:
                    logger.error(f"Failed to adjust brackets for {symbol}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error evaluating {symbol}: {e}")
            return None
    
    def _adjust_brackets(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        stop_loss: float,
        take_profit: float,
        quantity: int,
        side: str,
        signal: MomentumSignal,
        market_data: Dict
    ) -> bool:
        """
        Adjust stop loss and take profit orders.
        
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"🎯 Adjusting brackets for {symbol}")
            
            # Calculate new levels
            risk = abs(entry_price - stop_loss)
            
            # New target: extend from +2R to +3R (or configured value)
            if side == 'long':
                new_target = entry_price + (risk * self.config.extended_target_r)
                # New stop: breakeven + 0.5R
                new_stop = entry_price + (risk * self.config.progressive_stop_r)
            else:  # short
                new_target = entry_price - (risk * self.config.extended_target_r)
                new_stop = entry_price - (risk * self.config.progressive_stop_r)
            
            # Use ATR trailing if enabled
            if self.config.use_atr_trailing:
                atr = self.atr_calculator.calculate(
                    market_data['high'],
                    market_data['low'],
                    market_data['close']
                )
                
                if atr > 0:
                    trailing_distance = atr * self.config.atr_trailing_multiplier
                    
                    if side == 'long':
                        atr_stop = current_price - trailing_distance
                        # Use the higher of progressive stop or ATR trailing
                        new_stop = max(new_stop, atr_stop)
                    else:
                        atr_stop = current_price + trailing_distance
                        new_stop = min(new_stop, atr_stop)
                    
                    logger.info(f"ATR trailing: ${atr_stop:.2f} (ATR: {atr:.4f})")
            
            logger.info(f"New levels for {symbol}:")
            logger.info(f"  Target: ${take_profit:.2f} → ${new_target:.2f} (+{self.config.extended_target_r}R)")
            logger.info(f"  Stop: ${stop_loss:.2f} → ${new_stop:.2f} (BE + {self.config.progressive_stop_r}R)")
            
            # Step 1: Cancel existing bracket orders
            success = self._cancel_bracket_orders(symbol)
            if not success:
                logger.error(f"Failed to cancel existing brackets for {symbol}")
                return False
            
            # Step 2: Create new bracket orders
            success = self._create_new_brackets(
                symbol=symbol,
                quantity=quantity,
                side=side,
                stop_price=new_stop,
                target_price=new_target
            )
            
            if success:
                logger.info(f"✅ Successfully adjusted brackets for {symbol}")
                return True
            else:
                logger.error(f"Failed to create new brackets for {symbol}")
                return False
            
        except Exception as e:
            logger.error(f"Error adjusting brackets for {symbol}: {e}")
            return False
    
    def _cancel_bracket_orders(self, symbol: str) -> bool:
        """Cancel existing stop loss and take profit orders"""
        try:
            orders = self.alpaca.list_orders(status='open', symbols=[symbol])
            cancelled_count = 0
            
            for order in orders:
                # Cancel stop loss and take profit orders
                if order.type in ['stop', 'limit', 'stop_limit']:
                    try:
                        self.alpaca.cancel_order(order.id)
                        cancelled_count += 1
                        logger.info(f"Cancelled {order.type} order {order.id}")
                    except Exception as e:
                        logger.warning(f"Could not cancel order {order.id}: {e}")
            
            if cancelled_count > 0:
                logger.info(f"Cancelled {cancelled_count} orders for {symbol}")
                # Brief pause to let cancellations process
                time.sleep(0.5)
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling orders for {symbol}: {e}")
            return False
    
    def _create_new_brackets(
        self,
        symbol: str,
        quantity: int,
        side: str,
        stop_price: float,
        target_price: float
    ) -> bool:
        """Create new stop loss and take profit orders"""
        try:
            # Determine order sides
            if side == 'long':
                stop_side = 'sell'
                target_side = 'sell'
            else:
                stop_side = 'buy'
                target_side = 'buy'
            
            # Create stop loss order
            stop_order = self.alpaca.submit_order(
                symbol=symbol,
                qty=quantity,
                side=stop_side,
                type='stop',
                time_in_force='gtc',
                stop_price=round(stop_price, 2)
            )
            
            if not stop_order:
                logger.error(f"Failed to create stop loss order for {symbol}")
                return False
            
            logger.info(f"✅ Created stop loss at ${stop_price:.2f}")
            
            # Create take profit order
            target_order = self.alpaca.submit_order(
                symbol=symbol,
                qty=quantity,
                side=target_side,
                type='limit',
                time_in_force='gtc',
                limit_price=round(target_price, 2)
            )
            
            if not target_order:
                logger.error(f"Failed to create take profit order for {symbol}")
                # Cancel the stop loss we just created
                try:
                    self.alpaca.cancel_order(stop_order.id)
                except:
                    pass
                return False
            
            logger.info(f"✅ Created take profit at ${target_price:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating bracket orders for {symbol}: {e}")
            return False
    
    def remove_position_tracking(self, symbol: str):
        """Remove position from tracking when closed"""
        if symbol in self.adjusted_positions:
            del self.adjusted_positions[symbol]
            logger.info(f"Removed {symbol} from momentum tracking")
    
    def get_adjusted_positions(self) -> Dict[str, PositionEnhancement]:
        """Get all positions with adjusted brackets"""
        return self.adjusted_positions.copy()
    
    def is_position_adjusted(self, symbol: str) -> bool:
        """Check if position has been adjusted"""
        return symbol in self.adjusted_positions
    
    def batch_evaluate(
        self,
        positions: List[Dict],
        market_data: Dict[str, Dict]
    ) -> Dict[str, MomentumSignal]:
        """
        Evaluate and adjust multiple positions.
        
        Args:
            positions: List of position dicts
            market_data: Dict mapping symbol to OHLCV data
            
        Returns:
            Dict mapping symbol to MomentumSignal
        """
        results = {}
        
        for position in positions:
            symbol = position['symbol']
            
            if symbol not in market_data:
                logger.warning(f"No market data for {symbol}")
                continue
            
            signal = self.evaluate_and_adjust(
                symbol=symbol,
                entry_price=position['entry_price'],
                current_price=position['current_price'],
                stop_loss=position['stop_loss'],
                take_profit=position['take_profit'],
                quantity=position['quantity'],
                side=position['side'],
                market_data=market_data[symbol]
            )
            
            if signal:
                results[symbol] = signal
        
        logger.info(f"Evaluated {len(results)} positions for momentum adjustment")
        return results
    
    def update_config(self, new_config: MomentumConfig):
        """Update configuration"""
        self.config = new_config
        self.validator.update_config(new_config)
        logger.info("✅ Bracket adjustment engine config updated")
