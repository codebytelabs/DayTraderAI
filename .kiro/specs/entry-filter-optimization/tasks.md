# Implementation Plan

- [ ] 1. Create filter infrastructure and base classes
  - Create `backend/trading/entry_filters.py` with base FilterResult and FilterConfig classes
  - Create FilterStatistics class for tracking rejections and acceptances
  - Add filter configuration parameters to `backend/config.py`
  - _Requirements: 4.4, 6.1, 6.2, 6.3_

- [ ] 1.1 Write property test for filter statistics completeness
  - **Property 6: Statistics Tracking Completeness**
  - **Validates: Requirements 4.1, 4.3**

- [ ] 2. Implement ADX Trend Filter
  - Create ADXTrendFilter class with threshold checking logic
  - Integrate with existing ADX calculation in `data/features.py`
  - Implement regime-aware threshold adjustment using RegimeManager
  - Add bypass logic for confidence >90%
  - Add comprehensive logging for rejections and acceptances
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 5.3, 5.4, 7.2_

- [ ] 2.1 Write property test for ADX filter consistency
  - **Property 1: ADX Filter Consistency**
  - **Validates: Requirements 1.2, 5.3, 5.4**

- [ ] 2.2 Write property test for regime adjustment correctness
  - **Property 5: Regime Adjustment Correctness**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

- [ ] 3. Implement Time-of-Day Filter
  - Create TimeOfDayFilter class with time range checking
  - Implement timezone conversion (UTC → Eastern Time)
  - Add restricted hours checking (11am-2pm ET default)
  - Implement bypass logic for confidence >85%
  - Add comprehensive logging for rejections and bypasses
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 7.1_

- [ ] 3.1 Write property test for time filter consistency
  - **Property 2: Time Filter Consistency**
  - **Validates: Requirements 2.2, 7.1**

- [ ] 3.2 Write property test for time zone consistency
  - **Property 10: Time Zone Consistency**
  - **Validates: Requirements 2.1**

- [ ] 4. Implement Confidence Filter
  - Create ConfidenceFilter class with threshold checking
  - Implement confluence adjustment (3+ signals → 60% threshold)
  - Add signal counting logic to detect confluence
  - Add comprehensive logging for rejections and adjustments
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 7.3_

- [ ] 4.1 Write property test for confidence filter consistency
  - **Property 3: Confidence Filter Consistency**
  - **Validates: Requirements 3.2, 7.3**

- [ ] 4.2 Write property test for filter bypass monotonicity
  - **Property 4: Filter Bypass Monotonicity**
  - **Validates: Requirements 7.1, 7.2**

- [ ] 5. Integrate filters into strategy module
  - Modify `backend/trading/strategy.py` to call filter system
  - Add filter evaluation after signal generation, before position sizing
  - Implement filter evaluation order (time → ADX → confidence)
  - Add early exit on first rejection for performance
  - Ensure filter bypass logic is respected
  - _Requirements: 1.1, 2.1, 3.1, 7.4, 7.5_

- [ ] 5.1 Write property test for filter order independence
  - **Property 8: Filter Order Independence**
  - **Validates: Requirements 1.4, 2.5, 3.4**

- [ ] 5.2 Write property test for bypass logic safety
  - **Property 9: Bypass Logic Safety**
  - **Validates: Requirements 7.5**

- [ ] 6. Implement filter statistics and reporting
  - Add daily statistics tracking to FilterStatistics class
  - Implement daily report generation with rejection counts
  - Add filter value tracking for accepted trades
  - Create statistics reset at day boundary
  - Add statistics logging at end of trading day
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 6.1 Write unit tests for statistics tracking
  - Test rejection counting per filter
  - Test acceptance tracking with filter values
  - Test daily report generation format
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 7. Implement configuration management
  - Add filter configuration loading from config.py
  - Implement configuration validation with range checking
  - Add safe default values for missing parameters
  - Implement configuration reload on file change
  - Add configuration error logging
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 7.1 Write property test for configuration validation
  - **Property 7: Configuration Validation**
  - **Validates: Requirements 6.5**

- [ ] 7.2 Write unit tests for configuration management
  - Test loading valid configuration
  - Test handling invalid parameters
  - Test safe defaults when parameters missing
  - Test configuration reload mechanism
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 8. Add comprehensive error handling
  - Implement ADX calculation failure handling
  - Implement timezone conversion error handling
  - Implement confidence score unavailable handling
  - Implement regime manager unavailable handling
  - Add error rate tracking and alerting
  - _Requirements: 1.5, 3.5_

- [ ] 8.1 Write unit tests for error handling
  - Test ADX calculation failures
  - Test timezone conversion errors
  - Test missing confidence scores
  - Test regime manager failures
  - Verify fail-safe behavior (reject on error)
  - _Requirements: 1.5, 3.5_

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Deploy in shadow mode for monitoring
  - Add ENTRY_FILTERS_SHADOW_MODE config flag
  - Implement shadow mode logging (log but don't filter)
  - Deploy to production in shadow mode
  - Collect 2-3 days of statistics
  - Analyze filter impact on historical signals
  - _Requirements: All requirements (validation)_

- [ ] 11. Enable filters gradually in production
  - Enable time filter only, monitor for 2 days
  - Enable ADX filter, monitor for 2 days
  - Enable confidence filter, monitor for 2 days
  - Enable all regime adjustments
  - Enable all bypass logic
  - Monitor performance metrics and statistics
  - _Requirements: All requirements (deployment)_

- [ ] 12. Final validation and documentation
  - Verify all filters working correctly in production
  - Verify statistics tracking accurately
  - Verify configuration management working
  - Document filter performance and impact
  - Create operator guide for filter tuning
  - _Requirements: All requirements (completion)_
