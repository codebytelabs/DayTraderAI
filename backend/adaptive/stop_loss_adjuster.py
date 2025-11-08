"""
Stop Loss Adjuster
Dynamically adjusts stop loss based on performance
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class StopLossAdjuster:
    """
    Adjusts stop loss parameters based on trade performance
    
    Analyzes:
    - Average loss size
    - Stop hit frequency
    - Premature stop-outs
    - Optimal stop distance
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        logger.info("Stop Loss Adjuster initialized")
    
    async def optimize(self, trades_data: List[Dict]) -> Dict[str, Any]:
        """Optimize stop loss based on recent trades"""
        try:
            if not trades_data:
                return {'changed': False, 'reason': 'No trades to analyze'}
            
            # Analyze losing trades
            losing_trades = [t for t in trades_data if t.get('pnl', 0) < 0]
            
            if not losing_trades:
                return {'changed': False, 'reason': 'No losing trades'}
            
            # Calculate metrics
            avg_loss = sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades)
            max_loss = min(t.get('pnl', 0) for t in losing_trades)
            
            # Count large losses (> $200)
            large_losses = sum(1 for t in losing_trades if t.get('pnl', 0) < -200)
            large_loss_rate = large_losses / len(losing_trades)
            
            # Determine adjustment
            current_stop = 1.0  # Default 1%
            new_stop = current_stop
            reason = "No adjustment needed"
            changed = False
            
            if large_loss_rate > 0.3:
                # Too many large losses - tighten stops
                new_stop = current_stop * 0.8
                reason = f"Tightening stops: {large_loss_rate:.1%} large losses"
                changed = True
            elif avg_loss > -50 and large_loss_rate < 0.1:
                # Small losses, few large losses - can widen slightly
                new_stop = current_stop * 1.1
                reason = "Widening stops: losses well controlled"
                changed = True
            
            # Bounds checking
            new_stop = max(0.5, min(new_stop, 3.0))
            
            return {
                'changed': changed,
                'old_value': current_stop,
                'new_value': round(new_stop, 2),
                'reason': reason,
                'metrics': {
                    'avg_loss': round(avg_loss, 2),
                    'max_loss': round(max_loss, 2),
                    'large_loss_rate': round(large_loss_rate * 100, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizing stop loss: {e}")
            return {'changed': False, 'error': str(e)}
