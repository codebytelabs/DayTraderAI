# Implementation Plan - Intelligent Profit Protection System

## Overview

This implementation plan breaks down the Intelligent Profit Protection System into discrete, manageable coding tasks. Each task builds incrementally on previous work, ensuring the system can be tested and validated at each step.

---

## Phase 1: Core Infrastructure

- [x] 1. Set up project structure and core data models
  - Create `backend/trading/profit_protection/` directory structure
  - Define `PositionState` and `ProtectionState` dataclasses
  - Define `PartialProfit` and `ShareAllocation` dataclasses
  - Create database migration for `position_states` table
  - Create database migration for `partial_profits` table
  - Create database migration for `stop_loss_history` table
  - _Requirements: 4.1, 10.1_

- [x] 1.1 Write property test for position state initialization
  - **Property 15: Position Initialization Completeness**
  - **Validates: Requirements 4.1**

- [x] 1.2 Implement PositionStateTracker class
  - Implement `track_position()` method to initialize position tracking
  - Implement `update_current_price()` method with R-multiple calculation
  - Implement `get_r_multiple()` method for real-time R calculation
  - Implement `get_protection_state()` method for state queries
  - Implement `remove_position()` method for cleanup
  - Add in-memory cache for fast lookups
  - _Requirements: 4.1, 4.2, 4.4, 4.5_

- [x] 1.3 Write property test for R-multiple calculation
  - **Property 16: R-Multiple Calculation Performance**
  - **Validates: Requirements 4.2, 8.4**

- [x] 1.4 Write property test for unrealized P/L maintenance
  - **Property 17: Unrealized P/L Maintenance**
  - **Validates: Requirements 4.4**

- [x] 1.5 Write property test for position state freshness
  - **Property 18: Position State Freshness**
  - **Validates: Requirements 4.5**

- [x] 1.6 Implement protection state machine
  - Define state enum: INITIAL_RISK, BREAKEVEN_PROTECTED, PARTIAL_PROFIT_TAKEN, ADVANCED_PROFIT_TAKEN, FINAL_PROFIT_TAKEN
  - Implement state transition logic based on R-multiple thresholds
  - Implement `transition_state()` method with validation
  - Add state transition event emission
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.5_

- [x] 1.7 Write property test for state machine initial state
  - **Property 19: State Machine Initial State**
  - **Validates: Requirements 5.1**

- [ ] 1.8 Write property test for state transition triggers
  - **Property 20: State Transition Triggers Actions**
  - **Validates: Requirements 5.5**

- [ ] 1.9 Write property test for state transition event emission
  - **Property 34: State Transition Event Emission**
  - **Validates: Requirements 9.5**

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 2: Intelligent Stop Management

- [x] 3. Implement IntelligentStopManager class
  - Create `IntelligentStopManager` class with Alpaca client dependency
  - Implement `calculate_trailing_stop()` method with R-multiple based logic
  - Implement trailing stop algorithm (0.5R at 1.5R, 1.0R at 2.0R, etc.)
  - Add stop price validation (must be >= previous stop)
  - _Requirements: 1.2, 1.5_

- [x] 3.1 Write property test for trailing stop monotonicity
  - **Property 2: Trailing Stop Monotonicity**
  - **Validates: Requirements 1.2, 1.5**

- [x] 3.2 Implement breakeven protection logic
  - Implement `move_to_breakeven()` method
  - Add logic to move stop to entry price at 1.0R
  - Integrate with state machine transition to BREAKEVEN_PROTECTED
  - _Requirements: 1.1, 5.2_

- [x] 3.3 Write property test for breakeven protection activation
  - **Property 1: Breakeven Protection Activation**
  - **Validates: Requirements 1.1, 5.2**

- [x] 3.4 Write property test for profitable position stop invariant
  - **Property 3: Profitable Position Stop Invariant**
  - **Validates: Requirements 1.4**

- [x] 3.5 Implement stop loss update execution
  - Implement `update_stop_for_position()` method
  - Add latency tracking for performance monitoring
  - Integrate with OrderSequencer for conflict-free updates
  - Add stop loss history logging
  - _Requirements: 1.3, 8.1, 9.1_

- [x] 3.6 Write property test for stop update latency
  - **Property 4: Stop Update Latency**
  - **Validates: Requirements 1.3, 8.1**

- [x] 3.7 Write property test for trailing stop logging completeness
  - **Property 31: Trailing Stop Logging Completeness**
  - **Validates: Requirements 9.1**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 3: Profit Taking Engine

- [x] 5. Implement ProfitTakingEngine class
  - Create `ProfitTakingEngine` class with Alpaca client dependency
  - Implement `check_profit_milestones()` method to detect 2R, 3R, 4R
  - Implement milestone detection logic with hysteresis (avoid flapping)
  - Add profit action decision logic
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 5.1 Implement share allocation tracking
  - Create `ShareAllocation` class to track original and remaining quantities
  - Implement `calculate_partial_quantity()` method based on original position
  - Add logic for 50% at 2R, 25% at 3R, remaining at 4R
  - Implement validation to prevent over-selling
  - _Requirements: 2.4_

- [x] 5.2 Write property test for partial quantity calculation
  - **Property 8: Partial Quantity Calculation**
  - **Validates: Requirements 2.4**

- [x] 5.3 Write property test for partial profit quantities sum
  - **Property test: Partial profit quantities must sum to original position**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [x] 5.4 Implement partial profit execution
  - Implement `execute_partial_exit()` method
  - Add market order submission for partial quantity
  - Implement fill confirmation with timeout
  - Add latency tracking for performance monitoring
  - Integrate with OrderSequencer for atomic execution
  - _Requirements: 8.2_

- [x] 5.5 Write property test for partial profit at 2R
  - **Property 5: Partial Profit at 2R**
  - **Validates: Requirements 2.1, 5.3**

- [x] 5.6 Write property test for partial profit at 3R
  - **Property 6: Partial Profit at 3R**
  - **Validates: Requirements 2.2, 5.4**

- [x] 5.7 Write property test for partial profit at 4R
  - **Property 7: Partial Profit at 4R**
  - **Validates: Requirements 2.3**

- [x] 5.8 Write property test for profit milestone execution latency
  - **Property 28: Profit Milestone Execution Latency**
  - **Validates: Requirements 8.2**

- [x] 5.9 Implement position state updates after partial fills
  - Implement `update_position_after_fill()` method
  - Update remaining quantity in PositionStateTracker
  - Update ShareAllocation tracking
  - Persist changes to database
  - _Requirements: 2.5, 4.3_

- [x] 5.10 Write property test for position state consistency after partial fill
  - **Property 9: Position State Consistency After Partial Fill**
  - **Validates: Requirements 2.5, 4.3**

- [x] 5.11 Implement partial profit recording and logging
  - Implement `record_partial_profit()` method
  - Insert records into `partial_profits` table
  - Log R-multiple, shares sold, and profit amount
  - _Requirements: 9.2_

- [x] 5.12 Write property test for partial profit logging completeness
  - **Property 32: Partial Profit Logging Completeness**
  - **Validates: Requirements 9.2**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 4: Order Sequencer & Conflict Resolution

- [x] 7. Implement OrderSequencer class
  - Create `OrderSequencer` class with Alpaca client dependency
  - Implement `detect_conflicts()` method to identify order conflicts
  - Implement conflict detection for shares locked, duplicate orders, invalid prices
  - Add conflict logging with full context
  - _Requirements: 3.5, 9.3_

- [x] 7.1 Write property test for conflict detection and logging
  - **Property 14: Conflict Detection and Logging**
  - **Validates: Requirements 3.5, 9.3**

- [x] 7.2 Implement stop loss modification sequence
  - Implement `execute_stop_update()` method
  - Add logic to cancel existing stop loss before creating new one
  - Implement cancellation confirmation wait (max 2 seconds)
  - Add new stop loss submission
  - Implement verification of new order active status
  - _Requirements: 3.1_

- [x] 7.3 Write property test for stop loss modification sequence
  - **Property 10: Stop Loss Modification Sequence**
  - **Validates: Requirements 3.1**

- [x] 7.4 Implement share availability verification
  - Implement `verify_shares_available()` method
  - Query current position and open orders
  - Calculate locked shares from existing orders
  - Return available shares for new orders
  - _Requirements: 3.2_

- [x] 7.5 Write property test for share availability verification
  - **Property 11: Share Availability Verification**
  - **Validates: Requirements 3.2**

- [x] 7.6 Implement retry logic with exponential backoff
  - Implement `retry_with_backoff()` utility function
  - Add exponential delay calculation (0.5s, 1s, 2s)
  - Implement max retry limit (3 attempts)
  - Add retry logging
  - _Requirements: 3.3, 7.1_

- [x] 7.7 Write property test for retry with exponential backoff
  - **Property 12: Retry with Exponential Backoff**
  - **Validates: Requirements 3.3, 7.1**

- [x] 7.8 Implement atomic operation support
  - Implement `execute_atomic_operation()` method
  - Add transaction-like semantics for multi-step operations
  - Implement rollback capability on failure
  - Add operation state tracking
  - _Requirements: 3.4, 6.1, 6.3_

- [x] 7.9 Write property test for atomic operation all-or-nothing
  - **Property 13: Atomic Operation All-or-Nothing**
  - **Validates: Requirements 3.4, 6.1, 6.3**

- [x] 7.10 Implement partial exit with stop update sequence
  - Implement `execute_partial_exit_with_stop_update()` method
  - Cancel all exit orders (stop + take profit)
  - Submit partial exit market order
  - Wait for fill confirmation
  - Calculate new position size
  - Submit new stop loss and take profit for remaining position
  - Verify all orders active
  - _Requirements: 6.1_

- [x] 7.11 Implement rollback mechanism
  - Implement `rollback_sequence()` method
  - Store pre-operation state
  - Restore previous order state on failure
  - Cancel any partially created orders
  - Log rollback actions
  - _Requirements: 6.2, 6.3_

- [x] 7.12 Write property test for stop loss update rollback
  - **Property 21: Stop Loss Update Rollback**
  - **Validates: Requirements 6.2**

- [x] 7.13 Write property test for post-operation state verification
  - **Property 23: Post-Operation State Verification**
  - **Validates: Requirements 6.5**

- [x] 7.14 Implement concurrent modification prevention
  - Add position-level locking mechanism
  - Implement lock acquisition with timeout
  - Add lock release on operation completion
  - Implement deadlock detection
  - _Requirements: 6.4_

- [x] 7.15 Write property test for concurrent modification prevention
  - **Property 22: Concurrent Modification Prevention**
  - **Validates: Requirements 6.4**

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 5: Error Handling & Recovery

- [x] 9. Implement error handling infrastructure
  - Create custom exception classes for different error types
  - Implement `RetryableError`, `ConflictError`, `StateError` exceptions
  - Add error categorization logic
  - Implement error context capture
  - _Requirements: 7.1, 7.2_

- [x] 9.1 Implement exhausted retry alerting
  - Implement `alert_operator()` method for critical failures
  - Add integration with alerting system (email, Slack, PagerDuty)
  - Implement failure logging with full context
  - Add alert deduplication logic
  - _Requirements: 7.2_

- [x] 9.2 Write property test for exhausted retry alerting
  - **Property 24: Exhausted Retry Alerting**
  - **Validates: Requirements 7.2**

- [x] 9.3 Implement offline operation queueing
  - Create `OperationQueue` class for pending operations
  - Implement queue persistence to database
  - Add network connectivity monitoring
  - Implement queue processing on connectivity restoration
  - Add queue overflow handling
  - _Requirements: 7.3_

- [x] 9.4 Write property test for offline operation queueing
  - **Property 25: Offline Operation Queueing**
  - **Validates: Requirements 7.3**

- [x] 9.5 Implement error recovery mode
  - Add system state tracking (NORMAL, RECOVERY, ERROR)
  - Implement `enter_recovery_mode()` method
  - Add logic to reject new positions during recovery
  - Implement recovery completion validation
  - _Requirements: 7.4, 7.5_

- [x] 9.6 Write property test for error recovery mode restrictions
  - **Property 26: Error Recovery Mode Restrictions**
  - **Validates: Requirements 7.4**

- [x] 9.7 Write property test for recovery validation
  - **Property 27: Recovery Validation**
  - **Validates: Requirements 7.5**

- [x] 9.8 Implement state recovery mechanism
  - Implement `recover_from_state_error()` method
  - Query fresh data from broker API
  - Rebuild local state from broker data
  - Validate state consistency
  - Update local state if valid
  - _Requirements: 7.5_

- [x] 9.9 Implement circuit breaker pattern
  - Create `CircuitBreaker` class
  - Implement failure counting and threshold detection
  - Add circuit states: CLOSED, OPEN, HALF_OPEN
  - Implement timeout-based recovery attempts
  - Add circuit breaker metrics
  - _Requirements: 7.1, 7.2_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 6: Performance Optimization & Monitoring

- [ ] 11. Implement performance optimizations
  - Add caching for frequently accessed position states
  - Implement batch R-multiple calculations
  - Optimize database queries with indexes
  - Add connection pooling for database
  - Implement async operations where possible
  - _Requirements: 8.3, 8.4, 8.5_

- [ ] 11.1 Write property test for monitoring frequency
  - **Property 29: Monitoring Frequency**
  - **Validates: Requirements 8.3**

- [ ] 11.2 Write property test for concurrent update performance
  - **Property 30: Concurrent Update Performance**
  - **Validates: Requirements 8.5**

- [ ] 11.3 Implement metrics exposure
  - Add Prometheus metrics for stop updates, partial exits, conflicts
  - Implement latency histograms for all operations
  - Add gauge metrics for positions by protection state
  - Expose R-multiple and protection state for each position
  - _Requirements: 9.4_

- [ ] 11.4 Write property test for metrics exposure
  - **Property 33: Metrics Exposure**
  - **Validates: Requirements 9.4**

- [ ] 11.5 Implement monitoring dashboard
  - Create Grafana dashboard for profit protection metrics
  - Add panels for stop update latency, partial profit execution
  - Add position state distribution visualization
  - Add conflict rate monitoring
  - Add alert configuration for critical thresholds
  - _Requirements: 9.4_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 7: Integration & Migration

- [x] 13. Integrate with existing TradingEngine
  - Add profit protection monitoring loop to TradingEngine
  - Implement loop to run every 1 second (check for triggers)
  - Integrate PositionStateTracker with position updates
  - Add IntelligentStopManager calls on price updates
  - Add ProfitTakingEngine milestone checks
  - _Requirements: 8.3_

- [x] 13.1 Replace existing stop_loss_protection.py
  - Deprecate old StopLossProtectionManager
  - Update all references to use new IntelligentStopManager
  - Remove legacy trailing stop logic from position_manager.py
  - Update configuration settings
  - _Requirements: 1.1, 1.2_

- [x] 13.2 Integrate with PositionManager
  - Update PositionManager to use PositionStateTracker
  - Add calls to IntelligentStopManager on position updates
  - Integrate ProfitTakingEngine for partial profit execution
  - Update position sync logic
  - _Requirements: 4.1, 4.3_

- [ ] 14. Implement backward compatibility layer
  - Create migration utility to scan existing positions
  - Implement logic to calculate current R-multiple for existing positions
  - Add logic to apply appropriate protection level based on R-multiple
  - Implement bracket order correction for incorrect orders
  - _Requirements: 10.1, 10.2, 10.3_

- [ ] 14.1 Write property test for startup position scanning
  - **Property 35: Startup Position Scanning**
  - **Validates: Requirements 10.1, 10.2**

- [ ] 14.2 Write property test for bracket order self-healing
  - **Property 36: Bracket Order Self-Healing**
  - **Validates: Requirements 10.3**

- [ ] 14.3 Implement migration with minimal disruption
  - Add logic to only modify incorrect or missing orders
  - Implement validation to avoid unnecessary changes
  - Add dry-run mode for migration testing
  - Implement migration logging
  - _Requirements: 10.4_

- [ ] 14.4 Write property test for migration minimal disruption
  - **Property 37: Migration Minimal Disruption**
  - **Validates: Requirements 10.4**

- [ ] 14.5 Implement post-migration verification
  - Add verification that all positions have stop loss orders
  - Add verification that all positions have take profit orders
  - Implement verification report generation
  - Add automated alerts for verification failures
  - _Requirements: 10.5_

- [ ] 14.6 Write property test for post-migration verification
  - **Property 38: Post-Migration Verification**
  - **Validates: Requirements 10.5**

- [ ] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 8: Testing & Validation

- [ ] 16. Implement integration tests
  - Create end-to-end test for full position lifecycle
  - Test position from entry through 1R, 2R, 3R, 4R to exit
  - Verify all state transitions occur correctly
  - Verify all partial profits execute correctly
  - Verify trailing stops update correctly
  - _Requirements: All_

- [ ] 16.1 Implement performance tests
  - Create load test with 100 concurrent positions
  - Measure stop update latency under load
  - Measure R-multiple calculation performance
  - Measure profit execution latency
  - Verify all performance requirements met
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 16.2 Implement error scenario tests
  - Test broker API failures and retry logic
  - Test network connectivity loss and recovery
  - Test order conflicts and resolution
  - Test state inconsistencies and recovery
  - Test circuit breaker activation
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 16.3 Implement backward compatibility tests
  - Test migration of existing positions at various R-multiples
  - Test correction of incorrect bracket orders
  - Test minimal disruption during migration
  - Test post-migration verification
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 17. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 9: Deployment

- [ ] 18. Deploy to production
  - Enable shadow mode (log decisions without executing)
  - Monitor shadow mode for 24 hours
  - Enable canary deployment (10% of positions)
  - Monitor canary for 48 hours
  - Increase to 50% of positions
  - Monitor for 48 hours
  - Enable for 100% of positions
  - Monitor for 1 week
  - _Requirements: All_

- [ ] 18.1 Configure monitoring and alerts
  - Set up Prometheus metrics collection
  - Configure Grafana dashboards
  - Set up critical alerts (stop update latency, conflicts, etc.)
  - Configure PagerDuty integration
  - Test alert delivery
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 18.2 Create operational documentation
  - Document system architecture and components
  - Document monitoring and alerting setup
  - Document troubleshooting procedures
  - Document rollback procedures
  - Create runbook for common issues
  - _Requirements: All_

- [ ] 18.3 Conduct final verification
  - Verify zero profitable positions with stops below entry
  - Verify 100% of positions have active stop loss protection
  - Verify partial profit execution at 2R+ milestones
  - Verify zero order conflicts
  - Verify all performance targets met
  - Generate success criteria report
  - _Requirements: All_

---

## Summary

**Total Tasks**: 18 major tasks with 80+ subtasks
**Estimated Timeline**: 8-9 weeks
**Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 7 → Phase 9
**Test Coverage Target**: 90%+ code coverage
**Property Tests**: 38 properties to validate
**Performance Tests**: 5 latency requirements to verify

This implementation plan ensures systematic development of the Intelligent Profit Protection System with comprehensive testing and validation at each phase.
