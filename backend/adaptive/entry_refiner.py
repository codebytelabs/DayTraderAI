"""
Entry Refiner
Dynamically refines entry criteria based on performance
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class EntryRefiner:
    """
    Refines entry criteria based on trade outcomes
    
    Analyzes:
    - Win rate by entry conditions
    - RSI levels at entry
    - ADX levels at entry
    - Volume conditions
    - Market regime correlation
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        logger.info("Entry Refiner initialized")
    
    async def optimize(self, trades_data: List[Dict]) -> Dict[str, Any]:
        """Optimize entry criteria based on recent trades"""
        try:
            if not trades_data:
                return {'changed': False, 'reason': 'No trades to analyze'}
            
            # Calculate win rate
            total_trades = len(trades_data)
            winning_trades = sum(1 for t in trades_data if t.get('pnl', 0) > 0)
            win_rate = (winning_trades / total_trades) * 100
            
            # Analyze entry quality (would need features data)
            # For now, use simple win rate based adjustment
            
            # Current criteria
            current_criteria = {
                'min_rsi': 30,
                'max_rsi': 70,
                'min_adx': 20,
                'min_volume_ratio': 1.5
            }
            
            new_criteria = current_criteria.copy()
            reason = "No adjustment needed"
            changed = False
            
            if win_rate < 45:
                # Low win rate - tighten criteria
                new_criteria['min_adx'] = min(current_criteria['min_adx'] + 2, 30)
                new_criteria['min_volume_ratio'] = min(current_criteria['min_volume_ratio'] + 0.2, 3.0)
                reason = f"Tightening criteria: win rate {win_rate:.1f}%"
                changed = True
            elif win_rate > 65:
                # High win rate - can relax slightly
                new_criteria['min_adx'] = max(current_criteria['min_adx'] - 1, 15)
                new_criteria['min_volume_ratio'] = max(current_criteria['min_volume_ratio'] - 0.1, 1.2)
                reason = f"Relaxing criteria: win rate {win_rate:.1f}%"
                changed = True
            
            return {
                'changed': changed,
                'old_values': current_criteria,
                'new_values': new_criteria,
                'reason': reason,
                'metrics': {
                    'win_rate': round(win_rate, 1),
                    'total_trades': total_trades
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizing entry criteria: {e}")
            return {'changed': False, 'error': str(e)}
