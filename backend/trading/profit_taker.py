"""
Partial Profit Taking System (Sprint 6)
Scales out of winning positions to lock in gains

Features:
- Takes partial profits at +1R (configurable)
- Lets remaining position run to +2R (configurable)
- Shadow mode support for safe testing
- Integrates with trailing stops
- Tracks performance improvement
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ProfitTaker:
    """
    Manages partial profit taking for positions
    
    Features:
    - Takes partial profits at +1R (configurable)
    - Lets remaining position run to +2R (configurable)
    - Integrates with trailing stops
    - Shadow mode support for safe testing
    - Tracks performance improvement
    
    Configuration via backend/.env:
    - PARTIAL_PROFITS_ENABLED: Enable/disable feature
    - PARTIAL_PROFITS_FIRST_TARGET_R: First profit target in R (default: 1.0R)
    - PARTIAL_PROFITS_PERCENTAGE: Percentage to sell (default: 0.5 = 50%)
    - PARTIAL_PROFITS_SECOND_TARGET_R: Second target in R (default: 2.0R)
    - PARTIAL_PROFITS_USE_TRAILING: Use trailing stops on remaining (default: true)
    - MAX_PARTIAL_PROFIT_POSITIONS: Limit for gradual rollout (default: 999)
    """
    
    def __init__(self, supabase_client, config=None):
        """
        Initialize profit taker
        
        Args:
            supabase_client: Supabase database client
            config: Optional config object (uses settings if None)
        """
        self.supabase = supabase_client
        self.partial_profits_taken = {}  # symbol -> partial profit data
        
        # Load configuration
        if config is None:
            from config import settings
            config = settings
        
        self.enabled = config.partial_profits_enabled
        self.first_target_r = config.partial_profits_first_target_r
        self.profit_percentage = config.partial_profits_percentage
        self.second_target_r = config.partial_profits_second_target_r
        self.use_trailing = config.partial_profits_use_trailing
        self.max_positions = config.max_partial_profit_positions
        
        # Shadow mode tracking
        self.shadow_mode_active = not self.enabled
        self.shadow_predictions = []  # Track what would happen in shadow mode
        
        # Hydrate state from database
        self._load_state_from_db()
        
        status = "ENABLED" if self.enabled else "SHADOW MODE"
        logger.info(f"🎯 Profit Taker initialized - Status: {status}")
        logger.info(f"   First target: +{self.first_target_r}R | Percentage: {self.profit_percentage*100:.0f}%")
        logger.info(f"   Second target: +{self.second_target_r}R | Use trailing: {self.use_trailing}")
        logger.info(f"   Max positions: {self.max_positions}")
        logger.info(f"   Restored {len(self.partial_profits_taken)} partial profit states from DB")

    def _load_state_from_db(self):
        """Load partial profit state from trades table."""
        try:
            # Get all open positions first to know what to check
            # We can't access trading_state here easily as it might not be ready
            # So we query the positions table directly
            response = self.supabase.client.table('positions').select('symbol, entry_time').execute()
            positions = response.data if response.data else []
            
            for pos in positions:
                symbol = pos['symbol']
                entry_time = pos['entry_time']
                
                # Check for partial profit trades (no time filter needed - just check by symbol and reason)
                trades_response = self.supabase.client.table('trades')\
                    .select('*')\
                    .eq('symbol', symbol)\
                    .eq('reason', 'partial_profit')\
                    .order('timestamp', desc=True)\
                    .limit(1)\
                    .execute()
                
                if trades_response.data:
                    # Found a partial profit trade!
                    trade = trades_response.data[0]
                    self.partial_profits_taken[symbol] = {
                        'timestamp': trade['timestamp'],
                        'shares_sold': trade['qty'],
                        'price': trade['exit_price'],
                        'profit_r': trade.get('profit_r', 0),
                        'profit_amount': trade.get('profit_amount', 0)
                    }
                    logger.debug(f"Restored partial profit state for {symbol}")
                    
        except Exception as e:
            logger.error(f"Failed to load profit taker state: {e}")
    
    def should_take_partial_profits(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        stop_loss: float,
        side: str
    ) -> Dict[str, Any]:
        """
        Check if should take partial profits
        
        Args:
            symbol: Stock symbol
            entry_price: Entry price
            current_price: Current price
            stop_loss: Stop loss price
            side: Position side
            
        Returns:
            dict: Decision result with shadow mode info
        """
        try:
            # Check position limit (for gradual rollout)
            if self.enabled and len(self.partial_profits_taken) >= self.max_positions:
                # Already at max positions, only update existing ones
                if symbol not in self.partial_profits_taken:
                    return {
                        'should_take': False,
                        'reason': f'Max partial profit positions reached ({self.max_positions})',
                        'shadow_mode': False,
                        'at_limit': True
                    }
            
            # Skip if already taken partial profits
            if symbol in self.partial_profits_taken:
                return {
                    'should_take': False,
                    'reason': 'Partial profits already taken',
                    'shadow_mode': self.shadow_mode_active
                }
            
            # Calculate R (risk per share)
            if side == 'long':
                r = entry_price - stop_loss
                profit_r = (current_price - entry_price) / r if r > 0 else 0
            else:  # short
                r = stop_loss - entry_price
                profit_r = (entry_price - current_price) / r if r > 0 else 0
            
            # Check if target reached
            if profit_r >= self.first_target_r:
                profit_amount = abs(current_price - entry_price) * self.profit_percentage
                
                # SHADOW MODE: Log what WOULD happen but don't execute
                if self.shadow_mode_active:
                    logger.info(
                        f"[SHADOW] Would take partial profits for {symbol}: +{profit_r:.2f}R "
                        f"(target: +{self.first_target_r}R, would sell {self.profit_percentage*100:.0f}%)"
                    )
                    
                    # Track shadow prediction
                    self.shadow_predictions.append({
                        'timestamp': datetime.now().isoformat(),
                        'symbol': symbol,
                        'action': 'partial_profit_taking',
                        'profit_r': profit_r,
                        'target_r': self.first_target_r,
                        'percentage': self.profit_percentage,
                        'profit_amount': profit_amount,
                        'side': side
                    })
                    
                    return {
                        'should_take': False,  # Not actually taking in shadow mode
                        'shadow_mode': True,
                        'would_take': True,
                        'profit_r': profit_r,
                        'target_r': self.first_target_r,
                        'percentage': self.profit_percentage,
                        'profit_amount': profit_amount
                    }
                
                # LIVE MODE: Actually take partial profits
                logger.info(
                    f"✓ Partial profit target reached for {symbol}: +{profit_r:.2f}R "
                    f"(target: +{self.first_target_r}R, selling {self.profit_percentage*100:.0f}%)"
                )
                
                return {
                    'should_take': True,
                    'shadow_mode': False,
                    'profit_r': profit_r,
                    'target_r': self.first_target_r,
                    'percentage': self.profit_percentage,
                    'profit_amount': profit_amount
                }
            
            return {
                'should_take': False,
                'reason': f'Target not reached (+{profit_r:.2f}R < +{self.first_target_r}R)',
                'shadow_mode': self.shadow_mode_active,
                'profit_r': profit_r,
                'target_r': self.first_target_r
            }
            
        except Exception as e:
            logger.error(f"Error checking partial profits for {symbol}: {e}")
            return {
                'should_take': False,
                'error': str(e),
                'shadow_mode': self.shadow_mode_active
            }
    
    def record_partial_profit(
        self,
        symbol: str,
        shares_sold: int,
        price: float,
        profit_r: float,
        profit_amount: float
    ):
        """
        Record partial profit taking
        
        Args:
            symbol: Stock symbol
            shares_sold: Number of shares sold
            price: Sale price
            profit_r: Profit in R
            profit_amount: Profit amount in dollars
        """
        try:
            self.partial_profits_taken[symbol] = {
                'timestamp': datetime.now().isoformat(),
                'shares_sold': shares_sold,
                'price': price,
                'profit_r': profit_r,
                'profit_amount': profit_amount
            }
            
            logger.info(f"📊 Recorded partial profit for {symbol}: {shares_sold} shares @ ${price:.2f} (+{profit_r:.2f}R)")
            
        except Exception as e:
            logger.error(f"Error recording partial profit for {symbol}: {e}")
    
    def remove_partial_profit(self, symbol: str):
        """
        Remove partial profit tracking for a symbol (when position fully closed)
        
        Args:
            symbol: Stock symbol
        """
        if symbol in self.partial_profits_taken:
            del self.partial_profits_taken[symbol]
            logger.debug(f"Removed partial profit tracking for {symbol}")
    
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
        
        # Calculate average profit captured
        avg_profit_r = sum(p['profit_r'] for p in self.shadow_predictions) / total_predictions
        avg_profit_amount = sum(p['profit_amount'] for p in self.shadow_predictions) / total_predictions
        
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
            'avg_profit_r': round(avg_profit_r, 2),
            'avg_profit_amount': round(avg_profit_amount, 2),
            'symbols_tracked': len(symbols),
            'most_active_symbols': sorted(symbols.items(), key=lambda x: x[1], reverse=True)[:5],
            'latest_predictions': self.shadow_predictions[-5:]  # Last 5
        }
    
    def check_health(self) -> Dict[str, Any]:
        """
        Health check for partial profit system
        
        Returns:
            dict: Health status
        """
        try:
            issues = []
            warnings = []
            
            # Check if enabled but no partial profits taken
            if self.enabled and len(self.partial_profits_taken) == 0:
                warnings.append("Partial profits enabled but none taken yet (may be normal if no +1R positions)")
            
            # Check shadow mode predictions
            if self.shadow_mode_active and len(self.shadow_predictions) == 0:
                warnings.append("Shadow mode active but no predictions logged yet")
            
            # Check configuration
            if self.first_target_r <= 0:
                issues.append(f"Invalid first target: {self.first_target_r}R")
            
            if self.profit_percentage <= 0 or self.profit_percentage >= 1:
                issues.append(f"Invalid profit percentage: {self.profit_percentage}")
            
            if self.second_target_r <= self.first_target_r:
                issues.append(f"Second target ({self.second_target_r}R) must be > first target ({self.first_target_r}R)")
            
            status = "healthy" if not issues else "unhealthy"
            if warnings and not issues:
                status = "healthy_with_warnings"
            
            return {
                'status': status,
                'enabled': self.enabled,
                'shadow_mode': self.shadow_mode_active,
                'partial_profits_taken': len(self.partial_profits_taken),
                'shadow_predictions': len(self.shadow_predictions),
                'issues': issues,
                'warnings': warnings,
                'config': {
                    'first_target_r': self.first_target_r,
                    'profit_percentage': self.profit_percentage,
                    'second_target_r': self.second_target_r,
                    'use_trailing': self.use_trailing,
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
        Get partial profit taking performance metrics
        
        Returns:
            dict: Performance metrics
        """
        try:
            # Get trades with partial profits from database
            result = self.supabase.table('trades').select('*').eq(
                'exit_type', 'partial_profit'
            ).execute()
            
            partial_trades = result.data if result.data else []
            
            if not partial_trades:
                return {
                    'total_partial_trades': 0,
                    'message': 'No partial profit trades yet',
                    'shadow_mode': self.shadow_mode_active
                }
            
            # Calculate metrics
            total_trades = len(partial_trades)
            total_benefit = sum(t.get('profit_amount', 0) for t in partial_trades)
            avg_benefit = total_benefit / total_trades
            
            # Win rate improvement
            improved_trades = [t for t in partial_trades if t.get('profit_amount', 0) > 0]
            improvement_rate = (len(improved_trades) / total_trades) * 100
            
            return {
                'total_partial_trades': total_trades,
                'total_benefit': round(total_benefit, 2),
                'avg_benefit': round(avg_benefit, 2),
                'improvement_rate': round(improvement_rate, 1),
                'active_partial_positions': len(self.partial_profits_taken),
                'shadow_mode': self.shadow_mode_active
            }
            
        except Exception as e:
            logger.error(f"Error getting partial profit metrics: {e}")
            return {'error': str(e)}
