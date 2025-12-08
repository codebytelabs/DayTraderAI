"""Opportunity Scorer - 130-point scoring system for stock opportunities.

GROWTH-FOCUSED SCORING: Prioritizes momentum and growth potential over stability.

Scores stocks based on:
- Technical setup (40 points)
- Momentum (25 points) - ENHANCED for growth stocks
- Volume (20 points)
- Volatility (15 points) - Higher volatility = more opportunity
- Market regime (10 points)
- Market sentiment (10 points)
- Growth potential (10 points) ← NEW - rewards mid-caps with momentum
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Growth potential bonuses by stock characteristics
# Mid-caps and high-beta stocks get bonuses to compete with mega-caps
GROWTH_POTENTIAL_BONUSES = {
    'high_volatility': 5,      # >3% daily moves
    'strong_momentum': 5,      # ADX > 30 with clear direction
    'volume_surge': 3,         # 2x+ volume
    'fresh_breakout': 5,       # Near 52-week high
    'oversold_bounce': 4,      # RSI < 35 turning up
}


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
        
        MOMENTUM-FOCUSED: Rewards active momentum, not just trend existence.
        """
        score = 0.0
        
        try:
            # EMA crossover recency (15 points) - REWARD FRESH CROSSOVERS
            ema_diff_pct = features.get('ema_diff_pct', 0)
            abs_diff = abs(ema_diff_pct)
            
            # Fresh crossover (0.05-0.3%) = best for catching waves
            if 0.05 <= abs_diff <= 0.3:
                score += 15  # Perfect - just crossed, room to run
            elif 0.3 < abs_diff <= 0.5:
                score += 12  # Good - early in move
            elif 0.5 < abs_diff <= 1.0:
                score += 8   # Okay - mid-move
            elif abs_diff > 1.0:
                score += 4   # Late - might be extended
            else:
                score += 2   # No trend
            
            # RSI momentum zone (10 points) - REWARD MOMENTUM, NOT EXTREMES
            rsi = features.get('rsi', 50)
            # Best zones: 40-60 (room to move) or 30-40/60-70 (momentum building)
            if 45 <= rsi <= 55:
                score += 10  # Perfect neutral - can go either way
            elif 35 <= rsi <= 45 or 55 <= rsi <= 65:
                score += 8   # Good momentum zone
            elif 30 <= rsi <= 35 or 65 <= rsi <= 70:
                score += 6   # Momentum building
            elif rsi < 30 or rsi > 70:
                score += 3   # Oversold/overbought - risky
            else:
                score += 5
            
            # MACD histogram strength (10 points) - REWARD GROWING MOMENTUM
            macd_histogram = features.get('macd_histogram', 0)
            macd_signal = features.get('macd_signal', 0)
            
            # Check if histogram is growing (momentum increasing)
            if abs(macd_histogram) > abs(macd_signal) * 0.5:
                score += 10  # Strong momentum
            elif abs(macd_histogram) > 0.1:
                score += 7   # Decent momentum
            else:
                score += 3   # Weak momentum
            
            # VWAP position (5 points) - REWARD PRICE NEAR VWAP (good entry)
            vwap = features.get('vwap', 0)
            price = features.get('price', 0)
            if vwap > 0 and price > 0:
                vwap_dist = abs(price - vwap) / vwap * 100
                if vwap_dist < 0.5:
                    score += 5  # Very close to VWAP - great entry
                elif vwap_dist < 1.0:
                    score += 3  # Near VWAP
                else:
                    score += 1  # Far from VWAP
            else:
                score += 2
            
            return min(score, 40.0)
            
        except Exception as e:
            logger.error(f"Error scoring technical setup: {e}")
            return 15.0  # Default to lower score on error
    
    @staticmethod
    def score_momentum(features: Dict) -> float:
        """
        Score momentum (0-25 points).
        
        WAVE-RIDING FOCUS: Rewards ACTIVE momentum, not just trend existence.
        """
        score = 0.0
        
        try:
            # ADX strength (10 points) - REWARD STRONG TRENDS
            adx = features.get('adx', 0)
            if adx > 40:
                score += 10  # Very strong trend - ride the wave!
            elif adx > 30:
                score += 8   # Strong trend
            elif adx > 25:
                score += 6   # Moderate trend
            elif adx > 20:
                score += 4   # Weak trend
            else:
                score += 1   # No trend - avoid
            
            # Directional movement SPREAD (10 points) - REWARD CLEAR DIRECTION
            plus_di = features.get('plus_di', 0)
            minus_di = features.get('minus_di', 0)
            di_spread = abs(plus_di - minus_di)
            
            if di_spread > 20:
                score += 10  # Very clear direction
            elif di_spread > 15:
                score += 8   # Clear direction
            elif di_spread > 10:
                score += 5   # Moderate direction
            elif di_spread > 5:
                score += 3   # Weak direction
            else:
                score += 1   # No clear direction
            
            # Price momentum (5 points) - REWARD RECENT PRICE MOVEMENT
            price_change_pct = features.get('price_change_pct', 0)
            if abs(price_change_pct) > 2.0:
                score += 5   # Big move - momentum!
            elif abs(price_change_pct) > 1.0:
                score += 4   # Good move
            elif abs(price_change_pct) > 0.5:
                score += 2   # Small move
            else:
                score += 1   # No movement
            
            return min(score, 25.0)
            
        except Exception as e:
            logger.error(f"Error scoring momentum: {e}")
            return 8.0  # Default to lower score
    
    @staticmethod
    def score_volume(features: Dict) -> float:
        """
        Score volume (0-20 points).
        
        WAVE-RIDING FOCUS: High volume = institutional interest = bigger waves.
        """
        score = 0.0
        
        try:
            # Volume ratio (10 points) - REWARD HIGH VOLUME
            volume_ratio = features.get('volume_ratio', 1.0)
            if volume_ratio > 2.0:
                score += 10  # Very high volume - big interest!
            elif volume_ratio > 1.5:
                score += 8   # High volume
            elif volume_ratio > 1.0:
                score += 6   # Above average
            elif volume_ratio > 0.7:
                score += 4   # Normal volume
            elif volume_ratio > 0.5:
                score += 2   # Low volume
            else:
                score += 0   # Very low - avoid
            
            # Volume spike detection (5 points) - REWARD VOLUME SURGES
            # Volume surge indicates institutional activity
            if volume_ratio > 1.5:
                score += 5   # Volume surge!
            elif volume_ratio > 1.2:
                score += 3   # Elevated volume
            else:
                score += 1   # Normal
            
            # OBV direction (5 points) - REWARD VOLUME CONFIRMING PRICE
            obv_trend = features.get('obv_trend', 0)
            price_trend = 1 if features.get('ema_diff_pct', 0) > 0 else -1
            
            if obv_trend * price_trend > 0:
                score += 5   # Volume confirms price direction
            elif obv_trend == 0:
                score += 2   # Neutral
            else:
                score += 0   # Divergence - caution
            
            return min(score, 20.0)
            
        except Exception as e:
            logger.error(f"Error scoring volume: {e}")
            return 5.0  # Default to lower score
    
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
    
    def score_growth_potential(self, features: Dict) -> float:
        """
        Score growth potential (0-10 points).
        
        NEW: Rewards characteristics that indicate higher upside potential.
        This helps mid-caps and growth stocks compete with stable mega-caps.
        """
        score = 0.0
        
        try:
            # High volatility bonus (more opportunity for day trading)
            atr = features.get('atr', 0)
            price = features.get('price', 100)
            if price > 0:
                atr_pct = (atr / price) * 100
                if atr_pct > 3.0:  # >3% daily range
                    score += 3
                elif atr_pct > 2.0:
                    score += 2
                elif atr_pct > 1.5:
                    score += 1
            
            # Strong momentum bonus (ADX > 30 with clear direction)
            adx = features.get('adx', 0)
            plus_di = features.get('plus_di', 0)
            minus_di = features.get('minus_di', 0)
            di_spread = abs(plus_di - minus_di)
            
            if adx > 30 and di_spread > 15:
                score += 3  # Strong trend with clear direction
            elif adx > 25 and di_spread > 10:
                score += 2
            
            # Volume surge bonus (institutional interest)
            volume_ratio = features.get('volume_ratio', 1.0)
            if volume_ratio > 2.0:
                score += 2  # 2x+ volume = big interest
            elif volume_ratio > 1.5:
                score += 1
            
            # RSI momentum bonus (not overbought/oversold extremes)
            rsi = features.get('rsi', 50)
            if 40 <= rsi <= 60:
                score += 2  # Room to move in either direction
            elif 30 <= rsi <= 40 or 60 <= rsi <= 70:
                score += 1  # Momentum building
            
            return min(score, 10.0)
            
        except Exception as e:
            logger.error(f"Error scoring growth potential: {e}")
            return 3.0  # Default moderate score
    
    def calculate_total_score(self, features: Dict, direction: str = 'long') -> Dict[str, float]:
        """
        Calculate total opportunity score (0-130 with growth potential).
        
        GROWTH-FOCUSED: Mid-caps with momentum can now outrank stable mega-caps.
        
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
            growth = self.score_growth_potential(features)  # NEW
            
            # Total score (now 0-130 with growth potential)
            total = technical + momentum + volume + volatility + regime + sentiment + growth
            
            return {
                'total_score': round(total, 1),
                'technical_score': round(technical, 1),
                'momentum_score': round(momentum, 1),
                'volume_score': round(volume, 1),
                'volatility_score': round(volatility, 1),
                'regime_score': round(regime, 1),
                'sentiment_score': round(sentiment, 1),
                'growth_score': round(growth, 1),  # NEW
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
                'growth_score': 0.0,
                'grade': 'F'
            }
    
    @staticmethod
    def _get_grade(score: float) -> str:
        """Convert score to letter grade (adjusted for 0-130 scale)."""
        if score >= 100:
            return 'A+'
        elif score >= 92:
            return 'A'
        elif score >= 85:
            return 'A-'
        elif score >= 78:
            return 'B+'
        elif score >= 72:
            return 'B'
        elif score >= 66:
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
