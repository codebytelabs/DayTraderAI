# Watchlist Management & Enhanced Controls Spec

## 1. Watchlist Commands

### New Slash Commands

#### `/watchlist` or `/wl`
View current watchlist with stats

**Response:**
```
📋 Current Watchlist (10 symbols)

Symbol | Price   | Change | Signal | Position
-------|---------|--------|--------|----------
AAPL   | $175.50 | +1.2%  | BUY    | 200 shares
MSFT   | $385.20 | -0.5%  | HOLD   | -
NVDA   | $485.80 | +2.3%  | BUY    | 50 shares
TSLA   | $305.50 | +0.8%  | SELL   | -
...

Total: 10 symbols | Active positions: 3/10
```

#### `/watchlist add SYMBOL` or `/wl add SYMBOL`
Add symbol to watchlist

**Examples:**
- `/watchlist add COIN`
- `/wl add COIN SHOP RBLX` (multiple)

**Response:**
```
✅ Added to watchlist: COIN
Current watchlist: SPY, QQQ, AAPL, MSFT, NVDA, TSLA, AMD, GOOGL, META, AMZN, COIN (11 symbols)

⚠️ Note: Watchlist changes persist until backend restart. 
To make permanent, update .env file.
```

#### `/watchlist remove SYMBOL` or `/wl remove SYMBOL`
Remove symbol from watchlist

**Examples:**
- `/watchlist remove TSLA`
- `/wl remove TSLA AMD` (multiple)

**Response:**
```
✅ Removed from watchlist: TSLA
Current watchlist: SPY, QQQ, AAPL, MSFT, NVDA, AMD, GOOGL, META, AMZN (9 symbols)

⚠️ Warning: If you have open positions in TSLA, they will NOT be automatically closed.
```

#### `/watchlist reset`
Reset to default watchlist from .env

**Response:**
```
✅ Watchlist reset to default
Current watchlist: SPY, QQQ, AAPL, MSFT, NVDA, TSLA, AMD, GOOGL, META, AMZN (10 symbols)
```

### Backend Implementation

**File:** `backend/copilot/command_handler.py`

```python
async def execute_watchlist_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Execute watchlist management commands."""
    args = parsed.get("args", [])
    
    if not args or args[0] == "view":
        # View current watchlist
        return self._view_watchlist()
    
    action = args[0].lower()
    
    if action == "add":
        symbols = [s.upper() for s in args[1:]]
        return await self._add_to_watchlist(symbols)
    
    elif action == "remove":
        symbols = [s.upper() for s in args[1:]]
        return await self._remove_from_watchlist(symbols)
    
    elif action == "reset":
        return self._reset_watchlist()
    
    else:
        return {
            "success": False,
            "message": f"Unknown watchlist action: {action}"
        }
```

---

## 2. Market Status Indicator

### Visual Design

```
┌─────────────────────────────────────────────────────┐
│ 🔴 MARKET CLOSED                                    │
│ Opens in: 2h 15m 30s                                │
│ Local: 7:15 AM PST | Market: 10:15 AM EST          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 🟠 MARKET OPENING SOON                              │
│ Opens in: 45m 12s                                   │
│ Local: 8:45 AM PST | Market: 11:45 AM EST          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 🟢 MARKET OPEN                                      │
│ Closes in: 5h 23m 45s                               │
│ Local: 10:30 AM PST | Market: 1:30 PM EST          │
└─────────────────────────────────────────────────────┘
```

### Component Structure

**File:** `components/MarketStatusBanner.tsx`

```tsx
interface MarketStatus {
  isOpen: boolean;
  opensIn?: number; // seconds
  closesIn?: number; // seconds
  nextOpen?: string; // ISO timestamp
  nextClose?: string; // ISO timestamp
}

export function MarketStatusBanner() {
  const [status, setStatus] = useState<MarketStatus | null>(null);
  const [countdown, setCountdown] = useState<string>('');
  
  // Status colors
  const getStatusColor = () => {
    if (status?.isOpen) return 'green';
    if (status?.opensIn && status.opensIn < 3600) return 'orange'; // < 1 hour
    return 'red';
  };
  
  const getStatusText = () => {
    if (status?.isOpen) return 'MARKET OPEN';
    if (status?.opensIn && status.opensIn < 3600) return 'MARKET OPENING SOON';
    return 'MARKET CLOSED';
  };
  
  return (
    <div className={`market-status-banner ${getStatusColor()}`}>
      <div className="status-indicator">
        {getStatusColor() === 'green' && '🟢'}
        {getStatusColor() === 'orange' && '🟠'}
        {getStatusColor() === 'red' && '🔴'}
        <span className="status-text">{getStatusText()}</span>
      </div>
      
      <div className="countdown">
        {status?.isOpen ? (
          <span>Closes in: {countdown}</span>
        ) : (
          <span>Opens in: {countdown}</span>
        )}
      </div>
      
      <div className="time-zones">
        <span>Local: {formatLocalTime()}</span>
        <span className="separator">|</span>
        <span>Market: {formatMarketTime()}</span>
      </div>
    </div>
  );
}
```

### Backend API

**Endpoint:** `GET /market/status`

```json
{
  "isOpen": false,
  "opensIn": 8130,
  "closesIn": null,
  "nextOpen": "2025-11-04T14:30:00Z",
  "nextClose": "2025-11-04T21:00:00Z",
  "currentTime": "2025-11-04T12:15:30Z",
  "marketTime": "2025-11-04T08:15:30-04:00",
  "timezone": "America/New_York"
}
```

---

## 3. Options Trading Controls

### UI Design - Settings Panel

```
┌─────────────────────────────────────────────────────┐
│ ⚙️ Trading Settings                                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 📊 Stock Trading                                    │
│   ✅ Enabled                                        │
│   Max Positions: [20] ▼                            │
│   Risk Per Trade: [1.0]% ▼                         │
│                                                     │
│ 📈 Options Trading                                  │
│   ⚪ Disabled  🔘 Enabled                          │
│                                                     │
│   When enabled:                                     │
│   • Buys calls on BUY signals                      │
│   • Buys puts on SELL signals                      │
│   • 2% risk per options trade                      │
│   • 50% profit target / 50% stop loss              │
│                                                     │
│   Max Options Positions: [5] ▼                     │
│   Options Risk Per Trade: [2.0]% ▼                 │
│                                                     │
│ 🛡️ Risk Management                                 │
│   Circuit Breaker: [5.0]% daily loss ▼             │
│   Status: ✅ Active                                │
│                                                     │
│ [Save Changes]  [Reset to Defaults]                │
└─────────────────────────────────────────────────────┘
```

### Options Trading Behavior

#### When Enabled

**Stock Signal Generated:**
```
[10:15:00] 📈 BUY signal: AAPL @ $175.50
[10:15:01] ✅ Stock order: BUY 200 AAPL
[10:15:02] 📊 Checking options opportunity...
[10:15:03] ✅ Options order: BUY 2 AAPL calls
```

**Options Position Display:**
```
┌─────────────────────────────────────────────────────┐
│ 📊 Options Positions (2/5)                          │
├─────────────────────────────────────────────────────┤
│ AAPL250117C00175000                                 │
│ 2 contracts @ $8.50 → $12.40 (+45.9%)              │
│ Expires: Jan 17, 2025 (35 days)                    │
│ Target: $12.75 | Stop: $4.25                       │
│ [Close Position]                                    │
├─────────────────────────────────────────────────────┤
│ NVDA250117C00485000                                 │
│ 1 contract @ $18.20 → $22.80 (+25.3%)              │
│ Expires: Jan 17, 2025 (35 days)                    │
│ Target: $27.30 | Stop: $9.10                       │
│ [Close Position]                                    │
└─────────────────────────────────────────────────────┘
```

#### When Disabled

**Stock Signal Generated:**
```
[10:15:00] 📈 BUY signal: AAPL @ $175.50
[10:15:01] ✅ Stock order: BUY 200 AAPL
[10:15:02] ⚪ Options trading disabled, skipping options order
```

### Copilot Commands for Options

```
User: "Enable options trading"
Bot: ✅ Options trading enabled
     Max positions: 5
     Risk per trade: 2%
     The system will now trade options alongside stocks.

User: "Disable options trading"
Bot: ✅ Options trading disabled
     ⚠️ Note: Existing options positions will remain open.
     No new options trades will be placed.

User: "What are my options positions?"
Bot: 📊 You have 2 options positions:
     
     1. AAPL Jan 17 $175 Call (2 contracts)
        Entry: $8.50 | Current: $12.40 (+45.9%)
        Expires in 35 days
     
     2. NVDA Jan 17 $485 Call (1 contract)
        Entry: $18.20 | Current: $22.80 (+25.3%)
        Expires in 35 days
     
     Total options P/L: +$1,240 (+38.2%)

User: "Close all options positions"
Bot: ✅ Closing 2 options positions...
     ✅ Closed AAPL calls: +$780
     ✅ Closed NVDA calls: +$460
     Total realized: +$1,240
```

---

## 4. Frontend Controls Checklist

### Current Controls ✅

- [x] Enable/Disable Trading (toggle)
- [x] View Positions
- [x] View Orders
- [x] View Metrics
- [x] Manual Order Submission
- [x] Close Individual Position
- [x] Emergency Stop

### New Controls to Add ✅

#### Settings Panel
- [ ] Max Positions slider (1-50)
- [ ] Risk Per Trade slider (0.5%-5%)
- [ ] Circuit Breaker threshold (1%-10%)
- [ ] Options Trading toggle
- [ ] Max Options Positions (1-20)
- [ ] Options Risk Per Trade (0.5%-5%)

#### Watchlist Management
- [ ] View watchlist with stats
- [ ] Add symbol to watchlist
- [ ] Remove symbol from watchlist
- [ ] Reset to default watchlist

#### Market Status
- [ ] Market open/closed indicator
- [ ] Countdown timer
- [ ] Local time display
- [ ] Market time display

#### Options Display
- [ ] Options positions table
- [ ] Options P/L tracking
- [ ] Expiration warnings
- [ ] Close options position button

### Copilot Integration ✅

**All controls accessible via copilot:**

```
# Trading Controls
"Enable trading"
"Disable trading"
"Emergency stop"

# Watchlist
"/watchlist"
"/watchlist add COIN"
"/watchlist remove TSLA"
"/watchlist reset"

# Settings
"Set max positions to 15"
"Set risk per trade to 1.5%"
"Enable options trading"
"Disable options trading"
"Set circuit breaker to 3%"

# Positions
"Close AAPL position"
"Close all positions"
"Close all options positions"
"What are my positions?"
"What are my options positions?"

# Orders
"Buy 100 AAPL"
"Sell 50 NVDA"
"Cancel all orders"

# Status
"What's the market status?"
"When does the market open?"
"Show me my performance"
```

---

## Implementation Priority

### Phase 1: Market Status (High Priority)
1. Backend: `/market/status` endpoint
2. Frontend: `MarketStatusBanner` component
3. Real-time countdown updates
4. Time zone conversions

### Phase 2: Watchlist Commands (High Priority)
1. Backend: Watchlist management in `command_handler.py`
2. Copilot: Route `/watchlist` commands
3. Frontend: Watchlist display with stats
4. Persistence: Save to config/database

### Phase 3: Options Controls (Medium Priority)
1. Backend: Options toggle endpoint
2. Frontend: Settings panel with options section
3. Frontend: Options positions table
4. Copilot: Options management commands

### Phase 4: Enhanced Settings (Medium Priority)
1. Frontend: Settings panel component
2. Backend: Settings update endpoints
3. Validation and safety checks
4. Persist settings to database

---

## API Endpoints Summary

```
# Watchlist
GET    /watchlist
POST   /watchlist/add
POST   /watchlist/remove
POST   /watchlist/reset

# Market Status
GET    /market/status

# Settings
GET    /settings
POST   /settings/update
POST   /settings/reset

# Options
GET    /options/positions
POST   /options/enable
POST   /options/disable
POST   /options/close/{symbol}
POST   /options/close-all
```

---

## Success Metrics

- [ ] Users can manage watchlist without editing .env
- [ ] Market status visible at all times
- [ ] Options trading can be toggled on/off easily
- [ ] All settings accessible via UI and copilot
- [ ] Countdown timer accurate to the second
- [ ] Settings persist across sessions
- [ ] Options positions clearly displayed
- [ ] Risk controls easily adjustable

This spec provides a complete, user-friendly control system for the trading bot! 🚀
