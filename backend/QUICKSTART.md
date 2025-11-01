# Quick Start Guide

## You're Almost Ready! 🚀

Your `.env` is configured. Now just run the setup:

### Step 1: Setup Virtual Environment

```bash
cd backend
./setup.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Verify everything is ready

### Step 2: Start Backend

```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate
python main.py
```

### Step 3: Verify It's Working

Open another terminal and test:

```bash
# Health check
curl http://localhost:8006/health

# Get account info
curl http://localhost:8006/account

# Get positions
curl http://localhost:8006/positions
```

You should see your Alpaca paper trading account info!

## What's Configured

✅ **Alpaca**: Paper trading ready
✅ **Supabase**: Database connected
✅ **OpenRouter**: 
- Primary: Gemini 2.5 Flash (analysis)
- Secondary: Gemini 2.5 Flash Lite (chat)
- Backup: Minimax Free
✅ **Perplexity**: News and research

## Test a Trade

### Via API:
```bash
curl -X POST "http://localhost:8006/orders/submit?symbol=AAPL&side=buy&qty=10&reason=test"
```

### Via Frontend:
1. Start frontend: `npm run dev` (in root directory)
2. Open http://localhost:5176
3. In chat: `buy 10 AAPL`

## Common Issues

### "Virtual environment not found"
Run `./setup.sh` first

### "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Failed to connect to Alpaca"
Check your Alpaca keys in `.env`

### "Failed to connect to Supabase"
1. Verify Supabase URL and keys
2. Make sure you ran `supabase_schema.sql`

## Next Steps

1. ✅ Backend running
2. Test manual order submission
3. Watch it auto-trade during market hours
4. Monitor performance in dashboard
5. Adjust strategy in `.env` if needed

## Model Configuration

Your OpenRouter models are optimized for:
- **Analysis**: Gemini 2.5 Flash (best quality/cost)
- **Chat**: Gemini 2.5 Flash Lite (fast responses)
- **Backup**: Minimax Free (no cost)

See `MODEL_GUIDE.md` for alternatives.

## Emergency Controls

### Stop Trading
```bash
curl -X POST http://localhost:8006/trading/disable
```

### Emergency Stop (Close All)
```bash
curl -X POST http://localhost:8006/emergency/stop
```

### Enable Trading Again
```bash
curl -X POST http://localhost:8006/trading/enable
```

## Monitoring

Watch the backend terminal for:
- Order submissions
- Risk check results
- Signal detections
- Position updates
- Errors and warnings

## Ready to Trade!

Your bot is configured and ready. Just run:

```bash
cd backend
./setup.sh    # First time only
./run.sh      # Start trading
```

Happy trading! 📈💰
