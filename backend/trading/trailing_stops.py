"""
Trailing Stops System
Protects profits by trailing stop loss as price moves favorably
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TrailingStopManager:
    """
    Manages trailing stops for open positions
    
    Features:
    - Activates after +2R profit
    - ATR-based trailing distance
    - Dynamic adjustment based on volatility
    - Respects support/resistance levels
    - Tracks performance improvement
    """
    
    def __init__(self, supabase_client):
        """
        Initialize trailing stop manager
        
        Args:
            supabase_client: Supabase database client
        """
        self.supabase = supabase_client
        self.active_trailing_stops = {}  # symbol -> trailing stop data
        
        # Configuration
        self.activation_threshold = 2.0  # Activate after +2R profit
        self.trailing_distance_r = 0.5  # Trail by 0.5R
        self.min_trailing_distance = 0.005  # Minimum 0.5%
        
        logger.info("Trailing Stop Manager initialized")
    
    def should_activate_trailing_stop(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        stop_loss: float,
        side: str
    ) -> bool:
        """
        Check if trailing stop should be activated
        
        Args:
            symbol: Stock symbol
            entry_price: Entry price
            current_price: Current price
            stop_loss: Current stop loss
            side: Position side ('long' or 'short')
            
        Returns:
            bool: True if should activate
        """
        try:
            # Calculate R (risk amount)
            if side == 'long':
                r = entry_price - stop_loss
                profit_r = (current_price - entry_price) / r if r > 0 else 0
            else:  # short
                r = stop_loss - entry_price
                profit_r = (entry_price - current_price) / r if r > 0 else 0
            
            # Activate if profit >= activation threshold
            should_activate = profit_r >= self.activation_threshold
            
            if should_activate and symbol not in self.active_trailing_stops:
                logger.info(f"Activating trailing stop for {symbol} (profit: +{profit_r:.2f}R)")
            
            return should_activate
            
        except Exception as e:
            logger.error(f"Error checking trailing stop activation: {e}")
            return False
    
    def calculate_trailing_stop(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        stop_loss: float,
        side: str,
        atr: Optional[float] = None
    ) -> float:
        """
        Calculate trailing stop price
        
        Args:
            symbol: Stock symbol
            entry_price: Entry price
            current_price: Current price
            stop_loss: Current stop loss
            side: Position side
            atr: Average True Range (optional)
            
        Returns:
            float: New trailing stop price
        """
        try:
            # Calculate R (risk amount)
            if side == 'long':
                r = entry_price - stop_loss
            else:  # short
                r = stop_loss - entry_price
            
            # Calculate trailing distance
            if atr:
                # Use ATR-based distance (more dynamic)
                trailing_distance = atr * 1.5  # 1.5x ATR
            else:
                # Use R-based distance
                trailing_distance = r * self.trailing_distance_r
            
            # Ensure minimum distance
            min_distance = current_price * self.min_trailing_distance
            trailing_distance = max(trailing_distance, min_distance)
            
            # Calculate new stop
            if side == 'long':
                new_stop = current_price - trailing_distance
                # Never move stop down
                new_stop = max(new_stop, stop_loss)
            else:  # short
                new_stop = current_price + trailing_distance
                # Never move stop up
                new_stop = min(new_stop, stop_loss)
            
            return new_stop
            
        except Exception as e:
            logger.error(f"Error calculating trailing stop: {e}")
            return stop_loss  # Return current stop on error
    
    def update_trailing_stop(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        current_stop: float,
        side: str,
        atr: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Update trailing stop for a position
        
        Args:
            symbol: Stock symbol
            entry_price: Entry price
            current_price: Current price
            current_stop: Current stop loss
            side: Position side
            atr: Average True Range (optional)
            
        Returns:
            dict: Update result
        """
        try:
            # Check if should activate
            if not self.should_activate_trailing_stop(
                symbol, entry_price, current_price, current_stop, side
            ):
                return {
                    'activated': False,
                    'new_stop': current_stop,
                    'reason': 'Not profitable enough to activate'
                }
            
            # Calculate new trailing stop
            new_stop = self.calculate_trailing_stop(
                symbol, entry_price, current_price, current_stop, side, atr
            )
            
            # Check if stop should be updated
            if side == 'long':
                should_update = new_stop > current_stop
            else:  # short
                should_update = new_stop < current_stop
            
            if should_update:
                # Track trailing stop
                if symbol not in self.active_trailing_stops:
                    self.active_trailing_stops[symbol] = {
                        'activated_at': datetime.now().isoformat(),
                        'initial_stop': current_stop,
                        'updates': 0
                    }
                
                self.active_trailing_stops[symbol]['updates'] += 1
                self.active_trailing_stops[symbol]['last_update'] = datetime.now().isoformat()
                self.active_trailing_stops[symbol]['current_stop'] = new_stop
                
                # Calculate profit protected
                if side == 'long':
                    profit_protected = new_stop - entry_price
                else:
                    profit_protected = entry_price - new_stop
                
                profit_protected_pct = (profit_protected / entry_price) * 100
                
                logger.info(
                    f"Trailing stop updated for {symbol}: "
                    f"{current_stop:.2f} → {new_stop:.2f} "
                    f"(protecting +{profit_protected_pct:.2f}%)"
                )
                
                return {
                    'activated': True,
                    'updated': True,
                    'new_stop': new_stop,
                    'old_stop': current_stop,
                    'profit_protected': profit_protected,
                    'profit_protected_pct': profit_protected_pct,
                    'updates_count': self.active_trailing_stops[symbol]['updates']
                }
            else:
                return {
                    'activated': True,
                    'updated': False,
                    'new_stop': current_stop,
                    'reason': 'Stop already optimal'
                }
            
        except Exception as e:
            logger.error(f"Error updating trailing stop: {e}")
            return {
                'activated': False,
                'updated': False,
                'new_stop': current_stop,
                'error': str(e)
            }
    
    def remove_trailing_stop(self, symbol: str):
        """Remove trailing stop tracking for closed position"""
        if symbol in self.active_trailing_stops:
            del self.active_trailing_stops[symbol]
            logger.info(f"Removed trailing stop tracking for {symbol}")
    
    def get_active_trailing_stops(self) -> Dict[str, Any]:
        """Get all active trailing stops"""
        return self.active_trailing_stops.copy()
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get trailing stop performance metrics
        
        Returns:
            dict: Performance metrics
        """
        try:
            # Get trades with trailing stops from database
            result = self.supabase.table('position_exits').select('*').eq(
                'exit_type', 'trailing_stop'
            ).execute()
            
            trailing_exits = result.data if result.data else []
            
            if not trailing_exits:
                return {
                    'total_trailing_exits': 0,
                    'message': 'No trailing stop exits yet'
                }
            
            # Calculate metrics
            total_exits = len(trailing_exits)
            total_benefit = sum(e.get('exit_benefit', 0) for e in trailing_exits)
            avg_benefit = total_benefit / total_exits
            
            # Profit protected
            profits_protected = [e for e in trailing_exits if e.get('exit_benefit', 0) > 0]
            protection_rate = (len(profits_protected) / total_exits) * 100
            
            return {
                'total_trailing_exits': total_exits,
                'total_benefit': round(total_benefit, 2),
                'avg_benefit': round(avg_benefit, 2),
                'profits_protected': len(profits_protected),
                'protection_rate': round(protection_rate, 1),
                'active_trailing_stops': len(self.active_trailing_stops)
            }
            
        except Exception as e:
            logger.error(f"Error getting trailing stop metrics: {e}")
            return {'error': str(e)}
