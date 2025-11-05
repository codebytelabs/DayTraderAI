# Copilot Intelligence Enhancement Specification

## Problem Statement

The current copilot implementation has **critical intelligence gaps**:

1. ❌ Gives generic market news without portfolio context
2. ❌ Dumps raw account stats without analysis
3. ❌ No actionable recommendations
4. ❌ No synthesis of market + portfolio
5. ❌ No insights or intelligence

**User Experience**: Feels like talking to a data API, not an intelligent assistant.

---

## Current vs Desired Behavior

### Example 1: "what happened yesterday? summarize"

**Current Response** ❌:
```
Market Intelligence
US equities closed mixed after a strong October, with the Nasdaq Composite 
nearing 24,000... [generic news continues]

Route: news → perplexity
```

**Desired Response** ✅:
```
Yesterday's Market & Your Portfolio Summary:

MARKET OVERVIEW:
• Nasdaq near 24k (+0.3%), mixed close after strong October
• Fed rate cut odds: 67% (down from 95%)
• Tech sector: Strong despite volatility

YOUR PORTFOLIO PERFORMANCE:
• Daily P/L: +$245 (+0.18%)
• 3 trades executed:
  - AAPL: Closed at $178.50, +$125 profit (+0.71%)
  - NVDA: Stopped out at $848, -$80 loss (-0.94%)
  - MSFT: Closed at $385, +$200 profit (+1.04%)

CORRELATION ANALYSIS:
✓ Your tech positions benefited from Nasdaq strength
✗ NVDA underperformed sector (stopped out despite rally)
✓ AAPL and MSFT aligned with momentum

NEW POSITIONS:
• Opened SPY at $484.20 (bullish index signal)
• Position size: 20 shares, $9,684 deployed

INSIGHTS:
• Your portfolio captured 60% of market upside
• Tech concentration (60%) paid off yesterday
• NVDA stop loss prevented larger loss

RECOMMENDATION:
Consider reviewing NVDA strategy - it's lagging sector performance.
```

---

### Example 2: "what happened to my portfolio then?"

**Current Response** ❌:
```
Account Summary:
Equity: $138,508.19
Cash: $79,249.27
Buying Power: $142,327.16
Daily P/L: +$0.00 (+0.00%)
Open Positions: 10/20
Win Rate: 0.0%
Profit Factor: 0.00
Circuit Breaker: Clear ✓
```

**Desired Response** ✅:
```
Your Portfolio Deep Dive:

CURRENT STATE:
• Total Equity: $138,508 (up $245 from yesterday)
• Deployed Capital: $59,259 (43% of equity)
• Cash Reserve: $79,249 (57% - conservative)
• Open Positions: 10/20 (room for 10 more)

TODAY'S ACTIVITY:
• Daily P/L: $0 (market closed, no trades today)
• Unrealized P/L: +$1,245 (+2.1% on open positions)

POSITION BREAKDOWN:

Top Performers:
1. AAPL: 50 shares @ $175.50, now $180.20
   • Unrealized: +$235 (+2.7%)
   • Status: Approaching resistance, consider profit-taking

2. MSFT: 25 shares @ $380, now $385.50
   • Unrealized: +$137 (+1.4%)
   • Status: Strong momentum, hold

3. SPY: 20 shares @ $484.20, now $485.80
   • Unrealized: +$32 (+0.3%)
   • Status: New position, trending up

Underperformers:
1. NVDA: 15 shares @ $850, now $840
   • Unrealized: -$150 (-1.2%)
   • Status: Lagging sector, watch closely

2. QQQ: 10 shares @ $382, now $380.50
   • Unrealized: -$15 (-0.4%)
   • Status: Consolidating, normal

RISK ANALYSIS:
• Win Rate: 0% (all positions still open - no closed trades yet)
• Average Position Size: $5,926 (4.3% of equity) ✓ Good
• Largest Position: AAPL at $9,010 (6.5% of equity) ✓ Within limits
• Sector Exposure:
  - Technology: 60% (high concentration ⚠️)
  - Index Funds: 30%
  - Other: 10%

HEALTH CHECK:
✓ Diversification: Good (10 positions)
✓ Cash Reserves: Healthy (57%)
⚠️ Tech Concentration: High (60% - consider diversifying)
✓ Position Sizing: Appropriate
✓ Risk Limits: All within bounds
✓ Circuit Breaker: Clear

NEXT STEPS:
See recommendations with: "what can be done to my portfolio?"
```

---

### Example 3: "what can be done to my portfolio?"

**Current Response** ❌:
```
[Same raw account stats repeated]
```

**Desired Response** ✅:
```
Portfolio Action Plan - Prioritized Recommendations:

🎯 IMMEDIATE ACTIONS (High Priority):

1. TAKE PROFITS - AAPL
   • Current: +$235 (+2.7%), near resistance at $180
   • Action: "close AAPL" to lock in gains
   • Rationale: Approaching technical resistance, good profit
   • Expected: Realize $235 profit, free up $9,010 capital

2. SET TRAILING STOPS
   • Positions: AAPL, MSFT, SPY (all profitable)
   • Action: "set trailing stops" to protect gains
   • Rationale: Lock in profits while allowing upside
   • Protection: Prevents giving back gains on reversal

3. REVIEW NVDA
   • Current: -$150 (-1.2%), lagging sector
   • Action: "close NVDA" or tighten stop loss
   • Rationale: Underperforming despite tech rally
   • Risk: Further underperformance likely

📈 GROWTH OPPORTUNITIES (Medium Priority):

4. DEPLOY MORE CAPITAL
   • Current: 57% cash ($79k idle)
   • Opportunity: Deploy $20-30k more
   • Action: "buy 50 SPY" or "buy 30 QQQ"
   • Rationale: SPY breaking resistance, QQQ at support
   • Maintains: 40-50% cash buffer (safe)

5. DIVERSIFY SECTORS
   • Current: 60% tech concentration
   • Opportunity: Add healthcare, finance, energy
   • Action: "add XLV" (healthcare) or "add XLF" (finance)
   • Rationale: Reduce concentration risk
   • Target: 40-50% tech, 50-60% diversified

🛡️ RISK MANAGEMENT (Ongoing):

6. REBALANCE PORTFOLIO
   • Current: Tech-heavy (60%)
   • Target: More balanced (40-50% tech)
   • Action: Trim tech winners, add other sectors
   • Benefit: Smoother returns, lower volatility

7. HEDGE POSITIONS
   • Current: No hedges, 100% long
   • Opportunity: Add protective puts if VIX rises
   • Action: Monitor VIX, consider hedges above 18
   • Protection: Downside protection in volatility

📊 SPECIFIC TRADE IDEAS:

Ready to Execute:
• "close AAPL" - Take $235 profit
• "set trailing stops" - Protect all gains
• "buy 50 SPY at market" - Add index exposure
• "buy 30 QQQ at 380" - Add at support level
• "close NVDA" - Cut underperformer

Research Needed:
• Healthcare ETF (XLV) - Sector diversification
• Finance ETF (XLF) - Sector diversification
• Energy stocks - Inflation hedge

💬 READY TO ACT?

Just tell me what you want to do:
• "close AAPL" - I'll execute immediately
• "set trailing stops" - I'll set them up
• "buy 50 SPY" - I'll place the order
• "show me XLV analysis" - I'll research it

Or ask:
• "why should I close AAPL?" - I'll explain
• "what's the risk of buying more?" - I'll analyze
• "show me sector breakdown" - I'll visualize it
```

---

## Implementation Plan

### Phase 1: Enhanced Context Builder (Day 1-2)

**File**: `backend/copilot/context_builder.py`

**Add to Context**:
```python
{
    # Existing context...
    
    # NEW: Recent Activity
    "recent_trades": [
        {
            "symbol": "AAPL",
            "action": "close",
            "side": "long",
            "qty": 50,
            "entry_price": 175.50,
            "exit_price": 178.50,
            "pnl": 125.00,
            "pnl_pct": 0.71,
            "timestamp": "2025-11-01T15:45:00Z",
            "reason": "take_profit"
        },
        # ... more trades
    ],
    
    # NEW: Position Details
    "position_details": [
        {
            "symbol": "AAPL",
            "qty": 50,
            "side": "long",
            "entry_price": 175.50,
            "current_price": 180.20,
            "unrealized_pl": 235.00,
            "unrealized_pl_pct": 2.7,
            "market_value": 9010.00,
            "pct_of_portfolio": 6.5,
            "days_held": 3,
            "stop_loss": 170.00,
            "take_profit": 185.00,
            "technical_status": "approaching_resistance",
            "recommendation": "consider_profit_taking"
        },
        # ... more positions
    ],
    
    # NEW: Sector Exposure
    "sector_exposure": {
        "technology": 0.60,
        "index_funds": 0.30,
        "other": 0.10
    },
    
    # NEW: Risk Metrics
    "risk_metrics": {
        "concentration_risk": "high",  # 60% in tech
        "largest_position_pct": 6.5,
        "avg_position_size": 5926,
        "correlation_risk": "medium",
        "cash_buffer_pct": 57
    },
    
    # NEW: Recent Signals
    "recent_signals": [
        {
            "symbol": "TSLA",
            "signal": "buy",
            "timestamp": "2025-11-02T10:15:00Z",
            "ml_confidence": 0.58,
            "action_taken": "rejected",
            "reason": "ml_confidence_below_threshold"
        },
        # ... more signals
    ]
}
```

### Phase 2: Portfolio Correlator (Day 2)

**New File**: `backend/copilot/portfolio_correlator.py`

```python
class PortfolioCorrelator:
    """Correlates market events with portfolio positions."""
    
    def correlate_news_to_portfolio(
        self,
        news: List[Dict],
        positions: List[Dict]
    ) -> Dict:
        """
        Maps news events to affected positions.
        
        Returns:
        {
            "affected_positions": [
                {
                    "symbol": "AAPL",
                    "news_item": "Apple announces new product",
                    "impact": "positive",
                    "confidence": 0.85
                }
            ],
            "sector_impact": {
                "technology": "positive",
                "finance": "neutral"
            },
            "portfolio_impact": "positive"  # overall
        }
        """
        pass
    
    def calculate_market_portfolio_correlation(
        self,
        market_moves: Dict,
        portfolio_performance: Dict
    ) -> Dict:
        """
        Calculates how portfolio performed vs market.
        
        Returns:
        {
            "market_return": 0.5,  # SPY +0.5%
            "portfolio_return": 0.3,  # Portfolio +0.3%
            "beta": 0.6,  # Portfolio captured 60% of market move
            "alpha": -0.2,  # Underperformed by 0.2%
            "explanation": "Portfolio captured 60% of market upside..."
        }
        """
        pass
```

### Phase 3: Recommendation Engine (Day 3)

**New File**: `backend/copilot/recommendation_engine.py`

```python
class RecommendationEngine:
    """Generates actionable portfolio recommendations."""
    
    def generate_recommendations(
        self,
        context: Dict
    ) -> List[Dict]:
        """
        Generates prioritized recommendations.
        
        Returns:
        [
            {
                "priority": "high",
                "category": "profit_taking",
                "action": "close AAPL",
                "rationale": "Near resistance, good profit",
                "expected_outcome": "Realize $235 profit",
                "risk": "low",
                "confidence": 0.85
            },
            # ... more recommendations
        ]
        """
        pass
    
    def identify_profit_opportunities(self, positions: List[Dict]) -> List[Dict]:
        """Find positions ready for profit-taking."""
        pass
    
    def identify_loss_cutting(self, positions: List[Dict]) -> List[Dict]:
        """Find positions that should be closed."""
        pass
    
    def identify_new_opportunities(self, context: Dict) -> List[Dict]:
        """Find new position opportunities."""
        pass
    
    def assess_portfolio_risk(self, context: Dict) -> Dict:
        """Assess overall portfolio risk."""
        pass
    
    def suggest_rebalancing(self, context: Dict) -> List[Dict]:
        """Suggest portfolio rebalancing actions."""
        pass
```

### Phase 4: Response Formatter Enhancement (Day 4)

**File**: `backend/copilot/response_formatter.py`

**Add Methods**:
```python
def format_portfolio_summary(
    self,
    context: Dict,
    market_news: str,
    correlations: Dict,
    recommendations: List[Dict]
) -> str:
    """
    Synthesizes market news + portfolio + recommendations.
    
    Returns formatted response with:
    - Market overview
    - Portfolio performance
    - Correlation analysis
    - Actionable recommendations
    """
    pass

def format_position_analysis(
    self,
    positions: List[Dict],
    risk_metrics: Dict,
    recommendations: List[Dict]
) -> str:
    """
    Formats detailed position analysis.
    
    Returns formatted response with:
    - Position breakdown
    - Risk analysis
    - Health check
    - Next steps
    """
    pass

def format_action_plan(
    self,
    recommendations: List[Dict],
    context: Dict
) -> str:
    """
    Formats actionable recommendations.
    
    Returns formatted response with:
    - Prioritized actions
    - Specific commands
    - Risk/reward analysis
    - Ready-to-execute trades
    """
    pass
```

---

## Testing Plan

### Test Cases

1. **Market Summary Query**
   - Input: "what happened yesterday?"
   - Expected: Market news + portfolio performance + correlation
   - Verify: Includes trades, P/L, insights

2. **Portfolio Status Query**
   - Input: "what happened to my portfolio?"
   - Expected: Detailed position analysis + risk assessment
   - Verify: Explains metrics, provides context

3. **Action Request Query**
   - Input: "what can be done?"
   - Expected: Prioritized recommendations + specific actions
   - Verify: Actionable, specific, with rationale

4. **Follow-up Query**
   - Input: "why should I close AAPL?"
   - Expected: Detailed reasoning for recommendation
   - Verify: Technical analysis, risk/reward

5. **Execution Query**
   - Input: "close AAPL"
   - Expected: Executes trade + confirms + explains outcome
   - Verify: Trade executed, P/L realized

---

## Success Criteria

- [ ] Responses include portfolio context (not just generic news)
- [ ] Actionable recommendations provided (specific commands)
- [ ] Market events correlated to portfolio (cause & effect)
- [ ] Conversational and insightful (not data dumps)
- [ ] User can act immediately (ready-to-execute commands)
- [ ] Recommendations are intelligent (based on analysis)
- [ ] Risk assessment included (pros/cons)
- [ ] All recommendations logged (audit trail)

---

## Priority: CRITICAL

This enhancement is **critical** because:

1. **User Experience**: Current copilot feels dumb, not intelligent
2. **Autonomy**: Can't be autonomous without intelligent recommendations
3. **Trust**: Users won't trust system without good reasoning
4. **Actionability**: Users need specific actions, not data dumps
5. **Differentiation**: This is what makes it an AI assistant, not just an API

**Estimated Time**: 3-4 days  
**Impact**: Transforms copilot from data API to intelligent assistant  
**Dependencies**: None (can start immediately)

---

## Implementation Order

1. **Day 1**: Enhanced context builder
2. **Day 2**: Portfolio correlator
3. **Day 3**: Recommendation engine
4. **Day 4**: Response formatter + testing

**Total**: 4 days to intelligent copilot ✅
