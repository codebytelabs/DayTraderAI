# Design Document: Data-Driven Momentum Wave Rider

## Overview

This design replaces the slow AI-based opportunity discovery with a fast, data-driven momentum scanner. The system identifies stocks with active momentum (volume surges, breakouts, trend strength) and enters positions with confidence-based sizing to maximize profits while managing risk.

**Core Philosophy**: Professional momentum traders achieve 55-65% win rates with 2:1 risk-reward ratios. The key is not a high win rate, but favorable risk-reward combined with proper position sizing.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Momentum Wave Rider System                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Alpaca     │───▶│  Momentum    │───▶│  Confidence  │       │
│  │  Market Data │    │   Scanner    │    │   Scorer     │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Twelve     │───▶│   Volume     │───▶│  Position    │       │
│  │    Data      │    │   Filter     │    │   Sizer      │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                             │                   │                │
│                             ▼                   ▼                │
│                      ┌──────────────┐    ┌──────────────┐       │
│                      │   Entry      │───▶│   Exit       │       │
│                      │   Engine     │    │   Manager    │       │
│                      └──────────────┘    └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. MomentumScanner

**Purpose**: Replace AI discovery with fast, data-driven momentum detection.

```python
class MomentumScanner:
    """
    Data-driven momentum scanner using Alpaca and Twelve Data.
    Replaces slow AI-based discovery with real-time market data analysis.
    """
    
    async def scan_momentum_waves(self, max_symbols: int = 50) -> List[MomentumCandidate]:
        """
        Scan for active momentum waves in real-time.
        
        Returns:
            List of momentum candidates ranked by score
        """
        pass
    
    async def get_top_movers(self, direction: str, limit: int) -> List[Dict]:
        """
        Get top movers from Alpaca Market Data API.
        
        Args:
            direction: 'up' or 'down'
            limit: Maximum number of movers to return
        """
        pass
    
    def filter_by_volume_surge(self, candidates: List[Dict], min_ratio: float = 1.5) -> List[Dict]:
        """
        Filter candidates by volume surge (institutional interest).
        
        Args:
            candidates: List of stock candidates
            min_ratio: Minimum volume ratio (1.5 = 150% of average)
        """
        pass
```

### 2. MomentumScorer

**Purpose**: Score candidates based on momentum indicators AND upside potential.

```python
class MomentumScorer:
    """
    Momentum-focused scoring system.
    Rewards active momentum WITH room to run.
    """
    
    def calculate_score(self, features: Dict) -> MomentumScore:
        """
        Calculate momentum score (0-100) based on technical indicators.
        
        Components:
        - Volume Score (0-25): Volume surge relative to average
        - Momentum Score (0-20): ADX strength + RSI zone
        - Breakout Score (0-20): Price vs resistance + EMA crossover
        - Upside Potential (0-25): Distance to resistance + R/R ratio
        - Trend Score (0-10): Multi-timeframe alignment
        """
        pass
    
    def calculate_volume_score(self, volume_ratio: float) -> int:
        """
        Calculate volume score (0-25 points).
        
        - 200%+ volume: 25 points
        - 150-200%: 20 points
        - 100-150%: 10 points
        - <100%: 0 points
        """
        pass
    
    def calculate_momentum_score(self, adx: float, rsi: float) -> int:
        """
        Calculate momentum score (0-20 points).
        
        - ADX > 25: 12 points (strong trend)
        - RSI 40-70: 8 points (momentum zone)
        """
        pass
    
    def calculate_breakout_score(self, price: float, resistance: float, ema_diff: float) -> int:
        """
        Calculate breakout score (0-20 points).
        
        - Price above resistance: 12 points
        - Fresh EMA crossover (0.05-0.3%): 8 points
        """
        pass
    
    def calculate_upside_potential(self, price: float, resistance: float, support: float) -> int:
        """
        Calculate upside potential score (0-25 points).
        
        This is the KEY addition - measures room to run!
        
        - Distance to resistance > 5%: 25 points (excellent room)
        - Distance to resistance 3-5%: 20 points (good room)
        - Distance to resistance 2-3%: 15 points (some room)
        - Distance to resistance 1-2%: 10 points (limited room)
        - Distance to resistance < 1%: 0 points (no room)
        
        Also considers risk/reward:
        - R/R ratio > 3:1: +5 bonus points
        - R/R ratio > 2:1: +3 bonus points
        """
        pass
    
    def apply_penalties(self, score: int, rsi: float, ema_diff: float, upside_pct: float) -> int:
        """
        Apply penalties for overbought/oversold, extended moves, and no room.
        
        - RSI > 75 or < 25: -20 points
        - EMA diff > 1%: -15 points (extended move)
        - Upside < 1%: -15 points (no room to run)
        """
        pass
```

### 2.5 ResistanceAnalyzer

**Purpose**: Identify resistance levels and calculate upside potential.

```python
class ResistanceAnalyzer:
    """
    Analyzes price levels to find resistance and calculate room to run.
    This prevents chasing stocks at the top.
    """
    
    def find_resistance_level(self, bars: List[Dict], lookback: int = 20) -> float:
        """
        Find the next major resistance level using recent highs and pivot points.
        
        Methods:
        - Recent swing highs (local maxima)
        - Round number levels ($50, $100, etc.)
        - Previous day high
        - 52-week high proximity
        """
        pass
    
    def find_support_level(self, bars: List[Dict], lookback: int = 20) -> float:
        """
        Find recent support level using recent lows.
        
        Methods:
        - Recent swing lows (local minima)
        - VWAP level
        - Previous day low
        """
        pass
    
    def calculate_upside_percentage(self, price: float, resistance: float) -> float:
        """
        Calculate percentage distance from current price to resistance.
        
        Returns: (resistance - price) / price * 100
        """
        pass
    
    def calculate_risk_reward_ratio(self, price: float, resistance: float, support: float) -> float:
        """
        Calculate risk/reward ratio.
        
        Reward = resistance - price (potential upside)
        Risk = price - support (potential downside to stop)
        R/R = Reward / Risk
        """
        pass
    
    def classify_upside_quality(self, upside_pct: float) -> str:
        """
        Classify the upside quality.
        
        - >5%: 'excellent'
        - 3-5%: 'good'
        - 2-3%: 'some'
        - 1-2%: 'limited'
        - <1%: 'poor'
        """
        pass
```

### 3. ConfidenceBasedSizer

**Purpose**: Scale position sizes based on confidence level.

```python
class ConfidenceBasedSizer:
    """
    Dynamic position sizing based on confidence score.
    Higher confidence = larger position.
    """
    
    def calculate_position_size(
        self, 
        confidence: float, 
        equity: float, 
        volume_confirmed: bool
    ) -> PositionSize:
        """
        Calculate position size based on confidence.
        
        Confidence Tiers:
        - 90+: 15% max
        - 80-89: 12% max
        - 70-79: 10% max
        - 60-69: 8% max
        - <60: Skip trade
        
        Volume Bonus: +2% if volume confirmed (up to 15% max)
        """
        pass
    
    def should_skip_trade(self, confidence: float, adx: float) -> bool:
        """
        Determine if trade should be skipped.
        
        Skip if:
        - Confidence < 60
        - ADX < 20 (choppy market)
        """
        pass
```

### 4. WaveEntryEngine

**Purpose**: Optimize entry timing for wave-riding.

```python
class WaveEntryEngine:
    """
    Entry timing optimization for momentum waves.
    Catches waves early, avoids chasing extended moves.
    """
    
    def classify_crossover(self, ema_diff: float) -> CrossoverType:
        """
        Classify EMA crossover type.
        
        - 0.05-0.3%: FRESH (ideal entry)
        - 0.3-1.0%: DEVELOPING (acceptable)
        - >1.0%: EXTENDED (reduce confidence)
        """
        pass
    
    def calculate_entry_bonus(self, price: float, vwap: float) -> int:
        """
        Calculate entry point bonus.
        
        - Within 0.5% of VWAP: +5 points
        """
        pass
    
    def check_timeframe_alignment(self, features: Dict) -> bool:
        """
        Check if multiple timeframes show aligned momentum.
        
        Returns True if 5-min and 1-hour both show same direction.
        """
        pass
```

### 5. ProfitProtectionManager

**Purpose**: Lock in profits while letting winners run.

```python
class ProfitProtectionManager:
    """
    Profit protection with partial profit taking and trailing stops.
    """
    
    def check_profit_targets(self, position: Position, current_price: float) -> ProfitAction:
        """
        Check if profit targets are hit.
        
        Actions:
        - 2R: Take 50% profit, move stop to breakeven
        - 3R: Tighten trailing stop to 1R
        """
        pass
    
    def check_exit_signals(self, position: Position, features: Dict) -> bool:
        """
        Check for exit signals.
        
        Exit if:
        - RSI divergence (price up, RSI down)
        - ADX drops below 20 (momentum loss)
        """
        pass
    
    def calculate_trailing_stop(self, position: Position, r_multiple: float) -> float:
        """
        Calculate trailing stop based on R-multiple.
        
        - <2R: Initial stop (1.5% or 1.5-2 ATR)
        - 2R: Breakeven
        - 3R+: 1R trailing
        """
        pass
```

## Data Models

### MomentumCandidate

```python
@dataclass
class MomentumCandidate:
    symbol: str
    price: float
    volume_ratio: float  # Current volume / 20-period average
    momentum_score: int  # 0-100
    confidence: int  # 0-100 (score with bonuses/penalties)
    
    # Component scores
    volume_score: int  # 0-25
    momentum_score: int  # 0-20
    breakout_score: int  # 0-20
    upside_score: int  # 0-25 (NEW - room to run)
    trend_score: int  # 0-10
    
    # Technical indicators
    adx: float
    rsi: float
    ema_diff: float  # EMA9 - EMA21 as percentage
    vwap_distance: float  # Distance from VWAP as percentage
    
    # Resistance analysis (NEW - prevents chasing tops)
    resistance_level: float  # Next major resistance
    support_level: float  # Recent support
    distance_to_resistance: float  # Percentage to resistance
    risk_reward_ratio: float  # Potential reward / risk
    
    # Classification
    crossover_type: str  # 'fresh', 'developing', 'extended'
    entry_quality: str  # 'ideal', 'acceptable', 'poor'
    upside_quality: str  # 'excellent', 'good', 'some', 'limited', 'poor'
```

### PositionSize

```python
@dataclass
class PositionSize:
    shares: int
    dollar_amount: float
    percent_of_equity: float
    confidence_tier: str  # 'high', 'medium', 'low'
    volume_bonus_applied: bool
    skip_trade: bool
    skip_reason: Optional[str]
```

### ProfitAction

```python
@dataclass
class ProfitAction:
    action: str  # 'hold', 'partial_profit', 'tighten_stop', 'exit'
    r_multiple: float
    new_stop_price: Optional[float]
    shares_to_sell: Optional[int]
    reason: str
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Volume Filter Correctness
*For any* set of candidates returned by the scanner, all candidates should have volume_ratio >= 1.5 (150% of average)
**Validates: Requirements 1.3**

### Property 2: Score Range Invariant
*For any* valid input features, the calculated momentum score should be between 0 and 100 inclusive
**Validates: Requirements 2.1**

### Property 3: Volume Score Calculation
*For any* volume ratio, the volume score should be: 30 if ratio >= 2.0, 20 if ratio >= 1.5, 10 if ratio >= 1.0, 0 otherwise
**Validates: Requirements 2.2**

### Property 4: Momentum Score Calculation
*For any* ADX and RSI values, the momentum score should correctly award 15 points for ADX > 25 and 10 points for RSI in 40-70 range
**Validates: Requirements 2.3**

### Property 5: Overbought/Oversold Penalty
*For any* RSI > 75 or RSI < 25, the score should be reduced by exactly 20 points
**Validates: Requirements 2.7**

### Property 18: Upside Potential Scoring
*For any* distance to resistance, the upside score should be: 25 if >5%, 20 if 3-5%, 15 if 2-3%, 10 if 1-2%, 0 if <1%
**Validates: Requirements 2.5, 3.3, 3.4, 3.5, 3.6, 3.7**

### Property 19: Insufficient Room Penalty
*For any* upside potential <1% to resistance, the score should be reduced by 15 points
**Validates: Requirements 2.8, 3.7**

### Property 20: Risk/Reward Bonus
*For any* R/R ratio >3:1, the upside score should include +5 bonus; for R/R >2:1, +3 bonus
**Validates: Requirements 3.8, 3.9**

### Property 6: Position Size Tiers
*For any* confidence score, the position size percentage should match the tier: 90+ = 15%, 80-89 = 12%, 70-79 = 10%, 60-69 = 8%
**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 7: Low Confidence Skip
*For any* confidence score below 60, the system should skip the trade
**Validates: Requirements 3.5**

### Property 8: Volume Bonus Cap
*For any* position with volume bonus, the total position size should not exceed 15% of equity
**Validates: Requirements 3.6**

### Property 9: Fresh Crossover Classification
*For any* EMA difference between 0.05% and 0.3%, the crossover should be classified as "fresh"
**Validates: Requirements 4.1**

### Property 10: Extended Crossover Penalty
*For any* EMA difference > 1%, the confidence should be reduced by 15 points
**Validates: Requirements 4.2**

### Property 11: ADX Filter
*For any* ADX below 20, the trade should be skipped
**Validates: Requirements 4.4**

### Property 12: Partial Profit at 2R
*For any* position reaching 2R profit, the system should take 50% partial profit
**Validates: Requirements 5.1**

### Property 13: Stop to Breakeven After Partial
*For any* position after partial profit is taken, the stop loss should be at entry price (breakeven)
**Validates: Requirements 5.2**

### Property 14: Minimum Stop Distance
*For any* new position, the stop loss should be at least 1.5% from entry price
**Validates: Requirements 6.1**

### Property 15: Risk Per Trade Limit
*For any* trade, the risk (position size × stop distance) should not exceed 1% of equity
**Validates: Requirements 6.2**

### Property 16: Stop Loss Invariant
*For any* open position, there should always be an active stop loss order
**Validates: Requirements 6.5**

### Property 17: R-Multiple Logging
*For any* closed trade, the R-multiple achieved should be logged
**Validates: Requirements 8.4**

## Error Handling

### Scanner Errors
- If Alpaca API fails, fall back to cached data or static watchlist
- If Twelve Data fails, use Alpaca-only indicators
- Log all API errors with retry counts

### Scoring Errors
- If any indicator is missing, use default neutral value
- If calculation fails, return score of 0 (skip trade)
- Log all scoring errors for debugging

### Position Sizing Errors
- If equity calculation fails, use last known equity
- If confidence is invalid, skip trade
- Never exceed 15% position size regardless of errors

### Exit Errors
- If stop order fails, retry up to 3 times
- If partial profit fails, keep full position with original stop
- Log all exit errors and alert user

## Testing Strategy

### Unit Tests
- Test each scoring component independently
- Test position sizing tiers
- Test crossover classification
- Test profit target calculations

### Property-Based Tests
Using Hypothesis library for Python:

1. **Score Range Property**: Generate random features, verify score is 0-100
2. **Volume Filter Property**: Generate random candidates, verify all have volume >= 1.5
3. **Position Size Property**: Generate random confidence scores, verify correct tier
4. **Stop Distance Property**: Generate random entries, verify stop >= 1.5%
5. **Risk Limit Property**: Generate random positions, verify risk <= 1% equity

### Integration Tests
- Test full scan → score → size → entry flow
- Test profit protection with simulated price movements
- Test error handling with mocked API failures
