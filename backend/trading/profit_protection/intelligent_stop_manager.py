"""
Intelligent Stop Manager

Dynamically adjusts stop losses based on position profitability and market conditions.
Implements trailing stops, breakeven protection, and R-multiple based stop management.
"""

from typing import Optional
from datetime import datetime
import time

from .models import PositionState, ProtectionStateEnum
from .position_state_tracker import get_position_tracker
from core.alpaca_client import AlpacaClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class StopUpdateResult:
    """Result of a stop loss update operation"""
    
    def __init__(self, success: bool, message: str, old_stop: Optional[float] = None, new_stop: Optional[float] = None):
        self.success = success
        self.message = message
        self.old_stop = old_stop
        self.new_stop = new_stop
        self.timestamp = datetime.utcnow()


class IntelligentStopManager:
    """
    Manages dynamic stop losses with trailing logic and breakeven protection.
    """
    
    def __init__(self, alpaca_client: AlpacaClient):
        self.alpaca = alpaca_client
        self.tracker = get_position_tracker()
        logger.info("✅ Intelligent Stop Manager initialized")
    
    def calculate_trailing_stop(
        self,
        entry_price: float,
        current_price: float,
        initial_risk: float,
        r_multiple: float
    ) -> float:
        """
        Calculate trailing stop price based on R-multiple.
        
        Trailing Stop Algorithm:
        - At 1.0R: Move stop to breakeven (entry price)
        - At 1.5R: Trail at 0.5R below current (lock in 0.5R profit)
        - At 2.0R: Trail at 1.0R below current (lock in 1.0R profit)
        - At 3.0R: Trail at 1.5R below current (lock in 1.5R profit)
        - At 4.0R+: Trail at 2.0R below current (lock in 2.0R profit)
        
        Args:
            entry_price: Original entry price
            current_price: Current market price
            initial_risk: Initial risk amount (entry - stop)
            r_multiple: Current R-multiple
            
        Returns:
            New stop loss price
        """
        if r_multiple < 1.0:
            # Below breakeven - keep initial stop
            return entry_price - initial_risk
        elif r_multiple < 1.5:
            # At breakeven - move stop to entry
            return entry_price
        elif r_multiple < 2.0:
            # Trail at 0.5R
            return entry_price + (0.5 * initial_risk)
        elif r_multiple < 3.0:
            # Trail at 1.0R
            return entry_price + (1.0 * initial_risk)
        elif r_multiple < 4.0:
            # Trail at 1.5R
            return entry_price + (1.5 * initial_risk)
        else:
            # Trail at 2.0R
            return entry_price + (2.0 * initial_risk)
    
    def move_to_breakeven(self, symbol: str) -> bool:
        """
        Move stop loss to breakeven (entry price) for a position.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if successful
        """
        position_state = self.tracker.get_position_state(symbol)
        if not position_state:
            logger.warning(f"Cannot move to breakeven: position {symbol} not found")
            return False
        
        # Check if position is profitable enough for breakeven
        if position_state.r_multiple < 1.0:
            logger.warning(
                f"Position {symbol} at {position_state.r_multiple:.2f}R - "
                f"not profitable enough for breakeven protection"
            )
            return False
        
        # Update stop to entry price
        success = self.tracker.update_stop_loss(symbol, position_state.entry_price)
        
        if success:
            logger.info(
                f"🛡️  Breakeven protection activated for {symbol}: "
                f"stop moved to ${position_state.entry_price:.2f}"
            )
        
        return success
    
    def update_stop_for_position(self, position_state: PositionState) -> StopUpdateResult:
        """
        Update stop loss for a position based on current R-multiple and protection state.
        
        Args:
            position_state: Current position state
            
        Returns:
            StopUpdateResult with operation details
        """
        start_time = time.perf_counter()
        
        try:
            # Calculate initial risk
            if position_state.side == 'long':
                initial_risk = position_state.entry_price - position_state.stop_loss
            else:
                initial_risk = position_state.stop_loss - position_state.entry_price
            
            # Calculate new stop based on trailing logic
            new_stop = self.calculate_trailing_stop(
                position_state.entry_price,
                position_state.current_price,
                initial_risk,
                position_state.r_multiple
            )
            
            # Validate stop update (must be better than current)
            if position_state.side == 'long' and new_stop <= position_state.stop_loss:
                return StopUpdateResult(
                    success=False,
                    message=f"New stop ${new_stop:.2f} not better than current ${position_state.stop_loss:.2f}",
                    old_stop=position_state.stop_loss
                )
            elif position_state.side == 'short' and new_stop >= position_state.stop_loss:
                return StopUpdateResult(
                    success=False,
                    message=f"New stop ${new_stop:.2f} not better than current ${position_state.stop_loss:.2f}",
                    old_stop=position_state.stop_loss
                )
            
            # Update stop in tracker
            old_stop = position_state.stop_loss
            success = self.tracker.update_stop_loss(position_state.symbol, new_stop)
            
            if success:
                # Log the update
                self._log_stop_update(
                    position_state.symbol,
                    old_stop,
                    new_stop,
                    position_state.r_multiple
                )
                
                # Check latency requirement (< 100ms)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                if elapsed_ms > 100:
                    logger.warning(
                        f"Stop update for {position_state.symbol} took {elapsed_ms:.2f}ms > 100ms limit"
                    )
                
                return StopUpdateResult(
                    success=True,
                    message=f"Stop updated from ${old_stop:.2f} to ${new_stop:.2f}",
                    old_stop=old_stop,
                    new_stop=new_stop
                )
            else:
                return StopUpdateResult(
                    success=False,
                    message="Failed to update stop in tracker",
                    old_stop=old_stop
                )
                
        except Exception as e:
            logger.error(f"Error updating stop for {position_state.symbol}: {e}")
            return StopUpdateResult(
                success=False,
                message=f"Exception during stop update: {str(e)}"
            )
    
    def _log_stop_update(
        self,
        symbol: str,
        old_stop: float,
        new_stop: float,
        r_multiple: float
    ):
        """
        Log stop loss update with complete details.
        
        Args:
            symbol: Stock symbol
            old_stop: Previous stop price
            new_stop: New stop price
            r_multiple: Current R-multiple
        """
        # Determine reason for update
        position = self.tracker.get_position_state(symbol)
        if position:
            if r_multiple >= 1.0 and abs(new_stop - position.entry_price) < 0.01:
                reason = "breakeven_protection"
            else:
                reason = "trailing_stop"
        else:
            reason = "stop_adjustment"
        
        # Log with all required details (validates Property 31)
        logger.info(
            f"🔄 Stop Update - {symbol}: "
            f"Old: ${old_stop:.2f}, New: ${new_stop:.2f}, "
            f"R: {r_multiple:.2f}, Reason: {reason}"
        )
    
    def check_all_positions_for_updates(self) -> dict:
        """
        Check all tracked positions and identify those needing stop updates.
        
        Returns:
            Dict mapping symbol to update reason
        """
        updates_needed = {}
        
        all_positions = self.tracker.get_all_positions()
        
        for symbol, position_state in all_positions.items():
            # Calculate initial risk
            if position_state.side == 'long':
                initial_risk = position_state.entry_price - position_state.stop_loss
            else:
                initial_risk = position_state.stop_loss - position_state.entry_price
            
            # Calculate what the stop should be
            optimal_stop = self.calculate_trailing_stop(
                position_state.entry_price,
                position_state.current_price,
                initial_risk,
                position_state.r_multiple
            )
            
            # Check if update is needed
            if position_state.side == 'long' and optimal_stop > position_state.stop_loss:
                if position_state.r_multiple >= 1.0 and position_state.protection_state.state == ProtectionStateEnum.INITIAL_RISK:
                    updates_needed[symbol] = "move_to_breakeven"
                else:
                    updates_needed[symbol] = "trailing_stop"
            elif position_state.side == 'short' and optimal_stop < position_state.stop_loss:
                if position_state.r_multiple >= 1.0 and position_state.protection_state.state == ProtectionStateEnum.INITIAL_RISK:
                    updates_needed[symbol] = "move_to_breakeven"
                else:
                    updates_needed[symbol] = "trailing_stop"
        
        return updates_needed
    
    def execute_batch_updates(self, max_concurrent: int = 5) -> dict:
        """
        Execute stop updates for all positions that need them.
        
        Args:
            max_concurrent: Maximum number of concurrent updates
            
        Returns:
            Dict mapping symbol to update result
        """
        updates_needed = self.check_all_positions_for_updates()
        results = {}
        
        if not updates_needed:
            logger.info("No stop loss updates needed")
            return results
        
        logger.info(f"Executing {len(updates_needed)} stop loss updates")
        
        # Process updates
        for symbol, reason in updates_needed.items():
            position_state = self.tracker.get_position_state(symbol)
            if position_state:
                result = self.update_stop_for_position(position_state)
                results[symbol] = result
                
                # Small delay to avoid overwhelming the system
                time.sleep(0.1)
        
        # Log summary
        successful = sum(1 for r in results.values() if r.success)
        logger.info(f"Stop update batch complete: {successful}/{len(results)} successful")
        
        return results


# Global instance
_stop_manager: Optional[IntelligentStopManager] = None


def get_stop_manager(alpaca_client: AlpacaClient) -> IntelligentStopManager:
    """Get or create the global stop manager instance."""
    global _stop_manager
    
    if _stop_manager is None:
        _stop_manager = IntelligentStopManager(alpaca_client)
    
    return _stop_manager
