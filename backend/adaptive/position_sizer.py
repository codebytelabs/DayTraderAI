"""
Adaptive Position Sizer
Dynamically adjusts position sizes based on performance
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AdaptivePositionSizer:
    """
    Adjusts position sizing based on performance and risk
    
    Analyzes:
    - Win rate
    - Profit factor
    - Drawdown
    - Volatility
    - Account growth
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        logger.info("Adaptive Position Sizer initialized")
    
    async def optimize(self, trades_data: List[Dict]) -> Dict[str, Any]:
        """Optimize position sizing based on recent performance"""
        try:
            if not trades_data:
                return {'changed': False, 'reason': 'No trades to analyze'}
            
            # Calculate performance metrics
            total_trades = len(trades_data)
            winning_trades = sum(1 for t in trades_data if t.get('pnl', 0) > 0)
            win_rate = (winning_trades / total_trades) * 100
            
            total_pnl = sum(t.get('pnl', 0) for t in trades_data)
            
            # Calculate drawdown
            running_pnl = 0
            peak = 0
            max_drawdown = 0
            
            for trade in trades_data:
                running_pnl += trade.get('pnl', 0)
                if running_pnl > peak:
                    peak = running_pnl
                drawdown = peak - running_pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Determine adjustment
            current_size = 2.0  # Default 2%
            new_size = current_size
            reason = "No adjustment needed"
            changed = False
            
            if win_rate < 40 or max_drawdown > 1000:
                # Poor performance or high drawdown - reduce size
                new_size = current_size * 0.8
                reason = f"Reducing size: win rate {win_rate:.1f}% or drawdown ${max_drawdown:.0f}"
                changed = True
            elif win_rate > 60 and max_drawdown < 300 and total_pnl > 500:
                # Strong performance - increase size
                new_size = current_size * 1.2
                reason = f"Increasing size: win rate {win_rate:.1f}%, controlled risk"
                changed = True
            
            # Bounds checking
            new_size = max(0.5, min(new_size, 5.0))
            
            return {
                'changed': changed,
                'old_value': current_size,
                'new_value': round(new_size, 2),
                'reason': reason,
                'metrics': {
                    'win_rate': round(win_rate, 1),
                    'total_pnl': round(total_pnl, 2),
                    'max_drawdown': round(max_drawdown, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizing position size: {e}")
            return {'changed': False, 'error': str(e)}
