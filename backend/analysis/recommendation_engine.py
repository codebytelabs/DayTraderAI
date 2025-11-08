"""
Recommendation Engine
Generates actionable parameter recommendations
"""

import logging
from typing import Dict, Any, List
from datetime import date, timedelta

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generates parameter recommendations based on performance
    
    Features:
    - Position size recommendations
    - Stop loss adjustments
    - Take profit adjustments
    - Entry criteria refinements
    - Risk management suggestions
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        logger.info("Recommendation Engine initialized")
    
    async def generate_recommendations(
        self, 
        trades_data: List[Dict], 
        positions_data: List[Dict], 
        ml_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive recommendations
        
        Args:
            trades_data: Trade data
            positions_data: Position exit data
            ml_data: ML prediction data
            
        Returns:
            dict: Recommendations by category
        """
        try:
            recommendations = {
                'position_sizing': await self._recommend_position_sizing(trades_data),
                'stop_loss': await self._recommend_stop_loss(trades_data),
                'take_profit': await self._recommend_take_profit(trades_data),
                'entry_criteria': await self._recommend_entry_criteria(trades_data, ml_data),
                'risk_management': await self._recommend_risk_management(trades_data, positions_data),
                'priority_actions': []
            }
            
            # Determine priority actions
            recommendations['priority_actions'] = self._determine_priority_actions(recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {'error': str(e)}
    
    async def _recommend_position_sizing(self, trades_data: List[Dict]) -> Dict:
        """Recommend position sizing adjustments"""
        if not trades_data:
            return {'recommendation': 'No data available', 'confidence': 0}
        
        # Calculate current performance metrics
        total_trades = len(trades_data)
        winning_trades = sum(1 for t in trades_data if t.get('pnl', 0) > 0)
        win_rate = (winning_trades / total_trades) * 100
        
        total_pnl = sum(t.get('pnl', 0) for t in trades_data)
        avg_pnl = total_pnl / total_trades
        
        # Calculate max drawdown
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
        
        # Generate recommendation
        recommendation = 'MAINTAIN'
        reason = 'Current position sizing is appropriate'
        confidence = 0.7
        
        if win_rate < 40 or max_drawdown > 1000:
            recommendation = 'REDUCE'
            reason = 'Low win rate or high drawdown - reduce risk'
            confidence = 0.9
        elif win_rate > 60 and max_drawdown < 300:
            recommendation = 'INCREASE'
            reason = 'Strong performance with controlled risk - can increase size'
            confidence = 0.8
        
        return {
            'recommendation': recommendation,
            'reason': reason,
            'confidence': confidence,
            'current_metrics': {
                'win_rate': round(win_rate, 1),
                'avg_pnl': round(avg_pnl, 2),
                'max_drawdown': round(max_drawdown, 2)
            }
        }
    
    async def _recommend_stop_loss(self, trades_data: List[Dict]) -> Dict:
        """Recommend stop loss adjustments"""
        if not trades_data:
            return {'recommendation': 'No data available', 'confidence': 0}
        
        # Analyze losing trades
        losing_trades = [t for t in trades_data if t.get('pnl', 0) < 0]
        
        if not losing_trades:
            return {
                'recommendation': 'MAINTAIN',
                'reason': 'No losing trades to analyze',
                'confidence': 0.5
            }
        
        # Calculate average loss
        avg_loss = sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades)
        max_loss = min(t.get('pnl', 0) for t in losing_trades)
        
        # Calculate loss distribution
        small_losses = sum(1 for t in losing_trades if t.get('pnl', 0) > -100)
        large_losses = sum(1 for t in losing_trades if t.get('pnl', 0) < -200)
        
        # Generate recommendation
        recommendation = 'MAINTAIN'
        reason = 'Stop losses are working effectively'
        confidence = 0.7
        
        if large_losses > len(losing_trades) * 0.3:
            recommendation = 'TIGHTEN'
            reason = 'Too many large losses - tighten stop losses'
            confidence = 0.9
        elif small_losses > len(losing_trades) * 0.8 and avg_loss > -50:
            recommendation = 'WIDEN'
            reason = 'Stops may be too tight - consider wider stops'
            confidence = 0.7
        
        return {
            'recommendation': recommendation,
            'reason': reason,
            'confidence': confidence,
            'current_metrics': {
                'avg_loss': round(avg_loss, 2),
                'max_loss': round(max_loss, 2),
                'large_loss_rate': round((large_losses / len(losing_trades)) * 100, 1)
            }
        }
    
    async def _recommend_take_profit(self, trades_data: List[Dict]) -> Dict:
        """Recommend take profit adjustments"""
        if not trades_data:
            return {'recommendation': 'No data available', 'confidence': 0}
        
        # Analyze winning trades
        winning_trades = [t for t in trades_data if t.get('pnl', 0) > 0]
        
        if not winning_trades:
            return {
                'recommendation': 'MAINTAIN',
                'reason': 'No winning trades to analyze',
                'confidence': 0.5
            }
        
        # Calculate average win
        avg_win = sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades)
        max_win = max(t.get('pnl', 0) for t in winning_trades)
        
        # Calculate win distribution
        small_wins = sum(1 for t in winning_trades if t.get('pnl', 0) < 100)
        large_wins = sum(1 for t in winning_trades if t.get('pnl', 0) > 200)
        
        # Generate recommendation
        recommendation = 'MAINTAIN'
        reason = 'Take profit levels are appropriate'
        confidence = 0.7
        
        if small_wins > len(winning_trades) * 0.8:
            recommendation = 'WIDEN'
            reason = 'Many small wins - consider wider profit targets'
            confidence = 0.8
        elif large_wins > len(winning_trades) * 0.3 and avg_win > 150:
            recommendation = 'MAINTAIN_OR_WIDEN'
            reason = 'Good profit capture - current approach working well'
            confidence = 0.9
        
        return {
            'recommendation': recommendation,
            'reason': reason,
            'confidence': confidence,
            'current_metrics': {
                'avg_win': round(avg_win, 2),
                'max_win': round(max_win, 2),
                'small_win_rate': round((small_wins / len(winning_trades)) * 100, 1)
            }
        }
    
    async def _recommend_entry_criteria(self, trades_data: List[Dict], ml_data: List[Dict]) -> Dict:
        """Recommend entry criteria adjustments"""
        if not trades_data:
            return {'recommendation': 'No data available', 'confidence': 0}
        
        # Calculate win rate
        total_trades = len(trades_data)
        winning_trades = sum(1 for t in trades_data if t.get('pnl', 0) > 0)
        win_rate = (winning_trades / total_trades) * 100
        
        # Analyze ML performance if available
        ml_accuracy = 0
        if ml_data:
            correct_predictions = sum(1 for p in ml_data if p.get('was_correct'))
            ml_accuracy = (correct_predictions / len(ml_data)) * 100
        
        # Generate recommendation
        recommendation = 'MAINTAIN'
        reason = 'Entry criteria are working well'
        confidence = 0.7
        
        if win_rate < 45:
            recommendation = 'STRICTER'
            reason = 'Low win rate - tighten entry criteria'
            confidence = 0.9
        elif win_rate > 65:
            recommendation = 'MAINTAIN_OR_RELAX'
            reason = 'High win rate - current criteria excellent'
            confidence = 0.8
        
        # ML-specific recommendations
        ml_recommendation = None
        if ml_data and ml_accuracy < 50:
            ml_recommendation = 'Review ML model - accuracy below baseline'
        elif ml_data and ml_accuracy > 60:
            ml_recommendation = 'ML model performing well - trust predictions'
        
        return {
            'recommendation': recommendation,
            'reason': reason,
            'confidence': confidence,
            'ml_recommendation': ml_recommendation,
            'current_metrics': {
                'win_rate': round(win_rate, 1),
                'ml_accuracy': round(ml_accuracy, 1) if ml_data else None
            }
        }
    
    async def _recommend_risk_management(self, trades_data: List[Dict], positions_data: List[Dict]) -> Dict:
        """Recommend risk management adjustments"""
        if not trades_data:
            return {'recommendation': 'No data available', 'confidence': 0}
        
        # Calculate risk metrics
        total_pnl = sum(t.get('pnl', 0) for t in trades_data)
        
        # Calculate max drawdown
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
        
        # Analyze early exits
        early_exit_benefit = sum(p.get('exit_benefit', 0) for p in positions_data)
        
        # Generate recommendation
        recommendations = []
        
        if max_drawdown > 1000:
            recommendations.append('HIGH PRIORITY: Reduce position sizes - drawdown too large')
        elif max_drawdown > 500:
            recommendations.append('Monitor drawdown closely - approaching risk limits')
        
        if early_exit_benefit > 0:
            recommendations.append('Early exit system working well - continue using')
        elif len(positions_data) > 0 and early_exit_benefit < -200:
            recommendations.append('Review early exit criteria - may be exiting too early')
        
        if total_pnl < 0:
            recommendations.append('Negative P/L - consider reducing trading frequency')
        
        return {
            'recommendations': recommendations if recommendations else ['Risk management is appropriate'],
            'current_metrics': {
                'max_drawdown': round(max_drawdown, 2),
                'total_pnl': round(total_pnl, 2),
                'early_exit_benefit': round(early_exit_benefit, 2)
            }
        }
    
    def _determine_priority_actions(self, recommendations: Dict) -> List[str]:
        """Determine priority actions from all recommendations"""
        priority_actions = []
        
        # Check position sizing
        pos_sizing = recommendations.get('position_sizing', {})
        if pos_sizing.get('recommendation') == 'REDUCE' and pos_sizing.get('confidence', 0) > 0.8:
            priority_actions.append(f"🔴 URGENT: {pos_sizing.get('reason')}")
        
        # Check stop loss
        stop_loss = recommendations.get('stop_loss', {})
        if stop_loss.get('recommendation') == 'TIGHTEN' and stop_loss.get('confidence', 0) > 0.8:
            priority_actions.append(f"🟡 HIGH: {stop_loss.get('reason')}")
        
        # Check entry criteria
        entry = recommendations.get('entry_criteria', {})
        if entry.get('recommendation') == 'STRICTER' and entry.get('confidence', 0) > 0.8:
            priority_actions.append(f"🟡 HIGH: {entry.get('reason')}")
        
        # Check risk management
        risk_mgmt = recommendations.get('risk_management', {})
        risk_recs = risk_mgmt.get('recommendations', [])
        for rec in risk_recs:
            if 'HIGH PRIORITY' in rec:
                priority_actions.append(f"🔴 URGENT: {rec}")
        
        if not priority_actions:
            priority_actions.append("✅ No urgent actions required - continue current approach")
        
        return priority_actions
