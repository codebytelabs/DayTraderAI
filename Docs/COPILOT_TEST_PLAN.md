# Copilot Test Plan

## Issues Fixed

### 1. ✅ Markdown Rendering
**Problem:** Some responses were plain text instead of markdown
**Fix:** Updated main.py to format section titles with `**bold**` markdown
**Test:** All responses should now render with proper markdown formatting

### 2. ✅ Irrelevant Responses for "Opportunities"
**Problem:** "Show me trading opportunities" returned account summary instead of trade ideas
**Fix:** 
- Updated action_classifier.py to recognize "opportunities", "ideas", "signals" as advise keywords
- Added phrases like "trading opportunities", "trade ideas", "show me opportunities"
- Updated system prompt to specifically handle opportunity queries with entry points, SL, TP, R/R

**Test:** "Show me trading opportunities" should now return specific trade ideas

### 3. ✅ Command System Integration
**Problem:** Commands weren't being detected properly
**Fix:** 
- Integrated CommandHandler into query router
- Added command detection in query_router.py
- Created CommandPalette UI component

**Test:** Type `/` or `#` in chat to see command palette

## Test Scenarios

### Scenario 1: Market Summary
**Query:** "Give me a comprehensive market summary"
**Expected:** 
- Markdown formatted response
- Market overview section
- Portfolio impact section
- Key insights

**Test Command:**
```
Give me a comprehensive market summary including major indices, sector performance, VIX, key movers, and how this affects my portfolio
```

### Scenario 2: Portfolio Analysis
**Query:** "Complete portfolio analysis"
**Expected:**
- Markdown formatted response
- Current positions with P/L
- Sector exposure
- Risk metrics
- Performance vs benchmarks

**Test Command:**
```
Complete portfolio analysis: current positions, P/L, sector exposure, risk metrics, performance vs benchmarks
```

### Scenario 3: Trading Opportunities
**Query:** "Show me trading opportunities"
**Expected:**
- Markdown formatted response
- Specific symbols with entry points
- Stop loss and take profit levels
- Risk/reward ratios
- ML-validated signals

**Test Command:**
```
Show me trading opportunities: new position ideas, strong signals, ML-validated opportunities, risk/reward analysis
```

### Scenario 4: Action Recommendations
**Query:** "What should I do with my portfolio?"
**Expected:**
- Markdown formatted response
- Immediate actions (high priority)
- Growth opportunities (medium priority)
- Optimization suggestions (low priority)
- Specific commands to execute

**Test Command:**
```
What should I do with my portfolio right now? Immediate actions, profit-taking, loss-cutting, rebalancing, risk management
```

### Scenario 5: Slash Commands
**Query:** Type `/` in chat
**Expected:**
- Command palette opens
- Shows categorized commands
- Keyboard navigation works
- Selecting command fills input

**Test:**
1. Type `/` in chat input
2. See command palette
3. Use arrow keys to navigate
4. Press Enter to select
5. Command prompt fills input

### Scenario 6: Portfolio Actions
**Query:** Type `#` in chat
**Expected:**
- Command palette opens
- Shows all open positions
- Shows quick actions (close-all, cancel-all)
- Selecting action executes immediately

**Test:**
1. Type `#` in chat input
2. See portfolio actions
3. Type `#AAPL` to filter
4. See AAPL-specific actions
5. Select `#AAPL close` to close position

### Scenario 7: News Query
**Query:** "What happened yesterday?"
**Expected:**
- Markdown formatted response
- Market overview from Perplexity
- Portfolio performance
- Correlation analysis
- Key insights

**Test Command:**
```
what happened yesterday?
```

### Scenario 8: Risk Analysis
**Query:** "Analyze my portfolio risk"
**Expected:**
- Markdown formatted response
- Risk level assessment
- Risk factors identified
- Concentration analysis
- Recommendations

**Test Command:**
```
Comprehensive risk analysis: position sizing, sector concentration, correlation risk, drawdown analysis, recommendations
```

## Verification Checklist

### Markdown Rendering
- [ ] All section titles are bold (`**Title**`)
- [ ] Bullet points render correctly
- [ ] Code blocks render correctly
- [ ] Links are clickable
- [ ] Tables render properly

### Response Relevance
- [ ] Market summary includes market data
- [ ] Portfolio analysis includes positions
- [ ] Opportunities include specific trade ideas
- [ ] Recommendations are actionable
- [ ] Risk analysis includes risk metrics

### Command System
- [ ] `/` opens command palette
- [ ] `#` opens portfolio actions
- [ ] Arrow keys navigate commands
- [ ] Enter selects command
- [ ] Escape closes palette
- [ ] Commands execute correctly

### Response Quality
- [ ] Responses are concise
- [ ] Responses are actionable
- [ ] Responses include specific numbers
- [ ] Responses include recommendations
- [ ] Responses are portfolio-aware

## Expected Response Formats

### Market Summary Format
```markdown
**Market Overview**

• SPY: $XXX.XX (+X.XX%)
• QQQ: $XXX.XX (+X.XX%)
• VIX: XX.XX (low/medium/high volatility)

**Your Portfolio Impact**

• Daily P/L: $XXX (+X.XX%)
• Correlation: Your portfolio moved X% vs market X%
• Beta: X.XX (captured XX% of market move)

**Key Insights**

• Insight 1
• Insight 2
• Insight 3
```

### Trading Opportunities Format
```markdown
**Trading Opportunities**

**High Confidence Setups:**

1. **SYMBOL**
   • Entry: $XXX.XX
   • Stop Loss: $XXX.XX (-X%)
   • Take Profit: $XXX.XX (+X%)
   • Risk/Reward: 1:X
   • Signal: [ML-validated signal description]
   • Confidence: XX%

2. **SYMBOL**
   ...
```

### Action Recommendations Format
```markdown
**Portfolio Action Plan**

**🎯 IMMEDIATE ACTIONS (High Priority):**

1. **ACTION**
   • Rationale: [reason]
   • Expected: [outcome]
   • Command: `#SYMBOL action`
   • Confidence: XX%

**📈 GROWTH OPPORTUNITIES (Medium Priority):**

1. **ACTION**
   ...

**🛡️ OPTIMIZATION (Low Priority):**

1. **ACTION**
   ...
```

## Testing Instructions

1. **Start the backend:**
   ```bash
   cd backend
   ./run.sh
   ```

2. **Start the frontend:**
   ```bash
   npm run dev
   ```

3. **Open the app:**
   - Navigate to http://localhost:5173
   - Open the Chat panel

4. **Run each test scenario:**
   - Copy the test command
   - Paste into chat
   - Verify the response matches expected format
   - Check markdown rendering
   - Verify response relevance

5. **Test command system:**
   - Type `/` and verify command palette
   - Type `#` and verify portfolio actions
   - Test keyboard navigation
   - Test command execution

6. **Document results:**
   - Note any issues
   - Screenshot responses
   - Record any errors

## Success Criteria

✅ All responses render with proper markdown
✅ All responses are relevant to the query
✅ Command palette works correctly
✅ Portfolio actions execute successfully
✅ No TypeScript errors
✅ No Python errors
✅ Response times < 5 seconds
✅ Confidence scores > 70%

## Known Limitations

1. **Market Data:** Requires market to be open for real-time data
2. **API Keys:** Requires OpenRouter and Perplexity API keys
3. **Positions:** Requires open positions for portfolio analysis
4. **Historical Data:** Limited to available Alpaca history

## Next Steps After Testing

1. Fix any identified issues
2. Optimize response times
3. Improve confidence scoring
4. Add more command presets
5. Enhance markdown formatting
6. Add response caching
7. Implement streaming responses
