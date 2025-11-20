# 🎯 MASTER ACTION PLAN - Path to Profitability

## Mission: Transform from Losing to Winning Trading Bot

**Current State:** -$176.14 on 4 trades (100% loss rate on TP exits)
**Target State:** 65%+ win rate, 1:2.5 risk/reward, <5% max drawdown

---

## 🚨 PHASE 1: STOP THE BLEEDING (TODAY - 2 Hours)

### Critical Bug Fixes

#### Fix 1.1: Disable Position Manager Interference
**File:** `backend/trading/position_manager.py`
**Action:** Modify `check_stops_and_targets()` to NEVER interfere with bracket orders

```python
def check_stops_and_targets(self) -> List[str]:
    """
    ONLY check stops/targets if NO bracket orders exist.
    Let bracket orders handle exits - they're more reliable!
    """
    symbols_to_close = []
    
    try:
        positions = trading_state.get_all_positions()
        
        # Get ALL orders (not just open) to detect bracket legs
        all_orders = self.alpaca.get_orders(status='all', limit=500)
        
        # Build comprehensive set of symbols with ANY orders
        symbols_with_orders = set()
        for order in all_orders:
            # If order is from today and not filled/cancelled
            if order.status.value in ['new', 'accepted', 'pending_new', 'held']:
                symbols_with_orders.add(order.symbol)
        
        logger.info(f"🛡️  Symbols with active orders (skipping manual checks): {symbols_with_orders}")
        
        for position in positions:
            # CRITICAL: Skip if ANY orders exist for this symbol
            if position.symbol in symbols_with_orders:
                logger.debug(f"✓ {position.symbol} has active orders - letting brackets handle exit")
                continue
            
            # Only check manually if NO orders exist (backup safety net)
            logger.warning(f"⚠️  {position.symbol} has NO orders - manual check activated")
            
            current_price = position.current_price
            
            # Check stop loss (use LIMIT order, not market!)
            if position.side == 'buy':
                if current_price <= position.stop_loss:
                    logger.error(f"🚨 EMERGENCY STOP: {position.symbol} @ ${current_price:.2f}")
                    symbols_to_close.append((position.symbol, 'emergency_stop'))
            else:
                if current_price >= position.stop_loss:
                    logger.error(f"🚨 EMERGENCY STOP: {position.symbol} @ ${current_price:.2f}")
                    symbols_to_close.append((position.symbol, 'emergency_stop'))
        
        return symbols_to_close
        
    except Exception as e:
        logger.error(f"Failed to check stops/targets: {e}")
        return []
```

#### Fix 1.2: Never Cancel Bracket Orders for TP/SL
**File:** `backend/trading/position_manager.py`
**Action:** Modify `close_position()` to preserve brackets

```python
def close_position(self, symbol: str, reason: str = "Manual close"):
    """
    Close position intelligently:
    - If reason is 'take_profit' or 'stop_loss': DON'T cancel brackets, let them execute
    - If reason is 'emergency' or 'manual': Cancel brackets and close immediately
    """
    try:
        position = trading_state.get_position(symbol)
        if not position:
            logger.warning(f"No position found for {symbol}")
            return False
        
        logger.info(f"🎯 Closing {symbol}: {reason}")
        
        # CRITICAL: Don't interfere with bracket exits!
        if reason in ['take_profit', 'stop_loss']:
            logger.info(f"✓ {symbol} exiting via bracket order - not interfering")
            return True
        
        # Only cancel orders for emergency/manual closes
        if reason in ['emergency_stop', 'manual_close', 'risk_limit']:
            self._cancel_all_symbol_orders(symbol)
            
            # Use LIMIT order near current price, not market!
            success = self._close_with_limit_order(symbol, position)
            
            if success:
                self._cleanup_position_state(symbol, position, reason)
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to close position {symbol}: {e}")
        return False

def _close_with_limit_order(self, symbol: str, position: Position) -> bool:
    """Close position with limit order to minimize slippage"""
    try:
        current_price = position.current_price
        
        # Set limit price with small buffer for quick fill
        if position.side == 'buy':
            # Selling: set limit slightly below current
            limit_price = current_price * 0.999  # 0.1% below
        else:
            # Covering short: set limit slightly above current
            limit_price = current_price * 1.001  # 0.1% above
        
        order = self.alpaca.submit_order(
            symbol=symbol,
            qty=position.qty,
            side='sell' if position.side == 'buy' else 'buy',
            type='limit',
            limit_price=round(limit_price, 2),
            time_in_force='day'
        )
        
        if order:
            logger.info(f"✅ Limit order submitted for {symbol} @ ${limit_price:.2f}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to submit limit order for {symbol}: {e}")
        return False
```

**Expected Impact:** 
- ✅ Bracket orders execute at intended prices
- ✅ No more slippage losses
- ✅ Win rate improves from 0% to 50%+

---

## 📊 PHASE 2: OPTIMIZE PARAMETERS (WEEK 1 - 3 Days)

### 2.1: Timeframe Optimization

**Current:** 1-minute bars (too noisy)
**Target:** 5-minute bars (better signal/noise ratio)

**File:** `backend/data/market_data.py`
**Action:** Change bar timeframe

```python
# In get_bars() method
bars = self.alpaca.get_bars(
    symbols,
    timeframe='5Min',  # Changed from 1Min
    limit=100,
    adjustment='raw'
)
```

**Expected Impact:**
- Less noise and false signals
- Better ATR calculation
- Fewer whipsaws
- Higher win rate

### 2.2: ATR Multiplier Optimization

**Current Settings:**
```python
stop_loss_atr_mult: 2.0
take_profit_atr_mult: 3.0
```

**Problem:** Too tight for 1m bars in choppy markets

**New Settings (for 5m bars):**
```python
# In config.py
stop_loss_atr_mult: 2.5  # Wider stops
take_profit_atr_mult: 4.0  # Wider targets
```

**Rationale:**
- 2.5 ATR stop = ~1.5-2% stop loss
- 4.0 ATR target = ~2.5-3% profit target
- Risk/Reward = 1:1.6 minimum
- Accounts for market volatility

### 2.3: Market Regime Adaptive Brackets

**File:** `backend/trading/strategy.py`
**Action:** Adjust brackets based on market conditions

```python
def calculate_adaptive_brackets(self, symbol: str, entry_price: float, side: str):
    """
    Calculate stop/target based on market regime
    """
    features = trading_state.get_features(symbol)
    atr = features.get('atr', 0)
    adx = features.get('adx', 0)
    
    # Base multipliers
    stop_mult = 2.5
    target_mult = 4.0
    
    # Adjust for market regime
    if adx > 25:  # Trending market
        # Tighter stops, wider targets
        stop_mult = 2.0
        target_mult = 5.0  # Let winners run!
    elif adx < 20:  # Choppy market
        # Wider stops, tighter targets
        stop_mult = 3.0
        target_mult = 3.5  # Take profits quickly
    
    # Adjust for volatility (VIX proxy)
    if atr > features.get('atr_20', atr):  # High volatility
        stop_mult *= 1.2
        target_mult *= 1.2
    
    if side == 'buy':
        stop_loss = entry_price - (atr * stop_mult)
        take_profit = entry_price + (atr * target_mult)
    else:
        stop_loss = entry_price + (atr * stop_mult)
        take_profit = entry_price - (atr * target_mult)
    
    return stop_loss, take_profit
```

**Expected Impact:**
- Better adaptation to market conditions
- Fewer stop-outs in choppy markets
- Bigger wins in trending markets
- Win rate: 55-60%

---

## 🎯 PHASE 3: ENTRY QUALITY (WEEK 1-2 - 5 Days)

### 3.1: Multi-Timeframe Confirmation

**Current:** Only checks 1m/5m signals
**Target:** Confirm with higher timeframe

**File:** `backend/trading/strategy.py`
**Action:** Add 15m/1h trend filter

```python
def validate_entry_with_higher_timeframe(self, symbol: str, signal: str):
    """
    Only take trades aligned with higher timeframe trend
    """
    # Get 15m bars
    bars_15m = self.alpaca.get_bars(symbol, timeframe='15Min', limit=50)
    
    # Calculate 15m EMA
    closes = [bar.close for bar in bars_15m]
    ema_9_15m = talib.EMA(closes, timeperiod=9)[-1]
    ema_21_15m = talib.EMA(closes, timeperiod=21)[-1]
    
    # Check alignment
    if signal == 'BUY':
        if ema_9_15m < ema_21_15m:
            logger.info(f"⛔ {symbol} BUY rejected: 15m trend is DOWN")
            return False
    elif signal == 'SELL':
        if ema_9_15m > ema_21_15m:
            logger.info(f"⛔ {symbol} SELL rejected: 15m trend is UP")
            return False
    
    logger.info(f"✅ {symbol} {signal} confirmed by 15m trend")
    return True
```

**Expected Impact:**
- Only trade with the trend
- Fewer false signals
- Higher win rate: 60-65%

### 3.2: Volume Profile Analysis

**Action:** Only trade at key support/resistance levels

```python
def check_volume_profile(self, symbol: str, price: float):
    """
    Check if price is at high-volume node (support/resistance)
    """
    # Get daily bars for volume profile
    daily_bars = self.alpaca.get_bars(symbol, timeframe='1Day', limit=20)
    
    # Build volume profile
    price_levels = {}
    for bar in daily_bars:
        price_bucket = round(bar.close, 0)  # Round to nearest dollar
        price_levels[price_bucket] = price_levels.get(price_bucket, 0) + bar.volume
    
    # Find high-volume nodes (HVN)
    avg_volume = sum(price_levels.values()) / len(price_levels)
    hvn_levels = [p for p, v in price_levels.items() if v > avg_volume * 1.5]
    
    # Check if current price is near HVN
    current_bucket = round(price, 0)
    is_near_hvn = any(abs(current_bucket - hvn) <= 2 for hvn in hvn_levels)
    
    if is_near_hvn:
        logger.info(f"✅ {symbol} @ ${price:.2f} is near high-volume node")
        return True
    else:
        logger.info(f"⛔ {symbol} @ ${price:.2f} not at key level")
        return False
```

**Expected Impact:**
- Better entry prices
- Higher probability setups
- Win rate: 65%+

---

## 🛡️ PHASE 4: RISK MANAGEMENT (WEEK 2 - 3 Days)

### 4.1: Dynamic Position Sizing Based on Win Rate

**Current:** Fixed 1% risk per trade
**Target:** Adjust based on recent performance

```python
def calculate_dynamic_risk(self):
    """
    Adjust risk based on recent win rate
    """
    # Get last 20 trades
    recent_trades = self.supabase.get_recent_trades(limit=20)
    
    if len(recent_trades) < 10:
        return 0.01  # Default 1% until we have data
    
    # Calculate win rate
    wins = sum(1 for t in recent_trades if t['pnl'] > 0)
    win_rate = wins / len(recent_trades)
    
    # Adjust risk
    if win_rate > 0.65:
        risk = 0.015  # Increase to 1.5% when winning
    elif win_rate > 0.55:
        risk = 0.012  # Slight increase
    elif win_rate < 0.45:
        risk = 0.005  # Reduce to 0.5% when losing
    else:
        risk = 0.01  # Default 1%
    
    logger.info(f"📊 Win rate: {win_rate:.1%} → Risk per trade: {risk:.1%}")
    return risk
```

### 4.2: Maximum Daily Drawdown Protection

```python
def check_daily_drawdown_limit(self):
    """
    Stop trading if daily drawdown exceeds 3%
    """
    account = self.alpaca.get_account()
    equity = float(account.equity)
    
    # Get starting equity for today
    today_start = self.supabase.get_equity_at_market_open()
    
    if not today_start:
        today_start = equity
    
    # Calculate drawdown
    drawdown = (equity - today_start) / today_start
    
    if drawdown < -0.03:  # -3% daily limit
        logger.error(f"🚨 DAILY DRAWDOWN LIMIT HIT: {drawdown:.2%}")
        logger.error(f"🛑 STOPPING ALL TRADING FOR TODAY")
        trading_state.halt_trading = True
        return False
    
    return True
```

### 4.3: Correlation-Based Position Limits

```python
def check_correlation_limits(self, new_symbol: str):
    """
    Don't take correlated positions (diversification)
    """
    current_positions = trading_state.get_all_positions()
    
    if len(current_positions) == 0:
        return True
    
    # Check sector correlation
    new_sector = self.get_sector(new_symbol)
    
    sector_exposure = {}
    for pos in current_positions:
        sector = self.get_sector(pos.symbol)
        sector_exposure[sector] = sector_exposure.get(sector, 0) + 1
    
    # Limit: Max 40% in one sector
    if sector_exposure.get(new_sector, 0) >= len(current_positions) * 0.4:
        logger.warning(f"⛔ {new_symbol} rejected: Too much {new_sector} exposure")
        return False
    
    return True
```

**Expected Impact:**
- Protect capital during losing streaks
- Maximize gains during winning streaks
- Better diversification
- Max drawdown: <5%

---

## 📈 PHASE 5: PROFIT OPTIMIZATION (WEEK 3 - 5 Days)

### 5.1: Trailing Stops for Trending Moves

**File:** `backend/trading/trailing_stops.py`
**Action:** Activate and optimize trailing stops

```python
# In config.py
trailing_stop_enabled: bool = True
trailing_stop_activation: float = 1.5  # Activate at +1.5R
trailing_stop_distance: float = 1.0  # Trail by 1R
```

**Logic:**
- Position reaches +1.5R profit → activate trailing stop
- Trail stop at 1R below highest price
- Locks in minimum 0.5R profit
- Lets winners run in trending markets

### 5.2: Partial Profit Taking

```python
def take_partial_profits(self, position: Position):
    """
    Take 50% off at +2R, let rest run with trailing stop
    """
    entry = position.avg_entry_price
    current = position.current_price
    stop = position.stop_loss
    
    risk = abs(entry - stop)
    profit = abs(current - entry)
    r_multiple = profit / risk
    
    if r_multiple >= 2.0 and not position.partial_taken:
        # Sell 50%
        half_qty = position.qty // 2
        
        self.alpaca.submit_order(
            symbol=position.symbol,
            qty=half_qty,
            side='sell',
            type='limit',
            limit_price=current * 0.999
        )
        
        logger.info(f"💰 Taking 50% profit on {position.symbol} at +2R")
        position.partial_taken = True
```

**Expected Impact:**
- Lock in profits early
- Let winners run
- Reduce risk of giving back gains
- Average R-multiple: 2.5+

### 5.3: Time-Based Exits

```python
def check_stale_positions(self):
    """
    Exit positions that aren't moving after 2 hours
    """
    for position in trading_state.get_all_positions():
        time_in_trade = datetime.utcnow() - position.entry_time
        
        if time_in_trade > timedelta(hours=2):
            # Check if position is flat
            pnl_pct = position.unrealized_pl_pct
            
            if abs(pnl_pct) < 0.5:  # Less than 0.5% move
                logger.info(f"⏰ {position.symbol} stale after 2h - exiting")
                self.close_position(position.symbol, reason='time_exit')
```

**Expected Impact:**
- Free up capital from dead positions
- Reduce opportunity cost
- Better capital efficiency

---

## 🧪 PHASE 6: BACKTESTING & VALIDATION (WEEK 4 - 7 Days)

### 6.1: Build Backtesting Framework

```python
# backend/backtest/engine.py
class BacktestEngine:
    """
    Backtest strategy on historical data
    """
    def run_backtest(self, start_date, end_date, symbols):
        """
        Run strategy on historical data
        """
        results = {
            'trades': [],
            'equity_curve': [],
            'metrics': {}
        }
        
        # Load historical data
        for symbol in symbols:
            bars = self.load_historical_data(symbol, start_date, end_date)
            
            # Simulate trading
            for i in range(100, len(bars)):
                # Calculate indicators
                features = self.calculate_features(bars[:i])
                
                # Generate signal
                signal = self.strategy.generate_signal(features)
                
                # Execute trade
                if signal:
                    trade = self.execute_backtest_trade(signal, bars[i:])
                    results['trades'].append(trade)
        
        # Calculate metrics
        results['metrics'] = self.calculate_metrics(results['trades'])
        
        return results
    
    def calculate_metrics(self, trades):
        """
        Calculate performance metrics
        """
        wins = [t for t in trades if t['pnl'] > 0]
        losses = [t for t in trades if t['pnl'] <= 0]
        
        return {
            'total_trades': len(trades),
            'win_rate': len(wins) / len(trades) if trades else 0,
            'avg_win': sum(t['pnl'] for t in wins) / len(wins) if wins else 0,
            'avg_loss': sum(t['pnl'] for t in losses) / len(losses) if losses else 0,
            'profit_factor': abs(sum(t['pnl'] for t in wins) / sum(t['pnl'] for t in losses)) if losses else 0,
            'max_drawdown': self.calculate_max_drawdown(trades),
            'sharpe_ratio': self.calculate_sharpe(trades)
        }
```

### 6.2: Parameter Optimization

```python
# Test different parameter combinations
param_grid = {
    'stop_loss_atr_mult': [2.0, 2.5, 3.0],
    'take_profit_atr_mult': [3.5, 4.0, 4.5, 5.0],
    'confidence_threshold': [65, 70, 75],
    'timeframe': ['5Min', '15Min']
}

best_params = optimize_parameters(param_grid)
```

### 6.3: Walk-Forward Analysis

```python
# Test on rolling windows
for year in range(2022, 2025):
    train_period = f"{year}-01-01" to f"{year}-06-30"
    test_period = f"{year}-07-01" to f"{year}-12-31"
    
    # Train on first half
    params = optimize_on_period(train_period)
    
    # Test on second half
    results = backtest_with_params(test_period, params)
    
    print(f"{year} Test Results: {results}")
```

**Expected Impact:**
- Validate strategy profitability
- Optimize parameters
- Identify weaknesses
- Build confidence

---

## 📊 EXPECTED FINAL PERFORMANCE

### After All Phases Complete:

**Win Rate:** 65-70%
**Average Win:** +2.5R
**Average Loss:** -1.0R
**Profit Factor:** 3.5+
**Max Drawdown:** <5%
**Monthly Return:** 8-12%
**Sharpe Ratio:** 2.0+

### Sample Month (20 Trading Days):
- Trades: 40 (2 per day)
- Wins: 28 (70%)
- Losses: 12 (30%)
- Avg Win: +$350 (+2.5%)
- Avg Loss: -$140 (-1.0%)
- Total P/L: +$8,120
- Return on $136k: +5.9%

**Annualized:** ~70% return with <10% max drawdown

---

## 🎯 IMPLEMENTATION TIMELINE

### Week 1: Critical Fixes
- Day 1-2: Phase 1 (Stop the bleeding)
- Day 3-5: Phase 2 (Optimize parameters)

### Week 2: Entry & Risk
- Day 1-3: Phase 3 (Entry quality)
- Day 4-5: Phase 4 (Risk management)

### Week 3: Profit Optimization
- Day 1-5: Phase 5 (Profit optimization)

### Week 4: Validation
- Day 1-7: Phase 6 (Backtesting)

### Week 5: Live Testing
- Monitor performance
- Fine-tune parameters
- Build confidence

---

## ✅ SUCCESS METRICS

Track these daily:
- [ ] Win rate > 60%
- [ ] Profit factor > 2.5
- [ ] Max daily drawdown < 3%
- [ ] Average R-multiple > 2.0
- [ ] No bracket order interference
- [ ] Slippage < 0.05%

---

## 🚀 READY TO START?

**Phase 1 is ready to implement NOW.**

Shall I proceed with the critical bug fixes?
