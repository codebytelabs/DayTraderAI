"""
ML System Module
Sprint 1: ML Foundation + Position Management

This module provides machine learning capabilities for the trading system:
- Feature extraction from market data
- Model training and validation
- Real-time predictions
- Performance tracking
"""

from .ml_system import MLSystem
from .feature_extractor import FeatureExtractor
from .model_trainer import ModelTrainer
from .predictor import Predictor
from .performance_tracker import PerformanceTracker

__all__ = [
    'MLSystem',
    'FeatureExtractor',
    'ModelTrainer',
    'Predictor',
    'PerformanceTracker'
]

__version__ = '1.0.0'
