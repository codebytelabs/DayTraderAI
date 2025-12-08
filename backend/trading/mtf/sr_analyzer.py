"""
Multi-Timeframe Support/Resistance Analyzer.

Identifies support and resistance levels from higher timeframes.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
"""

import logging
from typing import List, Tuple, Optional
import pandas as pd

from trading.mtf.models import MTFFeatures, SRLevels, TimeframeFeatures

logger = logging.getLogger(__name__)


class SupportResistanceAnalyzer:
    """Identifies support and resistance levels from higher timeframes.
    
    Requirements:
    - 4.1: Identify swing highs/lows from last 50 bars on 15-min
    - 4.2: Identify previous day's high, low, close as key levels
    - 4.3: Reduce position size by 30% when buy near resistance
    - 4.4: Reduce position size by 30% when sell near support
    - 4.5: Place stops beyond nearest S/R level
    - 4.6: Use next S/R level as primary profit target
    """
    
    # Default lookback for swing point detection
    DEFAULT_LOOKBACK = 50
    
    # Threshold for "near" a level (0.3%)
    NEAR_LEVEL_THRESHOLD_PCT = 0.3
    
    # Position size reduction when near S/R
    SR_POSITION_REDUCTION = 0.30
    
    def __init__(self):
        """Initialize the S/R analyzer."""
        pass
    
    def find_swing_points(
        self, 
        df: pd.DataFrame, 
        lookback: int = 50
    ) -> Tuple[List[float], List[float]]:
        """Find swing highs and swing lows from price data.
        
        Requirement 4.1: Identify swing highs/lows from last 50 bars.
        
        A swing high is a bar where the high is higher than the highs
        of the bars immediately before and after it.
        A swing low is a bar where the low is lower than the lows
        of the bars immediately before and after it.
        
        Args:
            df: DataFrame with 'high' and 'low' columns
            lookback: Number of bars to analyze
            
        Returns:
            Tuple of (swing_highs, swing_lows) as lists of price levels
        """
        if df is None or len(df) < 3:
            return [], []
        
        # Normalize column names
        df = df.copy()
        df.columns = [col.lower() for col in df.columns]
        
        # Use last N bars
        df = df.tail(lookback)
        
        swing_highs = []
        swing_lows = []
        
        highs = df['high'].values
        lows = df['low'].values
        
        # Find swing points (need at least 1 bar on each side)
        for i in range(1, len(df) - 1):
            # Swing high: higher than neighbors
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                swing_highs.append(float(highs[i]))
            
            # Swing low: lower than neighbors
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                swing_lows.append(float(lows[i]))
        
        # Sort for easier access
        swing_highs.sort(reverse=True)  # Highest first
        swing_lows.sort()  # Lowest first
        
        return swing_highs, swing_lows
    
    def get_nearest_levels(
        self, 
        price: float, 
        features: MTFFeatures,
        df_15min: Optional[pd.DataFrame] = None
    ) -> SRLevels:
        """Get nearest support and resistance levels.
        
        Requirements 4.1, 4.2:
        - Uses 15-min swing points for S/R
        - Uses daily high/low/close as key levels
        
        Args:
            price: Current price
            features: MTFFeatures containing daily data
            df_15min: Optional 15-min DataFrame for swing point calculation
            
        Returns:
            SRLevels with nearest support/resistance and daily levels
        """
        # Get daily levels
        daily = features.tf_daily
        daily_high = daily.high
        daily_low = daily.low
        daily_close = daily.close
        
        # Find swing points from 15-min data if provided
        swing_highs = []
        swing_lows = []
        if df_15min is not None:
            swing_highs, swing_lows = self.find_swing_points(df_15min)
        
        # Combine all resistance levels (above current price)
        all_resistance = [daily_high]
        all_resistance.extend([h for h in swing_highs if h > price])
        
        # Combine all support levels (below current price)
        all_support = [daily_low]
        all_support.extend([l for l in swing_lows if l < price])
        
        # Find nearest resistance (smallest value above price)
        nearest_resistance = min(all_resistance) if all_resistance else price * 1.02
        
        # Find nearest support (largest value below price)
        nearest_support = max(all_support) if all_support else price * 0.98
        
        return SRLevels(
            nearest_support=nearest_support,
            nearest_resistance=nearest_resistance,
            daily_high=daily_high,
            daily_low=daily_low,
            daily_close=daily_close,
            swing_highs=swing_highs,
            swing_lows=swing_lows,
        )
    
    def is_near_level(
        self, 
        price: float, 
        level: float, 
        threshold_pct: float = 0.3
    ) -> bool:
        """Check if price is within threshold of a level.
        
        Args:
            price: Current price
            level: S/R level to check
            threshold_pct: Threshold percentage (default 0.3%)
            
        Returns:
            True if price is within threshold of level
        """
        if level <= 0:
            return False
        
        distance_pct = abs(price - level) / level * 100
        return distance_pct <= threshold_pct
    
    def get_position_size_multiplier(
        self, 
        price: float, 
        signal: str, 
        sr_levels: SRLevels
    ) -> float:
        """Get position size multiplier based on S/R proximity.
        
        Requirements 4.3, 4.4:
        - Reduce by 30% when buy near resistance
        - Reduce by 30% when sell near support
        
        Args:
            price: Current price
            signal: Signal direction ('buy' or 'sell')
            sr_levels: SRLevels with nearest levels
            
        Returns:
            Position size multiplier (1.0 or 0.7)
        """
        signal_lower = signal.lower()
        
        if signal_lower == 'buy':
            # Check if near resistance
            if sr_levels.is_near_resistance(price, self.NEAR_LEVEL_THRESHOLD_PCT):
                logger.info(
                    f"Buy near resistance ({sr_levels.nearest_resistance:.2f}), "
                    f"reducing position by {self.SR_POSITION_REDUCTION*100:.0f}%"
                )
                return 1.0 - self.SR_POSITION_REDUCTION
        
        elif signal_lower == 'sell':
            # Check if near support
            if sr_levels.is_near_support(price, self.NEAR_LEVEL_THRESHOLD_PCT):
                logger.info(
                    f"Sell near support ({sr_levels.nearest_support:.2f}), "
                    f"reducing position by {self.SR_POSITION_REDUCTION*100:.0f}%"
                )
                return 1.0 - self.SR_POSITION_REDUCTION
        
        return 1.0
    
    def get_stop_level(
        self, 
        price: float, 
        signal: str, 
        sr_levels: SRLevels,
        buffer_pct: float = 0.1
    ) -> float:
        """Get stop loss level beyond nearest S/R.
        
        Requirement 4.5: Place stops beyond nearest S/R level.
        
        Args:
            price: Current price
            signal: Signal direction ('buy' or 'sell')
            sr_levels: SRLevels with nearest levels
            buffer_pct: Buffer beyond S/R level (default 0.1%)
            
        Returns:
            Suggested stop loss price
        """
        signal_lower = signal.lower()
        
        if signal_lower == 'buy':
            # Stop below nearest support
            stop = sr_levels.nearest_support * (1 - buffer_pct / 100)
        else:  # sell
            # Stop above nearest resistance
            stop = sr_levels.nearest_resistance * (1 + buffer_pct / 100)
        
        return stop
    
    def get_target_level(
        self, 
        price: float, 
        signal: str, 
        sr_levels: SRLevels
    ) -> float:
        """Get profit target at next S/R level.
        
        Requirement 4.6: Use next S/R level as primary target.
        
        Args:
            price: Current price
            signal: Signal direction ('buy' or 'sell')
            sr_levels: SRLevels with nearest levels
            
        Returns:
            Suggested profit target price
        """
        signal_lower = signal.lower()
        
        if signal_lower == 'buy':
            # Target at nearest resistance
            return sr_levels.nearest_resistance
        else:  # sell
            # Target at nearest support
            return sr_levels.nearest_support
