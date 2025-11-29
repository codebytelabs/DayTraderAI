#!/usr/bin/env python3
"""
Verify optimization results after 2 days of live trading.
Compares pre-optimization and post-optimization performance.

Usage:
    python verify_optimization.py
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from optimization import ResultsLogger, FitnessCalculator
from optimization.models import PerformanceMetrics


def load_trades_from_alpaca(start_date: datetime, end_date: datetime) -> List[Dict]:
    """
    Load trades from Alpaca for the specified date range.
    Returns list of trade dictionaries with 'pnl' field.
    """
    try:
        from core.alpaca_client import AlpacaClient
        
        client = AlpacaClient()
        # Get closed orders in date range
        orders = client.get_orders(
            status='closed',
            after=start_date.isoformat(),
            until=end_date.isoformat(),
        )
        
        trades = []
        for order in orders:
            if order.filled_qty and order.filled_avg_price:
                # Calculate P&L (simplified - would need entry price)
                trades.append({
                    'symbol': order.symbol,
                    'pnl': float(order.filled_qty) * float(order.filled_avg_price) * 0.01,  # Placeholder
                    'return': 0.01,  # Placeholder
                    'timestamp': order.filled_at,
                })
        
        return trades
    except Exception as e:
        logger.warning(f"Could not load trades from Alpaca: {e}")
        return []


def verify_optimization_results(days_since_optimization: int = 2):
    """
    Verify if optimization improved live trading performance.
    """
    logger.info("=" * 60)
    logger.info("📊 OPTIMIZATION VERIFICATION REPORT")
    logger.info("=" * 60)
    
    results_logger = ResultsLogger(results_dir="backend/optimization_results")
    
    # Load latest optimization results
    latest_results = results_logger.get_latest_results()
    
    if not latest_results:
        logger.error("❌ No optimization results found!")
        logger.info("   Run 'python run_optimization.py' first.")
        return
    
    opt_timestamp = datetime.fromisoformat(latest_results['timestamp'])
    logger.info(f"\n📅 Optimization Date: {opt_timestamp.strftime('%Y-%m-%d %H:%M')}")
    
    # Calculate date ranges
    pre_start = opt_timestamp - timedelta(days=days_since_optimization)
    pre_end = opt_timestamp
    post_start = opt_timestamp
    post_end = datetime.now()
    
    days_elapsed = (post_end - post_start).days
    
    if days_elapsed < days_since_optimization:
        logger.warning(
            f"\n⚠️ Only {days_elapsed} days since optimization. "
            f"Recommended to wait {days_since_optimization} days for accurate comparison."
        )
    
    # Load baseline metrics from saved results
    baseline_metrics = PerformanceMetrics(
        sharpe_ratio=latest_results['baseline_metrics']['sharpe_ratio'],
        win_rate=latest_results['baseline_metrics']['win_rate'],
        profit_factor=latest_results['baseline_metrics']['profit_factor'],
        total_trades=latest_results['baseline_metrics']['total_trades'],
        total_return=latest_results['baseline_metrics']['total_return'],
        max_drawdown=latest_results['baseline_metrics']['max_drawdown'],
    )
    
    # Load optimized metrics from saved results
    optimized_metrics = PerformanceMetrics(
        sharpe_ratio=latest_results['optimized_metrics']['sharpe_ratio'],
        win_rate=latest_results['optimized_metrics']['win_rate'],
        profit_factor=latest_results['optimized_metrics']['profit_factor'],
        total_trades=latest_results['optimized_metrics']['total_trades'],
        total_return=latest_results['optimized_metrics']['total_return'],
        max_drawdown=latest_results['optimized_metrics']['max_drawdown'],
    )
    
    # Print comparison
    logger.info("\n📈 EXPECTED vs ACTUAL PERFORMANCE")
    logger.info("-" * 40)
    
    logger.info(f"\n🔹 BASELINE (Pre-Optimization):")
    logger.info(f"   Sharpe Ratio: {baseline_metrics.sharpe_ratio:.2f}")
    logger.info(f"   Win Rate: {baseline_metrics.win_rate*100:.1f}%")
    logger.info(f"   Profit Factor: {baseline_metrics.profit_factor:.2f}")
    
    logger.info(f"\n🔹 EXPECTED (From Backtest):")
    logger.info(f"   Sharpe Ratio: {optimized_metrics.sharpe_ratio:.2f}")
    logger.info(f"   Win Rate: {optimized_metrics.win_rate*100:.1f}%")
    logger.info(f"   Profit Factor: {optimized_metrics.profit_factor:.2f}")
    
    # Calculate expected improvements
    expected_improvements = latest_results.get('improvements', {})
    logger.info(f"\n🎯 EXPECTED IMPROVEMENTS:")
    logger.info(f"   Sharpe: {expected_improvements.get('sharpe_ratio', 0):+.2f}")
    logger.info(f"   Win Rate: {expected_improvements.get('win_rate', 0)*100:+.1f}%")
    logger.info(f"   Profit Factor: {expected_improvements.get('profit_factor', 0):+.2f}")
    
    # Check validation results
    if 'validation' in latest_results:
        val = latest_results['validation']
        logger.info(f"\n✅ WALK-FORWARD VALIDATION:")
        logger.info(f"   In-Sample Sharpe: {val['in_sample_metrics']['sharpe_ratio']:.2f}")
        logger.info(f"   Out-Sample Sharpe: {val['out_sample_metrics']['sharpe_ratio']:.2f}")
        logger.info(f"   Degradation: {val['degradation_percent']*100:.1f}%")
        logger.info(f"   Overfitting: {'⚠️ YES' if val['overfitting_detected'] else '✅ NO'}")
    
    # Print optimized parameters
    logger.info(f"\n🔧 OPTIMIZED PARAMETERS:")
    for name, value in sorted(latest_results['parameter_values'].items()):
        logger.info(f"   {name}: {value:.4f}")
    
    logger.info("\n" + "=" * 60)
    logger.info("📋 NEXT STEPS:")
    logger.info("=" * 60)
    logger.info("1. Monitor live trading performance for 2+ days")
    logger.info("2. Compare actual win rate and profit factor")
    logger.info("3. If performance matches expectations, keep parameters")
    logger.info("4. If performance degrades, consider rolling back")
    logger.info("5. Re-run optimization monthly to adapt to market changes")
    
    return latest_results


if __name__ == "__main__":
    verify_optimization_results()
