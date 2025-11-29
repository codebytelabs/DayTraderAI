# 🎯 Parameter Optimization Quick Start

## Overview

The Parameter Optimization System uses scikit-opt (PSO/GA) with walk-forward validation to automatically tune your trading parameters. Based on academic research, this can improve:
- **Win Rate:** +3-8%
- **Profit Factor:** +10-20%
- **Sharpe Ratio:** Improved risk-adjusted returns

## Quick Commands

### 1. Run Full Optimization
```bash
cd backend
source ../venv/bin/activate
python run_optimization.py
```

### 2. Run Specific Optimization
```bash
# Optimize only regime parameters (profit targets, trailing stops)
python run_optimization.py --regime

# Optimize only momentum parameters (ADX, volume, trend thresholds)
python run_optimization.py --momentum

# Custom settings
python run_optimization.py --pop 50 --iter 100
```

### 3. Verify Results (After 2 Days)
```bash
python verify_optimization.py
```

## What Gets Optimized

### Regime Parameters (25 parameters)
- `profit_target_r` for each regime (extreme_fear, fear, neutral, greed, extreme_greed)
- `trailing_stop_r` for each regime
- `partial_profit_1_r` and `partial_profit_2_r` for each regime

### Momentum Parameters (5 parameters)
- `adx_threshold` (20-35)
- `volume_threshold` (1.2-2.0)
- `trend_threshold` (0.6-0.8)
- `atr_trailing_multiplier` (1.5-3.0)
- `evaluation_profit_r` (0.5-1.0)

## Understanding Results

### Good Results ✅
```
✅ No overfitting detected. Degradation: 15.0%
   In-Sample Sharpe: 2.5
   Out-Sample Sharpe: 2.1
```

### Warning Signs ⚠️
```
⚠️ Overfitting detected! Degradation: 30.0%
   In-Sample Sharpe: 3.0
   Out-Sample Sharpe: 2.1
```

If overfitting is detected:
1. Use more conservative parameters
2. Increase training data period
3. Reduce number of parameters being optimized

## Results Location

All optimization results are saved to:
```
backend/optimization_results/optimization_YYYYMMDD_HHMMSS.json
```

## Verification Checklist

After 2 days of live trading with optimized parameters:

- [ ] Run `python verify_optimization.py`
- [ ] Compare actual win rate vs expected
- [ ] Compare actual profit factor vs expected
- [ ] If performance matches expectations → Keep parameters
- [ ] If performance degrades → Consider rolling back

## Monthly Maintenance

Re-run optimization monthly to adapt to changing market conditions:
```bash
python run_optimization.py --all --pop 50 --iter 100
```

## Technical Details

- **Algorithm:** Particle Swarm Optimization (PSO) - faster than GA for trading
- **Fitness Function:** Sharpe Ratio (prevents overfitting to lucky trades)
- **Validation:** Walk-forward (70% train, 30% validate)
- **Overfitting Threshold:** 25% degradation
- **Property Tests:** 11 tests ensure correctness

## Files

| File | Purpose |
|------|---------|
| `optimization/optimizer.py` | PSO/GA optimization engine |
| `optimization/validator.py` | Walk-forward validation |
| `optimization/fitness.py` | Sharpe ratio calculator |
| `optimization/logger.py` | Results logging |
| `optimization/models.py` | Parameter bounds |
| `run_optimization.py` | CLI to run optimization |
| `verify_optimization.py` | CLI to verify results |
