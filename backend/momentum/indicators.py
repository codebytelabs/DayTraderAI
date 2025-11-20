# Technical indicator calculations for momentum detection

import numpy as np
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class ADXCalculator:
    """Calculates Average Directional Index"""
    
    def __init__(self, period: int = 14):
        self.period = period
    
    def calculate(self, high: List[float], low: List[float], close: List[float]) -> float:
        """Calculate ADX"""
        try:
            if len(high) < self.period + 1:
                return 0.0
            
            high = np.array(high)
            low = np.array(low)
            close = np.array(close)
            
            # Calculate True Range
            tr = self._calculate_true_range(high, low, close)
            
            # Calculate +DM and -DM
            plus_dm, minus_dm = self._calculate_directional_movement(high, low)
            
            # Smooth using Wilder's method
            atr = self._wilders_smoothing(tr, self.period)
            plus_di = 100 * self._wilders_smoothing(plus_dm, self.period) / atr
            minus_di = 100 * self._wilders_smoothing(minus_dm, self.period) / atr
            
            # Calculate DX
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
            
            # Calculate ADX
            adx = self._wilders_smoothing(dx, self.period)
            
            return float(adx[-1]) if len(adx) > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating ADX: {e}")
            return 0.0
    
    def _calculate_true_range(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """Calculate True Range"""
        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]
        
        tr1 = high - low
        tr2 = np.abs(high - prev_close)
        tr3 = np.abs(low - prev_close)
        
        return np.maximum(tr1, np.maximum(tr2, tr3))
    
    def _calculate_directional_movement(self, high: np.ndarray, low: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate +DM and -DM"""
        up_move = high - np.roll(high, 1)
        down_move = np.roll(low, 1) - low
        
        up_move[0] = 0
        down_move[0] = 0
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        return plus_dm, minus_dm
    
    def _wilders_smoothing(self, data: np.ndarray, period: int) -> np.ndarray:
        """Apply Wilder's smoothing"""
        alpha = 1.0 / period
        result = np.zeros_like(data)
        
        if len(data) >= period:
            result[period-1] = np.mean(data[:period])
            
            for i in range(period, len(data)):
                result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
        
        return result

class VolumeAnalyzer:
    """Analyzes volume relative to average"""
    
    def __init__(self, lookback_period: int = 20):
        self.lookback_period = lookback_period
    
    def calculate_volume_ratio(self, volumes: List[float]) -> float:
        """Calculate current volume vs average"""
        try:
            if len(volumes) < self.lookback_period + 1:
                return 1.0
            
            current_volume = volumes[-1]
            avg_volume = np.mean(volumes[-(self.lookback_period+1):-1])
            
            if avg_volume == 0:
                return 1.0
            
            return float(current_volume / avg_volume)
            
        except Exception as e:
            logger.error(f"Error calculating volume ratio: {e}")
            return 1.0

class TrendStrengthCalculator:
    """Calculates composite trend strength score"""
    
    def __init__(self, ema_periods: List[int] = None):
        self.ema_periods = ema_periods or [9, 21, 50]
    
    def calculate(self, close: List[float], high: List[float] = None, low: List[float] = None) -> float:
        """Calculate trend strength score (0-1)"""
        try:
            if len(close) < max(self.ema_periods) + 10:
                return 0.0
            
            close = np.array(close)
            current_price = close[-1]
            
            score = 0.0
            
            # Component 1: Price vs EMAs (0.4 weight)
            ema_score = self._calculate_ema_score(close, current_price)
            score += 0.4 * ema_score
            
            # Component 2: Rate of Change (0.3 weight)
            roc_score = self._calculate_roc_score(close)
            score += 0.3 * roc_score
            
            # Component 3: Higher highs (0.3 weight)
            if high is not None:
                hh_score = self._calculate_higher_highs_score(high)
            else:
                hh_score = self._calculate_higher_highs_score(close)
            score += 0.3 * hh_score
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 0.0
    
    def _calculate_ema_score(self, close: np.ndarray, current_price: float) -> float:
        """Calculate EMA alignment score"""
        emas = {}
        for period in self.ema_periods:
            if len(close) >= period:
                emas[period] = self._calculate_ema(close, period)[-1]
        
        if len(emas) == 0:
            return 0.0
        
        ema_values = list(emas.values())
        above_emas = sum(1 for ema in ema_values if current_price > ema) / len(ema_values)
        
        return min(1.0, above_emas)
    
    def _calculate_roc_score(self, close: np.ndarray, period: int = 10) -> float:
        """Calculate Rate of Change score"""
        if len(close) < period + 1:
            return 0.0
        
        roc = (close[-1] - close[-(period+1)]) / close[-(period+1)] * 100
        return max(0.0, min(1.0, roc / 5.0))
    
    def _calculate_higher_highs_score(self, prices: np.ndarray, lookback: int = 10) -> float:
        """Calculate higher highs pattern score"""
        if len(prices) < lookback * 2:
            return 0.0
        
        recent_high = np.max(prices[-lookback:])
        previous_high = np.max(prices[-(lookback*2):-lookback])
        
        if previous_high == 0:
            return 0.0
        
        improvement = (recent_high - previous_high) / previous_high
        return max(0.0, min(1.0, improvement / 0.03))
    
    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        alpha = 2.0 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        
        return ema

class ATRCalculator:
    """Calculates Average True Range"""
    
    def __init__(self, period: int = 14):
        self.period = period
    
    def calculate(self, high: List[float], low: List[float], close: List[float]) -> float:
        """Calculate ATR"""
        try:
            if len(high) < self.period + 1:
                return 0.0
            
            high = np.array(high)
            low = np.array(low)
            close = np.array(close)
            
            tr = self._calculate_true_range(high, low, close)
            atr = np.mean(tr[-self.period:])
            
            return float(atr)
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return 0.0
    
    def _calculate_true_range(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """Calculate True Range"""
        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]
        
        tr1 = high - low
        tr2 = np.abs(high - prev_close)
        tr3 = np.abs(low - prev_close)
        
        return np.maximum(tr1, np.maximum(tr2, tr3))
