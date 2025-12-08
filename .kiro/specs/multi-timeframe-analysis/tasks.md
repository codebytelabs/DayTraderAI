# Implementation Plan

- [x] 1. Set up MTF data infrastructure
  - [x] 1.1 Create MTF data models and configuration
    - Create `backend/trading/mtf/models.py` with TimeframeFeatures, MTFFeatures, TrendBias, SRLevels, MTFSignalResult, MTFConfig dataclasses
    - Add MTF configuration settings to `backend/config.py` (ENABLE_MTF_ANALYSIS, MTF_WEIGHTS, MTF_MIN_CONFIDENCE, MTF_STRICT_MODE)
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 1.2 Write property test for MTF configuration
    - **Property 11: Configuration Override**
    - **Property 12: Custom Weight Application**
    - **Validates: Requirements 9.1, 9.2**

  - [x] 1.3 Create MTF Data Manager
    - Create `backend/trading/mtf/data_manager.py` with MTFDataManager class
    - Implement fetch_all_timeframes() to get 1-min, 5-min, 15-min, daily bars from Alpaca
    - Implement caching with appropriate refresh intervals (5-min every 5 min, 15-min every 15 min, daily once per day)
    - Implement fallback to cached data on fetch failures
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.4 Write property test for data caching
    - **Property: Data Cache Fallback**
    - Test that fetch failures result in cached data being used
    - **Validates: Requirements 1.3, 1.4**

- [x] 2. Implement MTF Feature Engine
  - [x] 2.1 Create MTF Feature Engine
    - Create `backend/trading/mtf/feature_engine.py` with MTFFeatureEngine class
    - Implement calculate_timeframe_features() to compute EMA(9/21/50/200), RSI, MACD, ADX, volume ratio for each timeframe
    - Implement calculate_mtf_features() to aggregate features across all timeframes
    - _Requirements: 1.5_

  - [x] 2.2 Write property test for feature calculation
    - **Property: Feature Calculation Completeness**
    - Test that all required indicators are computed for each timeframe
    - **Validates: Requirements 1.5**

- [x] 3. Implement Trend Analyzer
  - [x] 3.1 Create Trend Analyzer
    - Create `backend/trading/mtf/trend_analyzer.py` with TrendAnalyzer class
    - Implement get_trend_bias() using 15-min EMA(50) vs EMA(200) relationship
    - Classify as bullish (EMA50 > EMA200 by >0.1%), bearish (EMA50 < EMA200 by >0.1%), or neutral (within 0.1%)
    - Implement check_trend_alignment() to verify signal matches trend bias
    - Add daily trend alignment check for confidence bonus
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 3.2 Write property test for trend classification
    - **Property 1: Trend Classification Consistency**
    - **Validates: Requirements 2.2, 2.3, 2.4**

  - [x] 3.3 Write property test for signal-trend alignment
    - **Property 2: Signal-Trend Alignment Rejection**
    - **Validates: Requirements 2.5, 7.1**

- [x] 4. Checkpoint - Make sure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement Momentum Analyzer
  - [x] 5.1 Create Momentum Analyzer
    - Create `backend/trading/mtf/momentum_analyzer.py` with MomentumAnalyzer class
    - Implement check_rsi_alignment() requiring RSI > 50 on 2+ timeframes for buys, RSI < 50 for sells
    - Implement check_macd_alignment() requiring MACD histogram alignment on 5-min and 15-min
    - Implement get_momentum_score() to calculate alignment score with bonuses/penalties
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 5.2 Write property test for RSI confirmation
    - **Property 3: RSI Confirmation Rule**
    - **Validates: Requirements 3.1, 3.2**

  - [x] 5.3 Write property test for MACD confirmation
    - **Property 4: MACD Momentum Confirmation**
    - **Validates: Requirements 3.3, 3.4**

  - [x] 5.4 Write property test for momentum alignment confidence
    - **Property 5: Momentum Alignment Confidence Adjustment**
    - **Validates: Requirements 3.5, 3.6**

- [x] 6. Implement Support/Resistance Analyzer
  - [x] 6.1 Create S/R Analyzer
    - Create `backend/trading/mtf/sr_analyzer.py` with SupportResistanceAnalyzer class
    - Implement find_swing_points() to identify swing highs/lows from last 50 bars on 15-min
    - Implement get_nearest_levels() to find nearest S/R levels and daily high/low/close
    - Implement is_near_level() to check if price is within threshold of a level
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 6.2 Write property test for S/R position sizing
    - **Property 6: Support/Resistance Position Sizing**
    - **Validates: Requirements 4.3, 4.4**

- [x] 7. Checkpoint - Make sure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement MTF Confidence Calculator
  - [x] 8.1 Create MTF Confidence Calculator
    - Create `backend/trading/mtf/confidence_calculator.py` with MTFConfidenceCalculator class
    - Implement calculate_confidence() with default weights (15-min: 40%, 5-min: 35%, 1-min: 25%)
    - Implement dynamic weight adjustment when 15-min ADX > 25 (increase to 50%)
    - Implement apply_alignment_bonus() for full timeframe alignment (+20 points)
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 8.2 Write property test for timeframe weights
    - **Property 7: Timeframe Weight Calculation**
    - **Validates: Requirements 5.1, 5.2**

- [x] 9. Implement Volume Analyzer
  - [x] 9.1 Create Volume Analyzer
    - Create `backend/trading/mtf/volume_analyzer.py` with VolumeAnalyzer class
    - Implement check_volume_confirmation() for 5-min volume > 1.5x average
    - Implement get_volume_penalty() for 15-min volume < 0.7x average (-10 points)
    - Implement check_volume_price_alignment() for volume-price divergence detection
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 9.2 Write property test for volume confirmation
    - **Property 9: Volume Confirmation Logic**
    - **Validates: Requirements 6.2, 6.3**

- [x] 10. Implement MTF Signal Filter
  - [x] 10.1 Create MTF Signal Filter
    - Create `backend/trading/mtf/signal_filter.py` with MTFSignalFilter class
    - Implement evaluate_signal() to orchestrate all analyzers and calculate final MTF confidence
    - Implement should_reject() with confidence threshold (< 60 = reject)
    - Implement position sizing based on confidence (60-70: 0.7x, 70-80: 1.0x, >80: 1.5x)
    - Implement ADX-based sizing (>1 TF with ADX < 20: -40% size, all ADX > 25: full size)
    - _Requirements: 5.4, 5.5, 5.6, 7.2, 7.3, 7.4_

  - [x] 10.2 Write property test for confidence-based sizing
    - **Property 8: Confidence-Based Position Sizing**
    - **Validates: Requirements 5.4, 5.5, 5.6**

  - [x] 10.3 Write property test for ADX-based sizing
    - **Property 10: ADX-Based Position Sizing**
    - **Validates: Requirements 7.3, 7.4**

- [x] 11. Checkpoint - Make sure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Integrate with existing strategy
  - [x] 12.1 Create MTF integration module
    - Create `backend/trading/mtf/__init__.py` to export all MTF components
    - Create `backend/trading/mtf/integration.py` with MTFIntegration class that wraps all components
    - Implement get_mtf_signal_result() as single entry point for strategy integration
    - _Requirements: All_

  - [x] 12.2 Update EMAStrategy to use MTF analysis
    - Modify `backend/trading/strategy.py` to import and initialize MTFIntegration
    - Add MTF evaluation in evaluate() method before generating signals
    - Apply MTF position sizing multiplier in execute_signal()
    - Use S/R levels for stop and target placement
    - Add logging for MTF analysis results
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 12.3 Update Trading Engine for MTF data refresh
    - Modify `backend/trading/trading_engine.py` to initialize MTFDataManager
    - Add scheduled refresh loops for 5-min, 15-min, and daily data
    - Ensure MTF data is available before strategy evaluation
    - _Requirements: 1.2_

- [x] 13. Add configuration and logging
  - [x] 13.1 Add MTF configuration to settings
    - Update `backend/config.py` with all MTF settings
    - Add environment variable support for MTF configuration
    - Implement hot-reload capability for configuration changes
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 13.2 Add comprehensive MTF logging
    - Add logging for trend direction from each timeframe
    - Add logging for signal rejections with reasons
    - Add logging for MTF confidence breakdown
    - Add logging for S/R levels used
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 14. Final Checkpoint - Make sure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
