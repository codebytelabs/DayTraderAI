# DayTraderAI - Complete Guide for Beginners

## What Is This?

DayTraderAI is an **automated trading bot** that:
- Watches stock prices 24/7
- Finds trading opportunities using technical analysis
- Buys and sells stocks automatically
- Protects your money with stop losses

Think of it as a robot trader that never sleeps, never gets emotional, and follows strict rules.

---

## Table of Contents

1. [How It Works (Simple Explanation)](#how-it-works-simple-explanation)
2. [Starting the Bot](#starting-the-bot)
3. [Understanding What the Bot Does](#understanding-what-the-bot-does)
4. [Checking Your Positions](#checking-your-positions)
5. [Understanding Order Statuses](#understanding-order-statuses)
6. [Safety Features](#safety-features)
7. [What Happens If Bot Crashes](#what-happens-if-bot-crashes)
8. [Common Questions](#common-questions)
9. [Troubleshooting](#troubleshooting)
10. [Configuration Guide](#configuration-guide)

---

## How It Works (Simple Explanation)

### The Strategy

The bot uses **EMA Crossover Strategy**:

1. **Watches two moving averages**:
   - Fast line (EMA 9) - reacts quickly to price changes
   - Slow line (EMA 21) - reacts slowly to price changes

2. **Buys when**:
   - Fast line crosses ABOVE slow line
   - This suggests price is going up

3. **Sells when**:
   - Fast line crosses BELOW slow line
   - This suggests price is going down

### Example

```
Price chart:
         /\    <- Fast line crosses above slow line = BUY SIGNAL
        /  \
   ----/----\---- <- Slow line
      /      \
     /        \
```

### What Happens After You Buy

When the bot buys a stock, it automatically sets:
- **Stop Loss**: Sells if price drops (protects from big losses)
- **Take Profit**: Sells if price rises (locks in profit)

---

## Starting the Bot

### Step 1: Start Backend

```bash
cd backend
source venv/bin/activate
python main.py
```

**What you'll see:**
```
✅ Backend initialized successfully
✅ Trading engine started
🚀 Starting Trading Engine...
📊 Market data loop started
🎯 Strategy loop started
```

### Step 2: Start Frontend (Optional)

```bash
cd ..  # Go back to root
npm run dev
```

Open browser: http://localhost:5173

### Step 3: Let It Run

That's it! The bot is now:
- ✅ Watching 10 stocks (SPY, QQQ, AAPL, MSFT, NVDA, TSLA, AMD, GOOG, AMZN, META)
- ✅ Looking for signals every 60 seconds
- ✅ Will trade automatically when it finds opportunities

---

## Understanding What the Bot Does

### Every Minute

The bot:
1. Fetches latest prices from Alpaca
2. Calculates technical indicators (EMAs, ATR)
3. Checks for crossover signals
4. If signal found → submits order
5. Repeats forever

### When It Finds a Signal

```
🔍 Evaluating 10 symbols
📈 Signal detected: BUY MSFT
⚠️  Stop distance adjusted (safety check)
⚠️  Position size capped (safety check)
✅ Risk check PASSED
✅ Order submitted: BUY 26 MSFT @ $509
```

### What Gets Created

For each trade, **3 orders** are created:

1. **Entry Order** (Market Buy)
   - Buys the stock immediately
   - Status: "filled" (done)

2. **Stop Loss Order** (Stop)
   - Sells if price drops
   - Status: "held" (active, waiting)
   - Example: Sell if price drops to $503

3. **Take Profit Order** (Limit)
   - Sells if price rises
   - Status: "new" or "held" (active, waiting)
   - Example: Sell if price rises to $510

---

## Checking Your Positions

### Method 1: Alpaca Dashboard (Easiest)

1. Go to: https://app.alpaca.markets/paper/dashboard/overview
2. Click "Positions" tab
3. You'll see all your current holdings

### Method 2: Frontend UI

1. Open: http://localhost:5173
2. Look at "Positions" section
3. Shows all active positions with P/L

### Method 3: Check Orders

1. Go to: https://app.alpaca.markets/paper/dashboard/orders
2. You'll see all orders (entry, stop loss, take profit)

---

## Understanding Order Statuses

### "filled" ✅
- Order completed
- Shares bought or sold
- **Example**: Your entry order after buying stock

### "held" ✅ (GOOD!)
- Order is active and waiting
- Alpaca is monitoring the price
- Will execute automatically when price is hit
- **Example**: Your stop loss protecting you

### "new" ⏳
- Order just submitted
- Being processed by Alpaca
- Will change to "held" soon
- **Example**: Take profit order being set up

### "canceled" ❌
- Order was canceled
- Won't execute
- **Example**: Take profit canceled because stop loss hit first

### "rejected" ❌
- Order failed
- Check logs for reason
- **Example**: Not enough buying power

---

## Safety Features

### 1. Stop Losses (Automatic)

**What it does**: Sells your stock if price drops too much

**Example**:
```
You buy MSFT at $509
Stop loss set at $503 (about 1% below)

If price drops to $503:
→ Alpaca automatically sells
→ You lose ~$6 per share
→ But you're protected from bigger losses
```

**Important**: Stop loss is on Alpaca's servers, not your bot. It works even if bot crashes!

### 2. Take Profit (Automatic)

**What it does**: Sells your stock if price rises enough

**Example**:
```
You buy MSFT at $509
Take profit set at $515 (about 1% above)

If price rises to $515:
→ Alpaca automatically sells
→ You profit ~$6 per share
→ Profit is locked in
```

### 3. Position Size Limits

**What it does**: Prevents taking huge positions

**Rules**:
- Max 10% of your account per trade
- If you have $100,000, max position is $10,000
- Protects you from putting all eggs in one basket

**Example**:
```
Account: $136,000
Max position: $13,600 (10%)

Bot wants to buy $135,000 of MSFT (too much!)
→ Bot caps it at $13,600
→ Buys only 26 shares instead of 267
```

### 4. Circuit Breaker

**What it does**: Stops trading if you lose too much in one day

**Rule**: If you lose 5% in one day, bot stops trading

**Example**:
```
Account starts at: $100,000
Loses 5% = $5,000
Account now: $95,000

→ Bot stops trading for the day
→ Prevents emotional revenge trading
→ Protects from catastrophic losses
```

### 5. Risk Per Trade

**What it does**: Limits how much you can lose per trade

**Rule**: Risk only 1% of account per trade

**Example**:
```
Account: $100,000
Risk per trade: $1,000 (1%)

Even if trade goes bad:
→ Max loss is ~$1,000
→ Need 100 bad trades to lose everything
→ Very safe
```

---

## What Happens If Bot Crashes

### Short Answer: You're Protected! ✅

### Why?

When bot submits an order, it creates **bracket orders** on Alpaca:
- Entry order
- Stop loss order
- Take profit order

All three orders live on **Alpaca's servers**, not your bot.

### Example Timeline

```
01:00 - Bot submits: BUY 26 MSFT with SL=$503, TP=$510
01:01 - Entry fills at $509
01:02 - Bot crashes! ❌
01:03 - Your computer shuts down ❌
02:00 - Price drops to $503
02:00 - Alpaca automatically sells (stop loss hit) ✅
```

**You're protected!** The stop loss executed even though bot was offline.

### What You Should Do

If bot crashes:
1. Don't panic - your positions are protected
2. Check Alpaca dashboard to see active orders
3. Restart bot when convenient
4. Bot will sync with Alpaca and continue

---

## Common Questions

### Q: How much money do I need?

**A**: Minimum $25,000 for day trading (SEC rule). But you can start with less for swing trading.

For this bot with current settings:
- Recommended: $50,000+
- Minimum: $10,000 (will take smaller positions)

### Q: How many trades per day?

**A**: Varies! Could be:
- 0 trades (no signals)
- 1-3 trades (typical)
- 5-10 trades (very active day)

EMA crossovers don't happen constantly, so don't expect trades every minute.

### Q: Can I lose all my money?

**A**: Extremely unlikely with safety features:
- Stop losses limit loss per trade to ~1%
- Circuit breaker stops trading after 5% daily loss
- Position limits prevent over-concentration
- Max positions limit (20) prevents over-trading

To lose everything, you'd need ~100 consecutive losing trades, which is statistically improbable.

### Q: Do I need to watch it constantly?

**A**: No! That's the point of automation.

You can:
- ✅ Let it run 24/7
- ✅ Check once a day
- ✅ Go on vacation
- ✅ Sleep peacefully

The bot handles everything automatically.

### Q: What if I want to stop trading?

**A**: Three options:

1. **Stop bot** (Ctrl+C in terminal)
   - Stops finding new signals
   - Existing positions stay protected
   - Stop losses still active on Alpaca

2. **Close all positions** (in Alpaca dashboard)
   - Sells everything immediately
   - Cancels all pending orders

3. **Disable trading** (in config)
   - Bot runs but doesn't trade
   - Just monitors

### Q: Can I trade manually while bot is running?

**A**: Yes, but be careful!

- Bot won't interfere with your manual trades
- But bot might trade the same stocks
- Could create confusion

**Recommendation**: Either use bot OR trade manually, not both.

### Q: How do I know if it's working?

**A**: Check the logs:

**Good signs**:
```
✅ Updated features for 10 symbols
✅ Evaluating 10 symbols
✅ Signal detected
✅ Order submitted
```

**Bad signs**:
```
❌ ERROR - Failed to fetch bars
❌ ERROR - Failed to submit order
❌ Circuit breaker triggered
```

### Q: What's the difference between paper and live trading?

**Paper Trading** (what you're using now):
- Fake money
- Real market data
- No real risk
- Perfect for testing

**Live Trading**:
- Real money
- Real profits/losses
- Same code, different API keys
- Only switch when confident!

---

## Troubleshooting

### Bot Won't Start

**Error**: `ModuleNotFoundError`

**Fix**:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### No Trades Happening

**Possible reasons**:

1. **Market is closed**
   - Bot only trades 9:30 AM - 4:00 PM ET
   - Check: Is market open?

2. **No signals**
   - EMA crossovers are rare
   - This is normal!
   - Wait patiently

3. **Circuit breaker triggered**
   - Check logs for "Circuit breaker"
   - Resets next trading day

4. **Max positions reached**
   - Already have 20 positions
   - Wait for some to close

### Database Errors

**Error**: `Could not find column`

**Fix**: Run migrations in Supabase SQL Editor
```sql
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS prev_ema_short DECIMAL(10, 4);

ALTER TABLE features 
ADD COLUMN IF NOT EXISTS prev_ema_long DECIMAL(10, 4);

ALTER TABLE features 
ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ;
```

### WebSocket Errors

**Error**: `WebSocketDisconnect`

**Fix**: Ignore it! This is normal when frontend reconnects. Not a real error.

---

## Configuration Guide

### Where to Configure

File: `backend/config.py` or `backend/.env`

### Key Settings

#### Watchlist
```python
watchlist: str = "SPY,QQQ,AAPL,MSFT,NVDA,TSLA,AMD,GOOG,AMZN,META"
```
**What it does**: Stocks the bot watches

**To change**: Add or remove symbols
```python
watchlist: str = "SPY,AAPL,TSLA"  # Only 3 stocks
```

#### Max Positions
```python
max_positions: int = 20
```
**What it does**: Maximum number of positions at once

**To change**:
- More aggressive: `max_positions: int = 30`
- More conservative: `max_positions: int = 10`

#### Risk Per Trade
```python
risk_per_trade_pct: float = 0.01  # 1%
```
**What it does**: How much to risk per trade

**To change**:
- More aggressive: `0.02` (2%)
- More conservative: `0.005` (0.5%)

#### Max Position Size
```python
max_position_pct: float = 0.10  # 10%
```
**What it does**: Max % of account per position

**To change**:
- More aggressive: `0.15` (15%)
- More conservative: `0.05` (5%)

#### EMA Periods
```python
ema_short: int = 9
ema_long: int = 21
```
**What it does**: Moving average periods

**To change** (more signals):
```python
ema_short: int = 5
ema_long: int = 13
```

**Warning**: Shorter periods = more signals but lower quality

#### Stop Loss
```python
stop_loss_atr_mult: float = 2.0
```
**What it does**: Stop loss distance (2x ATR)

**To change**:
- Tighter stops: `1.5` (more losses, smaller losses)
- Wider stops: `3.0` (fewer losses, bigger losses)

#### Take Profit
```python
take_profit_atr_mult: float = 4.0
```
**What it does**: Take profit distance (4x ATR)

**To change**:
- Quicker profits: `2.0` (smaller profits, more frequent)
- Bigger profits: `6.0` (larger profits, less frequent)

### After Changing Config

1. Save the file
2. Restart bot (Ctrl+C, then `python main.py`)
3. New settings take effect immediately

---

## Daily Routine (Recommended)

### Morning (Before Market Open)

1. **Check bot is running**
   ```bash
   # Should see process running
   ps aux | grep python
   ```

2. **Check account balance**
   - Go to Alpaca dashboard
   - Note starting equity

3. **Review open positions**
   - Check what you're holding
   - Verify stop losses are active

### During Market Hours

**Do nothing!** Let the bot work.

Optional: Check once or twice
- Look at positions
- Check P/L
- Read logs if curious

### After Market Close

1. **Review performance**
   - Check daily P/L
   - Count wins vs losses
   - Note any issues

2. **Check logs**
   - Any errors?
   - How many signals?
   - Any rejected orders?

3. **Let bot run overnight**
   - It will prepare for next day
   - Fetches data
   - Calculates indicators

---

## Safety Checklist

Before leaving bot unattended:

- [ ] Stop losses are active (check Alpaca)
- [ ] Circuit breaker is working (check config)
- [ ] Position limits are set (check config)
- [ ] Using paper trading (not real money yet)
- [ ] Have tested for at least 1 week
- [ ] Understand how it works
- [ ] Know how to stop it (Ctrl+C)
- [ ] Have Alpaca dashboard bookmarked
- [ ] Can access from phone if needed

---

## When to Switch to Live Trading

**Don't rush!** Only switch when:

- [ ] Tested in paper for 30+ days
- [ ] Understand all features
- [ ] Comfortable with losses
- [ ] Have emergency fund (don't trade rent money!)
- [ ] Bot is stable (no crashes)
- [ ] Strategy is profitable in paper
- [ ] You can afford to lose the money
- [ ] Have read all documentation
- [ ] Know how to stop/restart bot
- [ ] Have backup plan if bot fails

**Start small**: Even in live, start with minimum account size and scale up slowly.

---

## Emergency Procedures

### Bot is Broken and Market is Open

1. **Don't panic** - positions are protected
2. **Check Alpaca** - verify stop losses are active
3. **Close positions manually** if needed (Alpaca dashboard)
4. **Fix bot later** - don't rush

### Lost Too Much Money

1. **Stop bot** (Ctrl+C)
2. **Close all positions** (Alpaca dashboard)
3. **Review what happened** (check logs)
4. **Adjust settings** (tighter stops, less risk)
5. **Test in paper again** before resuming

### Can't Access Computer

1. **Use phone** - Alpaca has mobile app
2. **Check positions** - verify stop losses active
3. **Close positions** if needed (from phone)
4. **Bot will continue** if computer is on
5. **Stop losses protect you** even if you can't access anything

---

## Final Tips

1. **Start small** - Don't risk money you can't afford to lose
2. **Be patient** - Good trades take time
3. **Trust the system** - Don't interfere with bot's decisions
4. **Keep learning** - Read about trading strategies
5. **Stay calm** - Losses are part of trading
6. **Review regularly** - Check performance weekly
7. **Adjust slowly** - Don't change settings drastically
8. **Paper trade first** - Test everything thoroughly
9. **Have fun** - Trading should be exciting, not stressful
10. **Ask questions** - Better to ask than to lose money

---

## Getting Help

### Check Logs
```bash
cd backend
tail -f logs/*.log
```

### Run Diagnostics
```bash
cd backend
python diagnose_trading.py
```

### Check Documentation
- `README.md` - Overview
- `QUICKSTART_GUIDE.md` - Setup instructions
- `ARCHITECTURE.md` - How it works
- `AI_USAGE_IN_AUTOPILOT.md` - AI costs

### Common Issues
- See `TROUBLESHOOTING.md` (if exists)
- Check GitHub issues
- Review error logs

---

## Glossary

**EMA**: Exponential Moving Average - shows average price over time

**ATR**: Average True Range - measures price volatility

**Bracket Order**: Entry + Stop Loss + Take Profit in one order

**Stop Loss**: Automatic sell order to limit losses

**Take Profit**: Automatic sell order to lock in profits

**Circuit Breaker**: Safety feature that stops trading after big losses

**Paper Trading**: Trading with fake money for practice

**Live Trading**: Trading with real money

**Position**: Stock you currently own

**Signal**: Trading opportunity detected by bot

**Crossover**: When fast EMA crosses slow EMA (buy/sell signal)

---

## Remember

- **The bot is a tool, not magic** - It can lose money
- **Past performance ≠ future results** - No guarantees
- **Always use stop losses** - Protect your capital
- **Start with paper trading** - Learn before risking real money
- **Don't invest more than you can afford to lose** - Seriously!

**Good luck and happy trading!** 🚀
