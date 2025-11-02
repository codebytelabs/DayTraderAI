# Implementation Plan

- [x] 1. Create ActionClassifier component

  - Implement intent classification logic (execute/advise/info)
  - Implement keyword-based pattern matching for action detection
  - Implement parameter extraction (symbols, prices, quantities)
  - Implement confidence scoring algorithm
  - Add ambiguity detection for unclear queries
  - _Requirements: 1.1, 5.1, 5.2, 6.1, 6.2_

- [x] 2. Create ActionExecutor component

  - Implement base ActionExecutor class with dependency injection
  - Implement check_market_status action using Alpaca clock API
  - Implement get_position_details action with market data enrichment
  - Implement get_account_summary action aggregating metrics
  - Implement close_position action with validation and execution
  - Implement close_all_positions action with iteration logic
  - Implement cancel_order action with order validation
  - Implement cancel_all_orders action
  - Implement modify_stop_loss action with level validation
  - Implement modify_take_profit action with level validation
  - Add risk validation checks before execution (circuit breaker, position limits)
  - Add before/after state capture for modifications
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 8.1, 8.2, 8.3, 8.4_

- [x] 3. Create ResponseFormatter component

  - Implement format_execution method for action results
  - Implement format_llm_response method for LLM outputs
  - Implement format_info_response method for data queries
  - Create response templates for each action type
  - Add markdown formatting for structured data
  - Add error message formatting with recovery suggestions
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 4. Integrate action layer into chat endpoint

  - Add ActionClassifier instantiation in main.py startup
  - Add ActionExecutor instantiation with required dependencies
  - Add ResponseFormatter instantiation
  - Modify /chat endpoint to call action classifier first
  - Implement execute intent routing to ActionExecutor
  - Implement info intent routing to data fetcher
  - Implement confirmation flow for high-value operations
  - Keep existing advise intent routing to LLM providers
  - Update response format to include structured details
  - _Requirements: 5.1, 5.2, 5.3, 2.3, 6.4_

- [x] 5. Add configuration and feature flags

  - Add action execution settings to CopilotConfig
  - Add confidence threshold configuration
  - Add confirmation value threshold configuration
  - Add bulk operation limits configuration
  - Add feature flag to enable/disable action execution
  - _Requirements: 2.3, 8.2, 8.3_

- [ ] 6. Implement error handling and validation

  - Add try-catch blocks for API failures in ActionExecutor
  - Add validation for symbol existence in watchlist
  - Add validation for stop-loss levels (below price for long, above for short)
  - Add validation for take-profit levels (above price for long, below for short)
  - Add validation for minimum stop distance based on ATR
  - Add circuit breaker check before trade execution
  - Add position limit check before modifications
  - Add equity utilization check before actions
  - Return structured error responses with specific constraint violations
  - _Requirements: 1.5, 2.5, 3.3, 3.4, 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 7. Add audit logging for actions

  - Log all action classifications with confidence scores
  - Log all execution attempts with parameters
  - Log execution results (success/failure)
  - Log risk validation outcomes
  - Store execution history in Supabase trades table
  - _Requirements: 5.5, 7.3_

- [ ] 8. Implement clarification flow for ambiguous queries

  - Detect when symbol cannot be determined from query
  - Detect when action type is unclear
  - Detect when multiple positions match partial symbol
  - Return clarification request with available options
  - Implement conversation context tracking for follow-ups
  - Add timeout for clarification requests (60 seconds)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 9. Create unit tests for ActionClassifier

  - Test execute intent classification with various command formats
  - Test advise intent classification with question formats
  - Test info intent classification with status queries
  - Test symbol extraction from queries
  - Test price extraction for stop-loss/take-profit modifications
  - Test quantity extraction for partial closes
  - Test confidence scoring accuracy
  - Test ambiguity detection
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1_

- [ ] 10. Create unit tests for ActionExecutor

  - Mock Alpaca client and test check_market_status
  - Mock trading state and test get_position_details
  - Mock trading engine and test close_position
  - Mock trading engine and test close_all_positions
  - Test cancel_order with mocked Alpaca client
  - Test modify_stop_loss with validation logic
  - Test modify_take_profit with validation logic
  - Test risk validation checks (circuit breaker, limits)
  - Test error handling for API failures
  - _Requirements: 1.1, 2.1, 2.2, 3.1, 3.2, 4.1, 8.1, 8.2, 8.3_

- [ ] 11. Create integration tests for end-to-end action flow

  - Test complete flow from query to execution for market status
  - Test complete flow for position query
  - Test complete flow for close position command
  - Test confirmation flow for high-value operations
  - Test fallback to LLM for ambiguous queries
  - Test error recovery paths
  - _Requirements: 1.1, 2.1, 2.3, 4.1, 5.2, 5.3, 6.1_

- [ ] 12. Create real API tests with paper trading

  - Test market status check with real Alpaca API
  - Test position queries with paper trading account
  - Test order cancellation with paper trading account
  - Test stop-loss modification with paper trading account
  - _Requirements: 1.1, 1.4, 2.4, 3.5, 4.1_

- [ ] 13. Update frontend to handle structured responses

  - Update ChatPanel to display execution confirmations
  - Add UI for confirmation dialogs (high-value operations)
  - Add structured data rendering for position details
  - Add status indicators for execution success/failure
  - Update response type handling for execute/info/advise
  - _Requirements: 7.1, 7.2, 7.4, 2.3_

- [ ] 14. Add performance monitoring and optimization
  - Add timing metrics for action classification
  - Add timing metrics for action execution
  - Add caching for market status (30 second TTL)
  - Implement parallel execution for bulk operations
  - Monitor and log latency for each action type
  - _Requirements: 1.4_
