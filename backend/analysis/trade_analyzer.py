"""
Trade Analyzer
Analyzes individual trades with AI insights
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TradeAnalyzer:
    """
    Analyzes individual trades and provides insights
    """
    
    def __init__(self, supabase_client, perplexity_client=None):
        self.supabase = supabase_client
        self.perplexity = perplexity_client
        logger.info("Trade Analyzer initialized")
    
    async def analyze_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single trade
        
        Args:
            trade: Trade data from database
            
        Returns:
            dict: Trade analysis with insights
        """
        analysis = {
            'trade_id': trade.get('id'),
            'symbol': trade['symbol'],
            'pnl': trade['pnl'],
            'outcome': 'win' if trade['pnl'] > 0 else 'loss',
            'insights': []
        }
        
        # Basic analysis
        if trade['pnl'] > 0:
            analysis['insights'].append(f"Profitable trade: +${trade['pnl']:.2f}")
        else:
            analysis['insights'].append(f"Loss: ${trade['pnl']:.2f}")
        
        # Hold time analysis
        if 'hold_duration_seconds' in trade:
            hold_minutes = trade['hold_duration_seconds'] / 60
            analysis['hold_time_minutes'] = hold_minutes
            
            if hold_minutes < 5:
                analysis['insights'].append("Quick scalp - held less than 5 minutes")
            elif hold_minutes > 60:
                analysis['insights'].append("Long hold - held over 1 hour")
        
        # Strategy analysis
        if 'strategy' in trade:
            analysis['strategy'] = trade['strategy']
            analysis['insights'].append(f"Strategy: {trade['strategy']}")
        
        # AI insights if available
        if self.perplexity:
            ai_insight = await self._get_ai_insight(trade)
            if ai_insight:
                analysis['ai_insight'] = ai_insight
        
        return analysis
    
    async def _get_ai_insight(self, trade: Dict[str, Any]) -> Optional[str]:
        """Get AI-powered insight for trade"""
        try:
            # This would call Perplexity API for deeper analysis
            # For now, return None
            return None
        except Exception as e:
            logger.error(f"Error getting AI insight: {e}")
            return None
