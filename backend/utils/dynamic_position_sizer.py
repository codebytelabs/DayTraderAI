"""
Dynamic Position Sizer - Adapts to available buying power and market conditions.
"""

from typing import Tuple
from core.alpaca_client import AlpacaClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DynamicPositionSizer:
    """
    Intelligently sizes positions based on:
    1. Available buying power
    2. Risk management rules
    3. Market conditions
    4. Existing positions
    """
    
    def __init__(self, alpaca_client: AlpacaClient):
        self.alpaca = alpaca_client
        
    def calculate_optimal_size(
        self,
        symbol: str,
        price: float,
        stop_distance: float,
        confidence: float,
        base_risk_pct: float = 0.01,
        max_position_pct: float = 0.10
    ) -> Tuple[int, str]:
        """
        Calculate optimal position size considering all constraints.
        
        Args:
            symbol: Stock symbol
            price: Entry price
            stop_distance: Actual stop distance in dollars (e.g., |entry - stop|)
            confidence: Signal confidence (0-100)
            base_risk_pct: Base risk percentage of equity
            max_position_pct: Maximum position size as % of equity
        
        Returns:
            (quantity, reasoning)
        """
        try:
            account = self.alpaca.get_account()
            equity = float(account.equity)
            cash = float(account.cash)
            regular_bp = float(account.buying_power)
            daytrading_bp = float(account.daytrading_buying_power)
            
            # Use the best available buying power source
            if account.pattern_day_trader and daytrading_bp > 0:
                available_bp = daytrading_bp
            else:
                # Fallback: use cash or regular buying power (whichever is higher)
                # This handles cases where daytrading_buying_power is 0 or account is not PDT
                available_bp = max(cash, regular_bp)
            
            logger.info(f"Account status for {symbol}: Equity=${equity:,.0f}, Cash=${cash:,.0f}, RegularBP=${regular_bp:,.0f}, DayTradingBP=${daytrading_bp:,.0f}, PDT={account.pattern_day_trader}")
            logger.info(f"  Using BP: ${available_bp:,.0f}")
            
            # 1. Calculate base position size from risk using ACTUAL stop distance
            # NOTE: base_risk_pct is already adjusted for confidence in strategy.py
            # Do NOT apply confidence scaling again here!
            risk_amount = equity * base_risk_pct
            
            # Use actual stop distance from strategy (no assumptions!)
            risk_based_qty = int(risk_amount / stop_distance)
            
            # 2. Calculate buying power constraint (with 20% buffer)
            bp_buffer = 0.8
            max_bp_qty = int((available_bp * bp_buffer) / price)
            
            # 3. Calculate equity constraint
            max_equity_value = equity * max_position_pct
            max_equity_qty = int(max_equity_value / price)
            
            # 4. Take the minimum of all constraints
            constraints = {
                'risk': risk_based_qty,
                'buying_power': max_bp_qty,
                'equity': max_equity_qty
            }
            
            # Find the limiting factor
            limiting_factor = min(constraints, key=constraints.get)
            final_qty = constraints[limiting_factor]
            
            # DEBUG: Log all constraints
            logger.info(f"Position sizing for {symbol}: risk={risk_based_qty}, bp={max_bp_qty}, equity={max_equity_qty}, final={final_qty}, limiting={limiting_factor}")
            logger.info(f"  Risk calc: ${risk_amount:.2f} / ${stop_distance:.2f} = {risk_based_qty} shares")
            
            # 5. Ensure minimum viable size (0.5% of equity minimum for meaningful positions)
            min_position_value = equity * 0.005  # 0.5% of equity minimum
            min_qty = max(1, int(min_position_value / price))
            
            if final_qty < min_qty:
                logger.warning(f"Position size {final_qty} below minimum {min_qty} shares (${min_position_value:.0f} min position)")
                return 0, f"Position too small: {final_qty} < {min_qty} minimum (risk_amount=${risk_amount:.2f}, stop_distance=${stop_distance:.2f})"
            
            # 6. Generate reasoning
            reasoning = self._generate_reasoning(
                symbol, price, final_qty, limiting_factor, 
                available_bp, equity, confidence, constraints
            )
            
            return final_qty, reasoning
            
        except Exception as e:
            logger.error(f"Error calculating position size for {symbol}: {e}")
            return 0, f"Calculation error: {e}"
    
    def _generate_reasoning(
        self, symbol: str, price: float, qty: int, limiting_factor: str,
        available_bp: float, equity: float, confidence: float, constraints: dict
    ) -> str:
        """Generate human-readable reasoning for position size."""
        
        position_value = qty * price
        
        reasoning = [
            f"Position: {qty} shares × ${price:.2f} = ${position_value:,.0f}",
            f"Confidence: {confidence:.0f}%",
            f"Available BP: ${available_bp:,.0f}",
            f"Limited by: {limiting_factor}"
        ]
        
        # Add constraint details
        if limiting_factor == 'buying_power':
            bp_usage = (position_value / available_bp) * 100
            reasoning.append(f"BP usage: {bp_usage:.1f}%")
        elif limiting_factor == 'equity':
            equity_usage = (position_value / equity) * 100
            reasoning.append(f"Equity usage: {equity_usage:.1f}%")
        elif limiting_factor == 'risk':
            reasoning.append(f"Risk-based sizing")
        
        return " | ".join(reasoning)
    
    def get_buying_power_status(self) -> dict:
        """Get current buying power status."""
        try:
            account = self.alpaca.get_account()
            positions = self.alpaca.get_positions()
            
            total_position_value = sum(abs(float(pos.market_value)) for pos in positions)
            
            return {
                'equity': float(account.equity),
                'day_trading_bp': float(account.daytrading_buying_power),
                'regular_bp': float(account.buying_power),
                'cash': float(account.cash),
                'positions_count': len(positions),
                'positions_value': total_position_value,
                'is_pdt': account.pattern_day_trader
            }
        except Exception as e:
            logger.error(f"Error getting buying power status: {e}")
            return {}