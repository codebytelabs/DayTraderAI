# DayTraderAI Backend

Production-grade trading bot backend with real Alpaca execution, Supabase persistence, and bulletproof risk management.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Setup Supabase

1. Create a Supabase project at https://supabase.com
2. Go to SQL Editor and run `supabase_schema.sql`
3. Get your project URL and keys from Settings > API

### 3. Setup Alpaca

1. Create account at https://alpaca.markets
2. Get paper trading API keys from dashboard
3. **Important**: Start with paper trading!

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your keys
```

Required variables:
- `ALPACA_API_KEY` - Your Alpaca API key
- `ALPACA_SECRET_KEY` - Your Alpaca secret key
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key
- `SUPABASE_SERVICE_KEY` - Your Supabase service role key

### 5. Run Backend

```bash
python main.py
```

Backend will start on http://localhost:8000

## API Endpoints

### Health & Status
- `GET /` - Service info
- `GET /health` - Health check
- `GET /account` - Account information
- `GET /metrics` - Trading metrics

### Trading
- `GET /positions` - Get all positions
- `GET /orders` - Get all orders
- `POST /orders/submit` - Submit new order
- `POST /orders/{order_id}/cancel` - Cancel order
- `POST /positions/{symbol}/close` - Close position

### Controls
- `POST /trading/enable` - Enable trading
- `POST /trading/disable` - Disable trading
- `POST /emergency/stop` - Emergency stop (close all)
- `POST /sync` - Sync state from Alpaca

## Architecture

```
backend/
├── main.py                 # FastAPI application
├── config.py              # Configuration management
├── core/
│   ├── alpaca_client.py  # Alpaca API wrapper
│   ├── supabase_client.py # Supabase wrapper
│   └── state.py          # Shared state management
├── trading/
│   ├── risk_manager.py   # Pre-trade risk checks
│   ├── order_manager.py  # Order execution
│   ├── position_manager.py # Position monitoring
│   └── strategy.py       # EMA strategy
├── data/
│   ├── market_data.py    # Data ingestion
│   └── features.py       # Indicator computation
└── utils/
    ├── helpers.py        # Utility functions
    └── logger.py         # Logging setup
```

## Risk Management

Every order passes through RiskManager with these checks:

1. **Trading enabled** - System not in emergency stop
2. **Circuit breaker** - Daily loss < 5%
3. **Market open** - No trading when market closed
4. **Position limits** - Max 5 concurrent positions
5. **Position sizing** - Risk ≤ 1% per trade
6. **Buying power** - Sufficient capital available

## Order Idempotency

Orders use deterministic IDs to prevent duplicates:

```python
order_id = hash(symbol + side + qty + price + timestamp_minute)
```

Same order intent within the same minute = same ID = Alpaca rejects duplicate.

## Strategy

**EMA Crossover Strategy**
- Entry: EMA(9) crosses EMA(21)
- Stop Loss: 2× ATR from entry
- Take Profit: 4× ATR from entry
- Position Size: 1% equity at risk

## Emergency Controls

### Circuit Breaker
Automatically triggers if daily loss exceeds 5%. Halts all new trades.

### Emergency Stop
```bash
curl -X POST http://localhost:8000/emergency/stop
```

Immediately:
1. Disables trading
2. Closes all positions
3. Cancels all orders

### Manual Controls
```bash
# Disable trading
curl -X POST http://localhost:8000/trading/disable

# Enable trading
curl -X POST http://localhost:8000/trading/enable
```

## Monitoring

Check logs for:
- Order submissions and rejections
- Risk check failures
- Circuit breaker triggers
- API errors

## Development

### Run with auto-reload
```bash
uvicorn main:app --reload --port 8000
```

### Test endpoints
```bash
# Health check
curl http://localhost:8000/health

# Get positions
curl http://localhost:8000/positions

# Submit order (will be rejected without proper setup)
curl -X POST "http://localhost:8000/orders/submit?symbol=AAPL&side=buy&qty=10&reason=test"
```

## Production Checklist

Before going live:

- [ ] Test extensively in paper trading (minimum 300 trades)
- [ ] Verify win rate ≥ 60%
- [ ] Verify profit factor ≥ 1.5
- [ ] Test circuit breaker triggers correctly
- [ ] Test emergency stop works
- [ ] Verify order idempotency (no duplicates)
- [ ] Monitor slippage and fill rates
- [ ] Setup alerting for errors
- [ ] Document runbooks for incidents
- [ ] Start with small capital allocation

## Troubleshooting

### "Failed to connect to Alpaca"
- Check API keys in .env
- Verify keys are for paper trading
- Check Alpaca service status

### "Failed to connect to Supabase"
- Check Supabase URL and keys
- Verify schema is created
- Check Supabase project status

### "Order rejected"
- Check logs for specific reason
- Verify market is open
- Check buying power
- Verify symbol in watchlist

## Safety Notes

⚠️ **This is experimental software**
- Start with paper trading
- Never risk more than you can afford to lose
- Monitor continuously during market hours
- Have emergency stop procedures ready
- Keep position sizes small initially

## Next Steps

1. Run backend and verify connection to Alpaca
2. Test order submission in paper trading
3. Monitor for a full trading day
4. Analyze performance metrics
5. Iterate on strategy parameters
6. Add more strategies
7. Implement LLM advisory system
8. Add backtesting framework

Happy trading! 🚀
