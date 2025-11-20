# Implementation Plan

- [x] 1. Set up momentum detection infrastructure
  - Create directory structure for momentum module components
  - Define configuration models and data classes
  - Set up logging infrastructure for momentum events
  - _Requirements: 8.1, 8.2_

- [x] 1.1 Implement MomentumConfig dataclass
  - Create configuration model with all thresholds and parameters
  - Add validation for configuration values
  - Implement environment-specific config loading (dev, paper, production)
  - _Requirements: 6.5_

- [x] 1.2 Implement MomentumSignal and Position enhancement models
  - Create MomentumSignal dataclass with indicator values
  - Enhance Position model with momentum tracking fields
  - Add helper properties for risk calculations
  - _Requirements: 2.5, 8.2_

- [ ] 2. Implement ADX calculation module
  - Create ADXCalculator class with configurable period
  - Implement +DI and -DI calculations from OHLC data
  - Calculate DX and smooth to ADX using Wilder's smoothing
  - Add data fetching from Alpaca API with error handling
  - _Requirements: 1.1, 1.2, 5.3_

- [ ] 2.1 Add ADX threshold validation
  - Implement is_trending method with configurable threshold
  - Add validation for ADX values (0-100 range)
  - Include logging for ADX calculations
  - _Requirements: 1.5, 5.4_

- [ ] 2.2 Write unit tests for ADX calculator
  - Test ADX calculation accuracy with known data
  - Test threshold validation logic
  - Test error handling for invalid data
  - _Requirements: 1.2_

- [ ] 3. Implement volume analysis module
  - Create VolumeAnalyzer class with configurable lookback period
  - Fetch volume data from Alpaca API
  - Calculate rolling average volume
  - Compute current volume ratio
  - _Requirements: 1.1, 1.3, 5.3_

- [ ] 3.1 Add volume confirmation logic
  - Implement is_volume_confirming method
  - Add validation for volume ratio values
  - Include logging for volume analysis
  - _Requirements: 1.5, 5.4_

- [ ] 3.2 Write unit tests for volume analyzer
  - Test volume ratio calculations
  - Test confirmation threshold logic
  - Test handling of missing volume data
  - _Requirements: 1.3_


- [ ] 4. Implement trend strength calculation module
  - Create TrendStrengthCalculator class
  - Fetch price data and calculate EMAs (9, 21, 50 periods)
  - Implement price vs EMA comparison component (0.3 weight)
  - Calculate Rate of Change (ROC) component (0.3 weight)
  - Detect higher highs pattern component (0.2 weight)
  - Add optional RSI component (0.2 weight)
  - Combine components into composite score (0-1 range)
  - _Requirements: 1.1, 1.4, 5.3_

- [ ] 4.1 Add trend strength validation
  - Implement is_strong_trend method with configurable threshold
  - Add validation for trend strength score (0-1 range)
  - Include detailed logging for each component
  - _Requirements: 1.5, 5.4_

- [ ] 4.2 Write unit tests for trend strength calculator
  - Test each component calculation
  - Test composite score aggregation
  - Test threshold validation
  - _Requirements: 1.4_

- [ ] 5. Implement momentum signal validator
  - Create MomentumSignalValidator class
  - Initialize ADX, volume, and trend strength calculators
  - Implement validate_momentum method
  - Check position profit level (+0.75R threshold)
  - Calculate all three indicators
  - Validate data freshness (within 60 seconds)
  - Implement consensus logic (all indicators must pass)
  - Return MomentumSignal with decision and values
  - _Requirements: 1.1, 1.5, 5.1, 5.2, 5.3, 5.4_

- [ ] 5.1 Add data validation and error handling
  - Implement _is_data_fresh method
  - Implement _validate_indicator_values method
  - Add comprehensive error logging
  - Handle missing or stale data gracefully
  - _Requirements: 5.3, 5.4, 5.5_

- [ ] 5.2 Write integration tests for signal validator
  - Test consensus logic with various indicator combinations
  - Test data freshness validation
  - Test error handling for invalid data
  - Test signal generation with real market data
  - _Requirements: 5.1, 5.2, 5.5_

- [ ] 6. Implement ATR calculator for trailing stops
  - Create ATRCalculator class with configurable period
  - Fetch OHLC data from Alpaca API
  - Calculate True Range for each period
  - Smooth to Average True Range
  - Add validation and error handling
  - _Requirements: 4.3, 7.1_


- [ ] 7. Implement bracket adjustment engine
  - Create BracketAdjustmentEngine class
  - Initialize with Alpaca client and config
  - Implement adjust_brackets method
  - Calculate extended target (+3R from entry)
  - Calculate progressive stop (breakeven + 0.5R)
  - Implement ATR-based trailing stop distance calculation
  - Add configuration for fixed vs ATR-based trailing
  - _Requirements: 2.1, 2.2, 4.1, 4.2_

- [ ] 7.1 Implement Alpaca API bracket update logic
  - Cancel existing stop and target orders
  - Submit new stop order at calculated level
  - Submit new target order at calculated level
  - Update position with new order IDs
  - Implement exponential backoff retry logic (max 3 attempts)
  - Handle AlpacaAPIError exceptions
  - _Requirements: 2.3, 2.4, 7.2, 7.3_

- [ ] 7.2 Add bracket adjustment logging
  - Log bracket adjustment decisions with before/after levels
  - Log all indicator values that triggered adjustment
  - Log API call success/failure
  - Track adjustment timestamps
  - _Requirements: 2.5, 8.2, 8.3_

- [ ] 7.3 Write unit tests for bracket engine
  - Test target and stop calculations
  - Test ATR-based trailing distance
  - Mock Alpaca API calls
  - Test retry logic and error handling
  - _Requirements: 2.1, 2.2, 7.3_

- [ ] 8. Integrate momentum system with position manager
  - Create EnhancedPositionManager class
  - Initialize momentum validator and bracket engine
  - Add feature flag check (config.momentum.enabled)
  - Implement monitor_position method
  - Check for momentum adjustment at +0.75R
  - Validate momentum signal
  - Adjust brackets if signal is positive
  - Mark position as brackets_adjusted
  - _Requirements: 2.1, 2.2, 6.5_

- [ ] 8.1 Maintain existing partial profit logic
  - Execute 50% partial profit at +1R (always, regardless of momentum)
  - Ensure partial profit happens before momentum evaluation
  - Mark position as partial_taken
  - Log partial profit execution
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 8.2 Implement trailing stop activation logic
  - Activate trailing stop at +3R for extended targets
  - Activate trailing stop at +2R for standard targets
  - Use ATR-based distance if configured
  - Submit trailing stop orders to Alpaca
  - Handle submission failures with retry
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_


- [ ] 8.3 Add graceful degradation for momentum failures
  - Wrap momentum logic in try-except block
  - Log errors and disable momentum for session on failure
  - Continue with standard bracket management
  - Ensure partial profits and trailing stops still work
  - _Requirements: 7.1, 7.3, 7.4, 7.5_

- [ ] 8.4 Write integration tests for position manager
  - Test momentum evaluation at +0.75R
  - Test partial profit execution at +1R
  - Test trailing stop activation
  - Test graceful degradation on errors
  - Test feature flag enable/disable
  - _Requirements: 3.1, 4.1, 6.5_

- [ ] 9. Implement backtesting framework
  - Create MomentumBacktester class
  - Load historical trade data from bot's trade history
  - Implement _simulate_fixed_brackets method (baseline)
  - Implement _simulate_momentum_brackets method (enhanced)
  - Calculate performance metrics for both strategies
  - Compare results side-by-side
  - _Requirements: 6.1, 6.2_

- [ ] 9.1 Implement BacktestResults dataclass
  - Track trade counts (total, extended)
  - Calculate win rates (baseline vs enhanced)
  - Calculate profit factors (baseline vs enhanced)
  - Calculate average R-multiples (baseline vs enhanced)
  - Track max drawdowns (baseline vs enhanced)
  - Calculate extension rate and extended trade metrics
  - _Requirements: 6.2, 6.3_

- [ ] 9.2 Implement validation logic
  - Create validate method in BacktestResults
  - Check minimum 100 trades requirement
  - Validate extension rate in 20-40% range
  - Verify enhanced metrics >= baseline metrics
  - Check drawdown increase is acceptable (<20%)
  - Generate validation report with pass/fail
  - _Requirements: 6.4, 6.5_

- [ ] 9.3 Write tests for backtesting framework
  - Test simulation accuracy with known trades
  - Test metric calculations
  - Test validation logic
  - _Requirements: 6.1, 6.2_

- [ ] 10. Implement logging and monitoring infrastructure
  - Create momentum-specific logger
  - Implement _log_momentum_evaluation method
  - Implement _log_bracket_adjustment method
  - Add structured logging with all indicator values
  - Include timestamps and position details
  - _Requirements: 8.1, 8.2, 8.3_


- [ ] 10.1 Implement daily metrics tracking
  - Create DailyMomentumMetrics dataclass
  - Track positions evaluated and signals detected
  - Track brackets adjusted and failures
  - Calculate extension rate and API success rate
  - Track extended trade performance
  - Calculate average indicator values on extension
  - _Requirements: 8.3, 8.4_

- [ ] 10.2 Enhance daily report with momentum section
  - Add momentum system status to daily report
  - Include signal statistics (evaluated, detected, adjusted)
  - Show extension rate and API success rate
  - Display extended trade performance metrics
  - Show average indicator values
  - Format report section clearly
  - _Requirements: 8.4_

- [ ] 10.3 Write tests for logging and metrics
  - Test log message formatting
  - Test metrics calculation
  - Test daily report generation
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 11. Create configuration management system
  - Create config/momentum_config.yaml file
  - Define default conservative configuration
  - Define aggressive configuration (post-validation)
  - Add environment-specific configs (dev, paper, production)
  - Implement config loading and validation
  - Add config override capability
  - _Requirements: 6.5_

- [ ] 11.1 Add configuration validation
  - Validate threshold ranges (ADX 20-35, volume 1.2-2.0, trend 0.6-0.8)
  - Validate R-multiple targets (2.5-4.0)
  - Validate ATR multipliers (1.5-2.5)
  - Log configuration on startup
  - _Requirements: 6.5_

- [ ] 12. Build test module CLI interface
  - Create standalone test script (test_momentum.py)
  - Add command-line arguments for config file
  - Add option to specify date range for backtest
  - Add option to output results to file
  - Display validation results clearly
  - Show comparison charts (baseline vs enhanced)
  - _Requirements: 6.1, 6.4_

- [ ] 12.1 Run initial backtest validation
  - Load last 100+ trades from bot history
  - Run backtest with default conservative config
  - Analyze results and document findings
  - Tune thresholds if needed
  - Validate extension rate is 20-40%
  - Verify performance improvements
  - _Requirements: 6.2, 6.3, 6.4_


- [ ] 13. Prepare for paper trading deployment
  - Update main bot configuration to include momentum config
  - Set momentum.enabled = True for paper trading environment
  - Add feature flag checks in position monitoring
  - Deploy to paper trading environment
  - Verify all components are working
  - _Requirements: 6.5_

- [ ] 13.1 Monitor paper trading performance
  - Run paper trading for minimum 2 weeks
  - Track at least 20 trades with momentum evaluation
  - Monitor extension rate daily
  - Track API success rate (target >95%)
  - Compare performance against baseline
  - Document any issues or anomalies
  - _Requirements: 7.5_

- [ ] 13.2 Create monitoring dashboard
  - Build simple dashboard for momentum metrics
  - Display real-time extension rate
  - Show indicator values for current positions
  - Track API call statistics
  - Alert on anomalies
  - _Requirements: 8.3, 8.4_

- [ ] 14. Prepare for live deployment
  - Review paper trading results and validate success criteria
  - Update production configuration with validated thresholds
  - Create deployment checklist
  - Plan gradual rollout (25% → 50% → 100%)
  - Set up monitoring alerts
  - Document rollback procedure
  - _Requirements: 6.5_

- [ ] 14.1 Implement gradual rollout mechanism
  - Add rollout_percentage config parameter
  - Randomly select positions for momentum system (based on percentage)
  - Track performance separately for momentum vs standard
  - Allow dynamic adjustment of rollout percentage
  - _Requirements: 6.5_

- [ ] 14.2 Create rollback procedure documentation
  - Document how to disable feature flag
  - Document how to verify system reverted to baseline
  - Create troubleshooting guide
  - Define criteria for rollback decision
  - _Requirements: 6.5_

- [ ] 15. Create comprehensive documentation
  - Write user guide for momentum system
  - Document configuration options and their effects
  - Create troubleshooting guide
  - Document expected performance improvements
  - Add examples of momentum signals
  - _Requirements: 8.5_

- [ ] 15.1 Create developer documentation
  - Document architecture and component interactions
  - Add code comments and docstrings
  - Create API reference for momentum classes
  - Document testing procedures
  - _Requirements: 8.5_
