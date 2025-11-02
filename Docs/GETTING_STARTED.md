# Getting Started with DayTraderAI

Complete guide to get your trading bot running from scratch.

## Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend)
- **Alpaca Account** (paper trading)
- **Supabase Account** (free tier works)

## Step 1: Clone and Setup

```bash
git clone https://github.com/codebytelabs/DayTraderAI.git
cd DayTraderAI
```

## Step 2: Setup Supabase

### 2.1 Create Project
1. Go to https://supabase.com
2. Click "New Project"
3. Choose a name and password
4. Wait for project to be ready (~2 minutes)

### 2.2 Run Schema
1. In Supabase dashboard, go to **SQL Editor**
2. Click "New Query"
3. Copy contents of `backend/supabase_schema.sql`
4. Paste and click "Run"
5. Verify tables created in **Table Editor**

### 2.3 Get API Keys
1. Go to **Settings** > **API**
2. Copy these values:
   - Project URL
   - `anon` `public` key
   - `service_role` `secret` key

## Step 3: Setup Alpaca

### 3.1 Create Account
1. Go to https://alpaca.markets
2. Sign up for free account
3. Verify email

### 3.2 Get Paper Trading Keys
1. Login to dashboard
2. Go to **Paper Trading** section
3. Generate API keys
4. **Important**: These are PAPER TRADING keys (no real money)

## Step 4: Setup Backend

```bash
cd backend

# Run setup script (Mac/Linux)
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4.1 Configure Environment

```bash
cp .env.example .env
nano .env  # or use your favorite editor
```

Fill in your keys:

```bash
# Alpaca (Paper Trading)
ALPACA_API_KEY=PK...
ALPACA_SECRET_KEY=...
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJ...  # anon key
SUPABASE_SERVICE_KEY=eyJ...  # service_role key

# Strategy (defaults are fine to start)
WATCHLIST=SPY,QQQ,AAPL,MSFT,NVDA
MAX_POSITIONS=5
RISK_PER_TRADE_PCT=0.01
```

### 4.2 Test Backend

```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Alpaca client initialized (PAPER TRADING)
INFO:     Supabase client initialized
INFO:     State synced: 0 positions, $100000.00 equity
INFO:     Backend initialized successfully
INFO:     Application startup complete.
```

Visit http://localhost:8000 - you should see:
```json
{
  "service": "DayTraderAI Backend",
  "status": "running",
  "version": "1.0.0",
  "trading_enabled": true
}
```

## Step 5: Setup Frontend

Open a **new terminal** (keep backend running):

```bash
cd DayTraderAI  # back to root
npm install
npm run dev
```

Visit http://localhost:5173

## Step 6: Configure Frontend

1. Click **Settings** (gear icon, top right)
2. Fill in the same keys you used for backend:
   - Alpaca keys
   - Supabase keys
   - (Optional) Perplexity and OpenRouter keys for LLM features
3. Click **Save Settings**

## Step 7: Verify Everything Works

### Backend Health Check
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "alpaca": "connected",
  "market": "open" or "closed",
  "trading_enabled": true
}
```

### Check Account
```bash
curl http://localhost:8000/account
```

Should show your paper trading account:
```json
{
  "equity": 100000.0,
  "cash": 100000.0,
  "buying_power": 400000.0,
  ...
}
```

### Frontend Dashboard
- Should show $0 P/L (no trades yet)
- Should show 0 open positions
- Should show your watchlist symbols
- Chat copilot should respond

## Step 8: Test Paper Trading

### Manual Order Test

In the frontend chat, type:
```
buy 10 AAPL
```

Or via API:
```bash
curl -X POST "http://localhost:8000/orders/submit?symbol=AAPL&side=buy&qty=10&reason=test"
```

Check:
1. Order appears in Orders table
2. Position appears after fill
3. Supabase `orders` and `positions` tables updated

### Close Position

In chat:
```
close AAPL
```

Or via API:
```bash
curl -X POST http://localhost:8000/positions/AAPL/close
```

## Step 9: Let Strategy Run

The backend automatically:
1. Monitors watchlist symbols
2. Computes EMA indicators
3. Detects crossover signals
4. Submits orders (if risk checks pass)
5. Monitors positions for stop/target

Just leave it running during market hours!

## Troubleshooting

### Backend won't start

**"Failed to connect to Alpaca"**
- Check API keys in `.env`
- Verify you're using paper trading keys
- Check https://status.alpaca.markets

**"Failed to connect to Supabase"**
- Check URL and keys in `.env`
- Verify schema was created
- Check project is active in Supabase dashboard

### No trades happening

**Check market hours**
```bash
curl http://localhost:8000/health
```
Look for `"market": "open"`

**Check trading enabled**
```bash
curl http://localhost:8000/metrics
```
Look for `"circuit_breaker_triggered": false`

**Check logs**
Backend terminal will show:
- Signal detections
- Order submissions
- Risk check failures

### Orders rejected

Check backend logs for reason:
- "Max positions reached" - close some positions
- "Insufficient buying power" - reduce position size
- "Circuit breaker triggered" - daily loss limit hit
- "Market is closed" - wait for market hours

## Next Steps

### Monitor Performance

Watch the dashboard for:
- Win rate (target: ≥60%)
- Profit factor (target: ≥1.5)
- Daily P/L
- Slippage and fill rates

### Adjust Strategy

Edit `backend/.env`:
```bash
# More conservative
RISK_PER_TRADE_PCT=0.005  # 0.5% instead of 1%
MAX_POSITIONS=3

# Different EMA periods
EMA_SHORT=12
EMA_LONG=26
```

Restart backend for changes to take effect.

### Add More Symbols

```bash
WATCHLIST=SPY,QQQ,AAPL,MSFT,NVDA,TSLA,AMD,GOOG,AMZN,META,NFLX,BABA
```

### Paper Trade Extensively

**Before going live:**
- Run for at least 300 trades
- Verify consistent profitability
- Test circuit breaker triggers correctly
- Test emergency stop works
- Monitor during volatile market conditions

### Go Live (When Ready)

⚠️ **Only after extensive paper trading success**

1. Get live trading approved by Alpaca
2. Generate live API keys
3. Update `.env`:
   ```bash
   ALPACA_BASE_URL=https://api.alpaca.markets
   ```
4. **Start with small capital allocation**
5. Monitor continuously

## Safety Reminders

- ✅ Always start with paper trading
- ✅ Test thoroughly before going live
- ✅ Never risk more than you can afford to lose
- ✅ Monitor during market hours
- ✅ Have emergency stop ready
- ✅ Keep position sizes small initially
- ✅ Understand the strategy before deploying

## Support

- Check `TODO.md` for development roadmap
- Check `DayTraderAI_idea.md` for full blueprint
- Check `backend/README.md` for API documentation
- Review logs for debugging

Happy trading! 🚀📈

---

**Disclaimer**: This is experimental software for educational purposes. Trading involves risk of loss. Past performance does not guarantee future results. Use at your own risk.
