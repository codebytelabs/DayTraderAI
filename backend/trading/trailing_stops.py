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
    - Activates after +2R profit (configurable)
    - ATR-based trailing distance (configurable)
    - Dynamic adjustment based on volatility
    - Shadow mode support for safe testing
    - Tracks performance improvement
    
    Configuration via backend/.env:
    - TRAILING_STOPS_ENABLED: Enable/disable feature
    - TRAILING_STOPS_ACTIVATION_THRESHOLD: Profit threshold to activate (default: 2.0R)
    - TRAILING_STOPS_DISTANCE_R: Trailing distance in R (default: 0.5R)
    - TRAILING_STOPS_MIN_DISTANCE_PCT: Minimum trailing distance % (default: 0.5%)
    - TRAILING_STOPS_USE_ATR: Use ATR for dynamic distance (default: true)
    - TRAILING_STOPS_ATR_MULTIPLIER: ATR multiplier (default: 1.5)
    - MAX_TRAILING_STOP_POSITIONS: Limit for gradual rollout (default: 999)
    """
    
    def __init__(self, supabase_client, config=None):
        """
        Initialize trailing stop manager
        
        Args:
            supabase_client: Supabase database client
            config: Optional config object (uses settings if None)
        """
        self.supabase = supabase_client
        self.active_trailing_stops = {}  # symbol -> trailing stop data
        
        # Load configuration
        if config is None:
            from config import settings
            config = settings
        
        self.enabled = config.trailing_stops_enabled
        self.activation_threshold = config.trailing_stops_activation_threshold
        self.trailing_distance_r = config.trailing_stops_distance_r
        self.min_trailing_distance = config.trailing_stops_min_distance_pct
        self.use_atr = config.trailing_stops_use_atr
        self.atr_multiplier = config.trailing_stops_atr_multiplier
        self.max_positions = config.max_trailing_stop_positions
        
        # Shadow mode tracking
        self.shadow_mode_active = not self.enabled
        self.shadow_predictions = []  # Track what would happen in shadow mode
        
        status = "ENABLED" if self.enabled else "SHADOW MODE"
        logger.info(f"🎯 Trailing Stop Manager initialized - Status: {status}")
        logger.info(f"   Activation: +{self.activation_threshold}R | Distance: {self.trailing_distance_r}R")
        logger.info(f"   ATR-based: {self.use_atr} | Max positions: {self.max_positions}")
    
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
            dict: Update result with 'shadow_mode' flag if not enabled
        """
        try:
            # Check position limit (for gradual rollout)
            if self.enabled and len(self.active_trailing_stops) >= self.max_positions:
                # Already at max positions, only update existing ones
                if symbol not in self.active_trailing_stops:
                    return {
                        'activated': False,
                        'new_stop': current_stop,
                        'reason': f'Max trailing stop positions reached ({self.max_positions})',
                        'shadow_mode': False,
                        'at_limit': True
                    }
            
            # Check if should activate
            if not self.should_activate_trailing_stop(
                symbol, entry_price, current_price, current_stop, side
            ):
                return {
                    'activated': False,
                    'new_stop': current_stop,
                    'reason': 'Not profitable enough to activate',
                    'shadow_mode': self.shadow_mode_active
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
                # Calculate profit protected
                if side == 'long':
                    profit_protected = new_stop - entry_price
                else:
                    profit_protected = entry_price - new_stop
                
                profit_protected_pct = (profit_protected / entry_price) * 100
                
                # SHADOW MODE: Log what WOULD happen but don't execute
                if self.shadow_mode_active:
                    logger.info(
                        f"[SHADOW] Would update trailing stop for {symbol}: "
                        f"{current_stop:.2f} → {new_stop:.2f} "
                        f"(would protect +{profit_protected_pct:.2f}%)"
                    )
                    
                    # Track shadow prediction
                    self.shadow_predictions.append({
                        'timestamp': datetime.now().isoformat(),
                        'symbol': symbol,
                        'action': 'update_trailing_stop',
                        'old_stop': current_stop,
                        'new_stop': new_stop,
                        'profit_protected_pct': profit_protected_pct,
                        'side': side
                    })
                    
                    return {
                        'activated': True,
                        'updated': False,  # Not actually updated in shadow mode
                        'shadow_mode': True,
                        'would_update': True,
                        'new_stop': new_stop,
                        'old_stop': current_stop,
                        'profit_protected': profit_protected,
                        'profit_protected_pct': profit_protected_pct
                    }
                
                # LIVE MODE: Actually update trailing stop
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
                
                logger.info(
                    f"✓ Trailing stop updated for {symbol}: "
                    f"{current_stop:.2f} → {new_stop:.2f} "
                    f"(protecting +{profit_protected_pct:.2f}%)"
                )
                
                return {
                    'activated': True,
                    'updated': True,
                    'shadow_mode': False,
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
                    'reason': 'Stop already optimal',
                    'shadow_mode': self.shadow_mode_active
                }
            
        except Exception as e:
            logger.error(f"Error updating trailing stop: {e}")
            return {
                'activated': False,
                'updated': False,
                'new_stop': current_stop,
                'error': str(e),
                'shadow_mode': self.shadow_mode_active
            }
    
    def remove_trailing_stop(self, symbol: str):
        """Remove trailing stop tracking for closed position"""
        if symbol in self.active_trailing_stops:
            del self.active_trailing_stops[symbol]
            logger.info(f"Removed trailing stop tracking for {symbol}")
    
    def get_active_trailing_stops(self) -> Dict[str, Any]:
        """Get all active trailing stops"""
        return self.active_trailing_stops.copy()
    
    def get_shadow_mode_report(self) -> Dict[str, Any]:
        """
        Get shadow mode predictions report
        
        Returns:
            dict: Shadow mode analysis
        """
        if not self.shadow_predictions:
            return {
                'shadow_mode': self.shadow_mode_active,
                'predictions': 0,
                'message': 'No shadow predictions yet'
            }
        
        total_predictions = len(self.shadow_predictions)
        
        # Calculate average profit protection
        avg_protection = sum(p['profit_protected_pct'] for p in self.shadow_predictions) / total_predictions
        
        # Group by symbol
        symbols = {}
        for pred in self.shadow_predictions:
            symbol = pred['symbol']
            if symbol not in symbols:
                symbols[symbol] = 0
            symbols[symbol] += 1
        
        return {
            'shadow_mode': True,
            'total_predictions': total_predictions,
            'avg_profit_protection_pct': round(avg_protection, 2),
            'symbols_tracked': len(symbols),
            'most_active_symbols': sorted(symbols.items(), key=lambda x: x[1], reverse=True)[:5],
            'latest_predictions': self.shadow_predictions[-5:]  # Last 5
        }
    
    def check_health(self) -> Dict[str, Any]:
        """
        Health check for trailing stops system
        
        Returns:
            dict: Health status
        """
        try:
            issues = []
            warnings = []
            
            # Check if enabled but no active stops
            if self.enabled and len(self.active_trailing_stops) == 0:
                warnings.append("Trailing stops enabled but none active (may be normal if no profitable positions)")
            
            # Check for stuck stops (stop price > current price for longs)
            for symbol, data in self.active_trailing_stops.items():
                if 'current_stop' in data:
                    # This would need current price to validate - skip for now
                    pass
            
            # Check shadow mode predictions
            if self.shadow_mode_active and len(self.shadow_predictions) == 0:
                warnings.append("Shadow mode active but no predictions logged yet")
            
            # Check configuration
            if self.activation_threshold <= 0:
                issues.append(f"Invalid activation threshold: {self.activation_threshold}")
            
            if self.trailing_distance_r <= 0:
                issues.append(f"Invalid trailing distance: {self.trailing_distance_r}")
            
            status = "healthy" if not issues else "unhealthy"
            if warnings and not issues:
                status = "healthy_with_warnings"
            
            return {
                'status': status,
                'enabled': self.enabled,
                'shadow_mode': self.shadow_mode_active,
                'active_trailing_stops': len(self.active_trailing_stops),
                'shadow_predictions': len(self.shadow_predictions),
                'issues': issues,
                'warnings': warnings,
                'config': {
                    'activation_threshold': self.activation_threshold,
                    'trailing_distance_r': self.trailing_distance_r,
                    'use_atr': self.use_atr,
                    'max_positions': self.max_positions
                }
            }
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
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
                    'message': 'No trailing stop exits yet',
                    'shadow_mode': self.shadow_mode_active
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
                'active_trailing_stops': len(self.active_trailing_stops),
                'shadow_mode': self.shadow_mode_active
            }
            
        except Exception as e:
            logger.error(f"Error getting trailing stop metrics: {e}")
            return {'error': str(e)}
