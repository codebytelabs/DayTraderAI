# 🚨 EMERGENCY: Position Size Bug

## CRITICAL ISSUE

The system just took a **1,006 share TSLA position** worth $455k (84% of buying power)!

## Root Cause

**ATR-based stops are too tight**, causing massive position sizes:

- Entry: $452.19
- Stop: $450.85 (only $1.34 away!)
- Risk: 1% of $135k = $1,353
- **Position size: $1,353 / $1.34 = 1,006 shares**

## Immediate Actions

### 1. Close the TSLA Position (DO THIS NOW!)

Option A - Via Alpaca Dashboard:
1. Go to https://app.alpaca.markets
2. Navigate to Positions
3. Close the TSLA position

Option B - Via API:
```bash
# In backend directory
python -c "from core.alpaca_client import AlpacaClient; AlpacaClient().close_all_positions()"
```

### 2. Stop the Backend

```bash
# Press Ctrl+C in the terminal running main.py
```

### 3. Fix the Configuration

Edit `backend/config.py` and change:

```python
# OLD (DANGEROUS):
stop_loss_atr_mult: float = 1.0
risk_per_trade_pct: float = 0.01  # 1%

# NEW (SAFER):
stop_loss_atr_mult: float = 2.0  # Wider stops
risk_per_trade_pct: float = 0.005  # 0.5% risk per trade

# ADD THIS - Max position value as % of equity
max_position_pct: float = 0.10  # Max 10% of equity per position
```

## Why This Happened

1. **Small ATR values** on some stocks (TSLA ATR was ~$1.34)
2. **1x ATR multiplier** creates very tight stops
3. **Position sizing formula**: Risk / Stop Distance = Huge Size
4. **No max position size check** in risk manager

## The Fix

### Update Risk Manager

Add max position value check to `backend/trading/risk_manager.py`:

```python
# In check_order method, add after line ~80:

# Check max position size as % of equity
max_position_value = equity * 0.10  # 10% max
if order_value > max_position_value:
    return False, f"Position too large: ${order_value:.2f} exceeds max ${max_position_value:.2f} (10% of equity)"
```

### Update Config

Add to `backend/config.py`:

```python
# Position sizing limits
max_position_pct: float = 0.10  # Max 10% of equity per position
min_stop_distance_pct: float = 0.01  # Min 1% stop distance
```

## Restart Safely

After making changes:

```bash
cd backend
source venv/bin/activate
python main.py
```

## Monitor

Watch for these in logs:
```
Risk check PASSED: buy X SYMBOL
```

Verify the quantity (X) is reasonable:
- For $450 stocks: Should be ~30 shares max (10% of $135k)
- For $200 stocks: Should be ~67 shares max
- For $50 stocks: Should be ~270 shares max

## Current Position

- **TSLA**: 1,006 shares @ $452.19
- **Value**: $454,901
- **P/L**: -$82.39
- **Risk**: If stop hits at $450.85, loss = $1,347

The stop is actually correct for 1% risk, but the position is way too large!

## Lessons

1. **Always have max position size limits**
2. **ATR-based stops need minimum distances**
3. **Test with small amounts first**
4. **Monitor position sizes in real-time**

## Action Checklist

- [ ] Close TSLA position immediately
- [ ] Stop backend
- [ ] Update config (wider stops, lower risk %)
- [ ] Add max position size check to risk manager
- [ ] Restart backend
- [ ] Monitor next trades carefully
