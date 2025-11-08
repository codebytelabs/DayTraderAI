"""
Daily Report Generator
Generates comprehensive daily trading reports
"""

import logging
from typing import Dict, Any, List
from datetime import date, datetime, timedelta
import json

from .trade_analyzer import TradeAnalyzer
from .pattern_detector import PatternDetector
from .recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class DailyReportGenerator:
    """
    Generates comprehensive daily trading reports
    
    Report sections:
    1. Executive Summary
    2. Trade-by-Trade Analysis
    3. Missed Opportunities
    4. System Performance
    5. Parameter Recommendations
    6. Market Regime Analysis
    7. Risk Metrics
    8. Next Day Suggestions
    """
    
    def __init__(self, supabase_client, perplexity_client=None):
        self.supabase = supabase_client
        self.perplexity = perplexity_client
        self.trade_analyzer = TradeAnalyzer(supabase_client, perplexity_client)
        self.pattern_detector = PatternDetector(supabase_client)
        self.recommendation_engine = RecommendationEngine(supabase_client)
        logger.info("Daily Report Generator initialized")
    
    async def generate_daily_report(self, report_date: date = None) -> Dict[str, Any]:
        """
        Generate complete daily report
        
        Args:
            report_date: Date to generate report for (defaults to today)
            
        Returns:
            dict: Complete daily report
        """
        if report_date is None:
            report_date = date.today()
        
        logger.info(f"Generating daily report for {report_date}")
        
        report = {
            'date': report_date.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'sections': {}
        }
        
        # Section 1: Executive Summary
        report['sections']['executive_summary'] = await self._generate_executive_summary(report_date)
        
        # Section 2: Trade Analysis
        report['sections']['trade_analysis'] = await self._generate_trade_analysis(report_date)
        
        # Section 3: Missed Opportunities
        report['sections']['missed_opportunities'] = await self._generate_missed_opportunities(report_date)
        
        # Section 4: System Performance
        report['sections']['system_performance'] = await self._generate_system_performance(report_date)
        
        # Section 5: Parameter Recommendations
        report['sections']['recommendations'] = await self._generate_recommendations(report_date)
        
        # Section 6: Market Regime Analysis
        report['sections']['market_analysis'] = await self._generate_market_analysis(report_date)
        
        # Section 7: Risk Metrics
        report['sections']['risk_metrics'] = await self._generate_risk_metrics(report_date)
        
        # Section 8: Next Day Suggestions
        report['sections']['next_day'] = await self._generate_next_day_suggestions(report_date)
        
        # Save report
        await self._save_report(report)
        
        logger.info(f"Daily report generated for {report_date}")
        return report
    
    async def _generate_executive_summary(self, report_date: date) -> Dict[str, Any]:
        """Generate executive summary"""
        # Get today's trades
        trades = await self._get_trades_for_date(report_date)
        
        if not trades:
            return {
                'total_trades': 0,
                'pnl': 0.0,
                'win_rate': 0.0,
                'grade': 'N/A'
            }
        
        total_pnl = sum(t['pnl'] for t in trades)
        wins = sum(1 for t in trades if t['pnl'] > 0)
        win_rate = (wins / len(trades)) * 100
        
        # Calculate grade
        if win_rate >= 60 and total_pnl > 1000:
            grade = 'A+'
        elif win_rate >= 55 and total_pnl > 500:
            grade = 'A'
        elif win_rate >= 50 and total_pnl > 0:
            grade = 'B'
        elif total_pnl > 0:
            grade = 'C'
        else:
            grade = 'D'
        
        return {
            'total_trades': len(trades),
            'winning_trades': wins,
            'losing_trades': len(trades) - wins,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl_per_trade': total_pnl / len(trades),
            'best_trade': max(trades, key=lambda t: t['pnl'])['pnl'],
            'worst_trade': min(trades, key=lambda t: t['pnl'])['pnl'],
            'grade': grade
        }
    
    async def _generate_trade_analysis(self, report_date: date) -> List[Dict[str, Any]]:
        """Generate trade-by-trade analysis"""
        trades = await self._get_trades_for_date(report_date)
        
        analyses = []
        for trade in trades:
            analysis = await self.trade_analyzer.analyze_trade(trade)
            analyses.append(analysis)
        
        return analyses
    
    async def _generate_missed_opportunities(self, report_date: date) -> Dict[str, Any]:
        """Analyze missed opportunities"""
        # Get opportunities that weren't taken
        opps = await self.pattern_detector.find_missed_opportunities(report_date)
        
        return {
            'count': len(opps),
            'opportunities': opps[:10],  # Top 10
            'total_potential_pnl': sum(o.get('potential_pnl', 0) for o in opps)
        }
    
    async def _generate_system_performance(self, report_date: date) -> Dict[str, Any]:
        """Generate system performance metrics"""
        trades = await self._get_trades_for_date(report_date)
        
        if not trades:
            return {}
        
        # Calculate metrics
        hold_times = [t.get('hold_duration_seconds', 0) / 60 for t in trades]
        
        return {
            'avg_hold_time_minutes': sum(hold_times) / len(hold_times) if hold_times else 0,
            'total_volume_traded': sum(t['qty'] for t in trades),
            'strategies_used': list(set(t.get('strategy', 'unknown') for t in trades)),
            'symbols_traded': list(set(t['symbol'] for t in trades))
        }
    
    async def _generate_recommendations(self, report_date: date) -> List[str]:
        """Generate parameter recommendations"""
        return await self.recommendation_engine.generate_recommendations(report_date)
    
    async def _generate_market_analysis(self, report_date: date) -> Dict[str, Any]:
        """Analyze market conditions"""
        return await self.pattern_detector.analyze_market_conditions(report_date)
    
    async def _generate_risk_metrics(self, report_date: date) -> Dict[str, Any]:
        """Calculate risk metrics"""
        trades = await self._get_trades_for_date(report_date)
        
        if not trades:
            return {}
        
        pnls = [t['pnl'] for t in trades]
        
        return {
            'max_drawdown': min(pnls) if pnls else 0,
            'max_profit': max(pnls) if pnls else 0,
            'volatility': self._calculate_std(pnls),
            'sharpe_estimate': self._calculate_sharpe(pnls)
        }
    
    async def _generate_next_day_suggestions(self, report_date: date) -> List[str]:
        """Generate suggestions for next trading day"""
        suggestions = []
        
        # Analyze recent performance
        trades = await self._get_trades_for_date(report_date)
        
        if trades:
            win_rate = sum(1 for t in trades if t['pnl'] > 0) / len(trades)
            
            if win_rate < 0.45:
                suggestions.append("Consider reducing position sizes - win rate below 45%")
            elif win_rate > 0.60:
                suggestions.append("Consider increasing position sizes - win rate above 60%")
            
            avg_pnl = sum(t['pnl'] for t in trades) / len(trades)
            if avg_pnl < 0:
                suggestions.append("Review entry criteria - average P/L negative")
        
        return suggestions
    
    async def _get_trades_for_date(self, report_date: date) -> List[Dict[str, Any]]:
        """Get all trades for a specific date"""
        try:
            result = self.supabase.table('trades').select('*').gte(
                'timestamp', report_date.isoformat()
            ).lt(
                'timestamp', (report_date + timedelta(days=1)).isoformat()
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            return []
    
    async def _save_report(self, report: Dict[str, Any]):
        """Save report to database"""
        try:
            # Create reports table if needed (add to migration)
            self.supabase.table('daily_reports').insert({
                'date': report['date'],
                'generated_at': report['generated_at'],
                'report_data': json.dumps(report)
            }).execute()
        except Exception as e:
            logger.warning(f"Could not save report: {e}")
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _calculate_sharpe(self, pnls: List[float]) -> float:
        """Calculate Sharpe ratio estimate"""
        if not pnls or len(pnls) < 2:
            return 0.0
        
        mean_return = sum(pnls) / len(pnls)
        std_return = self._calculate_std(pnls)
        
        if std_return == 0:
            return 0.0
        
        return (mean_return / std_return) * (252 ** 0.5)  # Annualized
    
    def format_report_markdown(self, report: Dict[str, Any]) -> str:
        """Format report as markdown"""
        md = f"# Daily Trading Report - {report['date']}\n\n"
        
        # Executive Summary
        summary = report['sections']['executive_summary']
        md += "## Executive Summary\n\n"
        md += f"- **Total Trades**: {summary['total_trades']}\n"
        md += f"- **Win Rate**: {summary['win_rate']:.1f}%\n"
        md += f"- **Total P/L**: ${summary['total_pnl']:.2f}\n"
        md += f"- **Grade**: {summary['grade']}\n\n"
        
        # Add other sections...
        
        return md
