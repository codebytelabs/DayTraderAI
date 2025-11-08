"""Opportunity Scorer - 120-point scoring system for stock opportunities.

Scores stocks based on:
- Technical setup (40 points)
- Momentum (25 points)
- Volume (20 points)
- Volatility (15 points)
- Market regime (10 points)
- Market sentiment (10 points) ← NEW
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


class OpportunityScorer:
    """Score stock opportunities on a 0-120 scale (includes sentiment)."""
    
    def __init__(self, sentiment_analyzer=None):
        """Initialize with optional sentiment analyzer."""
        self.sentiment_analyzer = sentiment_analyzer
        self._sentiment_cache = None
    
    @staticmethod
    def score_technical_setup(features: Dict) -> float:
        """
        Score technical setup (0-40 points).
        
        Simplified: Any reasonable technical setup gets good points.
        """
        score = 0.0
        
        try:
            # EMA alignment (15 points) - much more permissive
            ema_diff_pct = abs(features.get('ema_diff_pct', 0))
            if ema_diff_pct > 0.05:  # Any trend at all
                score += 15
            else:
                score += 10  # Even flat is okay
            
            # RSI position (10 points) - not oversold/overbought is good
            rsi = features.get('rsi', 50)
            if 25 <= rsi <= 75:  # Reasonable range
                score += 10
            elif 20 <= rsi <= 80:
                score += 7
            else:
                score += 5  # Even extreme RSI can work
            
            # MACD strength (10 points) - any signal is good
            macd_histogram = abs(features.get('macd_histogram', 0))
            if macd_histogram > 0.01:  # Any momentum
                score += 10
            else:
                score += 7  # Even no momentum is tradeable
            
            # VWAP position (5 points) - always give points
            score += 5  # VWAP is informational, not restrictive
            
            return min(score, 40.0)
            
        except Exception as e:
            logger.error(f"Error scoring technical setup: {e}")
            return 20.0  # Default to decent score on error
    
    @staticmethod
    def score_momentum(features: Dict) -> float:
        """
        Score momentum (0-25 points).
        
        Simplified: Any momentum is tradeable.
        """
        score = 0.0
        
        try:
            # ADX strength (10 points) - much more permissive
            adx = features.get('adx', 0)
            if adx > 15:  # Any trend
                score += 10
            else:
                score += 7  # Even weak trends work
            
            # Directional movement (10 points) - any direction is fine
            plus_di = features.get('plus_di', 0)
            minus_di = features.get('minus_di', 0)
            if plus_di > 0 or minus_di > 0:  # Any directional movement
                score += 10
            else:
                score += 7
            
            # Price momentum (5 points) - always give points
            score += 5  # Momentum can change quickly
            
            return min(score, 25.0)
            
        except Exception as e:
            logger.error(f"Error scoring momentum: {e}")
            return 15.0  # Default to decent score
    
    @staticmethod
    def score_volume(features: Dict) -> float:
        """
        Score volume (0-20 points).
        
        Simplified: Any volume is tradeable.
        """
        score = 0.0
        
        try:
            # Volume ratio (10 points) - much more permissive
            volume_ratio = features.get('volume_ratio', 1.0)
            if volume_ratio > 0.5:  # Any reasonable volume
                score += 10
            else:
                score += 7  # Even low volume can work
            
            # Volume spike (5 points) - always give points
            score += 5  # Volume patterns are informational
            
            # OBV direction (5 points) - always give points
            score += 5  # OBV is just one indicator
            
            return min(score, 20.0)
            
        except Exception as e:
            logger.error(f"Error scoring volume: {e}")
            return 15.0  # Default to decent score
    
    @staticmethod
    def score_volatility(features: Dict) -> float:
        """
        Score volatility (0-15 points).
        
        Simplified: Any volatility is tradeable with proper risk management.
        """
        score = 0.0
        
        try:
            # ATR level (10 points) - any volatility is fine
            atr = features.get('atr', 0)
            if atr > 0:  # Has some movement
                score += 10
            else:
                score += 7  # Even low volatility works
            
            # Volume Z-score (5 points) - always give points
            score += 5  # Volatility is managed by position sizing
            
            return min(score, 15.0)
            
        except Exception as e:
            logger.error(f"Error scoring volatility: {e}")
            return 12.0  # Default to decent score
    
    @staticmethod
    def score_market_regime(features: Dict) -> float:
        """
        Score market regime (0-10 points).
        
        Simplified: All regimes are tradeable with the right strategy.
        """
        score = 0.0
        
        try:
            regime = features.get('market_regime', 'transitional')
            
            # All regimes get good scores - we adapt to conditions
            if regime == 'trending':
                score += 10
            elif regime == 'transitional':
                score += 9  # Still very good
            elif regime == 'ranging':
                score += 8  # Range trading works too
            else:
                score += 8  # Unknown is fine
            
            return score
            
        except Exception as e:
            logger.error(f"Error scoring market regime: {e}")
            return 8.0  # Default to decent score
    
    def score_market_sentiment(self, direction: str = 'long') -> float:
        """
        Score market sentiment (0-10 points).
        
        Args:
            direction: 'long' or 'short' - adjusts scoring based on trade direction
        
        Returns:
            0-10 points based on sentiment alignment
        """
        if not self.sentiment_analyzer:
            return 5.0  # Neutral if no analyzer
        
        try:
            # Get or use cached sentiment
            if not self._sentiment_cache:
                # Check if using new sentiment aggregator or old analyzer
                if hasattr(self.sentiment_analyzer, 'get_sentiment'):
                    # New sentiment aggregator
                    sentiment_data = self.sentiment_analyzer.get_sentiment()
                    self._sentiment_cache = {'overall_score': sentiment_data['score']}
                else:
                    # Old sentiment analyzer
                    self._sentiment_cache = self.sentiment_analyzer.get_sentiment_score()
            
            sentiment_score = self._sentiment_cache['overall_score']
            
            # Score based on alignment with trade direction
            if direction.lower() == 'long':
                # For longs: higher sentiment = better
                if sentiment_score >= 60:  # Bullish
                    score = 8 + (sentiment_score - 60) / 20  # 8-10 points
                elif sentiment_score >= 40:  # Neutral
                    score = 5 + (sentiment_score - 40) / 10  # 5-7 points
                else:  # Bearish
                    score = max(0, 5 - (40 - sentiment_score) / 10)  # 0-5 points
            else:  # short
                # For shorts: lower sentiment = better
                if sentiment_score <= 40:  # Bearish
                    score = 8 + (40 - sentiment_score) / 20  # 8-10 points
                elif sentiment_score <= 60:  # Neutral
                    score = 5 + (60 - sentiment_score) / 10  # 5-7 points
                else:  # Bullish
                    score = max(0, 5 - (sentiment_score - 60) / 10)  # 0-5 points
            
            return min(10.0, max(0.0, score))
            
        except Exception as e:
            logger.error(f"Error scoring sentiment: {e}")
            return 5.0  # Neutral on error
    
    def calculate_total_score(self, features: Dict, direction: str = 'long') -> Dict[str, float]:
        """
        Calculate total opportunity score (0-120 with sentiment).
        
        Args:
            features: Stock features dict
            direction: 'long' or 'short' for sentiment alignment
        
        Returns:
            Dict with total score and component scores
        """
        try:
            # Calculate component scores
            technical = self.score_technical_setup(features)
            momentum = self.score_momentum(features)
            volume = self.score_volume(features)
            volatility = self.score_volatility(features)
            regime = self.score_market_regime(features)
            sentiment = self.score_market_sentiment(direction)
            
            # Total score (now 0-120)
            total = technical + momentum + volume + volatility + regime + sentiment
            
            return {
                'total_score': round(total, 1),
                'technical_score': round(technical, 1),
                'momentum_score': round(momentum, 1),
                'volume_score': round(volume, 1),
                'volatility_score': round(volatility, 1),
                'regime_score': round(regime, 1),
                'sentiment_score': round(sentiment, 1),
                'grade': self._get_grade(total)
            }
            
        except Exception as e:
            logger.error(f"Error calculating total score: {e}")
            return {
                'total_score': 0.0,
                'technical_score': 0.0,
                'momentum_score': 0.0,
                'volume_score': 0.0,
                'volatility_score': 0.0,
                'regime_score': 0.0,
                'sentiment_score': 0.0,
                'grade': 'F'
            }
    
    @staticmethod
    def _get_grade(score: float) -> str:
        """Convert score to letter grade (adjusted for 0-120 scale)."""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        elif score >= 50:
            return 'C-'
        elif score >= 45:
            return 'D'
        else:
            return 'F'
    
    @classmethod
    def rank_opportunities(cls, opportunities: Dict[str, Dict]) -> list:
        """
        Rank opportunities by score.
        
        Args:
            opportunities: Dict of {symbol: features}
            
        Returns:
            List of (symbol, score_dict) tuples, sorted by score
        """
        scored = []
        
        for symbol, features in opportunities.items():
            score_dict = cls.calculate_total_score(features)
            score_dict['symbol'] = symbol
            scored.append((symbol, score_dict))
        
        # Sort by total score (descending)
        scored.sort(key=lambda x: x[1]['total_score'], reverse=True)
        
        return scored
