# Design Document: Parameter Optimization System

## Overview

This document describes the design for a Parameter Optimization System that uses scikit-opt's swarm intelligence algorithms (PSO, GA) to automatically tune trading strategy parameters. The system implements walk-forward optimization to prevent overfitting and ensure optimized parameters perform well in live trading.

The system targets a 3-8% improvement in win rate and 10-20% improvement in profit factor based on academic research on algorithmic trading optimization.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Parameter Optimization System                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  Optimizer Core  │    │  Walk-Forward    │                   │
│  │  (PSO/GA)        │◄──►│  Validator       │                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                              │
│           ▼                       ▼                              │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  Fitness         │    │  Data Splitter   │                   │
│  │  Calculator      │    │  (70/30)         │                   │
│  └────────┬─────────┘    └──────────────────┘                   │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  Backtester      │    │  Results Logger  │                   │
│  │  (Sharpe Ratio)  │    │  & Verifier      │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. ParameterOptimizer

The core optimization engine that uses scikit-opt algorithms.

```python
class ParameterOptimizer:
    def __init__(self, algorithm: str = "PSO"):
        """Initialize with PSO or GA algorithm"""
        
    def optimize(
        self,
        parameter_space: Dict[str, Tuple[float, float]],
        fitness_function: Callable,
        max_iterations: int = 100,
        population_size: int = 40
    ) -> OptimizationResult:
        """Run optimization and return best parameters"""
        
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        """Return valid ranges for all optimizable parameters"""
```

### 2. WalkForwardValidator

Validates parameters using walk-forward methodology.

```python
class WalkForwardValidator:
    def __init__(self, train_months: int = 4, validate_months: int = 2):
        """Initialize with training and validation periods"""
        
    def split_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split data into training (70%) and validation (30%) sets"""
        
    def validate(
        self,
        parameters: Dict,
        train_data: pd.DataFrame,
        validate_data: pd.DataFrame
    ) -> ValidationResult:
        """Validate parameters on out-of-sample data"""
        
    def detect_overfitting(
        self,
        in_sample_metrics: Dict,
        out_sample_metrics: Dict,
        threshold: float = 0.25
    ) -> bool:
        """Return True if performance degradation exceeds threshold"""
```

### 3. FitnessCalculator

Calculates fitness metrics for parameter evaluation.

```python
class FitnessCalculator:
    def calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio from returns"""
        
    def calculate_fitness(
        self,
        parameters: Dict,
        historical_data: pd.DataFrame
    ) -> float:
        """Run backtest and return Sharpe ratio as fitness"""
        
    def calculate_metrics(
        self,
        trades: List[Trade]
    ) -> PerformanceMetrics:
        """Calculate win rate, profit factor, max drawdown"""
```

### 4. ResultsLogger

Logs and tracks optimization results.

```python
class ResultsLogger:
    def save_results(
        self,
        baseline_metrics: Dict,
        optimized_metrics: Dict,
        parameters: Dict
    ) -> str:
        """Save results to timestamped file, return filepath"""
        
    def compare_performance(
        self,
        pre_optimization_trades: List[Trade],
        post_optimization_trades: List[Trade]
    ) -> VerificationResult:
        """Compare live trading performance before/after optimization"""
```

## Data Models

### OptimizationResult
```python
@dataclass
class OptimizationResult:
    best_parameters: Dict[str, float]
    best_fitness: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    iterations_run: int
    convergence_history: List[float]
```

### ValidationResult
```python
@dataclass
class ValidationResult:
    in_sample_sharpe: float
    out_sample_sharpe: float
    in_sample_win_rate: float
    out_sample_win_rate: float
    overfitting_detected: bool
    degradation_percent: float
```

### ParameterSpace
```python
REGIME_PARAMETERS = {
    "extreme_fear_profit_target_r": (2.5, 5.0),
    "extreme_fear_trailing_stop_r": (1.0, 2.0),
    "fear_profit_target_r": (2.0, 4.0),
    "fear_trailing_stop_r": (0.75, 1.5),
    "neutral_profit_target_r": (1.5, 3.0),
    "neutral_trailing_stop_r": (0.5, 1.0),
    "greed_profit_target_r": (1.5, 3.5),
    "greed_trailing_stop_r": (0.75, 1.5),
    "extreme_greed_profit_target_r": (2.0, 4.0),
    "extreme_greed_trailing_stop_r": (1.0, 2.0),
}

MOMENTUM_PARAMETERS = {
    "adx_threshold": (20.0, 35.0),
    "volume_threshold": (1.2, 2.0),
    "trend_threshold": (0.6, 0.8),
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: All optimized parameters within bounds
*For any* optimization result, all parameter values should be within their predefined valid ranges (e.g., ADX 20-35, volume 1.2-2.0, trend 0.6-0.8)
**Validates: Requirements 1.4, 4.1, 4.2, 4.3**

### Property 2: Fitness function returns Sharpe ratio
*For any* set of parameters and historical data, the fitness function should return a value that equals the calculated Sharpe ratio of the backtested returns
**Validates: Requirements 1.2**

### Property 3: Data split maintains proportions
*For any* input dataset, the walk-forward validator should split it such that training data is approximately 70% and validation data is approximately 30% of the total
**Validates: Requirements 2.1**

### Property 4: Overfitting detection threshold
*For any* pair of in-sample and out-of-sample metrics where out-of-sample Sharpe ratio is less than 75% of in-sample Sharpe ratio, the overfitting flag should be True
**Validates: Requirements 2.4**

### Property 5: Regime parameters complete
*For any* optimization result targeting regime parameters, the result should contain profit_target_r and trailing_stop_r values for all 5 market regimes (extreme_fear, fear, neutral, greed, extreme_greed)
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 6: Logical parameter relationships preserved
*For any* optimized regime parameters, partial_profit_1_r should be less than profit_target_r for each regime
**Validates: Requirements 3.4**

### Property 7: Results contain required fields
*For any* saved optimization result, the file should contain baseline_metrics, optimized_metrics, and parameter_values fields
**Validates: Requirements 5.2**

### Property 8: Configuration unchanged on rejection
*For any* optimization where the user rejects results, the configuration files should remain identical to their pre-optimization state
**Validates: Requirements 6.4**

### Property 9: Validation reports both metric sets
*For any* completed validation, the result should contain both in_sample and out_sample performance metrics
**Validates: Requirements 2.3**

### Property 10: Improvement calculation accuracy
*For any* set of pre and post optimization trades, the calculated improvement percentages should accurately reflect the difference in win rate, profit factor, and Sharpe ratio
**Validates: Requirements 5.4**

## Error Handling

1. **Insufficient Data**: If historical data is less than 6 months, raise `InsufficientDataError`
2. **Optimization Failure**: If PSO/GA fails to converge after max iterations, return best found parameters with warning
3. **Invalid Parameters**: If optimized parameters violate constraints, clamp to valid range and log warning
4. **Backtest Failure**: If backtest produces no trades, return fitness of -infinity

## Testing Strategy

### Unit Tests
- Test fitness calculation with known returns
- Test data splitting proportions
- Test overfitting detection logic
- Test parameter constraint validation

### Property-Based Tests (using Hypothesis)
The following property-based tests will be implemented using the `hypothesis` library:

1. **Property 1 Test**: Generate random optimization results and verify all parameters within bounds
2. **Property 3 Test**: Generate random datasets and verify 70/30 split
3. **Property 4 Test**: Generate random metric pairs and verify overfitting detection
4. **Property 5 Test**: Generate regime optimization results and verify completeness
5. **Property 6 Test**: Generate regime parameters and verify logical relationships
6. **Property 8 Test**: Simulate rejection and verify config unchanged

Each property-based test will run a minimum of 100 iterations to ensure robustness.

### Integration Tests
- End-to-end optimization with sample data
- Walk-forward validation with real historical data
- Results logging and retrieval
