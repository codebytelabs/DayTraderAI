import pandas as pd
import numpy as np
from typing import Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


class FeatureEngine:
    """Compute technical indicators and features."""
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        return true_range.rolling(window=period).mean()
    
    @staticmethod
    def calculate_volume_zscore(volume: pd.Series, period: int = 20) -> float:
        """Calculate volume z-score."""
        if len(volume) < period:
            return 0.0
        
        recent_volume = volume.iloc[-period:]
        mean_vol = recent_volume.mean()
        std_vol = recent_volume.std()
        
        if std_vol == 0:
            return 0.0
        
        current_vol = volume.iloc[-1]
        return (current_vol - mean_vol) / std_vol
    
    @staticmethod
    def calculate_features(df: pd.DataFrame, ema_short: int = 9, ema_long: int = 21) -> Optional[Dict]:
        """
        Calculate all features for a symbol.
        df should have columns: open, high, low, close, volume
        """
        try:
            if df is None or len(df) < max(ema_long, 14):
                return None
            
            # EMAs
            df['ema_short'] = FeatureEngine.calculate_ema(df['close'], ema_short)
            df['ema_long'] = FeatureEngine.calculate_ema(df['close'], ema_long)
            
            # ATR
            df['atr'] = FeatureEngine.calculate_atr(df['high'], df['low'], df['close'])
            
            # Get latest values
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            features = {
                'price': float(latest['close']),
                'ema_short': float(latest['ema_short']),
                'ema_long': float(latest['ema_long']),
                'prev_ema_short': float(prev['ema_short']),
                'prev_ema_long': float(prev['ema_long']),
                'atr': float(latest['atr']),
                'volume': int(latest['volume']),  # Convert to int for BIGINT column
                'volume_zscore': FeatureEngine.calculate_volume_zscore(df['volume']),
                'ema_diff': float(latest['ema_short'] - latest['ema_long']),
                'ema_diff_pct': float((latest['ema_short'] / latest['ema_long'] - 1) * 100),
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Failed to calculate features: {e}")
            return None
    
    @staticmethod
    def detect_ema_crossover(features: Dict) -> Optional[str]:
        """
        Detect EMA crossover signal.
        Returns 'buy', 'sell', or None
        """
        if not features:
            return None
        
        current_short = features['ema_short']
        current_long = features['ema_long']
        prev_short = features['prev_ema_short']
        prev_long = features['prev_ema_long']
        
        # Bullish crossover: short crosses above long
        if prev_short <= prev_long and current_short > current_long:
            return 'buy'
        
        # Bearish crossover: short crosses below long
        if prev_short >= prev_long and current_short < current_long:
            return 'sell'
        
        return None
