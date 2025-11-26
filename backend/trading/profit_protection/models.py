"""
Data models for Intelligent Profit Protection System
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class ProtectionStateEnum(str, Enum):
    """Protection state for position lifecycle"""
    INITIAL_RISK = "INITIAL_RISK"  # 0-1R
    BREAKEVEN_PROTECTED = "BREAKEVEN_PROTECTED"  # 1-2R
    PARTIAL_PROFIT_TAKEN = "PARTIAL_PROFIT_TAKEN"  # 2-3R
    ADVANCED_PROFIT_TAKEN = "ADVANCED_PROFIT_TAKEN"  # 3-4R
    FINAL_PROFIT_TAKEN = "FINAL_PROFIT_TAKEN"  # 4R+


@dataclass
class PartialProfit:
    """Record of a partial profit execution"""
    r_multiple: float
    shares_sold: int
    price: float
    profit_amount: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ShareAllocation:
    """Tracks share allocation for partial profit taking"""
    original_quantity: int
    remaining_quantity: int
    partial_exits: List[PartialProfit] = field(default_factory=list)
    
    def calculate_next_exit_quantity(self, milestone: float) -> int:
        """
        Calculate quantity to exit at given R-multiple milestone.
        
        Args:
            milestone: R-multiple milestone (2.0, 3.0, or 4.0)
            
        Returns:
            Number of shares to sell
        """
        if milestone == 2.0:
            # 50% of original position
            return int(self.original_quantity * 0.5)
        elif milestone == 3.0:
            # 25% of original position
            return int(self.original_quantity * 0.25)
        elif milestone >= 4.0:
            # Remaining shares
            return self.remaining_quantity
        return 0
    
    def record_exit(self, partial_profit: PartialProfit):
        """Record a partial exit"""
        self.partial_exits.append(partial_profit)
        self.remaining_quantity -= partial_profit.shares_sold


@dataclass
class ProtectionState:
    """Protection state for a position"""
    state: ProtectionStateEnum
    stop_loss_price: float
    trailing_active: bool
    partial_profits_taken: List[PartialProfit] = field(default_factory=list)
    last_stop_update: Optional[datetime] = None
    
    def can_transition_to(self, new_state: ProtectionStateEnum) -> bool:
        """
        Check if transition to new state is valid.
        States can only move forward, never backward.
        """
        state_order = [
            ProtectionStateEnum.INITIAL_RISK,
            ProtectionStateEnum.BREAKEVEN_PROTECTED,
            ProtectionStateEnum.PARTIAL_PROFIT_TAKEN,
            ProtectionStateEnum.ADVANCED_PROFIT_TAKEN,
            ProtectionStateEnum.FINAL_PROFIT_TAKEN,
        ]
        
        current_idx = state_order.index(self.state)
        new_idx = state_order.index(new_state)
        
        return new_idx >= current_idx


@dataclass
class PositionState:
    """Complete state for a position"""
    symbol: str
    entry_price: float
    current_price: float
    stop_loss: float
    quantity: int
    side: str  # 'long' or 'short'
    r_multiple: float
    unrealized_pl: float
    unrealized_pl_pct: float
    protection_state: ProtectionState
    share_allocation: ShareAllocation
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_r_multiple(self) -> float:
        """
        Calculate current R-multiple.
        R = (Current Price - Entry Price) / (Entry Price - Stop Loss)
        """
        if self.side == 'long':
            risk = self.entry_price - self.stop_loss
            if risk <= 0:
                return 0.0
            profit = self.current_price - self.entry_price
            return profit / risk
        else:  # short
            risk = self.stop_loss - self.entry_price
            if risk <= 0:
                return 0.0
            profit = self.entry_price - self.current_price
            return profit / risk
    
    def update_price(self, new_price: float):
        """Update current price and recalculate metrics"""
        self.current_price = new_price
        self.r_multiple = self.calculate_r_multiple()
        
        # Calculate P/L
        if self.side == 'long':
            self.unrealized_pl = (new_price - self.entry_price) * self.quantity
        else:
            self.unrealized_pl = (self.entry_price - new_price) * self.quantity
        
        cost_basis = self.entry_price * self.quantity
        if cost_basis > 0:
            self.unrealized_pl_pct = (self.unrealized_pl / cost_basis) * 100
        
        self.last_updated = datetime.utcnow()
    
    def is_profitable(self) -> bool:
        """Check if position is currently profitable"""
        return self.unrealized_pl > 0
