"""Momentum Indicators: RSI and MACD

These indicators help identify momentum and potential reversal points.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    
    Args:
        prices: Price series (typically close prices)
        period: Lookback period for RSI calculation
        
    Returns:
        Series with RSI values (0-100)
    """
    # Calculate price changes
    delta = prices.diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # Calculate average gains and losses using Wilder's smoothing
    avg_gains = gains.ewm(alpha=1/period, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1/period, adjust=False).mean()
    
    # Calculate RS and RSI
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def rsi_momentum_filter(rsi: pd.Series, threshold: float = 50) -> pd.Series:
    """
    Use RSI as momentum filter for other strategies.
    
    Args:
        rsi: RSI series
        threshold: RSI threshold (50 = neutral)
        
    Returns:
        Series with momentum: 1 (bullish), -1 (bearish), 0 (neutral)
    """
    momentum = pd.Series(0, index=rsi.index)
    
    # Bullish momentum when RSI > threshold and rising
    momentum[(rsi > threshold) & (rsi > rsi.shift(1))] = 1
    
    # Bearish momentum when RSI < threshold and falling
    momentum[(rsi < threshold) & (rsi < rsi.shift(1))] = -1
    
    return momentum


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, 
                  signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    MACD Line = EMA(fast) - EMA(slow)
    Signal Line = EMA(MACD Line, signal_period)
    Histogram = MACD Line - Signal Line
    
    Args:
        prices: Price series (typically close prices)
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line EMA period
        
    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    # Calculate EMAs
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    
    # Calculate MACD line
    macd_line = ema_fast - ema_slow
    
    # Calculate signal line
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def macd_momentum_filter(histogram: pd.Series) -> pd.Series:
    """
    Use MACD histogram as momentum filter.
    
    Args:
        histogram: MACD histogram
        
    Returns:
        Series with momentum: 1 (bullish), -1 (bearish), 0 (neutral)
    """
    momentum = pd.Series(0, index=histogram.index)
    
    # Bullish momentum: histogram positive and increasing
    momentum[(histogram > 0) & (histogram > histogram.shift(1))] = 1
    
    # Bearish momentum: histogram negative and decreasing
    momentum[(histogram < 0) & (histogram < histogram.shift(1))] = -1
    
    return momentum
