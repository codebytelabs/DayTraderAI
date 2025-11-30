# Implementation Plan

- [x] 1. Create MomentumStrengthCalculator component
  - [x] 1.1 Create `backend/trading/momentum_strength.py` with MomentumStrengthCalculator class
    - Implement `calculate_strength()` method combining ADX, volume ratio, and trend strength
    - Implement `validate_inputs()` method for sanitizing invalid values
    - Use existing indicators from `backend/momentum/indicators.py`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [x] 1.2 Write property test for momentum strength bounds
    - **Property 1: Momentum strength is always bounded**
    - **Validates: Requirements 1.1**
  - [x] 1.3 Write property test for input validation
    - **Property 8: Invalid indicator values are sanitized**
    - **Validates: Requirements 8.2, 8.3, 8.4**

- [x] 2. Create VIXDataProvider component
  - [x] 2.1 Create `backend/trading/vix_provider.py` with VIXDataProvider class
    - Implement `get_vix()` method with caching and fallback
    - Implement `get_vix_cap()` method for tiered VIX caps
    - Add cache TTL of 15 minutes
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [x] 2.2 Write property test for VIX cap rules
    - **Property 4: VIX cap follows tiered rules**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [x] 3. Create MomentumConfirmedRegimeManager component
  - [x] 3.1 Create `backend/trading/momentum_confirmed_regime.py` with main manager class
    - Implement `get_momentum_multiplier()` for regime-specific momentum multipliers
    - Implement `get_effective_multiplier()` combining regime, momentum, and VIX
    - Implement `get_momentum_adjusted_params()` for R-targets and stops
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 5.1, 5.2, 5.3_
  - [x] 3.2 Write property test for extreme greed multipliers
    - **Property 2: Extreme greed position multiplier follows tiered rules**
    - **Validates: Requirements 2.1, 2.2, 2.3**
  - [x] 3.3 Write property test for extreme fear multipliers
    - **Property 3: Extreme fear position multiplier follows tiered rules**
    - **Validates: Requirements 3.1, 3.2**
  - [x] 3.4 Write property test for combined multiplier bounds
    - **Property 5: Combined multiplier is always bounded**
    - **Validates: Requirements 5.2, 5.3**
  - [x] 3.5 Write property test for combined multiplier calculation
    - **Property 6: Combined multiplier is product of components**
    - **Validates: Requirements 5.1**

- [x] 4. Implement R-target and stop loss adjustments
  - [x] 4.1 Add R-target adjustment logic to MomentumConfirmedRegimeManager
    - Implement momentum-based R-target adjustments (+/- 0.5R)
    - Implement extreme fear R-target cap (2.0R max)
    - Implement extreme greed R-targets (2.5R strong, 1.5R weak)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [x] 4.2 Add trailing stop adjustment logic
    - Implement extreme fear wide stop (1.0R)
    - Implement extreme greed tight stop (0.5R when strong momentum)
    - _Requirements: 2.4, 3.3_
  - [x] 4.3 Write property test for R-target adjustments
    - **Property 7: R-target adjustment follows momentum rules**
    - **Validates: Requirements 6.1, 6.2, 6.5**
  - [x] 4.4 Write property test for trailing stop rules
    - **Property 9: Extreme fear always uses wide trailing stop**
    - **Property 10: Extreme greed with strong momentum uses tight trailing stop**
    - **Validates: Requirements 2.4, 3.3**

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Integrate with existing RegimeManager
  - [x] 6.1 Update `backend/trading/regime_manager.py` to use MomentumConfirmedRegimeManager
    - Add `momentum_confirmed_manager` as optional component
    - Update `get_effective_position_multiplier()` to use momentum confirmation when available
    - Maintain backward compatibility with simple regime sizing
    - _Requirements: 5.1, 7.5_
  - [x] 6.2 Update `backend/utils/dynamic_position_sizer.py` to use momentum-confirmed multipliers
    - Pass momentum data to position sizing calculations
    - Use effective multiplier from MomentumConfirmedRegimeManager
    - _Requirements: 5.1_

- [x] 7. Add API endpoint and logging
  - [x] 7.1 Add regime summary endpoint to return momentum-confirmed status
    - Return current regime, momentum strength, VIX level, effective multiplier
    - Include component breakdown for debugging
    - _Requirements: 7.2_
  - [x] 7.2 Add comprehensive logging for momentum-confirmed decisions
    - Log all component values when trade is entered
    - Highlight when momentum changes default regime behavior
    - _Requirements: 7.1, 7.3_

- [x] 8. Create verification script
  - [x] 8.1 Create `backend/verify_momentum_confirmed_regime.py`
    - Verify all components are properly initialized
    - Test with sample data to confirm correct behavior
    - Display current regime status with momentum confirmation
    - _Requirements: 7.2_

- [x] 9. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

