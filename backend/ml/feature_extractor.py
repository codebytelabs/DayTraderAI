"""
Feature Extractor
Extracts features from market data for ML training and prediction
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extracts and normalizes features from market data
    
    Features extracted:
    - Technical indicators (EMA, RSI, MACD, ADX, VWAP)
    - Market regime and breadth
    - Timing features (time of day, day of week, session)
    - Historical performance
    """
    
    def __init__(self, supabase_client):
        """
        Initialize feature extractor
        
        Args:
            supabase_client: Supabase client for database queries
        """
        self.supabase = supabase_client
        logger.info("Feature Extractor initialized")
    
    async def extract_all_features(
        self,
        symbol: str,
        signal_type: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract all features for a trade signal
        
        Args:
            symbol: Stock symbol
            signal_type: 'long' or 'short'
            market_data: Current market data
            
        Returns:
            dict: Complete feature set
        """
        features = {}
        
        # Extract different feature types
        features.update(self.extract_technical_features(market_data))
        features.update(self.extract_market_features(market_data))
        features.update(self.extract_timing_features(datetime.now()))
        features.update(await self.extract_historical_features(symbol))
        
        # Add metadata
        features['symbol'] = symbol
        features['signal_type'] = signal_type
        
        return features
    
    def extract_technical_features(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract technical indicator features
        
        Args:
            market_data: Market data dictionary
            
        Returns:
            dict: Technical features
        """
        features = {}
        
        try:
            # EMA values
            features['ema_20'] = market_data.get('ema_20', 0.0)
            features['ema_50'] = market_data.get('ema_50', 0.0)
            
            # RSI
            features['rsi'] = market_data.get('rsi', 50.0)
            
            # MACD
            features['macd'] = market_data.get('macd', 0.0)
            features['macd_signal'] = market_data.get('macd_signal', 0.0)
            
            # ADX (trend strength)
            features['adx'] = market_data.get('adx', 0.0)
            
            # VWAP
            features['vwap'] = market_data.get('vwap', 0.0)
            
            # Price vs VWAP
            price = market_data.get('price', 0.0)
            vwap = features['vwap']
            if vwap > 0:
                features['price_vs_vwap'] = ((price - vwap) / vwap) * 100
            else:
                features['price_vs_vwap'] = 0.0
            
        except Exception as e:
            logger.error(f"Error extracting technical features: {e}")
        
        return features
    
    def extract_market_features(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract market regime and breadth features
        
        Args:
            market_data: Market data dictionary
            
        Returns:
            dict: Market features
        """
        features = {}
        
        try:
            # Market regime
            features['regime'] = market_data.get('regime', 'unknown')
            
            # Market breadth (% of stocks above EMA)
            features['market_breadth'] = market_data.get('market_breadth', 50.0)
            
            # VIX (volatility index)
            features['vix'] = market_data.get('vix', 15.0)
            
            # Sector strength
            features['sector_strength'] = market_data.get('sector_strength', 0.0)
            
        except Exception as e:
            logger.error(f"Error extracting market features: {e}")
        
        return features
    
    def extract_timing_features(self, timestamp: datetime) -> Dict[str, int]:
        """
        Extract timing-based features
        
        Args:
            timestamp: Current timestamp
            
        Returns:
            dict: Timing features
        """
        features = {}
        
        try:
            # Hour of day (0-23)
            features['hour_of_day'] = timestamp.hour
            
            # Day of week (0-6, Monday=0)
            features['day_of_week'] = timestamp.weekday()
            
            # Market session
            hour = timestamp.hour
            if hour < 9 or (hour == 9 and timestamp.minute < 30):
                session = 'pre_market'
            elif hour == 9 and timestamp.minute >= 30:
                session = 'open'
            elif 10 <= hour < 15:
                session = 'mid_day'
            elif hour == 15:
                session = 'close'
            else:
                session = 'after_hours'
            
            features['market_session'] = session
            
        except Exception as e:
            logger.error(f"Error extracting timing features: {e}")
        
        return features
    
    async def extract_historical_features(self, symbol: str) -> Dict[str, float]:
        """
        Extract historical performance features
        
        Args:
            symbol: Stock symbol
            
        Returns:
            dict: Historical features
        """
        features = {
            'recent_win_rate': 50.0,  # Default to 50%
            'current_streak': 0,
            'symbol_performance': 0.0
        }
        
        try:
            # Get last 10 trades
            result = self.supabase.table('trades').select('*').order(
                'timestamp', desc=True
            ).limit(10).execute()
            
            if result.data:
                trades = result.data
                wins = sum(1 for t in trades if t['pnl'] > 0)
                features['recent_win_rate'] = (wins / len(trades)) * 100
                
                # Calculate current streak
                streak = 0
                for trade in trades:
                    if trade['pnl'] > 0:
                        if streak >= 0:
                            streak += 1
                        else:
                            break
                    else:
                        if streak <= 0:
                            streak -= 1
                        else:
                            break
                features['current_streak'] = streak
            
            # Get symbol-specific performance
            symbol_result = self.supabase.table('trades').select('pnl').eq(
                'symbol', symbol
            ).execute()
            
            if symbol_result.data:
                avg_pnl = np.mean([t['pnl'] for t in symbol_result.data])
                features['symbol_performance'] = float(avg_pnl)
            
        except Exception as e:
            logger.error(f"Error extracting historical features: {e}")
        
        return features
    
    def normalize_features(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Normalize features to consistent scale
        
        Args:
            features: Raw features dictionary
            
        Returns:
            np.ndarray: Normalized feature vector
        """
        # TODO: Implement proper normalization with StandardScaler
        # For now, return raw features as array
        feature_list = []
        
        # Numeric features in order
        numeric_keys = [
            'ema_20', 'ema_50', 'rsi', 'macd', 'macd_signal', 'adx', 'vwap',
            'price_vs_vwap', 'market_breadth', 'vix', 'sector_strength',
            'hour_of_day', 'day_of_week', 'recent_win_rate', 'current_streak',
            'symbol_performance'
        ]
        
        for key in numeric_keys:
            feature_list.append(features.get(key, 0.0))
        
        return np.array(feature_list, dtype=np.float32)
    
    def flatten_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten features for database storage
        
        Args:
            features: Features dictionary
            
        Returns:
            dict: Flattened features ready for database
        """
        flattened = {}
        
        # Copy numeric features
        for key, value in features.items():
            if isinstance(value, (int, float, str)):
                flattened[key] = value
        
        return flattened
