#!/usr/bin/env python3
"""
Run parameter optimization with walk-forward validation.
Single command to optimize trading parameters.

Usage:
    python run_optimization.py [--regime] [--momentum] [--all]
"""

import argparse
import logging
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from optimization import (
    ParameterOptimizer,
    WalkForwardValidator,
    FitnessCalculator,
    ResultsLogger,
    REGIME_PARAMETERS,
    MOMENTUM_PARAMETERS,
)


def create_mock_backtest_func(base_win_rate: float = 0.70):
    """
    Create a mock backtest function for testing.
    In production, this would run actual backtests with historical data.
    """
    import random
    
    def backtest(params: Dict[str, float]) -> List[Dict]:
        """Simulate backtest with given parameters."""
        # Simulate trades based on parameters
        n_trades = random.randint(30, 100)
        trades = []
        
        # Parameters affect win rate
        param_bonus = sum(params.values()) / len(params) / 100 if params else 0
        adjusted_win_rate = min(0.85, base_win_rate + param_bonus * 0.1)
        
        for _ in range(n_trades):
            is_winner = random.random() < adjusted_win_rate
            if is_winner:
                pnl = random.uniform(50, 500)
            else:
                pnl = random.uniform(-300, -50)
            
            trades.append({
                'pnl': pnl,
                'return': pnl / 10000,
            })
        
        return trades
    
    return backtest


def run_optimization(
    optimize_regime: bool = True,
    optimize_momentum: bool = True,
    population_size: int = 30,
    max_iterations: int = 50,
):
    """
    Run parameter optimization with walk-forward validation.
    """
    logger.info("=" * 60)
    logger.info("🚀 PARAMETER OPTIMIZATION SYSTEM")
    logger.info("=" * 60)
    
    # Initialize components
    optimizer = ParameterOptimizer(
        algorithm="PSO",
        population_size=population_size,
        max_iterations=max_iterations,
    )
    validator = WalkForwardValidator()
    results_logger = ResultsLogger(results_dir="backend/optimization_results")
    fitness_calc = FitnessCalculator()
    
    # Create backtest functions (mock for now)
    # In production, these would use actual historical data
    train_backtest = create_mock_backtest_func(base_win_rate=0.70)
    validate_backtest = create_mock_backtest_func(base_win_rate=0.68)
    
    # Get baseline metrics
    logger.info("\n📊 Calculating baseline metrics...")
    baseline_trades = train_backtest({})
    baseline_metrics = fitness_calc.calculate_metrics(baseline_trades)
    logger.info(
        f"   Baseline: Sharpe={baseline_metrics.sharpe_ratio:.2f}, "
        f"WinRate={baseline_metrics.win_rate*100:.1f}%, "
        f"PF={baseline_metrics.profit_factor:.2f}"
    )
    
    results = {}
    
    # Optimize regime parameters
    if optimize_regime:
        logger.info("\n🎯 Optimizing REGIME parameters...")
        opt_result, val_result = optimizer.optimize_with_validation(
            REGIME_PARAMETERS,
            train_backtest,
            validate_backtest,
        )
        results['regime'] = {
            'optimization': opt_result,
            'validation': val_result,
        }
        
        # Print summary
        print(results_logger.generate_summary(opt_result, val_result))
    
    # Optimize momentum parameters
    if optimize_momentum:
        logger.info("\n📈 Optimizing MOMENTUM parameters...")
        opt_result, val_result = optimizer.optimize_with_validation(
            MOMENTUM_PARAMETERS,
            train_backtest,
            validate_backtest,
        )
        results['momentum'] = {
            'optimization': opt_result,
            'validation': val_result,
        }
        
        # Print summary
        print(results_logger.generate_summary(opt_result, val_result))
    
    # Save results
    if results:
        best_result = results.get('regime', results.get('momentum'))
        if best_result:
            filepath = results_logger.save_results(
                baseline_metrics,
                best_result['optimization'].metrics,
                best_result['optimization'].best_parameters,
                best_result['validation'],
            )
            logger.info(f"\n💾 Results saved to: {filepath}")
    
    # Check for overfitting
    any_overfitting = any(
        r['validation'].overfitting_detected 
        for r in results.values()
    )
    
    if any_overfitting:
        logger.warning("\n⚠️ OVERFITTING DETECTED in some parameters!")
        logger.warning("   Consider using more conservative parameters or more data.")
    else:
        logger.info("\n✅ No overfitting detected. Parameters look good!")
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 OPTIMIZATION COMPLETE")
    logger.info("=" * 60)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Run parameter optimization")
    parser.add_argument("--regime", action="store_true", help="Optimize regime parameters only")
    parser.add_argument("--momentum", action="store_true", help="Optimize momentum parameters only")
    parser.add_argument("--all", action="store_true", help="Optimize all parameters (default)")
    parser.add_argument("--pop", type=int, default=30, help="Population size")
    parser.add_argument("--iter", type=int, default=50, help="Max iterations")
    
    args = parser.parse_args()
    
    # Default to all if nothing specified
    if not args.regime and not args.momentum:
        args.regime = True
        args.momentum = True
    
    run_optimization(
        optimize_regime=args.regime or args.all,
        optimize_momentum=args.momentum or args.all,
        population_size=args.pop,
        max_iterations=args.iter,
    )


if __name__ == "__main__":
    main()
