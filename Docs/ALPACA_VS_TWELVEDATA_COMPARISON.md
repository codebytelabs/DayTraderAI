# Alpaca vs Twelve Data: Comprehensive Comparison

**Date:** November 11, 2025  
**Purpose:** Identify what Twelve Data offers beyond Alpaca

---

## 🎯 Executive Summary

**Verdict:** Twelve Data offers **significant additional capabilities** beyond Alpaca, especially for:
1. **Fundamental data** (earnings, financials, ratios)
2. **Multi-asset coverage** (forex, crypto, commodities)
3. **100+ technical indicators** (pre-calculated)
4. **Economic calendars** (macro events)
5. **Global markets** (international stocks)

**For Your Current Use Case:**
- Alpaca: Perfect for US stock trading execution and intraday data ✅
- Twelve Data: Perfect for daily bars and future expansion ✅

---

## 📊 Feature Comparison Matrix

| Feature | Alpaca (Paper/Free) | Alpaca (Paid) | Twelve Data (Free) | Twelve Data (Paid) |
|---------|---------------------|---------------|--------------------|--------------------|
| **US Stocks - Intraday** | ✅ IEX only | ✅ Full SIP | ✅ Yes | ✅ Yes |
| **US Stocks - Daily** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Order Execution** | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **Position Tracking** | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **Forex** | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| **Crypto** | ✅ Limited | ✅ Yes | ✅ Yes | ✅ Yes |
| **Options** | ✅ Limited | ✅ Yes | ❌ No | ❌ No |
| **Futures** | ❌ No | ❌ No | ❌ No | ❌ No |
| **ETFs** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Indices** | ✅ Limited | ✅ Yes | ✅ Yes | ✅ Yes |
| **Fundamental Data** | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| **Earnings Data** | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| **Financial Statements** | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| **Technical Indicators** | ❌ No | ❌ No | ✅ 100+ | ✅ 100+ |
| **Economic Calendar** | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| **Global Markets** | ❌ US only | ❌ US only | ✅ Worldwide | ✅ Worldwide |
| **WebSocket** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Batch Requests** | ❌ No | ❌ No | ✅ Yes | ✅ Yes |

---

## 🚀 What Twelve Data Does BETTER Than Alpaca

### 1. ✅ Fundamental Data (MAJOR ADVANTAGE)

**What Twelve Data Offers:**
- Income statements
- Balance sheets
- Cash flow statements
- Key financial ratios (P/E, P/B, ROE, etc.)
- Earnings per share (EPS)
- Dividends history
- Stock splits
- Company profiles
- Market capitalization

**What Alpaca Offers:**
- ❌ None of the above

**Use Cases for Your Trading:**
- **Long-term position sizing** based on fundamentals
- **Earnings calendar** to avoid trading before earnings
- **Dividend screening** for income strategies
- **Financial health checks** before entering positions
- **Sector rotation** based on fundamental strength

**Example API Call:**
```python
# Get Apple's fundamentals
response = requests.get(
    'https://api.twelvedata.com/profile',
    params={'symbol': 'AAPL', 'apikey': API_KEY}
)

# Returns:
{
    "name": "Apple Inc",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "market_cap": 2800000000000,
    "pe_ratio": 28.5,
    "dividend_yield": 0.52,
    "earnings_date": "2025-11-15"
}
```

---

### 2. ✅ Forex Trading Data (EXPANSION OPPORTUNITY)

**What Twelve Data Offers:**
- 2,000+ forex pairs
- Real-time and historical data
- Major, minor, and exotic pairs
- Bid/ask spreads
- Tick data

**What Alpaca Offers:**
- ❌ No forex trading
- ❌ No forex data

**Use Cases:**
- **Diversify into forex** (24/5 trading)
- **Currency hedging** for international positions
- **Correlation analysis** (USD strength vs stocks)
- **Macro trading** based on economic events

**Example Pairs:**
- EUR/USD, GBP/USD, USD/JPY (majors)
- EUR/GBP, AUD/NZD (minors)
- USD/TRY, EUR/ZAR (exotics)

---

### 3. ✅ Cryptocurrency Data (BETTER COVERAGE)

**What Twelve Data Offers:**
- 2,000+ crypto pairs
- Multiple exchanges (Binance, Coinbase, Kraken, etc.)
- Real-time and historical
- 24/7 data

**What Alpaca Offers:**
- Limited crypto pairs
- US-based exchanges only
- Restricted hours

**Use Cases:**
- **24/7 trading** (no market close)
- **Arbitrage opportunities** across exchanges
- **Crypto momentum strategies**
- **Portfolio diversification**

---

### 4. ✅ 100+ Pre-calculated Technical Indicators

**What Twelve Data Offers:**
- All indicators pre-calculated server-side
- No computation overhead
- Consistent calculations
- Historical indicator values

**Available Indicators:**
- Trend: EMA, SMA, WMA, DEMA, TEMA, TRIMA, KAMA, MAMA
- Momentum: RSI, STOCH, MACD, ADX, CCI, MOM, ROC, Williams %R
- Volatility: ATR, BBANDS, NATR, TRANGE
- Volume: OBV, AD, ADOSC
- And 80+ more...

**What Alpaca Offers:**
- ❌ No pre-calculated indicators
- Must calculate manually

**Use Cases:**
- **Faster strategy development** (no indicator coding)
- **Backtesting** with historical indicator values
- **Complex strategies** with multiple indicators
- **Reduced computation** on your server

**Example:**
```python
# Get RSI without calculating it yourself
response = requests.get(
    'https://api.twelvedata.com/rsi',
    params={
        'symbol': 'AAPL',
        'interval': '5min',
        'time_period': 14,
        'apikey': API_KEY
    }
)

# Returns ready-to-use RSI values
```

---

### 5. ✅ Economic Calendar & Events

**What Twelve Data Offers:**
- Economic event calendar
- Earnings announcements
- Dividend dates
- Stock splits
- IPO calendar
- Conference calls

**What Alpaca Offers:**
- ❌ None of the above

**Use Cases:**
- **Avoid trading before major events** (Fed announcements, NFP)
- **Earnings plays** (trade around earnings)
- **Dividend capture** strategies
- **IPO trading** opportunities
- **Risk management** (pause trading during high-impact events)

**Example Events:**
- FOMC meetings
- Non-Farm Payrolls (NFP)
- CPI/PPI releases
- GDP reports
- Company earnings

---

### 6. ✅ Global Market Coverage

**What Twelve Data Offers:**
- 100,000+ symbols worldwide
- 70+ exchanges globally
- International stocks (LSE, TSE, HKEX, etc.)
- ADRs and international ETFs

**What Alpaca Offers:**
- US markets only (NYSE, NASDAQ)
- ~10,000 symbols

**Use Cases:**
- **International diversification**
- **Follow-the-sun trading** (trade different time zones)
- **Emerging markets** exposure
- **ADR arbitrage** opportunities

---

### 7. ✅ Batch Requests (EFFICIENCY)

**What Twelve Data Offers:**
- Query up to 120 symbols in one request
- Reduces API calls
- Faster data retrieval

**What Alpaca Offers:**
- Individual requests only
- More API calls needed

**Use Cases:**
- **Efficient watchlist updates**
- **Portfolio-wide analysis**
- **Sector screening**
- **Correlation matrices**

**Example:**
```python
# Get data for 50 symbols in ONE request
symbols = ','.join(['AAPL', 'TSLA', 'NVDA', ...])  # up to 120
response = requests.get(
    'https://api.twelvedata.com/time_series',
    params={'symbol': symbols, 'interval': '1day', 'apikey': API_KEY}
)
```

---

### 8. ✅ Multiple Output Formats

**What Twelve Data Offers:**
- JSON (default)
- CSV (for Excel/spreadsheets)
- Pandas DataFrame (Python)

**What Alpaca Offers:**
- JSON only
- Must convert manually

**Use Cases:**
- **Quick Excel exports** for analysis
- **Direct pandas integration** for backtesting
- **Flexible data processing**

---

## ❌ What Alpaca Does BETTER Than Twelve Data

### 1. ✅ Order Execution
- Alpaca: Full broker with order execution
- Twelve Data: Data only, no trading

### 2. ✅ Position Management
- Alpaca: Real-time position tracking
- Twelve Data: No position management

### 3. ✅ Account Management
- Alpaca: Full account management
- Twelve Data: No account features

### 4. ✅ Paper Trading
- Alpaca: Free paper trading environment
- Twelve Data: No trading simulation

### 5. ✅ Options Trading
- Alpaca: Options data and trading
- Twelve Data: No options support

---

## 💡 RECOMMENDED STRATEGY: Use Both!

### Alpaca For:
✅ Order execution (buy/sell)  
✅ Position tracking  
✅ Account management  
✅ Intraday 5-minute bars (free)  
✅ Real-time quotes (free)  
✅ Paper trading environment  

### Twelve Data For:
✅ Daily bars (Sprint 7 filters)  
✅ Fundamental data (future enhancement)  
✅ Earnings calendar (risk management)  
✅ Economic events (macro awareness)  
✅ Pre-calculated indicators (efficiency)  
✅ Forex/crypto expansion (future)  
✅ Global markets (future)  

---

## 🚀 Future Enhancement Opportunities

### Phase 1: Current (Sprint 7)
- ✅ Daily bars for 200-EMA filter
- ✅ Multi-timeframe alignment

### Phase 2: Fundamental Integration (Sprint 9-10)
- Add earnings calendar check
- Avoid trading 1 day before/after earnings
- Filter by P/E ratio (avoid overvalued stocks)
- Check financial health before entries

### Phase 3: Economic Awareness (Sprint 11-12)
- Pause trading during FOMC meetings
- Reduce position sizes before NFP
- Track VIX vs economic events
- Macro regime detection

### Phase 4: Multi-Asset Expansion (Sprint 13+)
- Add forex pairs (EUR/USD, GBP/USD)
- Add crypto (BTC, ETH)
- 24/7 trading capability
- Cross-asset correlation

### Phase 5: Global Markets (Sprint 14+)
- International stocks
- Follow-the-sun trading
- Emerging markets
- ADR opportunities

---

## 💰 Cost Comparison

### Alpaca
- **Paper Trading:** FREE ✅
- **Live Trading:** FREE (commission-free)
- **Market Data (Basic):** FREE (IEX only)
- **Market Data (Unlimited):** $99/month (full SIP)

### Twelve Data
- **Free Tier:** 800 credits/day ✅
- **Basic Plan:** $29/month (3,000 credits/day)
- **Pro Plan:** $79/month (10,000 credits/day)
- **Enterprise:** Custom pricing

### Your Current Setup (Optimal)
- **Alpaca Paper:** FREE (trading + intraday data)
- **Twelve Data Free:** FREE (daily bars only)
- **Total Cost:** $0/month ✅
- **Capabilities:** Full trading + Sprint 7 filters

---

## 📊 Credit Usage Projection

### Current (Sprint 7 Only)
- Daily bars: 50 symbols × 1 credit = 50/day
- API usage check: 1/day
- **Total:** 51 credits/day (6.4% of free tier)

### Future (With Enhancements)
- Daily bars: 50 credits
- Fundamentals: 50 symbols × 1 credit = 50
- Earnings calendar: 1 credit
- Economic calendar: 1 credit
- **Total:** 152 credits/day (19% of free tier)

### Still Sustainable ✅
- Free tier: 800 credits/day
- Projected usage: 152 credits/day
- Headroom: 648 credits/day (81%)

---

## 🎯 Conclusion

### What Twelve Data Does Better:
1. ✅ **Fundamental data** (earnings, financials, ratios)
2. ✅ **Multi-asset coverage** (forex, crypto, global)
3. ✅ **Pre-calculated indicators** (100+ technical indicators)
4. ✅ **Economic calendar** (macro events)
5. ✅ **Batch requests** (efficiency)
6. ✅ **Global markets** (international stocks)
7. ✅ **Multiple formats** (JSON, CSV, pandas)

### What Alpaca Does Better:
1. ✅ **Order execution** (actual trading)
2. ✅ **Position management** (tracking)
3. ✅ **Account management** (full broker)
4. ✅ **Paper trading** (free simulation)
5. ✅ **Options trading** (options data)

### Optimal Strategy:
**Use BOTH together:**
- Alpaca: Trading execution + intraday data
- Twelve Data: Daily bars + fundamentals + future expansion

### Current Implementation:
- ✅ Alpaca for trading (FREE)
- ✅ Twelve Data for Sprint 7 (FREE)
- ✅ Total cost: $0/month
- ✅ Full capabilities unlocked

### Future Potential:
- Earnings-aware trading (avoid surprises)
- Fundamental screening (quality stocks)
- Economic event awareness (macro risk)
- Multi-asset expansion (forex, crypto)
- Global market access (international)

**Verdict:** Twelve Data is a **perfect complement** to Alpaca, not a replacement. Together they provide everything you need for professional algorithmic trading.

---

*Last Updated: November 11, 2025*  
*Status: Comprehensive comparison complete*  
*Recommendation: Implement Twelve Data for Sprint 7, explore fundamentals in Sprint 9+*
