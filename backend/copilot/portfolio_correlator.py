"""
Portfolio Correlator - Connects market events to portfolio positions.
"""

from typing import Any, Dict, List
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PortfolioCorrelator:
    """Correlates market events with portfolio positions and generates insights."""
    
    def correlate_news_to_portfolio(
        self,
        news: List[Dict],
        positions: List[Dict]
    ) -> Dict[str, Any]:
        """
        Maps news events to affected positions.
        
        Returns:
        {
            "affected_positions": [...],
            "sector_impact": {...},
            "portfolio_impact": "positive/negative/neutral"
        }
        """
        if not news or not positions:
            return {
                "affected_positions": [],
                "sector_impact": {},
                "portfolio_impact": "neutral"
            }
        
        affected = []
        position_symbols = {p["symbol"] for p in positions}
        
        for article in news:
            article_symbols = set(article.get("symbols", []))
            matching_symbols = article_symbols & position_symbols
            
            if matching_symbols:
                sentiment = article.get("sentiment", "neutral")
                for symbol in matching_symbols:
                    affected.append({
                        "symbol": symbol,
                        "headline": article.get("headline"),
                        "sentiment": sentiment,
                        "impact": self._sentiment_to_impact(sentiment),
                        "confidence": article.get("sentiment_confidence", 0.5)
                    })
        
        # Calculate overall portfolio impact
        if not affected:
            portfolio_impact = "neutral"
        else:
            impacts = [a["impact"] for a in affected]
            positive = sum(1 for i in impacts if i == "positive")
            negative = sum(1 for i in impacts if i == "negative")
            
            if positive > negative:
                portfolio_impact = "positive"
            elif negative > positive:
                portfolio_impact = "negative"
            else:
                portfolio_impact = "neutral"
        
        return {
            "affected_positions": affected,
            "sector_impact": self._calculate_sector_impact(affected, positions),
            "portfolio_impact": portfolio_impact
        }
    
    def calculate_market_portfolio_correlation(
        self,
        market_moves: Dict,
        portfolio_performance: Dict,
        positions: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculates how portfolio performed vs market.
        
        Returns correlation analysis and insights.
        """
        spy_return = market_moves.get("spy_return", 0)
        portfolio_return = portfolio_performance.get("daily_pl_pct", 0)
        
        if spy_return == 0:
            beta = 0
            alpha = portfolio_return
        else:
            beta = portfolio_return / spy_return
            alpha = portfolio_return - (beta * spy_return)
        
        # Generate explanation
        if beta > 1:
            beta_explanation = f"Portfolio captured {beta:.0%} of market move (high beta)"
        elif beta > 0.5:
            beta_explanation = f"Portfolio captured {beta:.0%} of market move (moderate beta)"
        else:
            beta_explanation = f"Portfolio captured {beta:.0%} of market move (low beta)"
        
        if alpha > 0:
            alpha_explanation = f"Outperformed market by {alpha:.2f}% (positive alpha)"
        elif alpha < 0:
            alpha_explanation = f"Underperformed market by {abs(alpha):.2f}% (negative alpha)"
        else:
            alpha_explanation = "Matched market performance"
        
        return {
            "market_return": spy_return,
            "portfolio_return": portfolio_return,
            "beta": beta,
            "alpha": alpha,
            "beta_explanation": beta_explanation,
            "alpha_explanation": alpha_explanation,
            "correlation_strength": "high" if abs(beta) > 0.8 else "moderate" if abs(beta) > 0.5 else "low"
        }
    
    def generate_portfolio_insights(
        self,
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable insights from portfolio context."""
        insights = []
        
        positions = context.get("position_details", [])
        account = context.get("account", {})
        risk_metrics = context.get("risk_metrics", {})
        recent_trades = context.get("recent_trades", [])
        
        # Cash deployment insight
        cash_pct = risk_metrics.get("cash_buffer_pct", 0)
        if cash_pct > 60:
            insights.append(f"💰 High cash reserves ({cash_pct:.0f}%) - consider deploying more capital")
        elif cash_pct < 20:
            insights.append(f"⚠️ Low cash reserves ({cash_pct:.0f}%) - limited buying power")
        
        # Concentration risk
        concentration = risk_metrics.get("concentration_risk", "low")
        largest_pct = risk_metrics.get("largest_position_pct", 0)
        if concentration == "high":
            insights.append(f"⚠️ High concentration risk - largest position is {largest_pct:.1f}% of portfolio")
        
        # Profit-taking opportunities
        profit_positions = [p for p in positions if p.get("recommendation") == "consider_profit_taking"]
        if profit_positions:
            symbols = ", ".join(p["symbol"] for p in profit_positions[:3])
            insights.append(f"🎯 Profit-taking opportunities: {symbols}")
        
        # Loss-cutting needs
        loss_positions = [p for p in positions if p.get("recommendation") == "consider_cutting_loss"]
        if loss_positions:
            symbols = ", ".join(p["symbol"] for p in loss_positions[:3])
            insights.append(f"✂️ Consider cutting losses: {symbols}")
        
        # Recent performance
        if recent_trades:
            wins = sum(1 for t in recent_trades if t.get("pnl", 0) > 0)
            total = len(recent_trades)
            recent_win_rate = (wins / total * 100) if total else 0
            insights.append(f"📊 Recent performance: {wins}/{total} wins ({recent_win_rate:.0f}% win rate)")
        
        # Sector exposure
        sector_exposure = context.get("sector_exposure", {})
        if sector_exposure:
            top_sector = max(sector_exposure.items(), key=lambda x: x[1])
            if top_sector[1] > 0.5:
                insights.append(f"⚠️ High {top_sector[0]} exposure ({top_sector[1]:.0%}) - consider diversifying")
        
        return insights

    @staticmethod
    def _sentiment_to_impact(sentiment: str) -> str:
        """Convert sentiment to impact."""
        sentiment_lower = sentiment.lower() if sentiment else "neutral"
        if "positive" in sentiment_lower or "bullish" in sentiment_lower:
            return "positive"
        elif "negative" in sentiment_lower or "bearish" in sentiment_lower:
            return "negative"
        return "neutral"
    
    @staticmethod
    def _calculate_sector_impact(affected: List[Dict], positions: List[Dict]) -> Dict[str, str]:
        """Calculate impact by sector."""
        # Simple implementation - can be enhanced
        sector_impacts = {}
        for item in affected:
            symbol = item["symbol"]
            impact = item["impact"]
            # Map symbol to sector (simplified)
            if symbol in ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "AMD"]:
                sector_impacts["technology"] = impact
            elif symbol in ["SPY", "QQQ", "DIA"]:
                sector_impacts["index"] = impact
        
        return sector_impacts

    @staticmethod
    def _minimal_context(query: str) -> Dict[str, Any]:
        return {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": "",
            "highlights": [],
        }
