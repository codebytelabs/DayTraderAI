"""
Multi-Timeframe Feature Engine.

Calculates technical indicators for each timeframe and aggregates them
into MTFFeatures for multi-timeframe analysis.

Requirements: 1.5
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Optional
import logging

from trading.mtf.models import TimeframeFeatures, MTFFeatures

logger = logging.getLogger(__name__)


class MTFFeatureEngine:
    """Calculates features for multiple timeframes.
    
    Computes EMA(9/21/50/200), RSI, MACD, ADX, and volume ratio for each
    timeframe and aggregates them into MTFFeatures.
    
    Requirement 1.5: Calculate indicators for each timeframe independently.
    """
    
    # Minimum bars required for indicator calculation
    MIN_BARS_REQUIRED = 200  # Need at least 200 bars for EMA(200)
    
    def __init__(self):
        """Initialize the feature engine."""
        pass
    
    def calculate_mtf_features(
        self, 
        symbol: str, 
        data: Dict[str, pd.DataFrame]
    ) -> Optional[MTFFeatures]:
        """Calculate features for all timeframes.
        
        Args:
            symbol: Stock symbol
            data: Dict mapping timeframe to DataFrame with OHLCV data
            
        Returns:
            MTFFeatures with all timeframe features, or None if insufficient data
        """
        try:
            # Calculate features for each timeframe
            tf_1min = self._calculate_or_default(data.get('1min'), '1min')
            tf_5min = self._calculate_or_default(data.get('5min'), '5min')
            tf_15min = self._calculate_or_default(data.get('15min'), '15min')
            tf_daily = self._calculate_or_default(data.get('daily'), 'daily')
            
            if tf_1min is None or tf_5min is None or tf_15min is None or tf_daily is None:
                logger.warning(f"Insufficient data for {symbol} MTF features")
                return None
            
            return MTFFeatures(
                symbol=symbol,
                tf_1min=tf_1min,
                tf_5min=tf_5min,
                tf_15min=tf_15min,
                tf_daily=tf_daily,
                timestamp=datetime.now(timezone.utc),
            )
            
        except Exception as e:
            logger.error(f"Error calculating MTF features for {symbol}: {e}")
            return None
    
    def _calculate_or_default(
        self, 
        df: Optional[pd.DataFrame], 
        timeframe: str
    ) -> Optional[TimeframeFeatures]:
        """Calculate features or return None if data is insufficient."""
        if df is None or df.empty:
            return None
        return self.calculate_timeframe_features(df, timeframe)
    
    def calculate_timeframe_features(
        self, 
        df: pd.DataFrame, 
        timeframe: str
    ) -> Optional[TimeframeFeatures]:
        """Calculate features for a single timeframe.
        
        Computes:
        - EMA(9), EMA(21), EMA(50), EMA(200)
        - RSI(14)
        - MACD(12, 26, 9)
        - ADX(14)
        - Volume ratio (current vs 20-period average)
        
        Args:
            df: DataFrame with columns: open, high, low, close, volume
            timeframe: Timeframe identifier ('1min', '5min', '15min', 'daily')
            
        Returns:
            TimeframeFeatures with all calculated indicators
        """
        try:
            # Normalize column names to lowercase
            df = self._normalize_columns(df)
            
            # Check minimum data requirements
            min_required = 26  # Minimum for MACD calculation
            if len(df) < min_required:
                logger.warning(f"Insufficient data for {timeframe}: {len(df)} bars < {min_required}")
                return None
            
            # Get close prices
            close = df['close']
            high = df['high']
            low = df['low']
            volume = df['volume']
            
            # Calculate EMAs
            ema_9 = self._calculate_ema(close, 9)
            ema_21 = self._calculate_ema(close, 21)
            ema_50 = self._calculate_ema(close, 50)
            ema_200 = self._calculate_ema(close, 200)
            
            # Calculate RSI
            rsi = self._calculate_rsi(close, 14)
            
            # Calculate MACD
            macd, macd_signal, macd_histogram = self._calculate_macd(close)
            
            # Calculate ADX
            adx = self._calculate_adx(high, low, close, 14)
            
            # Calculate volume ratio
            volume_avg = volume.rolling(window=20).mean()
            current_volume = float(volume.iloc[-1])
            avg_volume = float(volume_avg.iloc[-1]) if not pd.isna(volume_avg.iloc[-1]) else current_volume
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Get latest values
            latest_idx = -1
            
            return TimeframeFeatures(
                timeframe=timeframe,
                ema_short=float(ema_9.iloc[latest_idx]),
                ema_long=float(ema_21.iloc[latest_idx]),
                ema_50=float(ema_50.iloc[latest_idx]) if not pd.isna(ema_50.iloc[latest_idx]) else float(close.iloc[latest_idx]),
                ema_200=float(ema_200.iloc[latest_idx]) if not pd.isna(ema_200.iloc[latest_idx]) else float(close.iloc[latest_idx]),
                rsi=float(rsi.iloc[latest_idx]) if not pd.isna(rsi.iloc[latest_idx]) else 50.0,
                macd=float(macd.iloc[latest_idx]) if not pd.isna(macd.iloc[latest_idx]) else 0.0,
                macd_signal=float(macd_signal.iloc[latest_idx]) if not pd.isna(macd_signal.iloc[latest_idx]) else 0.0,
                macd_histogram=float(macd_histogram.iloc[latest_idx]) if not pd.isna(macd_histogram.iloc[latest_idx]) else 0.0,
                adx=float(adx.iloc[latest_idx]) if not pd.isna(adx.iloc[latest_idx]) else 0.0,
                volume=current_volume,
                volume_avg=avg_volume,
                volume_ratio=volume_ratio,
                high=float(high.iloc[latest_idx]),
                low=float(low.iloc[latest_idx]),
                close=float(close.iloc[latest_idx]),
            )
            
        except Exception as e:
            logger.error(f"Error calculating {timeframe} features: {e}")
            return None
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame column names to lowercase."""
        df = df.copy()
        df.columns = [col.lower() for col in df.columns]
        return df
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return prices.ewm(span=period, adjust=False).mean()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index (RSI).
        
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss
        """
        delta = prices.diff()
        
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        avg_gains = gains.ewm(alpha=1/period, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1/period, adjust=False).mean()
        
        # Avoid division by zero
        rs = avg_gains / avg_losses.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        
        # Handle edge cases
        rsi = rsi.replace([np.inf, -np.inf], 50.0)
        rsi = rsi.fillna(50.0)
        
        return rsi
    
    def _calculate_macd(
        self, 
        prices: pd.Series, 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9
    ) -> tuple:
        """Calculate MACD (Moving Average Convergence Divergence).
        
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def _calculate_adx(
        self, 
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        period: int = 14
    ) -> pd.Series:
        """Calculate Average Directional Index (ADX).
        
        ADX measures trend strength (0-100):
        - ADX > 25: Strong trend
        - ADX < 20: Weak trend (ranging market)
        """
        # Calculate True Range
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate Directional Movement
        high_diff = high.diff()
        low_diff = -low.diff()
        
        plus_dm = pd.Series(0.0, index=high.index)
        minus_dm = pd.Series(0.0, index=high.index)
        
        plus_dm[(high_diff > low_diff) & (high_diff > 0)] = high_diff
        minus_dm[(low_diff > high_diff) & (low_diff > 0)] = low_diff
        
        # Smooth using Wilder's method
        atr = true_range.ewm(alpha=1/period, adjust=False).mean()
        plus_di_raw = plus_dm.ewm(alpha=1/period, adjust=False).mean()
        minus_di_raw = minus_dm.ewm(alpha=1/period, adjust=False).mean()
        
        # Calculate DI lines
        plus_di = 100 * (plus_di_raw / atr.replace(0, np.inf))
        minus_di = 100 * (minus_di_raw / atr.replace(0, np.inf))
        
        # Calculate DX
        di_sum = plus_di + minus_di
        dx = 100 * abs(plus_di - minus_di) / di_sum.replace(0, np.inf)
        
        # Calculate ADX (smoothed DX)
        adx = dx.ewm(alpha=1/period, adjust=False).mean()
        
        # Handle edge cases
        adx = adx.replace([np.inf, -np.inf], 0.0)
        adx = adx.fillna(0.0)
        
        return adx
    
    def get_required_indicators(self) -> list:
        """Return list of indicators calculated by this engine.
        
        Used for validation and testing.
        """
        return [
            'ema_short',    # EMA(9)
            'ema_long',     # EMA(21)
            'ema_50',       # EMA(50)
            'ema_200',      # EMA(200)
            'rsi',          # RSI(14)
            'macd',         # MACD line
            'macd_signal',  # MACD signal line
            'macd_histogram',  # MACD histogram
            'adx',          # ADX(14)
            'volume',       # Current volume
            'volume_avg',   # 20-period average volume
            'volume_ratio', # Volume ratio
            'high',         # Current high
            'low',          # Current low
            'close',        # Current close
        ]
