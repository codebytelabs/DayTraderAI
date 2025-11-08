"""
Pattern Detector
Detects trading patterns and market conditions
"""

import logging
from typing import Dict, Any, List
from datetime import date, timedelta
from collections import Counter

logger = logging.getLogger(__name__)


class PatternDetector:
    """
    Detects patterns in trading data
    
    Features:
    - Win/loss streaks
    - Time-based patterns
    - Symbol performance patterns
    - Market regime correlations
    - Entry/exit timing patterns
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        logger.info("Pattern Detector initialized")
    
    async def detect_patterns(self, trades_data: List[Dict], report_date: date) -> Dict[str, Any]:
        """Detect all patterns in trading data"""
        try:
            patterns = {
                'streak_patterns': await self._detect_streak_patterns(trades_data, report_date),
                'time_patterns': await self._detect_time_patterns(trades_data),
                'symbol_patterns': await self._detect_symbol_patterns(trades_data, report_date),
                'regime_patterns': await self._detect_regime_patterns(trades_data),
                'entry_exit_patterns': await self._detect_entry_exit_patterns(trades_data)
            }
            
            patterns['summary'] = self._generate_pattern_summary(patterns)
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return {'error': str(e)}
    
    async def _detect_streak_patterns(self, trades_data: List[Dict], report_date: date) -> Dict:
        """Detect win/loss streak patterns"""
        if not trades_data:
            return {'current_streak': 0, 'type': 'none'}
        
        # Sort trades by time
        sorted_trades = sorted(trades_data, key=lambda x: x.get('entry_time', ''))
        
        # Calculate current streak
        current_streak = 0
        streak_type = 'none'
        last_outcome = None
        
        for trade in sorted_trades:
            pnl = trade.get('pnl', 0)
            outcome = 'win' if pnl > 0 else 'loss'
            
            if last_outcome is None or outcome == last_outcome:
                current_streak += 1
                last_outcome = outcome
            else:
                break
        
        streak_type = last_outcome if last_outcome else 'none'
        
        return {
            'current_streak': current_streak,
            'type': streak_type,
            'recommendation': self._get_streak_recommendation(current_streak, streak_type)
        }
    
    async def _detect_time_patterns(self, trades_data: List[Dict]) -> Dict:
        """Detect time-based trading patterns"""
        if not trades_data:
            return {'message': 'No trades to analyze'}
        
        hour_performance = {}
        
        for trade in trades_data:
            if trade.get('entry_time'):
                from datetime import datetime
                entry_dt = datetime.fromisoformat(trade['entry_time'].replace('Z', '+00:00'))
                hour = entry_dt.hour
                
                if hour not in hour_performance:
                    hour_performance[hour] = {'trades': 0, 'pnl': 0, 'wins': 0}
                
                hour_performance[hour]['trades'] += 1
                hour_performance[hour]['pnl'] += trade.get('pnl', 0)
                if trade.get('pnl', 0) > 0:
                    hour_performance[hour]['wins'] += 1
        
        # Find best and worst hours
        best_hour = max(hour_performance.items(), key=lambda x: x[1]['pnl'])[0] if hour_performance else None
        worst_hour = min(hour_performance.items(), key=lambda x: x[1]['pnl'])[0] if hour_performance else None
        
        return {
            'hourly_performance': hour_performance,
            'best_hour': best_hour,
            'worst_hour': worst_hour,
            'recommendations': self._get_time_recommendations(hour_performance)
        }
    
    async def _detect_symbol_patterns(self, trades_data: List[Dict], report_date: date) -> Dict:
        """Detect symbol-specific patterns"""
        if not trades_data:
            return {'message': 'No trades to analyze'}
        
        symbol_performance = {}
        
        for trade in trades_data:
            symbol = trade.get('symbol')
            if symbol:
                if symbol not in symbol_performance:
                    symbol_performance[symbol] = {'trades': 0, 'pnl': 0, 'wins': 0}
                
                symbol_performance[symbol]['trades'] += 1
                pnl = trade.get('pnl', 0)
                symbol_performance[symbol]['pnl'] += pnl
                if pnl > 0:
                    symbol_performance[symbol]['wins'] += 1
        
        # Calculate win rates
        for symbol, data in symbol_performance.items():
            data['win_rate'] = (data['wins'] / data['trades']) * 100 if data['trades'] > 0 else 0
        
        # Sort by performance
        sorted_symbols = sorted(symbol_performance.items(), key=lambda x: x[1]['pnl'], reverse=True)
        
        return {
            'symbol_performance': symbol_performance,
            'best_performers': sorted_symbols[:3] if len(sorted_symbols) >= 3 else sorted_symbols,
            'worst_performers': sorted_symbols[-3:] if len(sorted_symbols) >= 3 else []
        }
    
    async def _detect_regime_patterns(self, trades_data: List[Dict]) -> Dict:
        """Detect market regime correlation patterns"""
        regime_performance = {}
        
        for trade in trades_data:
            # Get regime from trade features if available
            regime = trade.get('regime', 'unknown')
            
            if regime not in regime_performance:
                regime_performance[regime] = {'trades': 0, 'pnl': 0, 'wins': 0}
            
            regime_performance[regime]['trades'] += 1
            pnl = trade.get('pnl', 0)
            regime_performance[regime]['pnl'] += pnl
            if pnl > 0:
                regime_performance[regime]['wins'] += 1
        
        # Calculate win rates
        for regime, data in regime_performance.items():
            data['win_rate'] = (data['wins'] / data['trades']) * 100 if data['trades'] > 0 else 0
        
        return {
            'regime_performance': regime_performance,
            'best_regime': max(regime_performance.items(), key=lambda x: x[1]['pnl'])[0] if regime_performance else None
        }
    
    async def _detect_entry_exit_patterns(self, trades_data: List[Dict]) -> Dict:
        """Detect entry and exit timing patterns"""
        if not trades_data:
            return {'message': 'No trades to analyze'}
        
        hold_times = []
        
        for trade in trades_data:
            if trade.get('entry_time') and trade.get('exit_time'):
                from datetime import datetime
                entry_dt = datetime.fromisoformat(trade['entry_time'].replace('Z', '+00:00'))
                exit_dt = datetime.fromisoformat(trade['exit_time'].replace('Z', '+00:00'))
                hold_time_minutes = (exit_dt - entry_dt).seconds // 60
                hold_times.append({
                    'hold_time': hold_time_minutes,
                    'pnl': trade.get('pnl', 0)
                })
        
        if hold_times:
            avg_hold_time = sum(h['hold_time'] for h in hold_times) / len(hold_times)
            
            return {
                'avg_hold_time_minutes': round(avg_hold_time, 1),
                'total_analyzed': len(hold_times),
                'recommendation': self._get_hold_time_recommendation(avg_hold_time)
            }
        
        return {'message': 'No hold time data available'}
    
    def _get_streak_recommendation(self, streak: int, streak_type: str) -> str:
        """Get recommendation based on streak"""
        if streak >= 5:
            if streak_type == 'win':
                return 'Strong winning streak - maintain discipline, avoid overconfidence'
            else:
                return 'Significant losing streak - consider reducing position size or taking a break'
        elif streak >= 3:
            if streak_type == 'win':
                return 'Good momentum - stay focused on process'
            else:
                return 'Losing streak developing - review recent trades for patterns'
        return 'Normal trading pattern'
    
    def _get_time_recommendations(self, hour_performance: Dict) -> List[str]:
        """Get time-based recommendations"""
        recommendations = []
        
        if not hour_performance:
            return recommendations
        
        # Find consistently profitable hours
        profitable_hours = [h for h, data in hour_performance.items() if data['pnl'] > 0 and data['trades'] >= 2]
        if profitable_hours:
            recommendations.append(f"Focus trading during hours: {', '.join(map(str, profitable_hours))}")
        
        # Find consistently unprofitable hours
        unprofitable_hours = [h for h, data in hour_performance.items() if data['pnl'] < 0 and data['trades'] >= 2]
        if unprofitable_hours:
            recommendations.append(f"Avoid or reduce trading during hours: {', '.join(map(str, unprofitable_hours))}")
        
        return recommendations
    
    def _get_hold_time_recommendation(self, avg_hold_time: float) -> str:
        """Get hold time recommendation"""
        if avg_hold_time < 5:
            return 'Very short hold times - consider if entries are premature'
        elif avg_hold_time < 15:
            return 'Short hold times - good for scalping strategy'
        elif avg_hold_time < 45:
            return 'Medium hold times - balanced approach'
        else:
            return 'Long hold times - consider tighter exit criteria'
    
    def _generate_pattern_summary(self, patterns: Dict) -> str:
        """Generate summary of detected patterns"""
        summary_parts = []
        
        # Streak summary
        streak = patterns.get('streak_patterns', {})
        if streak.get('current_streak', 0) >= 3:
            summary_parts.append(f"{streak['current_streak']} {streak['type']} streak")
        
        # Time summary
        time_patterns = patterns.get('time_patterns', {})
        if time_patterns.get('best_hour'):
            summary_parts.append(f"Best hour: {time_patterns['best_hour']}:00")
        
        # Symbol summary
        symbol_patterns = patterns.get('symbol_patterns', {})
        best_performers = symbol_patterns.get('best_performers', [])
        if best_performers:
            summary_parts.append(f"Top symbol: {best_performers[0][0]}")
        
        return ' | '.join(summary_parts) if summary_parts else 'No significant patterns detected'
