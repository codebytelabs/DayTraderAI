# Requirements Document: Smart Order Executor & Bracket Protection Fix

## Introduction

The trading bot has three critical issues preventing profitable operation:
1. Smart Order Executor is rejecting all trades with "Fill timeout" errors
2. Bracket recreation loop has returned, causing endless order cancellation/recreation cycles
3. Emergency stop system is triggering false positives and closing protected positions

This spec addresses these issues to restore bot functionality.

## Glossary

- **Smart Order Executor**: Component that submits limit orders and monitors fill status
- **Bracket Orders**: Stop-loss and take-profit orders that protect positions
- **Emergency Stop**: Safety mechanism that closes positions without proper protection
- **Fill Timeout**: Maximum time allowed for an order to fill before cancellation
- **Position Manager**: Component responsible for tracking and protecting open positions
- **Stop Loss Protection Manager**: Component that ensures all positions have stop-loss orders

## Requirements

### Requirement 1: Smart Order Executor Fill Timeout

**User Story:** As a trader, I want the Smart Order Executor to allow sufficient time for orders to fill, so that valid trades are not rejected prematurely.

#### Acceptance Criteria

1. WHEN the Smart Order Executor submits a limit order THEN the system SHALL wait at least 3 seconds before checking fill status
2. WHEN an order fills within the timeout period THEN the system SHALL accept the trade and create bracket orders
3. WHEN an order does not fill within the timeout period THEN the system SHALL cancel the order and log the rejection reason
4. WHEN the fill timeout is configured THEN the system SHALL use a minimum of 3 seconds and maximum of 10 seconds
5. WHEN an order is rejected due to timeout THEN the system SHALL include actual slippage data in the log message

### Requirement 2: Bracket Recreation Prevention

**User Story:** As a trader, I want bracket orders to remain stable once created, so that positions are not constantly disrupted by order cancellation/recreation cycles.

#### Acceptance Criteria

1. WHEN a position has both stop-loss and take-profit orders THEN the system SHALL NOT recreate brackets
2. WHEN a position has only a stop-loss order THEN the system SHALL NOT recreate brackets if shares are held
3. WHEN the Stop Loss Protection Manager detects missing brackets THEN the system SHALL wait at least 30 seconds before attempting recreation
4. WHEN bracket recreation is attempted THEN the system SHALL verify no existing orders before creating new ones
5. WHEN a take-profit order fails due to "potential wash trade" THEN the system SHALL accept the stop-loss only and NOT retry

### Requirement 3: Emergency Stop False Positive Prevention

**User Story:** As a trader, I want the emergency stop system to only trigger for genuinely unprotected positions, so that protected positions are not closed unnecessarily.

#### Acceptance Criteria

1. WHEN a position has an active stop-loss order THEN the system SHALL NOT trigger emergency stop
2. WHEN a position temporarily has no orders due to recreation THEN the system SHALL wait at least 10 seconds before triggering emergency stop
3. WHEN the Position Manager detects "NO orders" THEN the system SHALL verify with Alpaca API before triggering emergency stop
4. WHEN emergency stop is triggered THEN the system SHALL log the reason and all order states
5. WHEN a position is being protected by Stop Loss Protection Manager THEN the system SHALL NOT trigger emergency stop

### Requirement 4: Order State Synchronization

**User Story:** As a trader, I want the system to maintain accurate order state information, so that bracket protection decisions are based on current reality.

#### Acceptance Criteria

1. WHEN the system checks for bracket orders THEN the system SHALL query Alpaca API for current order status
2. WHEN an order is cancelled THEN the system SHALL update internal state within 1 second
3. WHEN an order fills THEN the system SHALL update internal state within 1 second
4. WHEN bracket recreation is considered THEN the system SHALL refresh order state from Alpaca API first
5. WHEN multiple components check order state THEN the system SHALL use a shared cache with 2-second TTL

### Requirement 5: Smart Order Executor Slippage Handling

**User Story:** As a trader, I want the Smart Order Executor to handle slippage intelligently, so that trades are executed at acceptable prices.

#### Acceptance Criteria

1. WHEN a limit order is submitted THEN the system SHALL set the limit price with 0.3% buffer from signal price
2. WHEN an order fills THEN the system SHALL calculate actual slippage from signal price
3. WHEN slippage exceeds 0.5% THEN the system SHALL log a warning but accept the fill
4. WHEN slippage exceeds 1.0% THEN the system SHALL reject the fill and cancel the order
5. WHEN an order is rejected THEN the system SHALL include actual fill price and slippage percentage in logs

### Requirement 6: Bracket Protection Coordination

**User Story:** As a trader, I want the Stop Loss Protection Manager and Position Manager to coordinate, so that bracket orders are not duplicated or conflicted.

#### Acceptance Criteria

1. WHEN Stop Loss Protection Manager creates brackets THEN the system SHALL notify Position Manager
2. WHEN Position Manager detects missing brackets THEN the system SHALL check if Stop Loss Protection Manager is already handling it
3. WHEN both components attempt bracket recreation THEN the system SHALL use a mutex lock to prevent conflicts
4. WHEN bracket recreation completes THEN the system SHALL update shared state within 1 second
5. WHEN a component queries bracket status THEN the system SHALL return consistent state across all components
