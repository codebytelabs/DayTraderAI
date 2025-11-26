# Requirements Document: Bracket Protection System Fix

## Introduction

The bracket protection system has a critical flaw causing endless bracket recreation loops, leading to emergency stops and lost profits. This spec addresses the root cause and implements a robust, self-healing bracket management system.

## Glossary

- **Bracket Order**: A combination of entry, stop-loss, and take-profit orders
- **Stop Loss Protection Manager**: System component that ensures all positions have active stop losses
- **Emergency Stop**: Forced position closure when no protective orders exist
- **Wash Trade Error**: Alpaca API error when trying to create conflicting orders
- **Order Recreation Loop**: Bug where brackets are repeatedly canceled and recreated

## Requirements

### Requirement 1: Accurate Stop Loss Detection

**User Story:** As a trader, I want the system to accurately detect existing stop losses, so that my protective orders aren't unnecessarily canceled and recreated.

#### Acceptance Criteria

1. WHEN checking for active stop losses THEN the system SHALL correctly identify stop orders in 'new', 'accepted', 'pending_new', or 'held' status
2. WHEN a stop loss exists THEN the system SHALL NOT attempt to create a duplicate stop loss
3. WHEN multiple stop orders exist for the same position THEN the system SHALL identify and resolve the conflict
4. WHEN checking stop loss status THEN the system SHALL use fresh order data from the API, not cached data
5. WHEN a stop loss is detected THEN the system SHALL log the stop price and order ID for verification

### Requirement 2: Safe Bracket Recreation

**User Story:** As a trader, I want bracket orders to be recreated only when truly necessary, so that my positions remain protected without causing order conflicts.

#### Acceptance Criteria

1. WHEN recreating brackets THEN the system SHALL cancel ALL existing exit orders before creating new ones
2. WHEN canceling orders THEN the system SHALL wait for cancellation confirmation before proceeding
3. WHEN creating new brackets THEN the system SHALL create the stop-loss order BEFORE the take-profit order
4. WHEN bracket creation fails THEN the system SHALL fall back to creating a standalone stop-loss order
5. WHEN a "wash trade" error occurs THEN the system SHALL retry with proper order sequencing

### Requirement 3: Minimum Stop Distance Enforcement

**User Story:** As a trader, I want all stop losses to maintain a minimum distance from entry price, so that I don't get stopped out by normal market noise.

#### Acceptance Criteria

1. WHEN calculating stop loss price THEN the system SHALL enforce a minimum 1.5% distance from entry price
2. WHEN using ATR-based stops THEN the system SHALL use the greater of ATR-based distance or 1.5% minimum
3. WHEN a stop price would be too close to current price THEN the system SHALL adjust it to maintain minimum distance
4. WHEN creating stops for volatile stocks THEN the system SHALL scale the distance based on ATR
5. WHEN stop distance is adjusted THEN the system SHALL log the reason and new distance

### Requirement 4: Recreation Loop Prevention

**User Story:** As a trader, I want the system to prevent endless bracket recreation loops, so that my orders remain stable and my positions aren't accidentally closed.

#### Acceptance Criteria

1. WHEN a position already has a valid stop loss THEN the system SHALL NOT recreate brackets
2. WHEN checking protection status THEN the system SHALL track which positions have been verified in the current cycle
3. WHEN a recreation attempt fails THEN the system SHALL NOT retry immediately in the same cycle
4. WHEN multiple protection checks occur THEN the system SHALL use a cooldown period between recreation attempts
5. WHEN brackets are recreated THEN the system SHALL mark the position as "recently protected" to prevent immediate re-checking

### Requirement 5: Order Conflict Resolution

**User Story:** As a trader, I want the system to resolve order conflicts automatically, so that my positions always have exactly one stop loss and one take profit.

#### Acceptance Criteria

1. WHEN multiple stop losses exist for a position THEN the system SHALL keep the most protective one and cancel others
2. WHEN multiple take profits exist for a position THEN the system SHALL keep the most favorable one and cancel others
3. WHEN conflicting orders prevent new order creation THEN the system SHALL cancel all exit orders and recreate cleanly
4. WHEN "insufficient qty" errors occur THEN the system SHALL identify and cancel the order locking the shares
5. WHEN order conflicts are resolved THEN the system SHALL log the action taken and final order state

### Requirement 6: Self-Healing Stop Loss Sync

**User Story:** As a trader, I want the system to automatically sync stop losses when they drift from expected values, so that my protection remains optimal as positions become profitable.

#### Acceptance Criteria

1. WHEN a stop loss price differs from the expected trailing stop THEN the system SHALL update the order to match
2. WHEN syncing stop losses THEN the system SHALL only move stops in the favorable direction (never worse protection)
3. WHEN a sync operation fails THEN the system SHALL log the error but NOT cancel the existing stop
4. WHEN positions become profitable THEN the system SHALL gradually trail stops upward
5. WHEN stop loss sync completes THEN the system SHALL update the position state with the new stop price

### Requirement 7: Emergency Stop Prevention

**User Story:** As a trader, I want emergency stops to only trigger when positions truly have no protection, so that I don't lose profits due to temporary order state issues.

#### Acceptance Criteria

1. WHEN checking for emergency stop conditions THEN the system SHALL verify no stop loss exists in ANY status
2. WHEN a stop loss is in 'pending' status THEN the system SHALL NOT trigger an emergency stop
3. WHEN brackets are being recreated THEN the system SHALL NOT trigger emergency stops during the recreation window
4. WHEN an emergency stop is triggered THEN the system SHALL log the full order state for debugging
5. WHEN positions have 'held' bracket legs THEN the system SHALL recognize them as valid protection

### Requirement 8: Robust Error Handling

**User Story:** As a trader, I want the system to handle API errors gracefully, so that temporary issues don't cause my positions to lose protection.

#### Acceptance Criteria

1. WHEN API calls fail THEN the system SHALL retry with exponential backoff
2. WHEN order creation fails THEN the system SHALL attempt alternative protection methods
3. WHEN rate limits are hit THEN the system SHALL queue protection operations and retry
4. WHEN network errors occur THEN the system SHALL maintain existing protection until connectivity is restored
5. WHEN errors are logged THEN the system SHALL include full context (symbol, order IDs, error message)

### Requirement 9: Protection Status Monitoring

**User Story:** As a trader, I want to monitor the protection status of all positions, so that I can verify the system is working correctly.

#### Acceptance Criteria

1. WHEN positions exist THEN the system SHALL provide a summary of protection status
2. WHEN protection checks complete THEN the system SHALL log the number of protected, unprotected, and failed positions
3. WHEN viewing protection status THEN the system SHALL show stop loss prices and order IDs
4. WHEN protection issues occur THEN the system SHALL highlight them in the status report
5. WHEN monitoring protection THEN the system SHALL track the time since last successful check per position

### Requirement 10: Bracket Recreation Audit Trail

**User Story:** As a trader, I want a complete audit trail of bracket recreation events, so that I can diagnose issues and verify system behavior.

#### Acceptance Criteria

1. WHEN brackets are recreated THEN the system SHALL log the reason for recreation
2. WHEN orders are canceled THEN the system SHALL log which orders were canceled and why
3. WHEN new orders are created THEN the system SHALL log the order details and IDs
4. WHEN recreation fails THEN the system SHALL log the full error and fallback action taken
5. WHEN reviewing logs THEN the system SHALL provide timestamps and sequence numbers for all bracket operations
