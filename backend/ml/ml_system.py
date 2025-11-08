"""
ML System - Main Coordinator
Coordinates all ML operations: feature extraction, training, prediction, tracking
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .feature_extractor import FeatureExtractor
from .model_trainer import ModelTrainer
from .predictor import Predictor
from .performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)


class MLSystem:
    """
    Main ML system coordinator
    
    Manages the entire ML pipeline:
    - Feature collection and storage
    - Model training and validation
    - Real-time predictions
    - Performance tracking
    """
    
    def __init__(self, supabase_client):
        """
        Initialize ML system
        
        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase = supabase_client
        self.feature_extractor = FeatureExtractor(supabase_client)
        self.model_trainer = ModelTrainer(supabase_client)
        self.predictor = Predictor(supabase_client)
        self.performance_tracker = PerformanceTracker(supabase_client)
        
        logger.info("ML System initialized")
    
    async def collect_trade_data(self, trade_data: Dict[str, Any]) -> bool:
        """
        Collect and store trade data with features
        
        Args:
            trade_data: Dictionary containing trade information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Extract features
            features = await self.feature_extractor.extract_all_features(
                symbol=trade_data['symbol'],
                signal_type=trade_data.get('signal_type', 'unknown'),
                market_data=trade_data.get('market_data', {})
            )
            
            # Store features in database
            result = self.supabase.table('ml_trade_features').insert({
                'trade_id': trade_data.get('trade_id'),
                'features_vector': features,
                **self.feature_extractor.flatten_features(features)
            }).execute()
            
            logger.info(f"Collected features for trade {trade_data.get('trade_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error collecting trade data: {e}")
            return False
    
    async def train_model(self, min_samples: int = 100) -> Optional[Dict[str, Any]]:
        """
        Train ML model on historical data
        
        Args:
            min_samples: Minimum number of samples required for training
            
        Returns:
            dict: Training results including metrics, or None if failed
        """
        try:
            logger.info("Starting model training...")
            
            # Train model
            results = await self.model_trainer.train_xgboost_model(
                min_samples=min_samples
            )
            
            if results and results.get('accuracy', 0) >= 0.55:
                logger.info(f"Model trained successfully: {results['accuracy']:.2%} accuracy")
                return results
            else:
                logger.warning(f"Model accuracy below threshold: {results.get('accuracy', 0):.2%}")
                return results
                
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return None
    
    async def predict(self, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make prediction for new trade signal
        
        Args:
            features: Feature dictionary
            
        Returns:
            dict: Prediction result with probability, confidence, prediction
        """
        try:
            # Make prediction
            prediction = await self.predictor.predict_trade_outcome(features)
            
            if prediction:
                logger.debug(f"Prediction: {prediction['prediction']} "
                           f"({prediction['probability']:.2%} confidence)")
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return None
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get ML system performance metrics
        
        Returns:
            dict: Performance metrics
        """
        try:
            metrics = await self.performance_tracker.get_current_metrics()
            return metrics
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    async def update_trade_outcome(self, trade_id: int, outcome: str, pnl_percent: float):
        """
        Update trade outcome after trade completes
        
        Args:
            trade_id: Trade ID
            outcome: 'WIN', 'LOSS', or 'BREAKEVEN'
            pnl_percent: P/L percentage
        """
        try:
            # Update features table
            self.supabase.table('ml_trade_features').update({
                'outcome': outcome,
                'pnl_percent': pnl_percent
            }).eq('trade_id', trade_id).execute()
            
            # Update predictions table
            self.supabase.table('ml_predictions').update({
                'actual_outcome': outcome,
                'was_correct': self.supabase.rpc('check_prediction_correct', {
                    'trade_id': trade_id
                })
            }).eq('trade_id', trade_id).execute()
            
            logger.info(f"Updated outcome for trade {trade_id}: {outcome}")
            
        except Exception as e:
            logger.error(f"Error updating trade outcome: {e}")
    
    def is_ready(self) -> bool:
        """
        Check if ML system is ready for predictions
        
        Returns:
            bool: True if model is loaded and ready
        """
        return self.predictor.is_model_loaded()
    
    async def initialize(self):
        """Initialize ML system (load latest model if available)"""
        try:
            await self.predictor.load_latest_model()
            logger.info("ML System initialized and ready")
        except Exception as e:
            logger.warning(f"Could not load model: {e}")
            logger.info("ML System initialized in collection-only mode")
