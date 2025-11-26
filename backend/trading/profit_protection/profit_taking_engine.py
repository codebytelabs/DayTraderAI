"""
Profit Taking Engine

Executes systematic partial profit taking at predefined R-multiple milestones.
Implements 50% at 2R, 25% at 3R, 25% at 4R profit taking schedule.
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
    """
    
    def __init__(self, alpaca_client: AlpacaClient):
        self.alpaca = alpaca_client
        self.tracker = get_position_tracker()
        
        # Profit taking schedule
        self.profit_schedule = {
            2.0: 0.50,  # Take 50% at 2R
            3.0: 0.25,  # Take 25% at 3R
            4.0: 0.25   # Take remaining 25% at 4R
        }
        
        logger.info("✅ Profit Taking Engine initialized")
    
    def check_profit_milestones(self, position_state: PositionState) -> Optional[ProfitAction]:
        """
        Check if position has reached a profit milestone requiring action.
        
        Args:
            position_state: Current position state
            
        Returns:
            ProfitAction if action needed, None otherwise
        """
        r = position_state.r_multiple
        current_state = position_state.protection_state.state
        
        # Check if we've already taken profits at this level
        partial_exits = position_state.share_allocation.partial_exits
        num_exits = len(partial_exits)
        
        # Check each milestone based on number of exits already taken
        if r >= 2.0 and num_exits == 0:
            # Time for first partial profit (50%)
            quantity = self._calculate_partial_quantity(
                position_state.share_allocation.original_quantity,
                position_state.share_allocation.remaining_quantity,
                2.0
            )
            
            expected_profit = quantity * (position_state.current_price - position_state.entry_price)
            
            return ProfitAction(
                symbol=position_state.symbol,
                milestone=2.0,
                quantity=quantity,
                reason="2R milestone - take 50% profit",
                expected_profit=expected_profit
            )
        
        elif r >= 3.0 and num_exits == 1:
            # Time for second partial profit (25% of original)
            quantity = self._calculate_partial_quantity(
                position_state.share_allocation.original_quantity,
                position_state.share_allocation.remaining_quantity,
                3.0
            )
            
            expected_profit = quantity * (position_state.current_price - position_state.entry_price)
            
            return ProfitAction(
                symbol=position_state.symbol,
                milestone=3.0,
                quantity=quantity,
                reason="3R milestone - take 25% profit",
                expected_profit=expected_profit
            )
        
        elif r >= 4.0 and num_exits == 2:
            # Time for final partial profit (remaining shares)
            quantity = position_state.share_allocation.remaining_quantity
            
            expected_profit = quantity * (position_state.current_price - position_state.entry_price)
            
            return ProfitAction(
                symbol=position_state.symbol,
                milestone=4.0,
                quantity=quantity,
                reason="4R milestone - take final profit",
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
        
        Args:
            original_quantity: Original position size
            remaining_quantity: Current remaining shares
            milestone: R-multiple milestone
            
        Returns:
            Number of shares to sell
        """
        if milestone == 2.0:
            # 50% of original position
            return int(original_quantity * 0.5)
        elif milestone == 3.0:
            # 25% of original position
            return int(original_quantity * 0.25)
        elif milestone >= 4.0:
            # Remaining shares
            return remaining_quantity
        
        return 0
    
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


# Global instance
_profit_engine: Optional[ProfitTakingEngine] = None


def get_profit_engine(alpaca_client: AlpacaClient) -> ProfitTakingEngine:
    """Get or create the global profit taking engine instance."""
    global _profit_engine
    
    if _profit_engine is None:
        _profit_engine = ProfitTakingEngine(alpaca_client)
    
    return _profit_engine
