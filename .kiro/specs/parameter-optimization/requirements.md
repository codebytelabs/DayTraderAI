# Requirements Document

## Introduction

This document specifies the requirements for implementing a Parameter Optimization System using scikit-opt (Genetic Algorithm and Particle Swarm Optimization) to automatically tune trading strategy parameters. The system will use walk-forward optimization to prevent overfitting and improve the trading bot's win rate, profit factor, and risk-adjusted returns.

Based on academic research, properly implemented parameter optimization with walk-forward validation can improve win rate by 3-8% and profit factor by 10-20%, while reducing overfitting risk.

## Glossary

- **Parameter_Optimizer**: The core system that uses swarm intelligence algorithms to find optimal trading parameters
- **Walk_Forward_Validator**: Component that validates optimized parameters on out-of-sample data to prevent overfitting
- **Fitness_Function**: The objective function that evaluates parameter combinations using backtested performance metrics
- **Sharpe_Ratio**: Risk-adjusted return metric (return / volatility), target > 1.5
- **Profit_Factor**: Gross profit / gross loss ratio, target > 1.5
- **PSO**: Particle Swarm Optimization algorithm
- **GA**: Genetic Algorithm
- **Overfitting**: When parameters perform well on historical data but fail in live trading
- **Out_of_Sample**: Data reserved for validation, not used during optimization

## Requirements

### Requirement 1

**User Story:** As a trader, I want the system to automatically optimize my trading parameters, so that I can achieve better risk-adjusted returns without manual trial-and-error.

#### Acceptance Criteria

1. WHEN the user initiates parameter optimization THEN the Parameter_Optimizer SHALL use PSO or GA from scikit-opt to search the parameter space
2. WHEN optimizing parameters THEN the Parameter_Optimizer SHALL use Sharpe_Ratio as the primary fitness metric to prevent overfitting to lucky trades
3. WHEN optimization completes THEN the Parameter_Optimizer SHALL return the best parameter set along with performance metrics
4. WHEN parameters are optimized THEN the Parameter_Optimizer SHALL constrain all values within predefined valid ranges

### Requirement 2

**User Story:** As a trader, I want walk-forward validation to prevent overfitting, so that optimized parameters actually work in live trading.

#### Acceptance Criteria

1. WHEN validating parameters THEN the Walk_Forward_Validator SHALL split data into training (70%) and validation (30%) periods
2. WHEN performing walk-forward optimization THEN the Walk_Forward_Validator SHALL train on 4 months of data and validate on 2 months
3. WHEN validation completes THEN the Walk_Forward_Validator SHALL report both in-sample and out-of-sample performance metrics
4. IF out-of-sample performance degrades more than 25% compared to in-sample THEN the Walk_Forward_Validator SHALL flag potential overfitting

### Requirement 3

**User Story:** As a trader, I want to optimize regime-specific parameters, so that my strategy adapts optimally to different market conditions.

#### Acceptance Criteria

1. WHEN optimizing regime parameters THEN the Parameter_Optimizer SHALL tune profit_target_r values for each of the 5 market regimes
2. WHEN optimizing regime parameters THEN the Parameter_Optimizer SHALL tune trailing_stop_r values for each regime
3. WHEN optimizing regime parameters THEN the Parameter_Optimizer SHALL tune partial_profit levels for each regime
4. WHEN regime parameters are optimized THEN the Parameter_Optimizer SHALL maintain logical relationships (e.g., partial_profit_1 < profit_target)

### Requirement 4

**User Story:** As a trader, I want to optimize momentum indicator thresholds, so that I can better identify high-probability setups.

#### Acceptance Criteria

1. WHEN optimizing momentum parameters THEN the Parameter_Optimizer SHALL tune ADX threshold within range 20-35
2. WHEN optimizing momentum parameters THEN the Parameter_Optimizer SHALL tune volume threshold within range 1.2-2.0
3. WHEN optimizing momentum parameters THEN the Parameter_Optimizer SHALL tune trend threshold within range 0.6-0.8
4. WHEN momentum parameters are optimized THEN the Parameter_Optimizer SHALL validate that the combination produces sufficient trade signals

### Requirement 5

**User Story:** As a trader, I want to track optimization results over time, so that I can verify if optimized parameters actually improve live performance.

#### Acceptance Criteria

1. WHEN optimization completes THEN the Parameter_Optimizer SHALL save results to a timestamped log file
2. WHEN saving results THEN the Parameter_Optimizer SHALL record baseline metrics, optimized metrics, and parameter values
3. WHEN the user requests verification THEN the Parameter_Optimizer SHALL compare pre-optimization and post-optimization live trading results
4. WHEN verification is requested THEN the Parameter_Optimizer SHALL calculate actual improvement in win rate, profit factor, and Sharpe ratio

### Requirement 6

**User Story:** As a trader, I want a simple way to run optimization and apply results, so that I can improve my strategy without deep technical knowledge.

#### Acceptance Criteria

1. WHEN the user runs the optimizer THEN the Parameter_Optimizer SHALL provide a single command to execute optimization
2. WHEN optimization completes THEN the Parameter_Optimizer SHALL display a summary of improvements
3. WHEN the user approves results THEN the Parameter_Optimizer SHALL update the configuration files with optimized values
4. IF the user rejects results THEN the Parameter_Optimizer SHALL preserve the original configuration unchanged
