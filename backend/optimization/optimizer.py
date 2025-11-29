"""
Parameter optimizer using scikit-opt (PSO/GA).
Optimizes trading parameters with walk-forward validation.
"""

import numpy as np
from typing import Dict, List, Tuple, Callable, Optional
from datetime import datetime
import logging

from sko.PSO import PSO
from sko.GA import GA

from .models import (
    OptimizationResult,
    PerformanceMetrics,
    REGIME_PARAMETERS,
    MOMENTUM_PARAMETERS,
    ALL_PARAMETERS,
    validate_parameters,
    clamp_parameters,
)
from .fitness import FitnessCalculator
from .validator import WalkForwardValidator

logger = logging.getLogger(__name__)


class ParameterOptimizer:
    """
    Optimizes trading parameters using swarm intelligence algorithms.
    Uses PSO (Particle Swarm Optimization) by default for faster convergence.
    """
    
    def __init__(
        self,
        algorithm: str = "PSO",
        population_size: int = 40,
        max_iterations: int = 100,
    ):
        """
        Initialize parameter optimizer.
        
        Args:
            algorithm: "PSO" or "GA"
            population_size: Number of particles/individuals
            max_iterations: Maximum optimization iterations
        """
        self.algorithm = algorithm.upper()
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.fitness_calculator = FitnessCalculator()
        self.validator = WalkForwardValidator()
        
        logger.info(
            f"🔧 Parameter Optimizer initialized: {self.algorithm}, "
            f"pop={population_size}, iter={max_iterations}"
        )
    
    def _create_fitness_function(
        self,
        parameter_names: List[str],
        backtest_func: Callable[[Dict[str, float]], List[Dict]],
    ) -> Callable:
        """
        Create fitness function for optimization.
        
        Args:
            parameter_names: List of parameter names in order
            backtest_func: Function that takes parameters and returns trades
            
        Returns:
            Fitness function for PSO/GA
        """
        def fitness(x):
            # Convert array to parameter dict
            params = {name: x[i] for i, name in enumerate(parameter_names)}
            
            # Run backtest
            try:
                trades = backtest_func(params)
                
                # Calculate fitness (negative because PSO minimizes)
                fitness_score = self.fitness_calculator.calculate_fitness(params, trades)
                
                return -fitness_score  # Negative for minimization
            except Exception as e:
                logger.warning(f"Backtest failed: {e}")
                return float('inf')  # Worst fitness
        
        return fitness
    
    def optimize(
        self,
        parameter_space: Dict[str, Tuple[float, float]],
        backtest_func: Callable[[Dict[str, float]], List[Dict]],
    ) -> OptimizationResult:
        """
        Run parameter optimization.
        
        Args:
            parameter_space: Dict of parameter name -> (min, max) bounds
            backtest_func: Function that takes parameters and returns trades
            
        Returns:
            OptimizationResult with best parameters and metrics
        """
        # Extract parameter names and bounds
        param_names = list(parameter_space.keys())
        n_dim = len(param_names)
        lb = [parameter_space[name][0] for name in param_names]
        ub = [parameter_space[name][1] for name in param_names]
        
        logger.info(f"🚀 Starting {self.algorithm} optimization with {n_dim} parameters")
        
        # Create fitness function
        fitness_func = self._create_fitness_function(param_names, backtest_func)
        
        # Run optimization
        convergence_history = []
        
        if self.algorithm == "PSO":
            optimizer = PSO(
                func=fitness_func,
                n_dim=n_dim,
                pop=self.population_size,
                max_iter=self.max_iterations,
                lb=lb,
                ub=ub,
                w=0.8,  # Inertia weight
                c1=0.5,  # Cognitive parameter
                c2=0.5,  # Social parameter
            )
            best_x, best_y = optimizer.run()
            convergence_history = list(-np.array(optimizer.gbest_y_hist))
            
        elif self.algorithm == "GA":
            optimizer = GA(
                func=fitness_func,
                n_dim=n_dim,
                size_pop=self.population_size,
                max_iter=self.max_iterations,
                lb=lb,
                ub=ub,
                prob_mut=0.1,
            )
            best_x, best_y = optimizer.run()
            convergence_history = list(-np.array(optimizer.generation_best_Y))
        else:
            raise ValueError(f"Unknown algorithm: {self.algorithm}")
        
        # Convert to parameter dict
        best_params = {name: best_x[i] for i, name in enumerate(param_names)}
        
        # Clamp to valid bounds
        best_params = clamp_parameters(best_params, parameter_space)
        
        # Get final metrics
        final_trades = backtest_func(best_params)
        metrics = self.fitness_calculator.calculate_metrics(final_trades)
        
        # Handle numpy array return from optimizer
        best_fitness = float(-best_y[0]) if hasattr(best_y, '__iter__') else float(-best_y)
        
        logger.info(
            f"✅ Optimization complete! Best fitness: {best_fitness:.4f}, "
            f"Sharpe: {metrics.sharpe_ratio:.2f}, WinRate: {metrics.win_rate*100:.1f}%"
        )
        
        return OptimizationResult(
            best_parameters=best_params,
            best_fitness=best_fitness,
            metrics=metrics,
            iterations_run=self.max_iterations,
            convergence_history=convergence_history,
        )
    
    def optimize_regime_parameters(
        self,
        backtest_func: Callable[[Dict[str, float]], List[Dict]],
    ) -> OptimizationResult:
        """
        Optimize regime-specific parameters (profit targets, trailing stops).
        
        Args:
            backtest_func: Function that takes parameters and returns trades
            
        Returns:
            OptimizationResult with optimized regime parameters
        """
        logger.info("🎯 Optimizing regime parameters...")
        return self.optimize(REGIME_PARAMETERS, backtest_func)
    
    def optimize_momentum_parameters(
        self,
        backtest_func: Callable[[Dict[str, float]], List[Dict]],
    ) -> OptimizationResult:
        """
        Optimize momentum indicator parameters.
        
        Args:
            backtest_func: Function that takes parameters and returns trades
            
        Returns:
            OptimizationResult with optimized momentum parameters
        """
        logger.info("📈 Optimizing momentum parameters...")
        return self.optimize(MOMENTUM_PARAMETERS, backtest_func)
    
    def optimize_with_validation(
        self,
        parameter_space: Dict[str, Tuple[float, float]],
        train_backtest_func: Callable[[Dict[str, float]], List[Dict]],
        validate_backtest_func: Callable[[Dict[str, float]], List[Dict]],
    ) -> Tuple[OptimizationResult, 'ValidationResult']:
        """
        Optimize parameters with walk-forward validation.
        
        Args:
            parameter_space: Dict of parameter name -> (min, max) bounds
            train_backtest_func: Backtest function for training data
            validate_backtest_func: Backtest function for validation data
            
        Returns:
            Tuple of (OptimizationResult, ValidationResult)
        """
        from .validator import WalkForwardValidator
        
        # Optimize on training data
        opt_result = self.optimize(parameter_space, train_backtest_func)
        
        # Validate on out-of-sample data
        train_trades = train_backtest_func(opt_result.best_parameters)
        validate_trades = validate_backtest_func(opt_result.best_parameters)
        
        val_result = self.validator.validate(
            opt_result.best_parameters,
            train_trades,
            validate_trades,
        )
        
        return opt_result, val_result
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        """Return all available parameter bounds."""
        return ALL_PARAMETERS.copy()
