"""
Take Profit Adjuster
Dynamically adjusts take profit targets based on performance
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class TakeProfitAdjuster:
    """
    Adjusts take profit parameters based on trade performance
    
    Analyzes:
    - Average win size
    - Profit target hit rate
    - Missed profit opportunities
    - Optimal profit distance
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        logger.info("Take Profit Adjuster initialized")
    
    async def optimize(self, trades_data: List[Dict]) -> Dict[str, Any]:
        """Optimize take profit based on recent trades"""
        try:
            if not trades_data:
                return {'changed': False, 'reason': 'No trades to analyze'}
            
            # Analyze winning trades
            winning_trades = [t for t in trades_data if t.get('pnl', 0) > 0]
            
            if not winning_trades:
                return {'changed': False, 'reason': 'No winning trades'}
            
            # Calculate metrics
            avg_win = sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades)
            max_win = max(t.get('pnl', 0) for t in winning_trades)
            
            # Count small wins (< $100)
            small_wins = sum(1 for t in winning_trades if t.get('pnl', 0) < 100)
            small_win_rate = small_wins / len(winning_trades)
            
            # Determine adjustment
            current_tp = 2.0  # Default 2%
            new_tp = current_tp
            reason = "No adjustment needed"
            changed = False
            
            if small_win_rate > 0.7:
                # Too many small wins - widen targets
                new_tp = current_tp * 1.2
                reason = f"Widening targets: {small_win_rate:.1%} small wins"
                changed = True
            elif avg_win > 200:
                # Large average wins - can maintain or widen
                new_tp = current_tp * 1.1
                reason = "Widening targets: capturing large moves"
                changed = True
            
            # Bounds checking
            new_tp = max(1.0, min(new_tp, 5.0))
            
            return {
                'changed': changed,
                'old_value': current_tp,
                'new_value': round(new_tp, 2),
                'reason': reason,
                'metrics': {
                    'avg_win': round(avg_win, 2),
                    'max_win': round(max_win, 2),
                    'small_win_rate': round(small_win_rate * 100, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizing take profit: {e}")
            return {'changed': False, 'error': str(e)}
