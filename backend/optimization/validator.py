"""
Walk-forward validator for parameter optimization.
Prevents overfitting by validating on out-of-sample data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

from .models import ValidationResult, PerformanceMetrics
from .fitness import FitnessCalculator

logger = logging.getLogger(__name__)


class WalkForwardValidator:
    """
    Validates optimized parameters using walk-forward methodology.
    Splits data into training and validation periods to detect overfitting.
    """
    
    def __init__(
        self,
        train_ratio: float = 0.70,
        overfitting_threshold: float = 0.25,
    ):
        """
        Initialize walk-forward validator.
        
        Args:
            train_ratio: Ratio of data for training (default 70%)
            overfitting_threshold: Performance degradation threshold for overfitting detection
        """
        self.train_ratio = train_ratio
        self.validate_ratio = 1.0 - train_ratio
        self.overfitting_threshold = overfitting_threshold
        self.fitness_calculator = FitnessCalculator()
    
    def split_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data into training and validation sets.
        Maintains chronological order.
        
        Args:
            data: DataFrame with datetime index or 'date' column
            
        Returns:
            Tuple of (training_data, validation_data)
        """
        if data.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # Ensure data is sorted by date
        if 'date' in data.columns:
            data = data.sort_values('date')
        elif isinstance(data.index, pd.DatetimeIndex):
            data = data.sort_index()
        
        # Calculate split point
        split_idx = int(len(data) * self.train_ratio)
        
        train_data = data.iloc[:split_idx].copy()
        validate_data = data.iloc[split_idx:].copy()
        
        logger.info(
            f"📊 Data split: {len(train_data)} training ({self.train_ratio*100:.0f}%), "
            f"{len(validate_data)} validation ({self.validate_ratio*100:.0f}%)"
        )
        
        return train_data, validate_data
    
    def split_by_months(
        self,
        data: pd.DataFrame,
        train_months: int = 4,
        validate_months: int = 2
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data by specific month periods.
        
        Args:
            data: DataFrame with datetime index or 'date' column
            train_months: Number of months for training
            validate_months: Number of months for validation
            
        Returns:
            Tuple of (training_data, validation_data)
        """
        if data.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # Get date column
        if 'date' in data.columns:
            dates = pd.to_datetime(data['date'])
        elif isinstance(data.index, pd.DatetimeIndex):
            dates = data.index
        else:
            # Fall back to ratio-based split
            return self.split_data(data)
        
        # Calculate date ranges
        end_date = dates.max()
        validate_start = end_date - timedelta(days=validate_months * 30)
        train_start = validate_start - timedelta(days=train_months * 30)
        
        # Filter data
        if 'date' in data.columns:
            train_mask = (data['date'] >= train_start) & (data['date'] < validate_start)
            validate_mask = data['date'] >= validate_start
        else:
            train_mask = (data.index >= train_start) & (data.index < validate_start)
            validate_mask = data.index >= validate_start
        
        train_data = data[train_mask].copy()
        validate_data = data[validate_mask].copy()
        
        logger.info(
            f"📊 Data split by months: {len(train_data)} training ({train_months}mo), "
            f"{len(validate_data)} validation ({validate_months}mo)"
        )
        
        return train_data, validate_data
    
    def detect_overfitting(
        self,
        in_sample_metrics: PerformanceMetrics,
        out_sample_metrics: PerformanceMetrics,
    ) -> Tuple[bool, float]:
        """
        Detect if parameters are overfitted.
        
        Args:
            in_sample_metrics: Performance on training data
            out_sample_metrics: Performance on validation data
            
        Returns:
            Tuple of (is_overfitted, degradation_percent)
        """
        # Calculate degradation in Sharpe ratio
        if in_sample_metrics.sharpe_ratio <= 0:
            # Can't calculate degradation if in-sample is non-positive
            return False, 0.0
        
        degradation = 1 - (out_sample_metrics.sharpe_ratio / in_sample_metrics.sharpe_ratio)
        
        # Also check win rate degradation
        if in_sample_metrics.win_rate > 0:
            win_rate_degradation = 1 - (out_sample_metrics.win_rate / in_sample_metrics.win_rate)
        else:
            win_rate_degradation = 0.0
        
        # Use the worse of the two degradations
        max_degradation = max(degradation, win_rate_degradation)
        
        is_overfitted = max_degradation > self.overfitting_threshold
        
        if is_overfitted:
            logger.warning(
                f"⚠️ Overfitting detected! Degradation: {max_degradation*100:.1f}% "
                f"(threshold: {self.overfitting_threshold*100:.0f}%)"
            )
        else:
            logger.info(
                f"✅ No overfitting detected. Degradation: {max_degradation*100:.1f}%"
            )
        
        return is_overfitted, max_degradation
    
    def validate(
        self,
        parameters: Dict[str, float],
        train_trades: List[Dict],
        validate_trades: List[Dict],
    ) -> ValidationResult:
        """
        Validate parameters on out-of-sample data.
        
        Args:
            parameters: Optimized parameter values
            train_trades: Trades from training period
            validate_trades: Trades from validation period
            
        Returns:
            ValidationResult with metrics and overfitting detection
        """
        # Calculate metrics for both periods
        in_sample_metrics = self.fitness_calculator.calculate_metrics(train_trades)
        out_sample_metrics = self.fitness_calculator.calculate_metrics(validate_trades)
        
        # Detect overfitting
        is_overfitted, degradation = self.detect_overfitting(
            in_sample_metrics, out_sample_metrics
        )
        
        logger.info(
            f"📈 In-sample: Sharpe={in_sample_metrics.sharpe_ratio:.2f}, "
            f"WinRate={in_sample_metrics.win_rate*100:.1f}%"
        )
        logger.info(
            f"📉 Out-sample: Sharpe={out_sample_metrics.sharpe_ratio:.2f}, "
            f"WinRate={out_sample_metrics.win_rate*100:.1f}%"
        )
        
        return ValidationResult(
            in_sample_metrics=in_sample_metrics,
            out_sample_metrics=out_sample_metrics,
            overfitting_detected=is_overfitted,
            degradation_percent=degradation,
        )
