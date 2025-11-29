"""
Results logger for parameter optimization.
Saves optimization results and tracks performance over time.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging

from .models import (
    OptimizationResult,
    ValidationResult,
    PerformanceMetrics,
    VerificationResult,
)

logger = logging.getLogger(__name__)


class ResultsLogger:
    """
    Logs and tracks optimization results.
    Saves to timestamped files for historical comparison.
    """
    
    def __init__(self, results_dir: str = "optimization_results"):
        """
        Initialize results logger.
        
        Args:
            results_dir: Directory to save results
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Results logger initialized: {self.results_dir}")
    
    def save_results(
        self,
        baseline_metrics: PerformanceMetrics,
        optimized_metrics: PerformanceMetrics,
        parameters: Dict[str, float],
        validation_result: Optional[ValidationResult] = None,
    ) -> str:
        """
        Save optimization results to timestamped file.
        
        Args:
            baseline_metrics: Performance before optimization
            optimized_metrics: Performance after optimization
            parameters: Optimized parameter values
            validation_result: Optional walk-forward validation result
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"optimization_{timestamp}.json"
        filepath = self.results_dir / filename
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "baseline_metrics": baseline_metrics.to_dict(),
            "optimized_metrics": optimized_metrics.to_dict(),
            "parameter_values": parameters,
            "improvements": {
                "sharpe_ratio": optimized_metrics.sharpe_ratio - baseline_metrics.sharpe_ratio,
                "win_rate": optimized_metrics.win_rate - baseline_metrics.win_rate,
                "profit_factor": optimized_metrics.profit_factor - baseline_metrics.profit_factor,
            },
        }
        
        if validation_result:
            result["validation"] = validation_result.to_dict()
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"💾 Results saved to: {filepath}")
        return str(filepath)
    
    def load_results(self, filepath: str) -> Dict:
        """Load results from file."""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def get_latest_results(self) -> Optional[Dict]:
        """Get the most recent optimization results."""
        files = sorted(self.results_dir.glob("optimization_*.json"))
        if not files:
            return None
        return self.load_results(str(files[-1]))
    
    def compare_performance(
        self,
        pre_trades: List[Dict],
        post_trades: List[Dict],
    ) -> VerificationResult:
        """
        Compare live trading performance before and after optimization.
        
        Args:
            pre_trades: Trades before optimization was applied
            post_trades: Trades after optimization was applied
            
        Returns:
            VerificationResult with improvement metrics
        """
        from .fitness import FitnessCalculator
        
        calculator = FitnessCalculator()
        pre_metrics = calculator.calculate_metrics(pre_trades)
        post_metrics = calculator.calculate_metrics(post_trades)
        
        # Calculate improvements
        win_rate_improvement = post_metrics.win_rate - pre_metrics.win_rate
        profit_factor_improvement = post_metrics.profit_factor - pre_metrics.profit_factor
        sharpe_improvement = post_metrics.sharpe_ratio - pre_metrics.sharpe_ratio
        
        result = VerificationResult(
            pre_metrics=pre_metrics,
            post_metrics=post_metrics,
            win_rate_improvement=win_rate_improvement,
            profit_factor_improvement=profit_factor_improvement,
            sharpe_improvement=sharpe_improvement,
        )
        
        logger.info(
            f"📊 Performance Comparison:\n"
            f"   Win Rate: {pre_metrics.win_rate*100:.1f}% → {post_metrics.win_rate*100:.1f}% "
            f"({win_rate_improvement*100:+.1f}%)\n"
            f"   Profit Factor: {pre_metrics.profit_factor:.2f} → {post_metrics.profit_factor:.2f} "
            f"({profit_factor_improvement:+.2f})\n"
            f"   Sharpe Ratio: {pre_metrics.sharpe_ratio:.2f} → {post_metrics.sharpe_ratio:.2f} "
            f"({sharpe_improvement:+.2f})"
        )
        
        return result
    
    def generate_summary(self, opt_result: OptimizationResult, val_result: Optional[ValidationResult] = None) -> str:
        """
        Generate human-readable summary of optimization results.
        
        Args:
            opt_result: Optimization result
            val_result: Optional validation result
            
        Returns:
            Formatted summary string
        """
        lines = [
            "=" * 60,
            "🎯 PARAMETER OPTIMIZATION RESULTS",
            "=" * 60,
            "",
            f"📅 Timestamp: {opt_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"🔄 Iterations: {opt_result.iterations_run}",
            f"🏆 Best Fitness: {opt_result.best_fitness:.4f}",
            "",
            "📈 Performance Metrics:",
            f"   Sharpe Ratio: {opt_result.metrics.sharpe_ratio:.2f}",
            f"   Win Rate: {opt_result.metrics.win_rate*100:.1f}%",
            f"   Profit Factor: {opt_result.metrics.profit_factor:.2f}",
            f"   Total Trades: {opt_result.metrics.total_trades}",
            f"   Max Drawdown: {opt_result.metrics.max_drawdown*100:.1f}%",
            "",
            "🔧 Optimized Parameters:",
        ]
        
        for name, value in sorted(opt_result.best_parameters.items()):
            lines.append(f"   {name}: {value:.4f}")
        
        if val_result:
            lines.extend([
                "",
                "✅ Walk-Forward Validation:",
                f"   In-Sample Sharpe: {val_result.in_sample_metrics.sharpe_ratio:.2f}",
                f"   Out-Sample Sharpe: {val_result.out_sample_metrics.sharpe_ratio:.2f}",
                f"   Degradation: {val_result.degradation_percent*100:.1f}%",
                f"   Overfitting: {'⚠️ YES' if val_result.overfitting_detected else '✅ NO'}",
            ])
        
        lines.extend(["", "=" * 60])
        
        return "\n".join(lines)
