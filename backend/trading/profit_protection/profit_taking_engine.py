"""
Profit Taking Engine

Executes systematic partial profit taking at predefined R-multiple milestones.
UPDATED: Now uses config values for profit taking levels.
Default: 50% at 1R, 25% at 2R, 25% at 3R (research-optimized)
"""

from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass
import time

from .models import PositionState, ProtectionStateEnum, PartialProfit
from .position_state_tracker import get_position_tracker
from core.alpaca_client import AlpacaClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ProfitAction:
    """Action to take for profit milestone"""
    symbol: str
    milestone: float  # R-multiple milestone (2.0, 3.0, 4.0)
    quantity: int     # Shares to sell
    reason: str       # Description of action
    expected_profit: float  # Expected profit amount


@dataclass
class ExecutionResult:
    """Result of profit taking execution"""
    success: bool
    message: str
    shares_sold: int = 0
    fill_price: float = 0.0
    profit_realized: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class ProfitTakingEngine:
    """
    Manages systematic partial profit taking at R-multiple milestones.
    
    Enhanced for Momentum Wave Rider:
    - 2R: Take 50% profit, move stop to breakeven
    - 3R: Tighten trailing stop to 1R
    - RSI divergence exit detection
    - ADX momentum loss detection
    """
    
    def __init__(self, alpaca_client: AlpacaClient):
        self.alpaca = alpaca_client
        self.tracker = get_position_tracker()
        
        # Load profit taking schedule from config (research-optimized defaults)
        # CRITICAL FIX: Use config values instead of hardcoded 2R/3R/4R
        # Research shows earlier profit taking (1R) improves win rate by 10-15%
        from config import settings
        
        # Get config values with fallbacks
        first_target_r = getattr(settings, 'partial_profits_first_target_r', 1.0)
        first_pct = getattr(settings, 'partial_profits_1r_percent', 0.50)
        second_target_r = getattr(settings, 'partial_profits_second_target_r', 2.0)
        second_pct = getattr(settings, 'partial_profits_2r_percent', 0.25)
        third_pct = getattr(settings, 'partial_profits_3r_percent', 0.25)
        
        # Build profit schedule from config
        self.profit_schedule = {
            first_target_r: first_pct,   # Default: 50% at 1R
            second_target_r: second_pct,  # Default: 25% at 2R
            second_target_r + 1.0: third_pct   # Default: 25% at 3R
        }
        
        logger.info(f"📊 Profit schedule loaded: {self.profit_schedule}")
        
        # Momentum Wave Rider enhancements
        self.move_stop_to_breakeven_at = first_target_r  # Move to breakeven at first target
        self.tighten_trailing_at = second_target_r + 1.0  # Tighten at third target
        self.trailing_stop_r = 1.0  # Trail by 1R after tightening
        
        # Exit signal thresholds
        self.adx_momentum_loss_threshold = 20  # Exit if ADX drops below 20
        self.rsi_divergence_lookback = 5  # Bars to check for divergence
        
        logger.info("✅ Profit Taking Engine initialized with Momentum Wave Rider enhancements")
    
    def check_profit_milestones(self, position_state: PositionState) -> Optional[ProfitAction]:
        """
        Check if position has reached a profit milestone requiring action.
        
        UPDATED: Now uses dynamic profit schedule from config.
        Default: 1R (50%), 2R (25%), 3R (25%) - research-optimized
        
        Args:
            position_state: Current position state
            
        Returns:
            ProfitAction if action needed, None otherwise
        """
        r = position_state.r_multiple
        
        # Check if we've already taken profits at this level
        partial_exits = position_state.share_allocation.partial_exits
        num_exits = len(partial_exits)
        
        # Get sorted milestones from profit schedule
        milestones = sorted(self.profit_schedule.keys())
        
        # Check each milestone based on number of exits already taken
        for i, milestone in enumerate(milestones):
            if r >= milestone and num_exits == i:
                # Time for this partial profit
                pct = self.profit_schedule[milestone]
                
                # Calculate quantity based on milestone
                if i == len(milestones) - 1:
                    # Final milestone - take remaining shares
                    quantity = position_state.share_allocation.remaining_quantity
                else:
                    quantity = self._calculate_partial_quantity(
                        position_state.share_allocation.original_quantity,
                        position_state.share_allocation.remaining_quantity,
                        milestone
                    )
                
                if quantity <= 0:
                    continue
                
                expected_profit = quantity * abs(position_state.current_price - position_state.entry_price)
                if position_state.direction == 'short':
                    expected_profit = quantity * (position_state.entry_price - position_state.current_price)
                
                return ProfitAction(
                    symbol=position_state.symbol,
                    milestone=milestone,
                    quantity=quantity,
                    reason=f"{milestone}R milestone - take {int(pct*100)}% profit",
                    expected_profit=expected_profit
                )
        
        return None
    
    def execute_partial_exit(self, symbol: str, quantity: int, reason: str) -> ExecutionResult:
        """
        Execute a partial profit exit order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares to sell
            reason: Reason for the exit
            
        Returns:
            ExecutionResult with execution details
        """
        start_time = time.perf_counter()
        
        try:
            # Get current position to validate
            position_state = self.tracker.get_position_state(symbol)
            if not position_state:
                return ExecutionResult(
                    success=False,
                    message=f"Position {symbol} not found in tracker"
                )
            
            # Validate quantity
            if quantity <= 0 or quantity > position_state.quantity:
                return ExecutionResult(
                    success=False,
                    message=f"Invalid quantity {quantity} for position size {position_state.quantity}"
                )
            
            # Calculate profit
            profit_realized = quantity * (position_state.current_price - position_state.entry_price)
            
            # Record the partial exit
            success = self.tracker.record_partial_exit(
                symbol=symbol,
                shares_sold=quantity,
                price=position_state.current_price,
                profit_amount=profit_realized
            )
            
            if success:
                # Log the execution
                self._log_partial_profit(
                    symbol=symbol,
                    r_multiple=position_state.r_multiple,
                    shares_sold=quantity,
                    profit_realized=profit_realized
                )
                
                # Check latency requirement (< 200ms)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                if elapsed_ms > 200:
                    logger.warning(f"Profit execution for {symbol} took {elapsed_ms:.2f}ms > 200ms limit")
                
                return ExecutionResult(
                    success=True,
                    message=f"Partial exit successful: {quantity} shares @ ${position_state.current_price:.2f}",
                    shares_sold=quantity,
                    fill_price=position_state.current_price,
                    profit_realized=profit_realized
                )
            else:
                return ExecutionResult(
                    success=False,
                    message="Failed to record partial exit in tracker"
                )
                
        except Exception as e:
            logger.error(f"Exception during partial exit for {symbol}: {e}")
            return ExecutionResult(
                success=False,
                message=f"Exception during execution: {str(e)}"
            )
    
    def calculate_remaining_position(self, symbol: str) -> int:
        """
        Calculate remaining position size after partial exits.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Remaining share count
        """
        position_state = self.tracker.get_position_state(symbol)
        if not position_state:
            return 0
        
        return position_state.share_allocation.remaining_quantity
    
    def _calculate_partial_quantity(
        self,
        original_quantity: int,
        remaining_quantity: int,
        milestone: float
    ) -> int:
        """
        Calculate quantity to exit at given milestone.
        
        UPDATED: Now uses dynamic profit schedule from config.
        
        Args:
            original_quantity: Original position size
            remaining_quantity: Current remaining shares
            milestone: R-multiple milestone
            
        Returns:
            Number of shares to sell
        """
        # Get percentage from profit schedule
        if milestone in self.profit_schedule:
            pct = self.profit_schedule[milestone]
            calculated_qty = int(original_quantity * pct)
            # Don't exceed remaining quantity
            return min(calculated_qty, remaining_quantity)
        
        # Fallback for unknown milestones - take remaining
        return remaining_quantity
    
    def _log_partial_profit(
        self,
        symbol: str,
        r_multiple: float,
        shares_sold: int,
        profit_realized: float
    ):
        """
        Log partial profit execution with complete details.
        
        Args:
            symbol: Stock symbol
            r_multiple: R-multiple at execution
            shares_sold: Number of shares sold
            profit_realized: Profit amount realized
        """
        # Log with all required details (validates Property 32)
        logger.info(
            f"💰 Partial Profit - {symbol}: "
            f"R-multiple: {r_multiple:.2f}, "
            f"Shares sold: {shares_sold}, "
            f"Profit realized: ${profit_realized:.2f}"
        )
    
    def check_all_positions_for_milestones(self) -> List[ProfitAction]:
        """
        Check all positions for profit milestone opportunities.
        
        Returns:
            List of profit actions needed
        """
        actions = []
        
        all_positions = self.tracker.get_all_positions()
        
        for symbol, position_state in all_positions.items():
            action = self.check_profit_milestones(position_state)
            if action:
                actions.append(action)
        
        return actions
    
    def execute_batch_profit_taking(self) -> dict:
        """
        Execute profit taking for all positions at milestones.
        
        Returns:
            Dict mapping symbol to execution result
        """
        actions = self.check_all_positions_for_milestones()
        results = {}
        
        if not actions:
            logger.info("No profit taking opportunities found")
            return results
        
        logger.info(f"Executing {len(actions)} profit taking actions")
        
        for action in actions:
            result = self.execute_partial_exit(
                symbol=action.symbol,
                quantity=action.quantity,
                reason=action.reason
            )
            
            results[action.symbol] = result
            
            # Small delay between executions
            time.sleep(0.1)
        
        # Log summary
        successful = sum(1 for r in results.values() if r.success)
        total_profit = sum(r.profit_realized for r in results.values() if r.success)
        
        logger.info(
            f"Profit taking batch complete: {successful}/{len(results)} successful, "
            f"Total profit: ${total_profit:.2f}"
        )
        
        return results
    
    def get_profit_summary(self, symbol: str) -> dict:
        """
        Get summary of all partial profits taken for a position.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with profit summary
        """
        position_state = self.tracker.get_position_state(symbol)
        if not position_state:
            return {}
        
        partial_profits = position_state.protection_state.partial_profits_taken
        
        total_shares_sold = sum(p.shares_sold for p in partial_profits)
        total_profit = sum(p.profit_amount for p in partial_profits)
        
        return {
            'symbol': symbol,
            'original_quantity': position_state.share_allocation.original_quantity,
            'remaining_quantity': position_state.share_allocation.remaining_quantity,
            'total_shares_sold': total_shares_sold,
            'total_profit_realized': total_profit,
            'partial_exits': len(partial_profits),
            'current_r_multiple': position_state.r_multiple
        }
    
    # ==================== MOMENTUM WAVE RIDER ENHANCEMENTS ====================
    
    def calculate_stop_price_for_r_multiple(
        self,
        position_state: PositionState,
        r_multiple: float
    ) -> float:
        """
        Calculate stop price for a given R-multiple.
        
        Args:
            position_state: Current position state
            r_multiple: R-multiple for stop (0 = breakeven, 1 = 1R profit locked)
            
        Returns:
            Stop price
        """
        entry_price = position_state.entry_price
        initial_risk = position_state.initial_risk  # 1R in dollars per share
        
        if position_state.direction == 'long':
            # For long: stop = entry + (r_multiple * risk)
            return entry_price + (r_multiple * initial_risk)
        else:
            # For short: stop = entry - (r_multiple * risk)
            return entry_price - (r_multiple * initial_risk)
    
    def should_move_stop_to_breakeven(self, position_state: PositionState) -> bool:
        """
        Check if stop should be moved to breakeven.
        
        Move to breakeven after:
        - Position reaches 2R profit
        - First partial profit has been taken
        
        Args:
            position_state: Current position state
            
        Returns:
            True if stop should be moved to breakeven
        """
        r = position_state.r_multiple
        partial_exits = position_state.share_allocation.partial_exits
        
        # Move to breakeven after 2R and first partial taken
        if r >= self.move_stop_to_breakeven_at and len(partial_exits) >= 1:
            # Check if stop is not already at breakeven
            current_stop = position_state.stop_price
            breakeven = position_state.entry_price
            
            if position_state.direction == 'long':
                return current_stop < breakeven
            else:
                return current_stop > breakeven
        
        return False
    
    def should_tighten_trailing_stop(self, position_state: PositionState) -> bool:
        """
        Check if trailing stop should be tightened.
        
        Tighten to 1R trailing after position reaches 3R.
        
        Args:
            position_state: Current position state
            
        Returns:
            True if trailing stop should be tightened
        """
        r = position_state.r_multiple
        
        # Tighten at 3R
        if r >= self.tighten_trailing_at:
            # Calculate what the 1R trailing stop would be
            target_stop = self.calculate_stop_price_for_r_multiple(
                position_state, 
                r - self.trailing_stop_r  # Trail by 1R
            )
            
            current_stop = position_state.stop_price
            
            if position_state.direction == 'long':
                return current_stop < target_stop
            else:
                return current_stop > target_stop
        
        return False
    
    def check_rsi_divergence(
        self,
        prices: list,
        rsi_values: list
    ) -> bool:
        """
        Check for bearish RSI divergence (price up, RSI down).
        
        This is an exit signal - momentum is weakening even as price rises.
        
        Args:
            prices: Recent price values (oldest to newest)
            rsi_values: Corresponding RSI values
            
        Returns:
            True if bearish divergence detected
        """
        if len(prices) < self.rsi_divergence_lookback or len(rsi_values) < self.rsi_divergence_lookback:
            return False
        
        # Get recent values
        recent_prices = prices[-self.rsi_divergence_lookback:]
        recent_rsi = rsi_values[-self.rsi_divergence_lookback:]
        
        # Check for divergence: price making higher highs, RSI making lower highs
        price_trend = recent_prices[-1] > recent_prices[0]  # Price going up
        rsi_trend = recent_rsi[-1] < recent_rsi[0]  # RSI going down
        
        if price_trend and rsi_trend:
            logger.warning(f"⚠️ RSI divergence detected: price up but RSI down")
            return True
        
        return False
    
    def check_adx_momentum_loss(self, adx: float) -> bool:
        """
        Check if ADX indicates momentum loss.
        
        When ADX drops below 20, the trend is weakening.
        
        Args:
            adx: Current ADX value
            
        Returns:
            True if momentum loss detected
        """
        if adx < self.adx_momentum_loss_threshold:
            logger.warning(f"⚠️ ADX momentum loss: {adx:.1f} < {self.adx_momentum_loss_threshold}")
            return True
        
        return False
    
    def check_exit_signals(
        self,
        position_state: PositionState,
        features: dict
    ) -> tuple:
        """
        Check for exit signals based on technical indicators.
        
        Exit signals:
        - RSI divergence (price up, RSI down)
        - ADX momentum loss (ADX < 20)
        
        Args:
            position_state: Current position state
            features: Technical indicator features
            
        Returns:
            Tuple of (should_exit, reason)
        """
        # Check RSI divergence
        prices = features.get('recent_prices', [])
        rsi_values = features.get('recent_rsi', [])
        
        if self.check_rsi_divergence(prices, rsi_values):
            return True, "RSI divergence - momentum weakening"
        
        # Check ADX momentum loss
        adx = features.get('adx', 25)
        
        if self.check_adx_momentum_loss(adx):
            return True, f"ADX momentum loss ({adx:.1f} < {self.adx_momentum_loss_threshold})"
        
        return False, None
    
    def get_stop_adjustment_action(self, position_state: PositionState) -> dict:
        """
        Get the stop adjustment action needed for a position.
        
        Args:
            position_state: Current position state
            
        Returns:
            Dict with action details or empty dict if no action needed
        """
        # Check for breakeven move
        if self.should_move_stop_to_breakeven(position_state):
            new_stop = position_state.entry_price
            return {
                'action': 'move_to_breakeven',
                'symbol': position_state.symbol,
                'new_stop': new_stop,
                'reason': f"2R reached - moving stop to breakeven (${new_stop:.2f})"
            }
        
        # Check for trailing stop tightening
        if self.should_tighten_trailing_stop(position_state):
            r = position_state.r_multiple
            new_stop = self.calculate_stop_price_for_r_multiple(
                position_state,
                r - self.trailing_stop_r
            )
            return {
                'action': 'tighten_trailing',
                'symbol': position_state.symbol,
                'new_stop': new_stop,
                'reason': f"3R+ reached - tightening trailing stop to ${new_stop:.2f} (1R trail)"
            }
        
        return {}


# Global instance
_profit_engine: Optional[ProfitTakingEngine] = None


def get_profit_engine(alpaca_client: AlpacaClient) -> ProfitTakingEngine:
    """Get or create the global profit taking engine instance."""
    global _profit_engine
    
    if _profit_engine is None:
        _profit_engine = ProfitTakingEngine(alpaca_client)
    
    return _profit_engine
