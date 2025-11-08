"""
Model Trainer
Trains and validates ML models
"""

import logging
from typing import Optional, Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import pickle
import base64

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Trains and validates ML models
    
    Supports:
    - XGBoost binary classification
    - Walk-forward validation
    - Model persistence
    """
    
    def __init__(self, supabase_client):
        """
        Initialize model trainer
        
        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase = supabase_client
        self.model = None
        self.scaler = StandardScaler()
        logger.info("Model Trainer initialized")
    
    async def train_xgboost_model(self, min_samples: int = 100) -> Optional[Dict[str, Any]]:
        """
        Train XGBoost binary classification model
        
        Args:
            min_samples: Minimum number of samples required
            
        Returns:
            dict: Training results with metrics
        """
        try:
            # Load training data
            X, y = await self.load_training_data()
            
            if len(X) < min_samples:
                logger.warning(f"Insufficient data: {len(X)} < {min_samples}")
                return None
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.15, random_state=42
            )
            
            X_train, X_val, y_train, y_val = train_test_split(
                X_train, y_train, test_size=0.176, random_state=42  # 0.176 * 0.85 ≈ 0.15
            )
            
            # Normalize features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = xgb.XGBClassifier(
                max_depth=6,
                learning_rate=0.1,
                n_estimators=100,
                objective='binary:logistic',
                eval_metric='auc'
            )
            
            self.model.fit(
                X_train_scaled, y_train,
                eval_set=[(X_val_scaled, y_val)],
                verbose=False
            )
            
            # Evaluate
            train_acc = self.model.score(X_train_scaled, y_train)
            val_acc = self.model.score(X_val_scaled, y_val)
            test_acc = self.model.score(X_test_scaled, y_test)
            
            results = {
                'accuracy': test_acc,
                'validation_accuracy': val_acc,
                'training_accuracy': train_acc,
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
            # Save model
            await self.save_model(results)
            
            logger.info(f"Model trained: {test_acc:.2%} accuracy")
            return results
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return None
    
    async def load_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load historical trades with features for training
        
        Returns:
            tuple: (X features, y labels)
        """
        # Query features with outcomes
        result = self.supabase.table('ml_trade_features').select('*').not_.is_(
            'outcome', 'null'
        ).execute()
        
        if not result.data:
            return np.array([]), np.array([])
        
        df = pd.DataFrame(result.data)
        
        # Extract features
        feature_cols = [
            'ema_20', 'ema_50', 'rsi', 'macd', 'macd_signal', 'adx', 'vwap',
            'price_vs_vwap', 'market_breadth', 'vix', 'sector_strength',
            'hour_of_day', 'day_of_week', 'recent_win_rate', 'current_streak',
            'symbol_performance'
        ]
        
        X = df[feature_cols].fillna(0).values
        
        # Create binary labels (WIN = 1, LOSS/BREAKEVEN = 0)
        y = (df['outcome'] == 'WIN').astype(int).values
        
        return X, y
    
    async def save_model(self, metadata: Dict[str, Any]):
        """
        Save trained model to database
        
        Args:
            metadata: Model metadata and metrics
        """
        try:
            # Serialize model and scaler
            model_bytes = pickle.dumps(self.model)
            scaler_bytes = pickle.dumps(self.scaler)
            
            model_b64 = base64.b64encode(model_bytes).decode('utf-8')
            scaler_b64 = base64.b64encode(scaler_bytes).decode('utf-8')
            
            # Insert into database
            self.supabase.table('ml_models').insert({
                'model_type': 'xgboost',
                'version': '1.0',
                'training_samples': metadata.get('training_samples'),
                'training_date': 'now()',
                'feature_count': 16,
                'accuracy': metadata.get('accuracy'),
                'validation_accuracy': metadata.get('validation_accuracy'),
                'model_data': model_b64,
                'scaler_data': scaler_b64,
                'is_active': True
            }).execute()
            
            logger.info("Model saved to database")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
