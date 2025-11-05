# Command System Specification - Slash Commands & Portfolio Actions

## Overview

A two-tier command system for intuitive copilot interaction:

1. **`/` Slash Commands** - Quick access to pre-configured prompts and features
2. **`#` Portfolio Actions** - Direct actions on positions, orders, and portfolio

---

## 1. Slash Commands (`/`) - Feature Discovery

### Purpose
- Discover all copilot capabilities
- Quick access to common queries
- Pre-configured prompts for best results
- Feature discoverability

### UI Behavior

**Trigger**: User types `/` in chat input

**Display**: Dropdown menu with categorized commands

```
┌─────────────────────────────────────────────────────┐
│ 📊 Market & Analysis                                │
├─────────────────────────────────────────────────────┤
│ /market-summary          Today's market overview    │
│ /market-sentiment        Current market sentiment   │
│ /sector-analysis         Sector performance         │
│ /news                    Latest market news         │
│ /economic-calendar       Upcoming events            │
├─────────────────────────────────────────────────────┤
│ 💼 Portfolio Analysis                               │
├─────────────────────────────────────────────────────┤
│ /portfolio-summary       Complete portfolio view    │
│ /performance             Performance metrics        │
│ /risk-analysis           Risk assessment            │
│ /positions               All open positions         │
│ /profit-loss             P/L breakdown              │
├─────────────────────────────────────────────────────┤
│ 🎯 Recommendations                                  │
├─────────────────────────────────────────────────────┤
│ /opportunities           Trading opportunities      │
│ /what-to-do              Actionable recommendations │
│ /take-profits            Profit-taking suggestions  │
│ /cut-losses              Loss-cutting suggestions   │
│ /rebalance               Portfolio rebalancing      │
├─────────────────────────────────────────────────────┤
│ 📈 Strategy & Signals                               │
├─────────────────────────────────────────────────────┤
│ /signals                 Recent trading signals     │
│ /strategy-performance    Strategy breakdown         │
│ /ml-status               ML model status            │
│ /watchlist               Current watchlist          │
│ /screener                Stock screener results     │
├─────────────────────────────────────────────────────┤
│ 🛡️ Risk Management                                  │
├─────────────────────────────────────────────────────┤
│ /exposure                Sector/position exposure   │
│ /risk-limits             Current risk limits        │
│ /circuit-breaker         Circuit breaker status     │
│ /correlation             Position correlations      │
│ /stress-test             Portfolio stress test      │
├─────────────────────────────────────────────────────┤
│ 📚 Help & Education                                 │
├─────────────────────────────────────────────────────┤
│ /help                    All available commands     │
│ /explain [symbol]        Explain a position         │
│ /why [action]            Explain a recommendation   │
│ /tutorial                Copilot tutorial           │
│ /examples                Example queries            │
└─────────────────────────────────────────────────────┘
```

### Command Definitions

#### Market & Analysis

**`/market-summary`**
```
Prompt: "Give me a comprehensive market summary including:
- Major indices (SPY, QQQ, DIA)
- Sector performance
- VIX and market sentiment
- Key market movers
- How this affects my portfolio"

Expected Response: Market overview + portfolio correlation
```

**`/market-sentiment`**
```
Prompt: "What's the current market sentiment? Include:
- Bull/bear indicators
- Fear & greed index
- Put/call ratio
- Analyst sentiment
- Should I be aggressive or defensive?"

Expected Response: Sentiment analysis + positioning advice
```

**`/sector-analysis`**
```
Prompt: "Analyze sector performance:
- Which sectors are leading/lagging?
- Sector rotation signals
- My sector exposure
- Rebalancing recommendations"

Expected Response: Sector breakdown + exposure analysis
```

**`/news`**
```
Prompt: "Latest market news affecting my portfolio:
- Breaking news
- Earnings announcements
- Economic data
- Fed statements
- Impact on my positions"

Expected Response: Relevant news + portfolio impact
```

**`/economic-calendar`**
```
Prompt: "Upcoming economic events:
- This week's calendar
- High-impact events
- Earnings dates for my positions
- Fed meetings
- How to prepare"

Expected Response: Calendar + preparation suggestions
```

#### Portfolio Analysis

**`/portfolio-summary`**
```
Prompt: "Complete portfolio analysis:
- Current positions and P/L
- Sector exposure
- Risk metrics
- Performance vs benchmarks
- Health check"

Expected Response: Comprehensive portfolio view
```

**`/performance`**
```
Prompt: "Portfolio performance analysis:
- Daily/weekly/monthly returns
- Win rate and profit factor
- Best/worst performers
- Comparison to SPY/QQQ
- Performance attribution"

Expected Response: Detailed performance metrics
```

**`/risk-analysis`**
```
Prompt: "Comprehensive risk analysis:
- Position sizing
- Sector concentration
- Correlation risk
- Drawdown analysis
- Risk-adjusted returns
- Recommendations"

Expected Response: Risk assessment + mitigation suggestions
```

**`/positions`**
```
Prompt: "Show all open positions with:
- Entry price and current price
- Unrealized P/L
- Days held
- Stop loss and take profit
- Technical status
- Recommendations for each"

Expected Response: Detailed position breakdown
```

**`/profit-loss`**
```
Prompt: "P/L breakdown:
- Today's P/L
- This week's P/L
- This month's P/L
- By position
- By strategy
- By sector"

Expected Response: Comprehensive P/L analysis
```

#### Recommendations

**`/opportunities`**
```
Prompt: "Show me trading opportunities:
- New position ideas
- Symbols showing strong signals
- ML-validated opportunities
- Risk/reward analysis
- Ready-to-execute trades"

Expected Response: Actionable trade ideas
```

**`/what-to-do`**
```
Prompt: "What should I do with my portfolio right now?
- Immediate actions
- Profit-taking opportunities
- Loss-cutting needs
- Rebalancing suggestions
- Risk management actions"

Expected Response: Prioritized action plan
```

**`/take-profits`**
```
Prompt: "Which positions should I take profits on?
- Positions near targets
- Positions at resistance
- Overextended positions
- Specific recommendations"

Expected Response: Profit-taking suggestions
```

**`/cut-losses`**
```
Prompt: "Which positions should I cut?
- Positions at stop loss
- Underperforming positions
- Positions with negative outlook
- Specific recommendations"

Expected Response: Loss-cutting suggestions
```

**`/rebalance`**
```
Prompt: "How should I rebalance my portfolio?
- Current allocation
- Target allocation
- Specific trades needed
- Expected impact"

Expected Response: Rebalancing plan
```

#### Strategy & Signals

**`/signals`**
```
Prompt: "Recent trading signals:
- Signals generated today
- Signals taken vs rejected
- ML confidence scores
- Why signals were rejected
- Upcoming signals"

Expected Response: Signal analysis
```

**`/strategy-performance`**
```
Prompt: "Strategy performance breakdown:
- EMA strategy performance
- Mean reversion performance
- Breakout strategy performance
- Which strategy is working best?
- Strategy recommendations"

Expected Response: Strategy comparison
```

**`/ml-status`**
```
Prompt: "ML model status:
- Model versions
- Training status
- Accuracy metrics
- Recent improvements
- Confidence levels"

Expected Response: ML system health
```

**`/watchlist`**
```
Prompt: "Current watchlist analysis:
- All watchlist symbols
- Technical status of each
- Signals and opportunities
- Recommendations to add/remove"

Expected Response: Watchlist breakdown
```

**`/screener`**
```
Prompt: "Stock screener results:
- Top candidates from screener
- Why they were selected
- Technical analysis
- Should I add to watchlist?"

Expected Response: Screener results + analysis
```

#### Risk Management

**`/exposure`**
```
Prompt: "Portfolio exposure analysis:
- Sector exposure breakdown
- Position size distribution
- Concentration risk
- Diversification score
- Recommendations"

Expected Response: Exposure analysis
```

**`/risk-limits`**
```
Prompt: "Current risk limits:
- Max positions (current/limit)
- Position size limits
- Sector limits
- Exposure limits
- Circuit breaker status"

Expected Response: Risk limits status
```

**`/circuit-breaker`**
```
Prompt: "Circuit breaker status:
- Current drawdown
- Trigger level
- Distance to trigger
- Recent triggers
- Risk assessment"

Expected Response: Circuit breaker analysis
```

**`/correlation`**
```
Prompt: "Position correlation analysis:
- Correlation matrix
- Highly correlated positions
- Diversification score
- Recommendations"

Expected Response: Correlation analysis
```

**`/stress-test`**
```
Prompt: "Portfolio stress test:
- What if market drops 5%?
- What if tech sector drops 10%?
- What if VIX spikes to 30?
- Expected portfolio impact
- Hedging recommendations"

Expected Response: Stress test results
```

#### Help & Education

**`/help`**
```
Prompt: "Show all available commands and features"

Expected Response: Complete command list
```

**`/explain [symbol]`**
```
Prompt: "Explain my [symbol] position:
- Why did I enter?
- Current status
- What should I do?
- Risk/reward"

Expected Response: Position explanation
```

**`/why [action]`**
```
Prompt: "Why are you recommending [action]?"

Expected Response: Detailed reasoning
```

**`/tutorial`**
```
Prompt: "Copilot tutorial:
- How to use slash commands
- How to use portfolio actions
- Example queries
- Best practices"

Expected Response: Interactive tutorial
```

**`/examples`**
```
Prompt: "Example queries I can ask"

Expected Response: List of example queries
```

---

## 2. Portfolio Actions (`#`) - Direct Commands

### Purpose
- Quick actions on specific positions
- Order management
- Portfolio operations
- Autocomplete with current portfolio data

### UI Behavior

**Trigger**: User types `#` in chat input

**Display**: Dropdown with portfolio-specific actions

```
┌─────────────────────────────────────────────────────┐
│ 📊 Your Positions (10)                              │
├─────────────────────────────────────────────────────┤
│ #AAPL                    50 shares, +$235 (+2.7%)   │
│ #MSFT                    25 shares, +$137 (+1.4%)   │
│ #NVDA                    15 shares, -$150 (-1.2%)   │
│ #SPY                     20 shares, +$32 (+0.3%)    │
│ #QQQ                     10 shares, -$15 (-0.4%)    │
│ ... (5 more)                                        │
├─────────────────────────────────────────────────────┤
│ 📝 Your Orders (3)                                  │
├─────────────────────────────────────────────────────┤
│ #order-abc123            BUY 50 TSLA @ $245         │
│ #order-def456            SELL 25 AAPL @ $180        │
│ #order-ghi789            BUY 30 QQQ @ $380          │
├─────────────────────────────────────────────────────┤
│ ⚡ Quick Actions                                     │
├─────────────────────────────────────────────────────┤
│ #close-all               Close all positions        │
│ #cancel-all              Cancel all orders          │
│ #set-stops               Set trailing stops         │
│ #take-profits            Take all profits           │
│ #emergency-stop          Emergency stop trading     │
└─────────────────────────────────────────────────────┘
```

### Action Definitions

#### Position Actions

**`#[SYMBOL]`** - Opens position menu
```
User types: #AAPL

Dropdown shows:
┌─────────────────────────────────────────────────────┐
│ AAPL - 50 shares @ $175.50 → $180.20 (+$235)       │
├─────────────────────────────────────────────────────┤
│ #AAPL close              Close entire position      │
│ #AAPL close 25           Close 25 shares            │
│ #AAPL stop 175           Set stop loss at $175      │
│ #AAPL target 185         Set take profit at $185    │
│ #AAPL trailing 2%        Set 2% trailing stop       │
│ #AAPL add 25             Add 25 more shares         │
│ #AAPL analyze            Detailed analysis          │
└─────────────────────────────────────────────────────┘
```

**Examples**:
- `#AAPL close` → Close entire AAPL position
- `#AAPL close 25` → Close 25 shares of AAPL
- `#NVDA stop 840` → Set stop loss at $840 for NVDA
- `#MSFT target 390` → Set take profit at $390 for MSFT
- `#SPY trailing 2%` → Set 2% trailing stop on SPY
- `#QQQ add 20` → Add 20 more shares of QQQ
- `#TSLA analyze` → Get detailed analysis of TSLA position

#### Order Actions

**`#order-[ID]`** - Opens order menu
```
User types: #order-abc123

Dropdown shows:
┌─────────────────────────────────────────────────────┐
│ Order abc123 - BUY 50 TSLA @ $245 (OPEN)           │
├─────────────────────────────────────────────────────┤
│ #order-abc123 cancel     Cancel this order          │
│ #order-abc123 modify     Modify order               │
│ #order-abc123 status     Check order status         │
└─────────────────────────────────────────────────────┘
```

**Examples**:
- `#order-abc123 cancel` → Cancel order abc123
- `#order-abc123 modify price 240` → Change order price to $240
- `#order-abc123 status` → Check order status

#### Quick Actions

**`#close-all`**
```
Action: Close all open positions
Confirmation: "Are you sure? This will close 10 positions."
Effect: Closes all positions at market price
```

**`#cancel-all`**
```
Action: Cancel all pending orders
Confirmation: "Are you sure? This will cancel 3 orders."
Effect: Cancels all open orders
```

**`#set-stops`**
```
Action: Set trailing stops on all positions
Prompt: "Set trailing stop percentage (default 2%):"
Effect: Sets trailing stops on all open positions
```

**`#take-profits`**
```
Action: Close all profitable positions
Confirmation: "This will close 6 profitable positions. Continue?"
Effect: Closes positions with positive P/L
```

**`#emergency-stop`**
```
Action: Emergency stop - close all & disable trading
Confirmation: "EMERGENCY STOP - Close all positions and halt trading?"
Effect: Closes everything, disables trading
```

#### New Position Actions

**`#buy [SYMBOL]`** - Opens buy menu
```
User types: #buy TSLA

Dropdown shows:
┌─────────────────────────────────────────────────────┐
│ Buy TSLA - Current price: $245.50                   │
├─────────────────────────────────────────────────────┤
│ #buy TSLA 50             Buy 50 shares at market    │
│ #buy TSLA 50 @ 240       Buy 50 shares at $240      │
│ #buy TSLA $5000          Buy $5000 worth             │
│ #buy TSLA analyze        Analyze before buying      │
└─────────────────────────────────────────────────────┘
```

**`#sell [SYMBOL]`** - Opens sell menu (for shorting)
```
User types: #sell TSLA

Dropdown shows:
┌─────────────────────────────────────────────────────┐
│ Sell TSLA - Current price: $245.50                  │
├─────────────────────────────────────────────────────┤
│ #sell TSLA 50            Sell short 50 shares       │
│ #sell TSLA 50 @ 250      Sell short at $250         │
│ #sell TSLA analyze       Analyze before shorting    │
└─────────────────────────────────────────────────────┘
```

---

## 3. Implementation Plan

### Phase 1: UI Components (Day 1)

**File**: `components/CommandPalette.tsx`

```typescript
interface Command {
  id: string;
  category: string;
  label: string;
  description: string;
  prompt: string;
  icon: string;
}

interface PortfolioAction {
  id: string;
  type: 'position' | 'order' | 'quick';
  symbol?: string;
  label: string;
  description: string;
  action: string;
  requiresConfirmation: boolean;
}

export const CommandPalette: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [filter, setFilter] = useState('');
  const [commands, setCommands] = useState<Command[]>([]);
  const [actions, setActions] = useState<PortfolioAction[]>([]);
  
  // Detect / or # trigger
  useEffect(() => {
    if (filter.startsWith('/')) {
      loadCommands();
    } else if (filter.startsWith('#')) {
      loadPortfolioActions();
    }
  }, [filter]);
  
  return (
    <div className="command-palette">
      {/* Dropdown with commands/actions */}
    </div>
  );
};
```

**File**: `components/ChatPanel.tsx` (enhance)

```typescript
// Add command palette integration
const [showCommandPalette, setShowCommandPalette] = useState(false);

const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  const value = e.target.value;
  setInput(value);
  
  // Show command palette on / or #
  if (value === '/' || value === '#') {
    setShowCommandPalette(true);
  } else if (!value.startsWith('/') && !value.startsWith('#')) {
    setShowCommandPalette(false);
  }
};
```

### Phase 2: Command Registry (Day 1)

**File**: `backend/copilot/command_registry.py`

```python
class CommandRegistry:
    """Registry of all slash commands."""
    
    COMMANDS = {
        # Market & Analysis
        "market-summary": {
            "category": "Market & Analysis",
            "description": "Today's market overview",
            "prompt": "Give me a comprehensive market summary...",
            "icon": "📊"
        },
        # ... all commands
    }
    
    def get_command(self, command_id: str) -> Dict:
        """Get command definition."""
        return self.COMMANDS.get(command_id)
    
    def get_all_commands(self) -> List[Dict]:
        """Get all commands grouped by category."""
        pass
    
    def search_commands(self, query: str) -> List[Dict]:
        """Search commands by keyword."""
        pass
```

### Phase 3: Action Handler (Day 2)

**File**: `backend/copilot/action_handler.py`

```python
class ActionHandler:
    """Handles portfolio actions (#commands)."""
    
    def parse_action(self, action_str: str) -> Dict:
        """
        Parse action string into structured command.
        
        Examples:
        - "#AAPL close" → {type: "close", symbol: "AAPL", qty: "all"}
        - "#AAPL close 25" → {type: "close", symbol: "AAPL", qty: 25}
        - "#AAPL stop 175" → {type: "set_stop", symbol: "AAPL", price: 175}
        """
        pass
    
    def execute_action(self, action: Dict) -> ExecutionResult:
        """Execute the parsed action."""
        pass
    
    def get_available_actions(self, context: Dict) -> List[Dict]:
        """Get available actions based on current portfolio."""
        pass
```

### Phase 4: API Endpoints (Day 2)

**File**: `backend/main.py`

```python
@app.get("/commands")
async def get_commands():
    """Get all available slash commands."""
    registry = CommandRegistry()
    return registry.get_all_commands()

@app.get("/actions")
async def get_portfolio_actions():
    """Get available portfolio actions based on current state."""
    handler = ActionHandler()
    context = build_context()
    return handler.get_available_actions(context)

@app.post("/execute-action")
async def execute_action(action: str):
    """Execute a portfolio action."""
    handler = ActionHandler()
    parsed = handler.parse_action(action)
    result = await handler.execute_action(parsed)
    return result
```

---

## 4. User Experience Flow

### Slash Command Flow

```
1. User types "/" in chat
2. Command palette opens with all commands
3. User types "/market" to filter
4. Shows: /market-summary, /market-sentiment
5. User clicks /market-summary
6. Input fills with pre-configured prompt
7. User hits enter
8. Copilot responds with comprehensive analysis
```

### Portfolio Action Flow

```
1. User types "#" in chat
2. Action palette opens with positions/orders
3. User types "#AAPL" to filter
4. Shows: #AAPL close, #AAPL stop, #AAPL target, etc.
5. User clicks "#AAPL close"
6. Confirmation dialog: "Close 50 shares of AAPL?"
7. User confirms
8. Action executed
9. Copilot responds: "Closed AAPL position. P/L: +$235"
```

---

## 5. Benefits

### For Users
- ✅ **Discoverability**: See all features at a glance
- ✅ **Speed**: Quick access to common actions
- ✅ **Accuracy**: Pre-configured prompts get best results
- ✅ **Learning**: Discover features through exploration
- ✅ **Efficiency**: Execute actions in 2-3 clicks

### For System
- ✅ **Consistency**: Standardized prompts
- ✅ **Analytics**: Track which features are used
- ✅ **Optimization**: Improve popular commands
- ✅ **Documentation**: Self-documenting interface

---

## 6. Success Criteria

- [ ] All slash commands implemented (30+ commands)
- [ ] All portfolio actions implemented (10+ actions)
- [ ] Command palette UI responsive and fast
- [ ] Autocomplete works correctly
- [ ] Confirmation dialogs for destructive actions
- [ ] Actions execute correctly
- [ ] Responses are intelligent and contextual
- [ ] User can discover all features through UI
- [ ] Analytics track command usage

---

## Priority: HIGH

**Estimated Time**: 2-3 days  
**Impact**: Dramatically improves UX and feature discoverability  
**Dependencies**: Copilot intelligence enhancement (Phase 1.0)

---

## Implementation Order

1. **Day 1 Morning**: UI components (CommandPalette, integration)
2. **Day 1 Afternoon**: Command registry (all 30+ commands)
3. **Day 2 Morning**: Action handler (portfolio actions)
4. **Day 2 Afternoon**: API endpoints + testing
5. **Day 3**: Polish, edge cases, analytics

**Total**: 2-3 days to complete command system ✅
