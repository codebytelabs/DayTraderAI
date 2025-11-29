"""
Position State Tracker

Maintains real-time state for all open positions including R-multiple,
profit levels, and protection status.
"""

from typing import Dict, Optional
from datetime import datetime
from .models import (
    PositionState, ProtectionState, ProtectionStateEnum,
    ShareAllocation, PartialProfit
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PositionStateTracker:
    """
    Tracks real-time state for all positions with R-multiple calculation
    and protection state management.
    """
    
    def __init__(self):
        self._positions: Dict[str, PositionState] = {}
        logger.info("✅ Position State Tracker initialized")
    
    def track_position(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        quantity: int,
        side: str
    ) -> PositionState:
        """
        Initialize tracking for a new position.
        
        Args:
            symbol: Stock symbol
            entry_price: Entry price
            stop_loss: Initial stop loss price
            quantity: Number of shares
            side: 'long' or 'short'
            
        Returns:
            PositionState object
        """
        # Create initial protection state
        protection_state = ProtectionState(
            state=ProtectionStateEnum.INITIAL_RISK,
            stop_loss_price=stop_loss,
            trailing_active=False,
            partial_profits_taken=[],
            last_stop_update=None
        )
        
        # Create share allocation tracker
        share_allocation = ShareAllocation(
            original_quantity=quantity,
            remaining_quantity=quantity,
            partial_exits=[]
        )
        
        # Calculate initial R-multiple (should be 0 at entry)
        if side == 'long':
            risk = entry_price - stop_loss
        else:
            risk = stop_loss - entry_price
        
        # Create position state
        position_state = PositionState(
            symbol=symbol,
            entry_price=entry_price,
            current_price=entry_price,  # Start at entry
            stop_loss=stop_loss,
            quantity=quantity,
            side=side,
            r_multiple=0.0,  # At entry, R = 0
            unrealized_pl=0.0,
            unrealized_pl_pct=0.0,
            protection_state=protection_state,
            share_allocation=share_allocation,
            last_updated=datetime.utcnow()
        )
        
        self._positions[symbol] = position_state
        
        logger.info(
            f"📊 Tracking {symbol}: Entry ${entry_price:.2f}, "
            f"Stop ${stop_loss:.2f}, Qty {quantity}, Side {side}"
        )
        
        return position_state
    
    def update_current_price(self, symbol: str, current_price: float) -> Optional[PositionState]:
        """
        Update current price and recalculate all metrics.
        
        Args:
            symbol: Stock symbol
            current_price: New current price
            
        Returns:
            Updated PositionState or None if not found
        """
        position = self._positions.get(symbol)
        if not position:
            logger.warning(f"Position {symbol} not found in tracker")
            return None
        
        # Update price and recalculate metrics
        position.update_price(current_price)
        
        # Check for state transitions
        self._check_state_transitions(position)
        
        return position
    
    def get_r_multiple(self, symbol: str) -> float:
        """
        Get current R-multiple for a position.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current R-multiple or 0.0 if not found
        """
        position = self._positions.get(symbol)
        if not position:
            return 0.0
        
        return position.r_multiple
    
    def get_protection_state(self, symbol: str) -> Optional[ProtectionState]:
        """
        Get protection state for a position.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            ProtectionState or None if not found
        """
        position = self._positions.get(symbol)
        if not position:
            return None
        
        return position.protection_state
    
    def get_position_state(self, symbol: str) -> Optional[PositionState]:
        """
        Get complete position state.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            PositionState or None if not found
        """
        return self._positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, PositionState]:
        """Get all tracked positions"""
        return self._positions.copy()
    
    def remove_position(self, symbol: str) -> None:
        """
        Remove position from tracking.
        
        Args:
            symbol: Stock symbol
        """
        if symbol in self._positions:
            del self._positions[symbol]
            logger.info(f"Removed {symbol} from position tracking")
    
    def update_stop_loss(self, symbol: str, new_stop: float) -> bool:
        """
        Update stop loss for a position.
        
        Args:
            symbol: Stock symbol
            new_stop: New stop loss price
            
        Returns:
            True if updated successfully
        """
        position = self._positions.get(symbol)
        if not position:
            logger.warning(f"Cannot update stop for {symbol}: position not found")
            return False
        
        # Validate stop update (must be higher for long, lower for short)
        if position.side == 'long' and new_stop < position.stop_loss:
            logger.warning(
                f"Invalid stop update for {symbol}: "
                f"new stop ${new_stop:.2f} < current ${position.stop_loss:.2f}"
            )
            return False
        elif position.side == 'short' and new_stop > position.stop_loss:
            logger.warning(
                f"Invalid stop update for {symbol}: "
                f"new stop ${new_stop:.2f} > current ${position.stop_loss:.2f}"
            )
            return False
        
        # Update stop loss
        old_stop = position.stop_loss
        position.stop_loss = new_stop
        position.protection_state.stop_loss_price = new_stop
        position.protection_state.last_stop_update = datetime.utcnow()
        position.last_updated = datetime.utcnow()
        
        # Recalculate R-multiple with new stop
        position.update_price(position.current_price)
        
        logger.info(
            f"🔄 Stop updated for {symbol}: ${old_stop:.2f} → ${new_stop:.2f}"
        )
        
        return True
    
    def record_partial_exit(
        self,
        symbol: str,
        shares_sold: int,
        price: float,
        profit_amount: float
    ) -> bool:
        """
        Record a partial profit exit.
        
        Args:
            symbol: Stock symbol
            shares_sold: Number of shares sold
            price: Exit price
            profit_amount: Profit realized
            
        Returns:
            True if recorded successfully
        """
        position = self._positions.get(symbol)
        if not position:
            logger.warning(f"Cannot record partial exit for {symbol}: position not found")
            return False
        
        # Create partial profit record
        partial_profit = PartialProfit(
            shares_sold=shares_sold,
            exit_price=price,
            profit_amount=profit_amount,
            r_multiple_at_exit=position.r_multiple,
            timestamp=datetime.utcnow()
        )
        
        # Update share allocation
        position.share_allocation.remaining_quantity -= shares_sold
        position.share_allocation.partial_exits.append(partial_profit)
        
        # Update protection state
        position.protection_state.partial_profits_taken.append(partial_profit)
        
        # Update quantity
        position.quantity = position.share_allocation.remaining_quantity
        position.last_updated = datetime.utcnow()
        
        logger.info(
            f"💰 Partial exit recorded for {symbol}: "
            f"{shares_sold} shares @ ${price:.2f}, Profit ${profit_amount:.2f}"
        )
        
        return True
    
    def _check_state_transitions(self, position: PositionState) -> None:
        """
        Check if position should transition to a new protection state.
        
        Args:
            position: Position to check
        """
        r = position.r_multiple
        current_state = position.protection_state.state
        
        # State transition logic based on R-multiple
        if r >= 4.0 and current_state != ProtectionStateEnum.FINAL_PROFIT_TAKEN:
            # At 4R, should be in final profit state
            if current_state == ProtectionStateEnum.ADVANCED_PROFIT_TAKEN:
                position.protection_state.state = ProtectionStateEnum.FINAL_PROFIT_TAKEN
                logger.info(f"🎯 {position.symbol} → FINAL_PROFIT_TAKEN at {r:.2f}R")
        
        elif r >= 3.0 and current_state == ProtectionStateEnum.PARTIAL_PROFIT_TAKEN:
            # At 3R, transition to advanced profit
            position.protection_state.state = ProtectionStateEnum.ADVANCED_PROFIT_TAKEN
            logger.info(f"🎯 {position.symbol} → ADVANCED_PROFIT_TAKEN at {r:.2f}R")
        
        elif r >= 2.0 and current_state == ProtectionStateEnum.BREAKEVEN_PROTECTED:
            # At 2R, transition to partial profit
            position.protection_state.state = ProtectionStateEnum.PARTIAL_PROFIT_TAKEN
            logger.info(f"🎯 {position.symbol} → PARTIAL_PROFIT_TAKEN at {r:.2f}R")
        
        elif r >= 1.0 and current_state == ProtectionStateEnum.INITIAL_RISK:
            # At 1R, transition to breakeven protected
            position.protection_state.state = ProtectionStateEnum.BREAKEVEN_PROTECTED
            logger.info(f"🎯 {position.symbol} → BREAKEVEN_PROTECTED at {r:.2f}R")


# Global instance
_position_tracker: Optional[PositionStateTracker] = None


def get_position_tracker() -> PositionStateTracker:
    """Get or create the global position tracker instance."""
    global _position_tracker
    
    if _position_tracker is None:
        _position_tracker = PositionStateTracker()
    
    return _position_tracker
