# Implementation Plan

- [x] 1. Create RegimeManager core component
  - [x] 1.1 Implement MarketRegime enum with five regime classifications
    - Define EXTREME_FEAR, FEAR, NEUTRAL, GREED, EXTREME_GREED
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [x] 1.2 Implement regime classification logic
    - Create `_classify_regime()` method with boundary logic
    - Handle edge cases (exactly 20, 40, 60, 80)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [x] 1.3 Implement regime parameter lookup table
    - Define parameters for all five regimes
    - Include profit_target_r, partial_profit_1_r, partial_profit_2_r, trailing_stop_r, position_size_mult
    - _Requirements: 1.1-1.5, 2.1, 3.1-3.5, 4.2-4.4_
  
  - [x] 1.4 Implement Fear & Greed Index fetching with caching
    - Integrate with FearGreedScraper
    - Implement 1-hour TTL cache
    - Handle fetch failures gracefully
    - _Requirements: 8.1, 8.2, 10.5_
  
  - [x] 1.5 Implement parameter retrieval methods
    - `get_current_regime()` method
    - `get_params()` method with optional regime parameter
    - `get_current_index_value()` method
    - _Requirements: 8.4_

- [x] 2. Integrate RegimeManager with Strategy module
  - [x] 2.1 Modify Strategy to accept regime_params
    - Update signal generation to use regime-specific profit targets
    - Replace fixed 2R targets with dynamic regime-based targets
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [x] 2.2 Add regime logging to trade decisions
    - Log regime, confidence, and targets on every trade entry
    - _Requirements: 9.1, 9.2_

- [x] 3. Integrate RegimeManager with Position Sizer
  - [x] 3.1 Modify DynamicPositionSizer to accept regime_data
    - Apply position_size_mult for high-confidence trades in extreme regimes
    - Implement confidence threshold check (>70%)
    - Respect maximum portfolio limits (2.5% cap)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 10.1_
  
  - [x] 3.2 Add regime context to sizing reasoning
    - Include regime name in reasoning string
    - Log position size multiplier when applied
    - _Requirements: 9.1_
  
  - [x] 3.3 Implement VIX-based position size reduction
    - Reduce all positions by 25% when VIX > 30
    - _Requirements: 2.5_

- [x] 4. Integrate RegimeManager with Profit Taker
  - [x] 4.1 Modify ProfitTaker to accept regime_params
    - Use partial_profit_1_r and partial_profit_2_r from regime
    - Implement dynamic partial profit level calculation
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 4.2 Add regime logging to partial profit events
    - Log regime, R-multiple achieved, and remaining position size
    - _Requirements: 9.4_

- [x] 5. Integrate RegimeManager with Trailing Stop Manager
  - [x] 5.1 Modify TrailingStopManager to accept regime_params
    - Use trailing_stop_r from regime for distance calculation
    - Implement regime-aware stop distance formula
    - _Requirements: 4.2, 4.3, 4.4_
  
  - [x] 5.2 Implement trailing stop activation at 2R profit
    - Activate trailing stops when position reaches 2R in any regime
    - _Requirements: 4.1_
  
  - [x] 5.3 Add regime logging to trailing stop updates
    - Log regime and stop distance on every update
    - _Requirements: 9.1_

- [x] 6. Implement stop loss tightening logic
  - [x] 6.1 Add ATR-based stop loss calculation
    - Calculate initial stop based on recent volatility
    - _Requirements: 5.1_
  
  - [x] 6.2 Implement stop loss bounds validation
    - Cap maximum stop at 1% of entry price
    - Set minimum stop at 0.3% of entry price
    - _Requirements: 5.2, 5.3, 10.3_
  
  - [x] 6.3 Add VIX-based stop loss adjustment
    - Increase stop distance by 25% when VIX > 25
    - _Requirements: 5.4_
  
  - [x] 6.4 Implement stop loss hit tracking
    - Record loss amount and update risk metrics
    - _Requirements: 5.5_

- [x] 7. Implement low-confidence trade filtering
  - [x] 7.1 Add confidence threshold checks
    - Reject trades below 40% confidence
    - Require 2 confirming indicators for 40-50% confidence
    - _Requirements: 6.1, 6.2_
  
  - [x] 7.2 Implement rejected signal tracking
    - Store rejected signals for performance analysis
    - Calculate hypothetical outcomes for learning
    - _Requirements: 6.3, 6.5_
  
  - [x] 7.3 Add signal re-evaluation logic
    - Re-evaluate rejected signals when conditions improve
    - _Requirements: 6.4_

- [x] 8. Implement position scaling for winning trades
  - [x] 8.1 Add position scaling logic
    - Scale into positions at 1.5R profit for high-confidence trades in extreme regimes
    - Add 50% to position size
    - _Requirements: 7.1_
  
  - [x] 8.2 Implement breakeven stop management
    - Move stop to breakeven on original entry when adding
    - Move stop to breakeven on add when it reaches 1R profit
    - _Requirements: 7.2, 7.4_
  
  - [x] 8.3 Add position size validation for scaling
    - Ensure total position size doesn't exceed 2.5% of capital
    - _Requirements: 7.3_
  
  - [x] 8.4 Implement average entry price tracking
    - Track average entry price when scaling
    - Adjust profit targets accordingly
    - _Requirements: 7.5_

- [x] 9. Implement configuration persistence
  - [x] 9.1 Add regime parameter storage
    - Store calculated regime parameters in config system
    - _Requirements: 8.1_
  
  - [x] 9.2 Implement parameter loading on restart
    - Load most recent regime parameters on bot restart
    - _Requirements: 8.2_
  
  - [x] 9.3 Add regime change logging
    - Log old and new values with timestamp on regime changes
    - _Requirements: 8.3_
  
  - [x] 9.4 Create API endpoint for regime settings
    - Expose current regime settings via API
    - _Requirements: 8.4_
  
  - [x] 9.5 Implement regime isolation for existing positions
    - Apply new regime parameters only to new trades
    - Maintain original parameters for existing positions
    - _Requirements: 8.5_

- [x] 10. Implement comprehensive logging
  - [x] 10.1 Add trade entry logging
    - Log regime, confidence, position size, and all targets
    - _Requirements: 9.1_
  
  - [x] 10.2 Add profit target adjustment logging
    - Log reason, old values, and new values
    - _Requirements: 9.2_
  
  - [x] 10.3 Add trade rejection logging
    - Log signal details and rejection reason
    - _Requirements: 9.3_
  
  - [x] 10.4 Add partial profit logging
    - Log regime, R-multiple, and remaining position size
    - _Requirements: 9.4_
  
  - [x] 10.5 Add regime-specific performance metrics to daily reports
    - Include performance breakdown by regime
    - _Requirements: 9.5_

- [x] 11. Implement parameter validation
  - [x] 11.1 Add position size validation
    - Validate position size doesn't exceed 2.5% of capital
    - _Requirements: 10.1_
  
  - [x] 11.2 Add profit target validation
    - Validate targets are between 1.5R and 10R
    - _Requirements: 10.2_
  
  - [x] 11.3 Add stop loss validation
    - Validate stops are between 0.3% and 2% of entry price
    - _Requirements: 10.3_
  
  - [x] 11.4 Implement safe default fallback
    - Use safe default values when validation fails
    - Log errors with details
    - _Requirements: 10.4_
  
  - [x] 11.5 Add Fear & Greed Index freshness check
    - Verify index is less than 1 hour old before applying
    - _Requirements: 10.5_

- [x] 12. Write comprehensive unit tests
  - [x] 12.1 Test regime classification for all boundary values
    - Test values: 0, 20, 21, 40, 41, 60, 61, 80, 81, 100
    - Verify correct regime assignment
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [x] 12.2 Test parameter retrieval for each regime
    - Verify all required fields present
    - Verify correct values for each regime
    - _Requirements: 1.1-1.5, 3.1-3.5, 4.2-4.4_
  
  - [x] 12.3 Test cache TTL behavior
    - Verify cache prevents excessive API calls
    - Verify refresh after TTL expiration
    - _Requirements: 10.5_
  
  - [x] 12.4 Test error handling for fetch failures
    - Verify graceful degradation
    - Verify default to NEUTRAL on first failure
    - _Requirements: 10.4_
  
  - [x] 12.5 Test trailing stop adaptation
    - Verify correct distance calculation for each regime
    - Test with various price levels
    - _Requirements: 4.2, 4.3, 4.4_
  
  - [x] 12.6 Test profit taker adaptation
    - Verify partial profit levels match regime
    - Test trigger conditions
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 12.7 Test position sizing with regime multipliers
    - Verify 1.5x multiplier applied correctly
    - Verify confidence threshold enforcement
    - Verify maximum limits respected
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 13. Write property-based tests
  - [x] 13.1 Property test: Classification consistency
    - **Property 1: Regime Classification Consistency**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
  
  - [x] 13.2 Property test: Parameter completeness
    - **Property 2: Parameter Retrieval Completeness**
    - **Validates: Requirements 1.1-1.5, 3.1-3.5, 4.2-4.4**
  
  - [x] 13.3 Property test: Profit target ordering
    - **Property 3: Profit Target Adaptation**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
  
  - [x] 13.4 Property test: Position size bounds
    - **Property 4: Position Size Scaling**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
  
  - [x] 13.5 Property test: Trailing stop distance
    - **Property 6: Trailing Stop Distance Adaptation**
    - **Validates: Requirements 4.2, 4.3, 4.4**

- [x] 14. Integration testing and verification
  - [x] 14.1 Test full trade lifecycle in each regime
    - Entry, partial profits, trailing stops, exit
    - Verify correct parameters used throughout
    - _Requirements: All_
  
  - [x] 14.2 Test regime transition during open position
    - Verify existing position maintains original parameters
    - Verify new trades use new regime parameters
    - _Requirements: 8.5_
  
  - [x] 14.3 Verify logging completeness
    - Check all required log entries present
    - Verify log format and content
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [x] 14.4 Run integration test suite
    - Execute all integration tests
    - Verify all tests pass
    - _Requirements: All_

- [x] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
