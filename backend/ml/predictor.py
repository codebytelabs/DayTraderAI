"""
Predictor
Real-time ML prediction engine
"""

import logging
from typing import Optional, Dict, Any
import numpy as np
import pickle
import base64
import time

logger = logging.getLogger(__name__)


class Predictor:
    """
    Real-time prediction engine
    
    Makes fast predictions (<50ms) for trade signals
    """
    
    def __init__(self, supabase_client):
        """
        Initialize predictor
        
        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase = supabase_client
        self.model = None
        self.scaler = None
        self.model_id = None
        logger.info("Predictor initialized")
    
    async def load_latest_model(self):
        """Load the latest active model from database"""
        try:
            result = self.supabase.table('ml_models').select('*').eq(
                'is_active', True
            ).order('created_at', desc=True).limit(1).execute()
            
            if not result.data:
                logger.warning("No active model found")
                return
            
            model_data = result.data[0]
            self.model_id = model_data['id']
            
            # Deserialize model and scaler
            model_bytes = base64.b64decode(model_data['model_data'])
            scaler_bytes = base64.b64decode(model_data['scaler_data'])
            
            self.model = pickle.loads(model_bytes)
            self.scaler = pickle.loads(scaler_bytes)
            
            logger.info(f"Loaded model {self.model_id} (accuracy: {model_data['accuracy']:.2%})")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
    
    async def predict_trade_outcome(self, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Predict outcome for trade signal
        
        Args:
            features: Feature dictionary
            
        Returns:
            dict: Prediction result with probability, confidence, prediction, latency
        """
        if not self.is_model_loaded():
            logger.warning("Model not loaded, cannot make prediction")
            return None
        
        try:
            start_time = time.time()
            
            # Convert features to array
            feature_array = self._features_to_array(features)
            
            # Normalize
            feature_scaled = self.scaler.transform(feature_array.reshape(1, -1))
            
            # Predict
            probability = self.model.predict_proba(feature_scaled)[0][1]  # Probability of WIN
            prediction = 'WIN' if probability >= 0.5 else 'LOSS'
            confidence = max(probability, 1 - probability)  # Distance from 0.5
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            result = {
                'probability': float(probability),
                'confidence': float(confidence),
                'prediction': prediction,
                'latency_ms': latency_ms,
                'model_id': self.model_id
            }
            
            # Log prediction to database
            await self._log_prediction(features, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return None
    
    def _features_to_array(self, features: Dict[str, Any]) -> np.ndarray:
        """Convert features dict to numpy array"""
        feature_keys = [
            'ema_20', 'ema_50', 'rsi', 'macd', 'macd_signal', 'adx', 'vwap',
            'price_vs_vwap', 'market_breadth', 'vix', 'sector_strength',
            'hour_of_day', 'day_of_week', 'recent_win_rate', 'current_streak',
            'symbol_performance'
        ]
        
        return np.array([features.get(k, 0.0) for k in feature_keys], dtype=np.float32)
    
    async def _log_prediction(self, features: Dict[str, Any], result: Dict[str, Any]):
        """Log prediction to database"""
        try:
            self.supabase.table('ml_predictions').insert({
                'trade_id': features.get('trade_id'),
                'model_id': self.model_id,
                'probability': result['probability'],
                'confidence': result['confidence'],
                'prediction': result['prediction'],
                'latency_ms': result['latency_ms'],
                'features_used': features
            }).execute()
        except Exception as e:
            logger.error(f"Error logging prediction: {e}")
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded and ready"""
        return self.model is not None and self.scaler is not None
