# Dynamic Universe Enhancement - December 9, 2024

## Problem Solved
The trading system was only scanning ~20 mega-cap stocks, missing opportunities in mid-caps and growth stocks that often have higher momentum and profit potential.

## Solution Implemented

### 1. Dynamic Universe Manager (`scanner/dynamic_universe.py`)
- **API-DRIVEN DISCOVERY** - Pulls real-time data from Alpaca API daily
- **224+ candidate stocks** across 12+ categories (base + API-discovered)
- **Daily refresh** at market open using live market data
- **Growth-focused scoring** - mid-caps with momentum score higher than stable mega-caps
- **Liquidity filtering** - only tradeable stocks with $1M+ daily volume

### API Discovery Sources
| Source | Description | Growth Score |
|--------|-------------|--------------|
| Top Gainers | Stocks up most today | 98 (highest) |
| Most Active | Highest volume stocks | 92 |
| Top Losers | Potential bounce plays | 75 |

### 2. Two-Tier Refresh System

#### Weekly Curated List (Base - 70/30 Split)
Refreshes every **Monday** with consistently profitable stocks:
- **70% Large-Caps**: Stable, liquid, consistent performers (AAPL, MSFT, JPM, etc.)
- **30% Mid-Caps**: Higher growth potential (PLTR, SNOW, DDOG, etc.)

#### Daily API Discovery (Top Layer)
Refreshes **daily at 9:45 AM ET** with real-time movers:
- Top gainers from Alpaca API
- Most active by volume
- Top losers (bounce plays)

### 3. Growth-Focused Categories (by priority)
| Category | Growth Score | Description |
|----------|-------------|-------------|
| api_top_gainer | 98 | Today's top gainers (API) |
| high_beta_momentum | 95 | Volatile movers (COIN, MARA, RIOT) |
| api_most_active | 92 | Highest volume today (API) |
| high_growth_tech | 90 | SaaS/Cloud growth (PLTR, SNOW, DDOG) |
| curated_mid_cap | 88 | Weekly curated mid-caps |
| ev_cleantech | 88 | EV & clean energy (TSLA, RIVN, LCID) |
| semiconductor_growth | 85 | Chip momentum (NVDA, AMD, MRVL) |
| biotech_growth | 82 | Biotech momentum (MRNA, CRSP) |
| curated_large_cap | 80 | Weekly curated large-caps |
| ai_cloud | 80 | AI leaders (MSFT, GOOGL, PANW) |
| fintech | 78 | Payment/fintech (SQ, PYPL, SOFI) |
| api_top_loser | 75 | Today's losers - bounce plays (API) |
| consumer_growth | 75 | Consumer tech (ABNB, UBER, RBLX) |
| industrial_growth | 70 | Aerospace/defense (BA, AXON, RKLB) |
| sector_etfs | 65 | Sector rotation plays |
| market_etfs | 60 | Index ETFs (SPY, QQQ) |
| mega_cap_stable | 50 | Stable mega-caps (AAPL, JNJ) |

### 3. Composite Scoring Formula
```
Composite Score = 
  Growth Potential × 40% +
  Recent Momentum × 30% +
  Volatility × 20% +
  Liquidity × 10%
```

This ensures mid-cap growth stocks can outrank stable mega-caps.

### 4. Enhanced Opportunity Scorer
- **New growth_score component** (0-10 points)
- **Total scale now 0-130** (was 0-120)
- Rewards: high volatility, strong momentum, volume surges, fresh breakouts

### 5. Configuration Changes
- `scanner_watchlist_size`: 21 → 50 (more opportunities)
- Dynamic universe integrated into momentum scanner
- Stock universe now pulls from dynamic universe first

## Test Results
```
Growth Stock Score: 110.0 (A+)
Stable Mega-Cap Score: 73.0 (B)
Growth beats Stable: ✅
```

## Files Modified
- `backend/scanner/dynamic_universe.py` - NEW
- `backend/scanner/opportunity_scorer.py` - Added growth scoring
- `backend/scanner/momentum_scanner.py` - Uses dynamic universe
- `backend/scanner/stock_universe.py` - Integrates dynamic universe
- `backend/trading/trading_engine.py` - Daily universe refresh
- `backend/config.py` - Increased watchlist size

## Timing - When Does It Refresh?

| Time | Action |
|------|--------|
| Pre-market (before 9:30 AM ET) | Uses curated list of 224 growth stocks |
| **9:30-9:35 AM ET** | Trades using curated list + tries API for early movers |
| **9:35 AM ET** | **First refresh** - fetches real day's movers from API |
| During market hours | Uses cached universe (refreshed at 9:35 AM) |
| After market close | Cache remains valid until next day |

### No Momentum Missed!
- **9:30 AM**: Bot starts trading immediately using curated list (PLTR, NVDA, AMD, etc.)
- **9:35 AM**: Quick refresh to add any new movers discovered in first 5 minutes
- The curated list already includes 224 high-momentum stocks, so early trades are covered

## How It Works
1. **At 9:45 AM ET**: Universe refreshes from Alpaca API
2. **API Discovery**: Fetches top gainers, losers, most active stocks
3. **Merge with curated list**: API-discovered + 224 curated candidates
4. **Score each stock**: Using real market data (volatility, momentum, volume)
5. **Select top 150**: By composite score (growth + momentum + volatility + liquidity)
6. **Cache for the day**: Universe cached until next trading day
7. **Pre-market fallback**: Uses curated list if started before market opens

## Data Sources
- **Alpaca API**: Top movers, most active, market data (after 9:30 AM ET)
- **Market Data Manager**: Historical bars for volatility/momentum calculation
- **Weekly Curated List**: 150 stocks (70% large-cap, 30% mid-cap) refreshed every Monday

## Files
- `scanner/dynamic_universe.py` - Daily universe manager (API + curated)
- `scanner/curated_universe.py` - Weekly curated list manager (70/30 split)
- `scanner/universe_cache.json` - Daily cache
- `scanner/curated_cache.json` - Weekly cache
