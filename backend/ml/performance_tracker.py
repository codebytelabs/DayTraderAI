"""
Performance Tracker
Tracks ML system performance metrics
"""

import logging
from typing import Dict, Any
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Tracks ML system performance
    
    Monitors:
    - Prediction accuracy
    - Performance vs baseline
    - Latency metrics
    - Financial impact
    """
    
    def __init__(self, supabase_client):
        """
        Initialize performance tracker
        
        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase = supabase_client
        logger.info("Performance Tracker initialized")
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics
        
        Returns:
            dict: Current metrics
        """
        try:
            # Get today's predictions
            today = date.today()
            
            result = self.supabase.table('ml_predictions').select('*').gte(
                'created_at', today.isoformat()
            ).execute()
            
            if not result.data:
                return {
                    'predictions_made': 0,
                    'accuracy': 0.0,
                    'avg_latency_ms': 0.0
                }
            
            predictions = result.data
            
            # Calculate metrics
            total = len(predictions)
            correct = sum(1 for p in predictions if p.get('was_correct'))
            accuracy = (correct / total) * 100 if total > 0 else 0.0
            
            latencies = [p['latency_ms'] for p in predictions if p.get('latency_ms')]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
            
            return {
                'predictions_made': total,
                'correct_predictions': correct,
                'accuracy': accuracy,
                'avg_latency_ms': avg_latency,
                'max_latency_ms': max(latencies) if latencies else 0,
                'min_latency_ms': min(latencies) if latencies else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
    
    async def update_daily_performance(self, model_id: int):
        """
        Update daily performance metrics
        
        Args:
            model_id: Model ID to track
        """
        try:
            today = date.today()
            metrics = await self.get_current_metrics()
            
            # Insert or update daily performance
            self.supabase.table('ml_performance').upsert({
                'date': today.isoformat(),
                'model_id': model_id,
                **metrics
            }).execute()
            
            logger.info(f"Updated daily performance: {metrics['accuracy']:.2%} accuracy")
            
        except Exception as e:
            logger.error(f"Error updating daily performance: {e}")
    
    async def get_performance_history(self, days: int = 30) -> Dict[str, Any]:
        """
        Get performance history
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            dict: Historical performance data
        """
        try:
            start_date = date.today() - timedelta(days=days)
            
            result = self.supabase.table('ml_performance').select('*').gte(
                'date', start_date.isoformat()
            ).order('date', desc=True).execute()
            
            return {
                'history': result.data if result.data else [],
                'days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting performance history: {e}")
            return {'history': [], 'days': days}
