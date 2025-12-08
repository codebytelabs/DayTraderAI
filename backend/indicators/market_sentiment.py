"""
Market Sentiment Analyzer - Quantify market fear/greed and sentiment.

Combines multiple sentiment indicators:
1. VIX (Fear Index)
2. Market Breadth (Advance/Decline)
3. Sector Rotation
4. Volume Trends
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta, timezone
from core.alpaca_client import AlpacaClient
from utils.logger import setup_logger
from alpaca.data.timeframe import TimeFrame
import pandas as pd

logger = setup_logger(__name__)


class MarketSentimentAnalyzer:
    """Analyze market sentiment from multiple sources."""
    
    def __init__(self, alpaca_client: AlpacaClient):
        self.alpaca = alpaca_client
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    def get_sentiment_score(self) -> Dict:
        """
        Get comprehensive market sentiment score (0-100).
        
        Returns:
            {
                'overall_score': 0-100 (0=extreme fear, 50=neutral, 100=extreme greed),
                'sentiment': 'extreme_fear' | 'fear' | 'neutral' | 'greed' | 'extreme_greed',
                'vix_score': 0-100,
                'breadth_score': 0-100,
                'sector_score': 0-100,
                'volume_score': 0-100,
                'components': {...},
                'recommendation': str
            }
        """
        # Check cache
        if self._is_cache_valid():
            return self.cache['sentiment']
        
        try:
            # Get individual components
            vix_score = self._get_vix_sentiment()
            breadth_score = self._get_market_breadth_sentiment()
            sector_score = self._get_sector_rotation_sentiment()
            volume_score = self._get_volume_sentiment()
            
            # Calculate weighted overall score
            weights = {
                'vix': 0.35,      # VIX is most important
                'breadth': 0.30,  # Market breadth is critical
                'sector': 0.20,   # Sector rotation matters
                'volume': 0.15    # Volume confirms moves
            }
            
            overall_score = (
                vix_score * weights['vix'] +
                breadth_score * weights['breadth'] +
                sector_score * weights['sector'] +
                volume_score * weights['volume']
            )
            
            # Classify sentiment
            sentiment = self._classify_sentiment(overall_score)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(overall_score, sentiment)
            
            result = {
                'overall_score': round(overall_score, 1),
                'sentiment': sentiment,
                'vix_score': round(vix_score, 1),
                'breadth_score': round(breadth_score, 1),
                'sector_score': round(sector_score, 1),
                'volume_score': round(volume_score, 1),
                'components': {
                    'vix': self.cache.get('vix_data', {}),
                    'breadth': self.cache.get('breadth_data', {}),
                    'sectors': self.cache.get('sector_data', {}),
                    'volume': self.cache.get('volume_data', {})
                },
                'recommendation': recommendation,
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache result
            self.cache['sentiment'] = result
            self.cache['timestamp'] = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating sentiment: {e}")
            return self._get_neutral_sentiment()
    
    def _get_vix_sentiment(self) -> float:
        """
        Get VIX-based sentiment score (0-100).
        
        VIX Interpretation:
        - <15: Extreme greed (100)
        - 15-20: Greed (75)
        - 20-25: Neutral (50)
        - 25-30: Fear (25)
        - >30: Extreme fear (0)
        """
        try:
            # Get VIX data
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=5)
            
            bars = self.alpaca.get_bars(
                symbols=['VIX'],
                timeframe=TimeFrame.Day,
                start=start,
                end=end
            )
            
            if bars is None or len(bars) == 0:
                logger.warning("No VIX data available")
                return 50.0  # Neutral
            
            # Get latest VIX value (bars is a DataFrame)
            latest_vix = float(bars.iloc[-1]['close'])
            
            # Calculate 5-day average for context
            vix_values = bars['close'].tolist()
            avg_vix = sum(vix_values) / len(vix_values)
            
            # Convert VIX to sentiment score (inverse relationship)
            if latest_vix < 15:
                score = 100  # Extreme greed
            elif latest_vix < 20:
                score = 75 + (20 - latest_vix) * 5  # 75-100
            elif latest_vix < 25:
                score = 50 + (25 - latest_vix) * 5  # 50-75
            elif latest_vix < 30:
                score = 25 + (30 - latest_vix) * 5  # 25-50
            else:
                score = max(0, 25 - (latest_vix - 30) * 2)  # 0-25
            
            self.cache['vix_data'] = {
                'current': latest_vix,
                'average_5d': round(avg_vix, 2),
                'trend': 'rising' if latest_vix > avg_vix else 'falling'
            }
            
            return score
            
        except Exception as e:
            logger.error(f"Error getting VIX sentiment: {e}")
            return 50.0  # Neutral on error
    
    def _get_market_breadth_sentiment(self) -> float:
        """
        Get market breadth sentiment (0-100).
        
        Analyzes how many stocks are participating in the move.
        """
        try:
            # Get data for major indices
            symbols = ['SPY', 'QQQ', 'IWM', 'DIA']
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=2)
            
            advancing = 0
            declining = 0
            
            for symbol in symbols:
                try:
                    bars = self.alpaca.get_bars(
                        symbols=[symbol],
                        timeframe=TimeFrame.Day,
                        start=start,
                        end=end
                    )
                    
                    if bars is not None and len(bars) >= 2:
                        today = float(bars.iloc[-1]['close'])
                        yesterday = float(bars.iloc[-2]['close'])
                        
                        if today > yesterday:
                            advancing += 1
                        else:
                            declining += 1
                except:
                    continue
            
            total = advancing + declining
            if total == 0:
                return 50.0
            
            # Calculate breadth score
            advance_pct = (advancing / total) * 100
            
            # Convert to sentiment score
            score = advance_pct
            
            self.cache['breadth_data'] = {
                'advancing': advancing,
                'declining': declining,
                'advance_pct': round(advance_pct, 1),
                'breadth': 'strong' if advance_pct > 75 else 'weak' if advance_pct < 25 else 'mixed'
            }
            
            return score
            
        except Exception as e:
            logger.error(f"Error getting breadth sentiment: {e}")
            return 50.0
    
    def _get_sector_rotation_sentiment(self) -> float:
        """
        Get sector rotation sentiment (0-100).
        
        Analyzes which sectors are leading (defensive vs growth).
        """
        try:
            # Sector ETFs
            growth_sectors = ['XLK', 'XLY']  # Tech, Consumer Discretionary
            defensive_sectors = ['XLU', 'XLP']  # Utilities, Consumer Staples
            
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=5)
            
            growth_performance = []
            defensive_performance = []
            
            # Calculate growth sector performance
            for symbol in growth_sectors:
                try:
                    bars = self.alpaca.get_bars(
                        symbols=[symbol],
                        timeframe=TimeFrame.Day,
                        start=start,
                        end=end
                    )
                    
                    if bars is not None and len(bars) >= 2:
                        perf = ((float(bars.iloc[-1]['close']) / float(bars.iloc[0]['close'])) - 1) * 100
                        growth_performance.append(perf)
                except:
                    continue
            
            # Calculate defensive sector performance
            for symbol in defensive_sectors:
                try:
                    bars = self.alpaca.get_bars(
                        symbols=[symbol],
                        timeframe=TimeFrame.Day,
                        start=start,
                        end=end
                    )
                    
                    if bars is not None and len(bars) >= 2:
                        perf = ((float(bars.iloc[-1]['close']) / float(bars.iloc[0]['close'])) - 1) * 100
                        defensive_performance.append(perf)
                except:
                    continue
            
            if not growth_performance or not defensive_performance:
                return 50.0
            
            avg_growth = sum(growth_performance) / len(growth_performance)
            avg_defensive = sum(defensive_performance) / len(defensive_performance)
            
            # Growth outperforming = bullish sentiment
            # Defensive outperforming = bearish sentiment
            if avg_growth > avg_defensive:
                # Growth leading = bullish
                diff = avg_growth - avg_defensive
                score = 50 + min(diff * 10, 50)  # 50-100
            else:
                # Defensive leading = bearish
                diff = avg_defensive - avg_growth
                score = 50 - min(diff * 10, 50)  # 0-50
            
            self.cache['sector_data'] = {
                'growth_performance': round(avg_growth, 2),
                'defensive_performance': round(avg_defensive, 2),
                'rotation': 'growth' if avg_growth > avg_defensive else 'defensive'
            }
            
            return score
            
        except Exception as e:
            logger.error(f"Error getting sector sentiment: {e}")
            return 50.0
    
    def _get_volume_sentiment(self) -> float:
        """
        Get volume-based sentiment (0-100).
        
        High volume on up days = bullish
        High volume on down days = bearish
        """
        try:
            # Analyze SPY volume
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=10)
            
            bars = self.alpaca.get_bars(
                symbols=['SPY'],
                timeframe=TimeFrame.Day,
                start=start,
                end=end
            )
            
            if bars is None or len(bars) < 5:
                return 50.0
            
            # Calculate average volume (bars is a DataFrame)
            volumes = bars['volume'].tolist()
            avg_volume = sum(volumes) / len(volumes)
            
            # Analyze recent days
            up_volume = 0
            down_volume = 0
            
            for i in range(1, min(5, len(bars))):
                today_close = float(bars.iloc[i]['close'])
                yesterday_close = float(bars.iloc[i-1]['close'])
                volume = float(bars.iloc[i]['volume'])
                
                if today_close > yesterday_close:
                    up_volume += volume
                else:
                    down_volume += volume
            
            total_volume = up_volume + down_volume
            if total_volume == 0:
                return 50.0
            
            # Calculate score
            up_volume_pct = (up_volume / total_volume) * 100
            score = up_volume_pct
            
            latest_volume = float(bars.iloc[-1]['volume'])
            volume_trend = 'high' if latest_volume > avg_volume * 1.2 else 'low' if latest_volume < avg_volume * 0.8 else 'normal'
            
            self.cache['volume_data'] = {
                'up_volume_pct': round(up_volume_pct, 1),
                'latest_volume': int(latest_volume),
                'average_volume': int(avg_volume),
                'trend': volume_trend
            }
            
            return score
            
        except Exception as e:
            logger.error(f"Error getting volume sentiment: {e}")
            return 50.0
    
    def _classify_sentiment(self, score: float) -> str:
        """Classify sentiment based on score."""
        if score >= 80:
            return 'extreme_greed'
        elif score >= 60:
            return 'greed'
        elif score >= 40:
            return 'neutral'
        elif score >= 20:
            return 'fear'
        else:
            return 'extreme_fear'
    
    def _generate_recommendation(self, score: float, sentiment: str) -> str:
        """Generate trading recommendation based on sentiment."""
        if sentiment == 'extreme_greed':
            return "Caution: Market may be overbought. Consider taking profits or reducing position sizes."
        elif sentiment == 'greed':
            return "Bullish sentiment. Good environment for long positions with proper risk management."
        elif sentiment == 'neutral':
            return "Mixed sentiment. Trade both directions based on technical setups."
        elif sentiment == 'fear':
            return "Bearish sentiment. Consider short positions or wait for better entry points."
        else:  # extreme_fear
            return "Opportunity: Extreme fear often marks bottoms. Look for oversold bounce plays."
    
    def _is_cache_valid(self) -> bool:
        """Check if cached sentiment is still valid."""
        if 'sentiment' not in self.cache or 'timestamp' not in self.cache:
            return False
        
        age = (datetime.now() - self.cache['timestamp']).total_seconds()
        return age < self.cache_duration
    
    def _get_neutral_sentiment(self) -> Dict:
        """Return neutral sentiment on error."""
        return {
            'overall_score': 50.0,
            'sentiment': 'neutral',
            'vix_score': 50.0,
            'breadth_score': 50.0,
            'sector_score': 50.0,
            'volume_score': 50.0,
            'components': {},
            'recommendation': 'Unable to determine sentiment. Trade with caution.',
            'timestamp': datetime.now().isoformat()
        }


# Singleton instance
_sentiment_analyzer = None

def get_sentiment_analyzer(alpaca_client: AlpacaClient) -> MarketSentimentAnalyzer:
    """Get or create sentiment analyzer instance."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = MarketSentimentAnalyzer(alpaca_client)
    return _sentiment_analyzer