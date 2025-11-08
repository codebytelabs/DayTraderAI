"""VWAP (Volume-Weighted Average Price) Indicator

VWAP is the average price weighted by volume, used by institutional traders
as a benchmark. It's crucial for intraday trading.
"""

import pandas as pd
import numpy as np


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Calculate Volume-Weighted Average Price (VWAP).
    
    VWAP = Cumulative(Price * Volume) / Cumulative(Volume)
    
    Args:
        df: DataFrame with columns ['high', 'low', 'close', 'volume']
        
    Returns:
        Series with VWAP values
    """
    # Typical price (HLC/3)
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    
    # Price * Volume
    pv = typical_price * df['volume']
    
    # Cumulative sums
    cumulative_pv = pv.cumsum()
    cumulative_volume = df['volume'].cumsum()
    
    # VWAP = Cumulative(PV) / Cumulative(Volume)
    vwap = cumulative_pv / cumulative_volume
    
    return vwap


def vwap_signals(price: pd.Series, vwap: pd.Series, threshold: float = 0.001) -> pd.Series:
    """
    Generate VWAP-based trading signals.
    
    Args:
        price: Current price series
        vwap: VWAP series
        threshold: Minimum deviation from VWAP to generate signal (as percentage)
        
    Returns:
        Series with signals: 1 (bullish), -1 (bearish), 0 (neutral)
    """
    # Calculate deviation from VWAP
    deviation = (price - vwap) / vwap
    
    # Generate signals
    signals = pd.Series(0, index=price.index)
    
    # Bullish when price is above VWAP by threshold
    signals[deviation > threshold] = 1
    
    # Bearish when price is below VWAP by threshold
    signals[deviation < -threshold] = -1
    
    return signals
