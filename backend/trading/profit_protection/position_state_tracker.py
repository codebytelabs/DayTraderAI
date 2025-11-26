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
        
        # Create position state
        position_state = PositionState(
            symbol=symbol,
            entry_price=entry_price,
            current_price=entry_price,
            stop_loss=stop_loss,
            quantity=quantity,
            side=side,
            r_multiple=0.0,
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
        """Update current price and recalculate all metrics."""
        position = self._positions.get(symbol)
        if not position:
            logger.warning(f"Position {symbol} not found in tracker")
            return None
        
        position.update_price(current_price)
        self._check_state_transitions(position)
        
        return position
    
    def get_r_multiple(self, symbol: str) -> float:
        """Get current R-multiple for a position."""
        position = self._positions.get(symbol)
        if not position:
            return 0.0
        return position.r_multiple
    
    def get_protection_state(self, symbol: str) -> Optional[ProtectionState]:
        """Get protection state for a position."""
        position = self._positions.get(symbol)
        if not position:
            return None
        return position.protection_state
    
    def get_position_state(self, symbol: str) -> Optional[PositionState]:
        """Get complete position state."""
        return self._positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, PositionState]:
        """Get all tracked positions"""
        return self._positions.copy()
    
    def remove_position(self, symbol: str) -> None:
        """Remove position from tracking."""
        if symbol in self._positions:
            del self._positions[symbol]
            logger.info(f"Removed {symbol} from position tracking")
    
    def update_stop_loss(self, symbol: str, new_stop: float) -> bool:
        """Update stop loss for a position."""
        position = self._positions.get(symbol)
        if not position:
            logger.warning(f"Cannot update stop for {symbol}: position not found")
            return False
        
        # Validate stop update
        if position.side == 'long' and new_stop < position.stop_loss:
            logger.warning(f"Invalid stop update for {symbol}")
            return False
        elif position.side == 'short' and new_stop > position.stop_loss:
            logger.warning(f"Invalid stop update for {symbol}")
            return False
        
        old_stop = position.stop_loss
        position.stop_loss = new_stop
        position.protection_state.stop_loss_price = new_stop
        position.protection_state.last_stop_update = datetime.utcnow()
        position.last_updated = datetime.utcnow()
        position.update_price(position.current_price)
        
        logger.info(f"🔄 Stop updated for {symbol}: ${old_stop:.2f} → ${new_stop:.2f}")
        return True
    
    def record_partial_exit(
        self,
        symbol: str,
        shares_sold: int,
        price: float,
        profit_amount: float
    ) -> bool:
        """Record a partial profit exit."""
        position = self._positions.get(symbol)
        if not position:
            logger.warning(f"Cannot record partial exit for {symbol}: position not found")
            return False
        
        partial_profit = PartialProfit(
            shares_sold=shares_sold,
            exit_price=price,
            profit_amount=profit_amount,
            r_multiple_at_exit=position.r_multiple,
            timestamp=datetime.utcnow()
        )
        
        position.share_allocation.remaining_quantity -= shares_sold
        position.share_allocation.partial_exits.append(partial_profit)
        position.protection_state.partial_profits_taken.append(partial_profit)
        position.quantity = position.share_allocation.remaining_quantity
        position.last_updated = datetime.utcnow()
        
        logger.info(
            f"💰 Partial exit recorded for {symbol}: "
            f"{shares_sold} shares @ ${price:.2f}, Profit ${profit_amount:.2f}"
        )
        return True
    
    def _check_state_transitions(self, position: PositionState) -> None:
        """Check if position should transition to a new protection state."""
        r = position.r_multiple
        current_state = position.protection_state.state
        
        if r >= 4.0 and current_state != ProtectionStateEnum.FINAL_PROFIT_TAKEN:
            if current_state == ProtectionStateEnum.ADVANCED_PROFIT_TAKEN:
                position.protection_state.state = ProtectionStateEnum.FINAL_PROFIT_TAKEN
                logger.info(f"🎯 {position.symbol} → FINAL_PROFIT_TAKEN at {r:.2f}R")
        
        elif r >= 3.0 and current_state == ProtectionStateEnum.PARTIAL_PROFIT_TAKEN:
            position.protection_state.state = ProtectionStateEnum.ADVANCED_PROFIT_TAKEN
            logger.info(f"🎯 {position.symbol} → ADVANCED_PROFIT_TAKEN at {r:.2f}R")
        
        elif r >= 2.0 and current_state == ProtectionStateEnum.BREAKEVEN_PROTECTED:
            position.protection_state.state = ProtectionStateEnum.PARTIAL_PROFIT_TAKEN
            logger.info(f"🎯 {position.symbol} → PARTIAL_PROFIT_TAKEN at {r:.2f}R")
        
        elif r >= 1.0 and current_state == ProtectionStateEnum.INITIAL_RISK:
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
