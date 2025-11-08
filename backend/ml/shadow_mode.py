"""
ML Shadow Mode
Integrates ML predictions into trading engine without affecting trades
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from .predictor import Predictor as MLPredictor
from .feature_extractor import FeatureExtractor

logger = logging.getLogger(__name__)


class MLShadowMode:
    """
    Runs ML predictions in shadow mode (0% weight)
    
    Features:
    - Predicts for every trade signal
    - Logs predictions to database
    - Tracks accuracy vs actual outcomes
    - Zero impact on trading decisions
    - Prepares for pilot mode
    """
    
    def __init__(self, supabase_client, ml_weight: float = 0.0):
        """
        Initialize ML shadow mode
        
        Args:
            supabase_client: Supabase database client
            ml_weight: ML weight (0.0 for shadow mode)
        """
        self.supabase = supabase_client
        self.ml_weight = ml_weight
        
        # Initialize ML components
        self.predictor = MLPredictor(supabase_client)
        self.feature_extractor = FeatureExtractor(supabase_client)
        
        # Statistics
        self.predictions_made = 0
        self.predictions_logged = 0
        self.errors = 0
        
        logger.info(f"ML Shadow Mode initialized (weight: {ml_weight})")
    
    async def get_prediction(
        self,
        symbol: str,
        signal_data: Dict[str, Any],
        existing_confidence: float
    ) -> Dict[str, Any]:
        """
        Get ML prediction for a trade signal
        
        Args:
            symbol: Stock symbol
            signal_data: Signal data (price, indicators, etc.)
            existing_confidence: Existing strategy confidence
            
        Returns:
            dict: Prediction result with blended confidence
        """
        try:
            start_time = datetime.now()
            
            # Extract features
            features = await self.feature_extractor.extract_features(
                symbol=symbol,
                signal_data=signal_data
            )
            
            if not features:
                logger.warning(f"Could not extract features for {symbol}")
                return self._create_fallback_result(existing_confidence)
            
            # Get ML prediction
            prediction = await self.predictor.predict(features)
            
            if not prediction:
                logger.warning(f"ML prediction failed for {symbol}")
                return self._create_fallback_result(existing_confidence)
            
            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Blend confidence (in shadow mode, ml_weight = 0, so no impact)
            blended_confidence = self._blend_confidence(
                existing_confidence,
                prediction['confidence']
            )
            
            # Create result
            result = {
                'symbol': symbol,
                'ml_confidence': prediction['confidence'],
                'ml_prediction': prediction['prediction'],
                'existing_confidence': existing_confidence,
                'blended_confidence': blended_confidence,
                'ml_weight': self.ml_weight,
                'features': features,
                'latency_ms': latency_ms,
                'timestamp': datetime.now().isoformat()
            }
            
            # Log prediction (async)
            asyncio.create_task(self._log_prediction(result, signal_data))
            
            self.predictions_made += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error in ML shadow mode prediction: {e}")
            self.errors += 1
            return self._create_fallback_result(existing_confidence)
    
    def _blend_confidence(self, existing: float, ml: float) -> float:
        """
        Blend existing and ML confidence
        
        Formula: blended = (1 - weight) * existing + weight * ml
        
        In shadow mode (weight=0): blended = existing (no impact)
        """
        return (1 - self.ml_weight) * existing + self.ml_weight * ml
    
    def _create_fallback_result(self, existing_confidence: float) -> Dict[str, Any]:
        """Create fallback result when ML fails"""
        return {
            'ml_confidence': None,
            'ml_prediction': None,
            'existing_confidence': existing_confidence,
            'blended_confidence': existing_confidence,  # No ML impact
            'ml_weight': 0.0,
            'features': None,
            'latency_ms': 0,
            'error': True
        }
    
    async def _log_prediction(self, prediction: Dict[str, Any], signal_data: Dict[str, Any]):
        """Log prediction to database"""
        try:
            # Prepare record
            record = {
                'symbol': prediction['symbol'],
                'ml_confidence': prediction['ml_confidence'],
                'ml_prediction': prediction['ml_prediction'],
                'existing_confidence': prediction['existing_confidence'],
                'blended_confidence': prediction['blended_confidence'],
                'ml_weight': prediction['ml_weight'],
                'latency_ms': prediction['latency_ms'],
                'signal_type': signal_data.get('signal_type'),
                'signal_price': signal_data.get('price'),
                'created_at': prediction['timestamp'],
                # Outcome will be updated later when trade completes
                'actual_outcome': None,
                'was_correct': None
            }
            
            # Insert into database
            self.supabase.table('ml_predictions').insert(record).execute()
            self.predictions_logged += 1
            
        except Exception as e:
            logger.error(f"Error logging ML prediction: {e}")
    
    async def update_prediction_outcome(
        self,
        symbol: str,
        timestamp: str,
        actual_pnl: float,
        trade_id: str
    ):
        """
        Update prediction with actual outcome
        
        Args:
            symbol: Stock symbol
            timestamp: Prediction timestamp
            actual_pnl: Actual P/L from trade
            trade_id: Trade ID
        """
        try:
            # Determine outcome
            actual_outcome = 'WIN' if actual_pnl > 0 else 'LOSS' if actual_pnl < 0 else 'BREAKEVEN'
            
            # Get prediction
            result = self.supabase.table('ml_predictions').select('*').eq(
                'symbol', symbol
            ).eq(
                'created_at', timestamp
            ).execute()
            
            if not result.data:
                logger.warning(f"Prediction not found for {symbol} at {timestamp}")
                return
            
            prediction = result.data[0]
            ml_prediction = prediction.get('ml_prediction')
            
            # Determine if prediction was correct
            was_correct = (
                (ml_prediction == 'WIN' and actual_outcome == 'WIN') or
                (ml_prediction == 'LOSS' and actual_outcome == 'LOSS')
            )
            
            # Update record
            self.supabase.table('ml_predictions').update({
                'actual_outcome': actual_outcome,
                'actual_pnl': actual_pnl,
                'was_correct': was_correct,
                'trade_id': trade_id,
                'updated_at': datetime.now().isoformat()
            }).eq('id', prediction['id']).execute()
            
            logger.info(f"Updated prediction outcome for {symbol}: {actual_outcome} (correct: {was_correct})")
            
        except Exception as e:
            logger.error(f"Error updating prediction outcome: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get shadow mode statistics"""
        return {
            'predictions_made': self.predictions_made,
            'predictions_logged': self.predictions_logged,
            'errors': self.errors,
            'ml_weight': self.ml_weight,
            'success_rate': (self.predictions_logged / max(self.predictions_made, 1)) * 100
        }
    
    async def get_accuracy_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get accuracy metrics for recent predictions
        
        Args:
            days: Number of days to analyze
            
        Returns:
            dict: Accuracy metrics
        """
        try:
            from datetime import timedelta
            
            # Get predictions from last N days
            start_date = datetime.now() - timedelta(days=days)
            
            result = self.supabase.table('ml_predictions').select('*').gte(
                'created_at', start_date.isoformat()
            ).not_.is_('actual_outcome', 'null').execute()
            
            predictions = result.data if result.data else []
            
            if not predictions:
                return {
                    'total_predictions': 0,
                    'accuracy': 0,
                    'message': 'No completed predictions yet'
                }
            
            # Calculate metrics
            total = len(predictions)
            correct = sum(1 for p in predictions if p.get('was_correct'))
            accuracy = (correct / total) * 100
            
            # By outcome
            wins = [p for p in predictions if p.get('actual_outcome') == 'WIN']
            losses = [p for p in predictions if p.get('actual_outcome') == 'LOSS']
            
            win_accuracy = (sum(1 for p in wins if p.get('was_correct')) / len(wins) * 100) if wins else 0
            loss_accuracy = (sum(1 for p in losses if p.get('was_correct')) / len(losses) * 100) if losses else 0
            
            # Average confidence
            avg_confidence = sum(p.get('ml_confidence', 0) for p in predictions) / total
            
            # Latency
            avg_latency = sum(p.get('latency_ms', 0) for p in predictions) / total
            max_latency = max(p.get('latency_ms', 0) for p in predictions)
            
            return {
                'total_predictions': total,
                'correct_predictions': correct,
                'accuracy': round(accuracy, 1),
                'win_accuracy': round(win_accuracy, 1),
                'loss_accuracy': round(loss_accuracy, 1),
                'avg_confidence': round(avg_confidence, 2),
                'avg_latency_ms': round(avg_latency, 1),
                'max_latency_ms': max_latency,
                'days_analyzed': days
            }
            
        except Exception as e:
            logger.error(f"Error calculating accuracy metrics: {e}")
            return {'error': str(e)}
    
    def set_ml_weight(self, new_weight: float):
        """
        Update ML weight
        
        Args:
            new_weight: New ML weight (0.0-1.0)
        """
        if not 0.0 <= new_weight <= 1.0:
            raise ValueError("ML weight must be between 0.0 and 1.0")
        
        old_weight = self.ml_weight
        self.ml_weight = new_weight
        
        logger.info(f"ML weight updated: {old_weight} → {new_weight}")
