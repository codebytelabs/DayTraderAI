"""Volume Analysis Indicators

Volume is crucial for confirming price movements and detecting institutional activity.
"""

import pandas as pd
import numpy as np


def calculate_volume_ratio(volume: pd.Series, window: int = 20) -> pd.Series:
    """
    Calculate volume ratio compared to average volume.
    
    Volume Ratio = Current Volume / Average Volume
    """
    avg_volume = volume.rolling(window=window).mean()
    volume_ratio = volume / avg_volume
    
    return volume_ratio


def detect_volume_spike(volume: pd.Series, threshold: float = 2.0, 
                       window: int = 20) -> pd.Series:
    """
    Detect volume spikes above normal levels.
    
    Returns:
        Series with boolean values (True = volume spike)
    """
    volume_ratio = calculate_volume_ratio(volume, window)
    spikes = volume_ratio > threshold
    
    return spikes


def calculate_on_balance_volume(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Calculate On-Balance Volume (OBV).
    
    OBV accumulates volume based on price direction:
    - If close > prev_close: OBV += volume
    - If close < prev_close: OBV -= volume
    """
    price_change = close.diff()
    
    # Determine volume direction
    volume_direction = pd.Series(0, index=close.index)
    volume_direction[price_change > 0] = 1
    volume_direction[price_change < 0] = -1
    
    # Calculate signed volume
    signed_volume = volume * volume_direction
    
    # Calculate cumulative OBV
    obv = signed_volume.cumsum()
    
    return obv
