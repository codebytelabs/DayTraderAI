"""
Sentiment Aggregator - Dual-Source Validation System
Combines multiple sentiment sources for reliability and accuracy.
"""

from typing import Dict, Optional
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SentimentAggregator:
    """Aggregate sentiment from multiple sources with failover."""
    
    def __init__(self, alpaca_client, ai_opportunity_finder=None):
        self.alpaca = alpaca_client
        self.ai_finder = ai_opportunity_finder
        
        # Track source reliability
        self.source_stats = {
            'perplexity': {'attempts': 0, 'successes': 0, 'failures': 0},
            'vix': {'attempts': 0, 'successes': 0, 'failures': 0}
        }
        
        logger.info("Sentiment Aggregator initialized with dual-source validation")
    
    def get_sentiment(self) -> Dict:
        """
        Get sentiment with automatic failover.
        
        Returns:
            dict: {
                'score': int (0-100),
                'classification': str,
                'source': str,
                'confidence': str,
                'timestamp': str
            }
        """
        
        # Primary: Multi-source Fear & Greed Index (most reliable)
        sentiment = self._get_vix_sentiment()  # Note: Despite name, this fetches Fear & Greed Index
        if sentiment and self._is_valid_sentiment(sentiment):
            self.source_stats['vix']['successes'] += 1
            # Only log at debug level to reduce noise
            logger.debug(f"✅ Using Fear & Greed Index: {sentiment['score']}/100")
            return sentiment
        
        self.source_stats['vix']['failures'] += 1
        
        # Fallback: Try Perplexity if available (from recent AI scan)
        sentiment = self._get_perplexity_sentiment()
        if sentiment and self._is_valid_sentiment(sentiment):
            self.source_stats['perplexity']['successes'] += 1
            logger.info(f"✅ Using Perplexity sentiment: {sentiment['score']}/100")
            return sentiment
        
        self.source_stats['perplexity']['failures'] += 1
        logger.warning("⚠️  All sentiment sources unavailable, using neutral default")
        
        # Final fallback: Neutral
        return {
            'score': 50,
            'classification': 'neutral',
            'source': 'default',
            'confidence': 'low',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_perplexity_sentiment(self) -> Optional[Dict]:
        """Get sentiment from Perplexity AI (via opportunity finder)."""
        try:
            self.source_stats['perplexity']['attempts'] += 1
            
            if not self.ai_finder:
                return None
            
            sentiment = self.ai_finder.get_current_sentiment()
            
            if not sentiment or sentiment['score'] == 50:
                # No data or default value
                return None
            
            return {
                'score': sentiment['score'],
                'classification': sentiment['classification'],
                'source': 'perplexity',
                'confidence': 'high',
                'timestamp': sentiment['timestamp']
            }
            
        except Exception as e:
            logger.error(f"Error getting Perplexity sentiment: {e}")
            return None
    
    def _get_vix_sentiment(self) -> Optional[Dict]:
        """
        Get sentiment from Fear & Greed Index (replacing VIX)
        Uses web scraping from reliable sources
        
        Returns:
            dict: Sentiment data or None if failed
        """
        try:
            self.source_stats['vix']['attempts'] += 1
            
            from indicators.fear_greed_scraper import FearGreedScraper
            
            scraper = FearGreedScraper()
            result = scraper.get_fear_greed_index()
            
            if not result.get('success'):
                logger.debug("Fear & Greed Index not available")
                return None
            
            score = result['score']
            classification = result['classification']
            
            logger.debug(f"Fear & Greed sentiment: {score}/100 ({classification}) from {result['source']}")
            
            return {
                'score': score,
                'classification': classification,
                'source': 'fear_greed_index',
                'confidence': 'high',
                'fear_greed_score': score,
                'timestamp': result['timestamp']
            }
            
        except Exception as e:
            logger.debug(f"Fear & Greed sentiment failed: {e}")
            return None
    
    def _vix_to_fear_greed(self, vix_value: float) -> tuple:
        """
        Convert VIX to Fear & Greed scale.
        
        VIX Interpretation:
        - <12: Extreme Greed (complacency)
        - 12-15: Greed
        - 15-20: Neutral
        - 20-30: Fear
        - >30: Extreme Fear (panic)
        
        Returns:
            tuple: (score, classification)
        """
        
        if vix_value < 12:
            return (85, 'extreme_greed')
        elif vix_value < 15:
            return (70, 'greed')
        elif vix_value < 20:
            return (50, 'neutral')
        elif vix_value < 30:
            return (30, 'fear')
        else:
            return (15, 'extreme_fear')
    
    def _is_valid_sentiment(self, sentiment: Dict) -> bool:
        """Validate sentiment data."""
        if not sentiment:
            return False
        
        score = sentiment.get('score')
        if score is None or not (0 <= score <= 100):
            return False
        
        classification = sentiment.get('classification')
        if not classification:
            return False
        
        return True
    
    def get_source_stats(self) -> Dict:
        """Get reliability statistics for each source."""
        stats = {}
        
        for source, data in self.source_stats.items():
            attempts = data['attempts']
            successes = data['successes']
            
            if attempts > 0:
                success_rate = (successes / attempts) * 100
            else:
                success_rate = 0
            
            stats[source] = {
                'attempts': attempts,
                'successes': successes,
                'failures': data['failures'],
                'success_rate': f"{success_rate:.1f}%"
            }
        
        return stats
    
    def get_sentiment_strategy(self, sentiment_score: int) -> Dict:
        """
        Get trading strategy recommendations based on sentiment.
        
        Returns:
            dict: {
                'allowed_caps': dict,
                'target_long_pct': float,
                'position_size_mult': float,
                'strategy': str
            }
        """
        
        if sentiment_score <= 25:  # Extreme Fear
            return {
                'allowed_caps': {
                    'large_caps': True,
                    'mid_caps': False,
                    'small_caps': False
                },
                'target_long_pct': 0.75,  # 75% long, 25% short
                'position_size_mult': 1.0,  # ✅ Extreme fear = contrarian buying opportunity (was 0.70)
                'strategy': 'Contrarian long bias - Focus large-caps only',
                'rationale': 'Extreme fear = buying opportunity, normal position sizing'
            }
        
        elif sentiment_score <= 45:  # Fear
            return {
                'allowed_caps': {
                    'large_caps': True,
                    'mid_caps': True,
                    'small_caps': False
                },
                'target_long_pct': 0.60,  # 60% long, 40% short
                'position_size_mult': 0.80,
                'strategy': 'Slight long bias - Large + selective mid-caps',
                'rationale': 'Fear = cautious buying, avoid small caps'
            }
        
        elif sentiment_score <= 54:  # Neutral
            return {
                'allowed_caps': {
                    'large_caps': True,
                    'mid_caps': True,
                    'small_caps': True
                },
                'target_long_pct': 0.50,  # 50/50
                'position_size_mult': 1.00,
                'strategy': 'Balanced - All market caps',
                'rationale': 'Neutral = normal trading conditions'
            }
        
        elif sentiment_score <= 75:  # Greed
            return {
                'allowed_caps': {
                    'large_caps': True,
                    'mid_caps': True,
                    'small_caps': True
                },
                'target_long_pct': 0.40,  # 40% long, 60% short
                'position_size_mult': 0.80,
                'strategy': 'Short bias - Profit taking, favor shorts',
                'rationale': 'Greed = take profits, prepare for reversal'
            }
        
        else:  # Extreme Greed (76-100)
            return {
                'allowed_caps': {
                    'large_caps': True,
                    'mid_caps': True,
                    'small_caps': False  # Avoid small-cap longs
                },
                'target_long_pct': 0.25,  # 25% long, 75% short
                'position_size_mult': 0.70,
                'strategy': 'Contrarian short bias - Focus large-cap shorts',
                'rationale': 'Extreme greed = bubble territory, prepare for crash'
            }


# Singleton instance
_sentiment_aggregator = None

def get_sentiment_aggregator(alpaca_client, ai_opportunity_finder=None):
    """Get singleton sentiment aggregator instance."""
    global _sentiment_aggregator
    if _sentiment_aggregator is None:
        _sentiment_aggregator = SentimentAggregator(alpaca_client, ai_opportunity_finder)
    return _sentiment_aggregator
