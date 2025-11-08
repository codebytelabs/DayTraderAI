"""
Partial Profit Taking System
Scales out of winning positions to lock in gains
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PartialProfitTaker:
    """
    Manages partial profit taking for open positions
    
    Features:
    - Takes 50% profit at +2R
    - Lets remaining 50% run with trailing stop
    - Tracks performance improvement
    - Configurable profit targets
    """
    
    def __init__(self, supabase_client):
        """
        Initialize partial profit taker
        
        Args:
            supabase_client: Supabase database client
        """
        self.supabase = supabase_client
        self.partial_exits = {}  # symbol -> partial exit data
        
        # Configuration
        self.profit_targets = [
            {'r_multiple': 2.0, 'percentage': 50},  # Take 50% at +2R
        ]
        
        logger.info("Partial Profit Taker initialized")
    
    def should_take_partial_profit(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        stop_loss: float,
        side: str,
        current_quantity: int
    ) -> Optional[Dict[str, Any]]:
        """
        Check if should take partial profit
        
        Args:
            symbol: Stock symbol
            entry_price: Entry price
            current_price: Current price
            stop_loss: Stop loss price
            side: Position side ('long' or 'short')
            current_quantity: Current position quantity
            
        Returns:
            dict: Partial profit action if should take, None otherwise
        """
        try:
            # Skip if already took partial profit
            if symbol in self.partial_exits:
                return None
            
            # Calculate R (risk amount)
            if side == 'long':
                r = entry_price - stop_loss
                profit_r = (current_price - entry_price) / r if r > 0 else 0
            else:  # short
                r = stop_loss - entry_price
                profit_r = (entry_price - current_price) / r if r > 0 else 0
            
            # Check each profit target
            for target in self.profit_targets:
                if profit_r >= target['r_multiple']:
                    # Calculate quantity to sell
                    quantity_to_sell = int(current_quantity * (target['percentage'] / 100))
                    
                    if quantity_to_sell > 0:
                        logger.info(
                            f"Partial profit trigger for {symbol}: "
                            f"+{profit_r:.2f}R (target: +{target['r_multiple']}R), "
                            f"selling {target['percentage']}% ({quantity_to_sell} shares)"
                        )
                        
                        return {
                            'symbol': symbol,
                            'quantity_to_sell': quantity_to_sell,
                            'percentage': target['percentage'],
                            'r_multiple': target['r_multiple'],
                            'profit_r': profit_r,
                            'current_price': current_price,
                            'reason': f'Partial profit at +{target["r_multiple"]}R'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking partial profit: {e}")
            return None
    
    def record_partial_exit(
        self,
        symbol: str,
        quantity_sold: int,
        exit_price: float,
        profit: float,
        r_multiple: float
    ):
        """
        Record partial profit exit
        
        Args:
            symbol: Stock symbol
            quantity_sold: Quantity sold
            exit_price: Exit price
            profit: Profit from partial exit
            r_multiple: R multiple at exit
        """
        try:
            self.partial_exits[symbol] = {
                'quantity_sold': quantity_sold,
                'exit_price': exit_price,
                'profit': profit,
                'r_multiple': r_multiple,
                'timestamp': datetime.now().isoformat()
            }
            
            # Log to database
            self.supabase.table('position_exits').insert({
                'symbol': symbol,
                'exit_type': 'partial_profit',
                'quantity': quantity_sold,
                'exit_price': exit_price,
                'exit_benefit': profit,
                'exit_reason': f'Partial profit at +{r_multiple:.2f}R',
                'created_at': datetime.now().isoformat()
            }).execute()
            
            logger.info(
                f"Recorded partial exit for {symbol}: "
                f"{quantity_sold} shares @ ${exit_price:.2f}, "
                f"profit: ${profit:.2f} (+{r_multiple:.2f}R)"
            )
            
        except Exception as e:
            logger.error(f"Error recording partial exit: {e}")
    
    def remove_partial_exit(self, symbol: str):
        """Remove partial exit tracking for closed position"""
        if symbol in self.partial_exits:
            del self.partial_exits[symbol]
            logger.info(f"Removed partial exit tracking for {symbol}")
    
    def get_partial_exit_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get partial exit data for symbol"""
        return self.partial_exits.get(symbol)
    
    def has_taken_partial_profit(self, symbol: str) -> bool:
        """Check if partial profit has been taken for symbol"""
        return symbol in self.partial_exits
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get partial profit performance metrics
        
        Returns:
            dict: Performance metrics
        """
        try:
            # Get partial profit exits from database
            result = self.supabase.table('position_exits').select('*').eq(
                'exit_type', 'partial_profit'
            ).execute()
            
            partial_exits = result.data if result.data else []
            
            if not partial_exits:
                return {
                    'total_partial_exits': 0,
                    'message': 'No partial profit exits yet'
                }
            
            # Calculate metrics
            total_exits = len(partial_exits)
            total_profit = sum(e.get('exit_benefit', 0) for e in partial_exits)
            avg_profit = total_profit / total_exits
            
            # Calculate improvement
            # Compare to if we had held full position
            # (This would require comparing to actual final exit)
            
            return {
                'total_partial_exits': total_exits,
                'total_profit_locked': round(total_profit, 2),
                'avg_profit_per_exit': round(avg_profit, 2),
                'active_partial_positions': len(self.partial_exits)
            }
            
        except Exception as e:
            logger.error(f"Error getting partial profit metrics: {e}")
            return {'error': str(e)}
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration"""
        return {
            'profit_targets': self.profit_targets,
            'active_partial_exits': len(self.partial_exits)
        }
    
    def update_configuration(self, new_targets: list):
        """
        Update profit targets
        
        Args:
            new_targets: List of profit targets
                Example: [{'r_multiple': 2.0, 'percentage': 50}]
        """
        self.profit_targets = new_targets
        logger.info(f"Updated profit targets: {new_targets}")
