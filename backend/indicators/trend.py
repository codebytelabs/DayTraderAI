"""Trend Indicators: ADX and Directional Movement

ADX (Average Directional Index) helps identify trend strength and market regime.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def calculate_true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """
    Calculate True Range (TR).
    
    TR = max(high - low, abs(high - prev_close), abs(low - prev_close))
    """
    prev_close = close.shift(1)
    
    tr1 = high - low
    tr2 = abs(high - prev_close)
    tr3 = abs(low - prev_close)
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    return true_range


def calculate_directional_movement(high: pd.Series, low: pd.Series) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Directional Movement (+DM and -DM).
    """
    high_diff = high.diff()
    low_diff = -low.diff()
    
    plus_dm = pd.Series(0.0, index=high.index)
    minus_dm = pd.Series(0.0, index=high.index)
    
    # +DM when up move is greater than down move
    plus_dm[(high_diff > low_diff) & (high_diff > 0)] = high_diff
    
    # -DM when down move is greater than up move
    minus_dm[(low_diff > high_diff) & (low_diff > 0)] = low_diff
    
    return plus_dm, minus_dm


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, 
                 period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate ADX (Average Directional Index) and DI lines.
    
    ADX measures trend strength (0-100):
    - ADX > 25: Strong trend
    - ADX < 20: Weak trend (ranging market)
    
    Returns:
        Tuple of (ADX, +DI, -DI) series
    """
    # Calculate True Range and Directional Movement
    tr = calculate_true_range(high, low, close)
    plus_dm, minus_dm = calculate_directional_movement(high, low)
    
    # Smooth TR and DM using Wilder's smoothing
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di_raw = plus_dm.ewm(alpha=1/period, adjust=False).mean()
    minus_di_raw = minus_dm.ewm(alpha=1/period, adjust=False).mean()
    
    # Calculate DI lines
    plus_di = 100 * (plus_di_raw / atr)
    minus_di = 100 * (minus_di_raw / atr)
    
    # Calculate DX (Directional Index)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    
    # Calculate ADX (smoothed DX)
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    
    return adx, plus_di, minus_di


def detect_market_regime(adx: pd.Series, trending_threshold: float = 25, 
                        ranging_threshold: float = 20) -> pd.Series:
    """
    Detect market regime based on ADX.
    
    Returns:
        Series with regime: 'trending', 'ranging', 'transitional'
    """
    regime = pd.Series('transitional', index=adx.index)
    
    # Trending market
    regime[adx > trending_threshold] = 'trending'
    
    # Ranging market
    regime[adx < ranging_threshold] = 'ranging'
    
    return regime
