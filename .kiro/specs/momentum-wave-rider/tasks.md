# Implementation Plan

## Overview
This plan implements the Data-Driven Momentum Wave Rider strategy, replacing slow AI discovery with fast market data analysis.

---

- [x] 1. Create Momentum Scanner Core
  - [x] 1.1 Create `backend/scanner/momentum_scanner.py` with MomentumScanner class
    - Implement `scan_momentum_waves()` method to fetch top movers
    - Implement `get_top_movers()` using Alpaca Market Data API
    - Implement `filter_by_volume_surge()` with 150% threshold
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [x] 1.2 Write property test for volume filter
    - **Property 1: Volume Filter Correctness**
    - **Validates: Requirements 1.3**
  - [x] 1.3 Create `MomentumCandidate` dataclass in `backend/scanner/momentum_models.py`
    - Include all fields: symbol, price, volume_ratio, scores, indicators
    - _Requirements: 1.2_

- [x] 2. Implement Momentum Scorer with Upside Analysis
  - [x] 2.1 Create `backend/scanner/momentum_scorer.py` with MomentumScorer class
    - Implement `calculate_score()` returning 0-100
    - Implement `calculate_volume_score()` with tier logic (0-25 pts)
    - Implement `calculate_momentum_score()` for ADX/RSI (0-20 pts)
    - Implement `calculate_breakout_score()` for price/EMA (0-20 pts)
    - Implement `calculate_upside_potential()` for resistance analysis (0-25 pts)
    - Implement `apply_penalties()` for overbought/extended/insufficient room
    - _Requirements: 2.1-2.8, 3.1-3.9_
  - [x] 2.2 Create `backend/scanner/resistance_analyzer.py` with ResistanceAnalyzer class
    - Implement `find_resistance_level()` using recent highs and pivot points
    - Implement `find_support_level()` using recent lows
    - Implement `calculate_upside_percentage()` to resistance
    - Implement `calculate_risk_reward_ratio()` using stop and target
    - Implement `classify_upside_quality()` for room classification
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  - [x] 2.3 Write property test for score range
    - **Property 2: Score Range Invariant**
    - **Validates: Requirements 2.1**
  - [x] 2.4 Write property test for volume score calculation
    - **Property 3: Volume Score Calculation**
    - **Validates: Requirements 2.2**
  - [x] 2.5 Write property test for overbought penalty
    - **Property 5: Overbought/Oversold Penalty**
    - **Validates: Requirements 2.7**
  - [x] 2.6 Write property test for upside potential scoring
    - **Property 18: Upside Potential Scoring**
    - **Validates: Requirements 2.5, 3.3-3.7**
  - [x] 2.7 Write property test for insufficient room penalty
    - **Property 19: Insufficient Room Penalty**
    - **Validates: Requirements 2.8, 3.7**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Confidence-Based Position Sizer
  - [x] 4.1 Create `backend/utils/confidence_sizer.py` with ConfidenceBasedSizer class
    - Implement `calculate_position_size()` with tier logic
    - Implement `should_skip_trade()` for low confidence/ADX
    - Implement volume bonus logic (up to 15% max)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  - [x] 4.2 Write property test for position size tiers
    - **Property 6: Position Size Tiers**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
  - [x] 4.3 Write property test for low confidence skip
    - **Property 7: Low Confidence Skip**
    - **Validates: Requirements 3.5**
  - [x] 4.4 Write property test for volume bonus cap
    - **Property 8: Volume Bonus Cap**
    - **Validates: Requirements 3.6**

- [x] 5. Implement Wave Entry Engine
  - [x] 5.1 Create `backend/trading/wave_entry.py` with WaveEntryEngine class
    - Implement `classify_crossover()` for fresh/developing/extended
    - Implement `calculate_entry_bonus()` for VWAP proximity
    - Implement `check_timeframe_alignment()` for multi-TF confirmation
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [x] 5.2 Write property test for crossover classification
    - **Property 9: Fresh Crossover Classification**
    - **Validates: Requirements 4.1**
  - [x] 5.3 Write property test for extended crossover penalty
    - **Property 10: Extended Crossover Penalty**
    - **Validates: Requirements 4.2**
  - [x] 5.4 Write property test for ADX filter
    - **Property 11: ADX Filter**
    - **Validates: Requirements 4.4**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Profit Protection Enhancements
  - [x] 7.1 Update `backend/trading/profit_protection/profit_taking_engine.py`
    - Add 2R partial profit taking (50%)
    - Add stop-to-breakeven after partial
    - Add 3R trailing stop tightening
    - _Requirements: 5.1, 5.2, 5.3_
  - [x] 7.2 Write property test for partial profit at 2R
    - **Property 12: Partial Profit at 2R**
    - **Validates: Requirements 5.1**
  - [x] 7.3 Write property test for stop to breakeven
    - **Property 13: Stop to Breakeven After Partial**
    - **Validates: Requirements 5.2**
  - [x] 7.4 Add RSI divergence exit detection
    - Implement divergence detection (price up, RSI down)
    - Add ADX momentum loss detection
    - _Requirements: 5.4, 5.5_

- [x] 8. Implement Risk Management Enhancements
  - [x] 8.1 Update `backend/trading/risk_manager.py`
    - Enforce 1.5% minimum stop distance
    - Enforce 1% max risk per trade
    - Add daily loss circuit breaker (2%)
    - Add consecutive loss size reduction
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - [x] 8.2 Write property test for minimum stop distance
    - **Property 14: Minimum Stop Distance**
    - **Validates: Requirements 6.1**
  - [x] 8.3 Write property test for risk per trade limit
    - **Property 15: Risk Per Trade Limit**
    - **Validates: Requirements 6.2**
  - [x] 8.4 Write property test for stop loss invariant
    - **Property 16: Stop Loss Invariant**
    - **Validates: Requirements 6.5**

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Integrate with Trading Engine
  - [x] 10.1 Update `backend/trading/trading_engine.py`
    - Add option to use momentum scanner instead of AI
    - Update scanner loop for 5-minute refresh (2-min in first hour)
    - Add high-confidence alert (score 85+)
    - _Requirements: 1.5, 7.1, 7.2, 7.3, 7.4_
  - [x] 10.2 Update `backend/scanner/opportunity_scanner.py`
    - Add `use_momentum_scanner` config option
    - Integrate MomentumScanner as alternative to AI finder
    - _Requirements: 1.5_
  - [x] 10.3 Update `backend/trading/strategy.py`
    - Integrate ConfidenceBasedSizer for position sizing
    - Integrate WaveEntryEngine for entry timing
    - _Requirements: 3.1-3.6, 4.1-4.5_

- [x] 11. Add Performance Tracking
  - [x] 11.1 Update trade logging to include R-multiple
    - Log R-multiple on trade close
    - Track win rate and average R/R
    - _Requirements: 8.4_
  - [x] 11.2 Write property test for R-multiple logging
    - **Property 17: R-Multiple Logging**
    - **Validates: Requirements 8.4**

- [x] 12. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Create Configuration and Documentation
  - [x] 13.1 Add momentum scanner config to `backend/config.py`
    - Add `USE_MOMENTUM_SCANNER` flag
    - Add `MOMENTUM_SCAN_INTERVAL` (5 min default)
    - Add `FIRST_HOUR_SCAN_INTERVAL` (2 min)
    - Add confidence tier thresholds
    - _Requirements: 7.1, 7.3_
  - [x] 13.2 Create `backend/MOMENTUM_WAVE_RIDER_GUIDE.md`
    - Document strategy overview
    - Document configuration options
    - Document expected performance metrics
    - _Requirements: 8.1, 8.2, 8.3_
