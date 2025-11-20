"""
Adaptive Confidence Thresholds
Dynamically adjusts minimum confidence requirements based on market conditions
"""

import logging
from typing import Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class AdaptiveThresholds:
    """
    Adjusts confidence thresholds based on:
    - Market regime (trending/choppy)
    - Time of day (morning/midday/afternoon)
    - Market sentiment (fear/greed)
    - VIX level (volatility)
    """
    
    def __init__(self):
        # Base thresholds (ideal conditions) - LOWERED for day trading
        # Industry standard: 50-60% for intraday with proper risk management
        self.base_long_threshold = 0.50  # Was 0.60
        self.base_short_threshold = 0.55  # Was 0.65
        
        logger.info("✅ Adaptive Thresholds initialized (day trading mode: 50/55% base)")
    
    def get_thresholds(
        self,
        market_regime: str,
        regime_multiplier: float,
        sentiment_score: int,
        current_time: datetime = None
    ) -> Tuple[float, float]:
        """
        Calculate dynamic confidence thresholds
        
        Args:
            market_regime: 'trending', 'transitional', 'ranging', 'choppy'
            regime_multiplier: 0.5-1.0 (from market regime)
            sentiment_score: 0-100 (fear & greed index)
            current_time: Current datetime (for time-of-day adjustment)
            
        Returns:
            (long_threshold, short_threshold) as percentages (0.0-1.0)
        """
        if current_time is None:
            # CRITICAL FIX: Use ET timezone, not local machine time
            import pytz
            current_time = datetime.now(tz=pytz.timezone('US/Eastern'))
        
        # Start with base thresholds
        long_threshold = self.base_long_threshold
        short_threshold = self.base_short_threshold
        
        # 1. MARKET REGIME ADJUSTMENT (most important)
        regime_adjustment = self._get_regime_adjustment(market_regime, regime_multiplier)
        long_threshold += regime_adjustment
        short_threshold += regime_adjustment
        
        # 2. TIME OF DAY ADJUSTMENT
        time_adjustment = self._get_time_adjustment(current_time)
        long_threshold += time_adjustment
        short_threshold += time_adjustment
        
        # 3. SENTIMENT ADJUSTMENT
        sentiment_adjustment = self._get_sentiment_adjustment(sentiment_score)
        long_threshold += sentiment_adjustment['long']
        short_threshold += sentiment_adjustment['short']
        
        # Cap thresholds at reasonable limits for day trading
        # Industry standard: Don't exceed 70% for longs, 75% for shorts
        long_threshold = min(max(long_threshold, 0.45), 0.70)  # 45-70%
        short_threshold = min(max(short_threshold, 0.50), 0.75)  # 50-75%
        
        logger.info(
            f"📊 Adaptive Thresholds: "
            f"Long={long_threshold*100:.0f}% | Short={short_threshold*100:.0f}% | "
            f"Regime={market_regime} | Time={current_time.strftime('%H:%M')} | "
            f"Sentiment={sentiment_score}"
        )
        
        return long_threshold, short_threshold
    
    def _get_regime_adjustment(self, regime: str, multiplier: float) -> float:
        """
        Adjust thresholds based on ACTUAL market regime (most important factor)
        
        Industry Standard Adjustments:
        - Choppy markets: +10-15% (was +20-25%)
        - Trending markets: 0-5% bonus
        - Strong trends: Up to 10% bonus
        
        Rationale: Even choppy markets can be traded with proper risk management
        """
        # Use multiplier as the primary signal (calculated from actual market data)
        if multiplier <= 0.4:
            # Extremely choppy: +15% (was +25%)
            return 0.15
        elif multiplier <= 0.5:
            # Very choppy: +12% (was +20%)
            return 0.12
        elif multiplier <= 0.6:
            # Moderately choppy: +8% (was +15%)
            return 0.08
        elif multiplier <= 0.7:
            # Slightly choppy: +5% (was +10%)
            return 0.05
        elif multiplier <= 0.8:
            # Transitional: +2% (was +5%)
            return 0.02
        elif multiplier <= 0.9:
            # Trending: No adjustment
            return 0.0
        elif multiplier <= 1.0:
            # Strong trend: -5% bonus
            return -0.05
        else:
            # Very strong trend: -10% bonus (easier to trade)
            return -0.10
    
    def _get_time_adjustment(self, current_time: datetime) -> float:
        """
        MINOR adjustment based on time of day
        
        Industry Standard: Minimal time-based adjustments (2-5%)
        - Volume filters handle time-of-day better than confidence adjustments
        - Market regime is the primary signal
        """
        hour = current_time.hour
        
        # Market hours: 9:30 AM - 4:00 PM ET
        
        if 9 <= hour < 10:
            # First 30 min: Slightly more volatile
            return 0.02  # Small penalty
        
        elif 10 <= hour < 11:
            # Morning session: Best trading conditions
            return -0.02  # Small bonus
        
        elif 11 <= hour < 14:
            # Midday lull: Lower volume but still tradeable
            return 0.03  # Minimal penalty (was +0.05)
        
        elif 14 <= hour < 15:
            # Afternoon: Normal conditions
            return 0.0  # No adjustment
        
        elif 15 <= hour < 16:
            # Power hour: Good volume
            return -0.02  # Small bonus
        
        else:
            # Pre-market or after-hours: Higher risk
            return 0.08  # Moderate penalty (was +0.10)
    
    def _get_sentiment_adjustment(self, sentiment: int) -> Dict[str, float]:
        """
        Adjust thresholds based on market sentiment
        
        Industry Standard: Minimal sentiment adjustments (0-8%)
        - Fear/greed creates opportunities, not just risk
        - Contrarian plays work well in extremes
        - Focus on technical setup quality over sentiment
        """
        if sentiment < 15:
            # Extreme fear: Contrarian long opportunities, risky shorts
            return {'long': 0.05, 'short': 0.08}  # Was 0.08/0.10
        
        elif sentiment < 25:
            # Strong fear: Good for longs, careful on shorts
            return {'long': 0.02, 'short': 0.05}  # Was 0.03/0.05
        
        elif sentiment < 40:
            # Fear: Slight caution
            return {'long': 0.0, 'short': 0.03}  # Was 0.0/0.03
        
        elif sentiment <= 60:
            # Neutral: Ideal conditions
            return {'long': 0.0, 'short': 0.0}
        
        elif sentiment <= 75:
            # Greed: Slight caution
            return {'long': 0.03, 'short': 0.0}  # Was 0.03/0.0
        
        elif sentiment <= 85:
            # Strong greed: Good for shorts, careful on longs
            return {'long': 0.05, 'short': 0.02}  # Was 0.05/0.03
        
        else:
            # Extreme greed: Contrarian short opportunities, risky longs
            return {'long': 0.08, 'short': 0.05}  # Was 0.10/0.08
    
    def should_pause_trading(
        self,
        market_regime: str,
        regime_multiplier: float,
        sentiment_score: int,
        current_time: datetime = None
    ) -> Tuple[bool, str]:
        """
        Determine if trading should be paused entirely
        
        Industry Standard: Only pause in truly extreme conditions
        - Most conditions can be traded with proper risk management
        - Pausing should be rare (< 5% of trading days)
        
        Returns:
            (should_pause, reason)
        """
        if current_time is None:
            import pytz
            current_time = datetime.now(tz=pytz.timezone('US/Eastern'))
        
        # Only pause in EXTREME choppy conditions (lowered threshold)
        if regime_multiplier <= 0.25:  # Was 0.35
            return True, f"Extremely choppy market (multiplier {regime_multiplier:.2f} ≤ 0.25)"
        
        # Pause in extreme sentiment + very choppy (more lenient)
        if (sentiment_score < 10 or sentiment_score > 90) and regime_multiplier <= 0.35:  # Was 0.5
            return True, f"Extreme sentiment ({sentiment_score}) + very choppy market ({regime_multiplier:.2f})"
        
        # Remove triple threat pause - too restrictive for day trading
        # Even choppy + midday + fear can be traded with proper filters
        
        return False, ""
    
    def get_summary(
        self,
        market_regime: str,
        regime_multiplier: float,
        sentiment_score: int,
        current_time: datetime = None
    ) -> Dict:
        """Get complete summary of current thresholds and conditions"""
        
        long_threshold, short_threshold = self.get_thresholds(
            market_regime, regime_multiplier, sentiment_score, current_time
        )
        
        should_pause, pause_reason = self.should_pause_trading(
            market_regime, regime_multiplier, sentiment_score, current_time
        )
        
        return {
            'long_threshold': long_threshold,
            'short_threshold': short_threshold,
            'long_threshold_pct': f"{long_threshold*100:.0f}%",
            'short_threshold_pct': f"{short_threshold*100:.0f}%",
            'market_regime': market_regime,
            'regime_multiplier': regime_multiplier,
            'sentiment_score': sentiment_score,
            'should_pause': should_pause,
            'pause_reason': pause_reason,
            'trading_difficulty': self._get_difficulty_rating(
                market_regime, regime_multiplier, sentiment_score, current_time
            )
        }
    
    def _get_difficulty_rating(
        self,
        market_regime: str,
        regime_multiplier: float,
        sentiment_score: int,
        current_time: datetime
    ) -> str:
        """Rate current trading difficulty (adjusted for day trading standards)"""
        
        long_threshold, short_threshold = self.get_thresholds(
            market_regime, regime_multiplier, sentiment_score, current_time
        )
        
        avg_threshold = (long_threshold + short_threshold) / 2
        
        # Adjusted ratings for day trading (lower thresholds)
        if avg_threshold >= 0.70:
            return "VERY HARD 🔴"  # Was 0.80
        elif avg_threshold >= 0.65:
            return "HARD 🟠"  # Was 0.75
        elif avg_threshold >= 0.60:
            return "MODERATE 🟡"  # Was 0.70
        elif avg_threshold >= 0.55:
            return "NORMAL 🟢"  # Was 0.65
        else:
            return "EASY 🟢🟢"  # < 0.55
