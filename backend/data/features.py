import pandas as pd
import numpy as np
from typing import Dict, Optional
from utils.logger import setup_logger

# Import new indicators
from indicators.vwap import calculate_vwap, vwap_signals
from indicators.momentum import calculate_rsi, calculate_macd, rsi_momentum_filter, macd_momentum_filter
from indicators.trend import calculate_adx, detect_market_regime
from indicators.volume import calculate_volume_ratio, detect_volume_spike, calculate_on_balance_volume

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
        Calculate all enhanced features for a symbol.
        df should have columns: open, high, low, close, volume
        """
        try:
            if df is None or len(df) < max(ema_long, 26):  # Need more data for MACD
                return None
            
            # EMAs (existing)
            df['ema_short'] = FeatureEngine.calculate_ema(df['close'], ema_short)
            df['ema_long'] = FeatureEngine.calculate_ema(df['close'], ema_long)
            
            # ATR (existing)
            df['atr'] = FeatureEngine.calculate_atr(df['high'], df['low'], df['close'])
            
            # NEW: VWAP
            vwap = calculate_vwap(df)
            
            # NEW: RSI
            rsi = calculate_rsi(df['close'])
            
            # NEW: MACD
            macd_line, macd_signal, macd_histogram = calculate_macd(df['close'])
            
            # NEW: ADX and market regime
            adx, plus_di, minus_di = calculate_adx(df['high'], df['low'], df['close'])
            market_regime = detect_market_regime(adx)
            
            # NEW: Enhanced volume analysis
            volume_ratio = calculate_volume_ratio(df['volume'])
            volume_spike = detect_volume_spike(df['volume'])
            obv = calculate_on_balance_volume(df['close'], df['volume'])
            
            # NEW: Multi-indicator signals
            vwap_signal = vwap_signals(df['close'], vwap)
            rsi_momentum = rsi_momentum_filter(rsi)
            macd_momentum = macd_momentum_filter(macd_histogram)
            
            # Get latest values
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            # NEW: Calculate confidence score
            confidence_score = FeatureEngine.calculate_confidence_score(
                latest['ema_short'], latest['ema_long'], 
                rsi.iloc[-1] if len(rsi) > 0 else 50.0,
                macd_histogram.iloc[-1] if len(macd_histogram) > 0 else 0.0,
                volume_ratio.iloc[-1] if len(volume_ratio) > 0 else 1.0,
                latest['close'], vwap.iloc[-1] if len(vwap) > 0 else latest['close']
            )
            
            features = {
                # Existing features
                'price': float(latest['close']),
                'ema_short': float(latest['ema_short']),
                'ema_long': float(latest['ema_long']),
                'prev_ema_short': float(prev['ema_short']),
                'prev_ema_long': float(prev['ema_long']),
                'atr': float(latest['atr']),
                'volume': int(latest['volume']),
                'volume_zscore': FeatureEngine.calculate_volume_zscore(df['volume']),
                'ema_diff': float(latest['ema_short'] - latest['ema_long']),
                'ema_diff_pct': float((latest['ema_short'] / latest['ema_long'] - 1) * 100),
                
                # NEW: Enhanced indicators
                'vwap': float(vwap.iloc[-1]) if len(vwap) > 0 else float(latest['close']),
                'rsi': float(rsi.iloc[-1]) if len(rsi) > 0 else 50.0,
                'macd': float(macd_line.iloc[-1]) if len(macd_line) > 0 else 0.0,
                'macd_signal': float(macd_signal.iloc[-1]) if len(macd_signal) > 0 else 0.0,
                'macd_histogram': float(macd_histogram.iloc[-1]) if len(macd_histogram) > 0 else 0.0,
                'adx': float(adx.iloc[-1]) if len(adx) > 0 else 0.0,
                'plus_di': float(plus_di.iloc[-1]) if len(plus_di) > 0 else 0.0,
                'minus_di': float(minus_di.iloc[-1]) if len(minus_di) > 0 else 0.0,
                'market_regime': str(market_regime.iloc[-1]) if len(market_regime) > 0 else 'transitional',
                
                # NEW: Volume indicators
                'volume_ratio': float(volume_ratio.iloc[-1]) if len(volume_ratio) > 0 else 1.0,
                'volume_spike': bool(volume_spike.iloc[-1]) if len(volume_spike) > 0 else False,
                'obv': float(obv.iloc[-1]) if len(obv) > 0 else 0.0,
                
                # NEW: Signal indicators
                'vwap_signal': int(vwap_signal.iloc[-1]) if len(vwap_signal) > 0 else 0,
                'rsi_momentum': int(rsi_momentum.iloc[-1]) if len(rsi_momentum) > 0 else 0,
                'macd_momentum': int(macd_momentum.iloc[-1]) if len(macd_momentum) > 0 else 0,
                
                # NEW: Confidence score
                'confidence_score': confidence_score,
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Failed to calculate enhanced features: {e}")
            return None
    
    @staticmethod
    def calculate_confidence_score(ema_short: float, ema_long: float, rsi: float, 
                                 macd_histogram: float, volume_ratio: float,
                                 price: float, vwap: float) -> float:
        """
        Calculate confidence score for trading signals (0-100).
        
        Higher score = higher confidence in signal quality.
        """
        try:
            score = 0.0
            
            # EMA alignment (20 points max)
            ema_diff_pct = abs((ema_short - ema_long) / ema_long) * 100
            if ema_diff_pct > 0.5:  # Strong trend
                score += 20
            elif ema_diff_pct > 0.2:  # Moderate trend
                score += 15
            elif ema_diff_pct > 0.1:  # Weak trend
                score += 10
            
            # RSI momentum (20 points max)
            if 30 <= rsi <= 70:  # Not overbought/oversold
                score += 10
            if rsi > 50:  # Bullish momentum
                score += 10
            elif rsi < 50:  # Bearish momentum (still valid)
                score += 5
            
            # MACD confirmation (20 points max)
            if abs(macd_histogram) > 0.1:  # Strong MACD signal
                score += 20
            elif abs(macd_histogram) > 0.05:  # Moderate MACD signal
                score += 15
            elif abs(macd_histogram) > 0.01:  # Weak MACD signal
                score += 10
            
            # Volume confirmation (20 points max)
            if volume_ratio > 2.0:  # High volume
                score += 20
            elif volume_ratio > 1.5:  # Above average volume
                score += 15
            elif volume_ratio > 1.2:  # Slightly above average
                score += 10
            elif volume_ratio > 0.8:  # Normal volume
                score += 5
            
            # VWAP position (20 points max)
            vwap_diff_pct = abs((price - vwap) / vwap) * 100
            if vwap_diff_pct < 0.1:  # Very close to VWAP
                score += 20
            elif vwap_diff_pct < 0.3:  # Close to VWAP
                score += 15
            elif vwap_diff_pct < 0.5:  # Moderate distance
                score += 10
            elif vwap_diff_pct < 1.0:  # Far from VWAP
                score += 5
            
            return min(score, 100.0)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 50.0  # Default neutral score
    
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
    
    @staticmethod
    def detect_enhanced_signal(features: Dict) -> Optional[Dict]:
        """
        Detect enhanced multi-indicator trading signals.
        
        NOW MORE PERMISSIVE: Generates signals based on trend direction,
        not just crossovers. If AI recommended it, we find an entry!
        
        Returns:
            Dictionary with signal info or None
        """
        try:
            # Check for EMA crossover (primary signal)
            ema_signal = FeatureEngine.detect_ema_crossover(features)
            
            # If no crossover, check if we're in a clear trend
            if not ema_signal:
                ema_short = features.get('ema_short', 0)
                ema_long = features.get('ema_long', 0)
                ema_diff_pct = features.get('ema_diff_pct', 0)
                
                # If EMAs are clearly separated, trade in that direction
                if abs(ema_diff_pct) > 0.1:  # 0.1% separation
                    if ema_short > ema_long:
                        ema_signal = 'buy'  # Uptrend
                    else:
                        ema_signal = 'sell'  # Downtrend
                else:
                    # No clear trend, skip
                    return None
            
            # Get confidence score
            confidence = features.get('confidence_score', 50.0)
            
            # Multi-indicator confirmation
            confirmations = []
            
            # RSI confirmation
            rsi = features.get('rsi', 50)
            if ema_signal == 'buy' and rsi > 50:
                confirmations.append('rsi_bullish')
            elif ema_signal == 'sell' and rsi < 50:
                confirmations.append('rsi_bearish')
            
            # MACD confirmation
            macd_histogram = features.get('macd_histogram', 0)
            if ema_signal == 'buy' and macd_histogram > 0:
                confirmations.append('macd_bullish')
            elif ema_signal == 'sell' and macd_histogram < 0:
                confirmations.append('macd_bearish')
            
            # Volume confirmation
            volume_ratio = features.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                confirmations.append('volume_confirmed')
            
            # VWAP confirmation
            vwap_signal = features.get('vwap_signal', 0)
            if (ema_signal == 'buy' and vwap_signal >= 0) or \
               (ema_signal == 'sell' and vwap_signal <= 0):
                confirmations.append('vwap_aligned')
            
            # Market regime check
            market_regime = features.get('market_regime', 'transitional')
            
            return {
                'signal': ema_signal,
                'confidence': confidence,
                'confirmations': confirmations,
                'confirmation_count': len(confirmations),
                'market_regime': market_regime,
                'rsi': rsi,
                'adx': features.get('adx', 0),
                'volume_ratio': volume_ratio
            }
            
        except Exception as e:
            logger.error(f"Error detecting enhanced signal: {e}")
            return None
