"""
Fitness calculator for parameter optimization.
Uses Sharpe ratio as the primary fitness metric to prevent overfitting.
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

from .models import PerformanceMetrics

logger = logging.getLogger(__name__)


class FitnessCalculator:
    """
    Calculates fitness metrics for parameter evaluation.
    Uses Sharpe ratio as primary metric to prevent overfitting to lucky trades.
    """
    
    def __init__(self, risk_free_rate: float = 0.05, trading_days_per_year: int = 252):
        """
        Initialize fitness calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate (default 5%)
            trading_days_per_year: Number of trading days per year
        """
        self.risk_free_rate = risk_free_rate
        self.trading_days_per_year = trading_days_per_year
        self.daily_risk_free = risk_free_rate / trading_days_per_year
    
    def calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """
        Calculate annualized Sharpe ratio from daily returns.
        
        Args:
            returns: List of daily returns (as decimals, e.g., 0.01 for 1%)
            
        Returns:
            Annualized Sharpe ratio
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        
        # Calculate excess returns
        excess_returns = returns_array - self.daily_risk_free
        
        # Calculate mean and std of excess returns
        mean_excess = np.mean(excess_returns)
        std_excess = np.std(excess_returns, ddof=1)
        
        # Handle zero volatility case
        if std_excess == 0 or np.isnan(std_excess):
            return 0.0
        
        # Calculate daily Sharpe and annualize
        daily_sharpe = mean_excess / std_excess
        annualized_sharpe = daily_sharpe * np.sqrt(self.trading_days_per_year)
        
        return float(annualized_sharpe)
    
    def calculate_win_rate(self, trades: List[Dict]) -> float:
        """
        Calculate win rate from list of trades.
        
        Args:
            trades: List of trade dictionaries with 'pnl' field
            
        Returns:
            Win rate as decimal (0.0 to 1.0)
        """
        if not trades:
            return 0.0
        
        winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
        return winning_trades / len(trades)
    
    def calculate_profit_factor(self, trades: List[Dict]) -> float:
        """
        Calculate profit factor (gross profit / gross loss).
        
        Args:
            trades: List of trade dictionaries with 'pnl' field
            
        Returns:
            Profit factor (>1 is profitable)
        """
        if not trades:
            return 0.0
        
        gross_profit = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
        gross_loss = abs(sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """
        Calculate maximum drawdown from equity curve.
        
        Args:
            equity_curve: List of equity values over time
            
        Returns:
            Maximum drawdown as decimal (e.g., 0.15 for 15%)
        """
        if not equity_curve or len(equity_curve) < 2:
            return 0.0
        
        equity = np.array(equity_curve)
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / peak
        
        return float(np.max(drawdown))
    
    def calculate_metrics(self, trades: List[Dict], equity_curve: Optional[List[float]] = None) -> PerformanceMetrics:
        """
        Calculate all performance metrics from trades.
        
        Args:
            trades: List of trade dictionaries with 'pnl' and 'return' fields
            equity_curve: Optional equity curve for drawdown calculation
            
        Returns:
            PerformanceMetrics object
        """
        if not trades:
            return PerformanceMetrics(
                sharpe_ratio=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                total_return=0.0,
                max_drawdown=0.0,
            )
        
        # Extract returns for Sharpe calculation
        returns = [t.get('return', t.get('pnl', 0) / 10000) for t in trades]  # Assume $10k base if no return
        
        # Calculate equity curve if not provided
        if equity_curve is None:
            equity_curve = [10000]  # Start with $10k
            for t in trades:
                equity_curve.append(equity_curve[-1] + t.get('pnl', 0))
        
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0] if equity_curve[0] > 0 else 0.0
        
        return PerformanceMetrics(
            sharpe_ratio=self.calculate_sharpe_ratio(returns),
            win_rate=self.calculate_win_rate(trades),
            profit_factor=self.calculate_profit_factor(trades),
            total_trades=len(trades),
            total_return=total_return,
            max_drawdown=self.calculate_max_drawdown(equity_curve),
        )
    
    def calculate_fitness(self, parameters: Dict[str, float], trades: List[Dict]) -> float:
        """
        Calculate fitness score for a parameter set.
        Uses Sharpe ratio as primary metric to prevent overfitting.
        
        Args:
            parameters: Dictionary of parameter values
            trades: List of trades generated with these parameters
            
        Returns:
            Fitness score (higher is better)
        """
        metrics = self.calculate_metrics(trades)
        
        # Primary fitness is Sharpe ratio
        fitness = metrics.sharpe_ratio
        
        # Penalize if too few trades (might be overfitting to specific conditions)
        if metrics.total_trades < 10:
            fitness *= 0.5
        
        # Penalize high drawdown
        if metrics.max_drawdown > 0.20:
            fitness *= (1 - metrics.max_drawdown)
        
        # Bonus for good win rate
        if metrics.win_rate > 0.55:
            fitness *= (1 + (metrics.win_rate - 0.55))
        
        return fitness
