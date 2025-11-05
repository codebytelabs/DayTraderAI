from typing import Optional, Tuple
from datetime import datetime
from config import settings
from core.state import trading_state, Position
from core.alpaca_client import AlpacaClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RiskManager:
    """
    Pre-trade risk checks. Every order MUST pass through here.
    No direct order submission allowed.
    """
    
    def __init__(self, alpaca_client: AlpacaClient):
        self.alpaca = alpaca_client
        self.max_positions = settings.max_positions
        self.risk_per_trade_pct = settings.risk_per_trade_pct
        self.circuit_breaker_pct = settings.circuit_breaker_pct
    
    def check_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        price: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Comprehensive pre-trade risk check.
        Returns (approved, reason)
        """
        
        # 1. Check if trading is enabled
        if not trading_state.is_trading_allowed():
            return False, "Trading is disabled"
        
        # 2. Check circuit breaker
        metrics = trading_state.get_metrics()
        if metrics.circuit_breaker_triggered:
            return False, "Circuit breaker triggered"
        
        if metrics.daily_pl_pct < -self.circuit_breaker_pct * 100:
            trading_state.update_metrics(circuit_breaker_triggered=True)
            logger.error(f"CIRCUIT BREAKER TRIGGERED: Daily loss {metrics.daily_pl_pct:.2f}%")
            return False, "Circuit breaker triggered by daily loss"
        
        # 3. Check market is open
        if not self.alpaca.is_market_open():
            return False, "Market is closed"
        
        # 4. Check position limits
        current_positions = len(trading_state.get_all_positions())
        existing_position = trading_state.get_position(symbol)
        
        if existing_position is None and current_positions >= self.max_positions:
            return False, f"Max positions reached ({self.max_positions})"
        
        # 5. Check if opening opposite position (not allowed without closing first)
        if existing_position and existing_position.side != side.lower():
            return False, f"Cannot open {side} position while holding {existing_position.side} position"
        
        # 6. Check buying power and max position size
        try:
            account = self.alpaca.get_account()
            buying_power = float(account.buying_power)
            equity = float(account.equity)
            
            if price:
                order_value = price * qty
            else:
                # Estimate for market order
                latest_bars = self.alpaca.get_latest_bars([symbol])
                if not latest_bars or symbol not in latest_bars:
                    return False, f"Cannot get price for {symbol}"
                price = float(latest_bars[symbol].close)
                order_value = price * qty
            
            if order_value > buying_power:
                return False, f"Insufficient buying power: need ${order_value:.2f}, have ${buying_power:.2f}"
            
            # Check max position size as % of equity
            max_position_value = equity * settings.max_position_pct
            if order_value > max_position_value:
                return False, f"Position too large: ${order_value:.2f} exceeds max ${max_position_value:.2f} ({settings.max_position_pct*100}% of equity)"
        
        except Exception as e:
            logger.error(f"Failed to check buying power: {e}")
            return False, "Failed to verify buying power"
        
        # 7. Check position sizing (risk per trade)
        equity = float(account.equity)
        max_risk_amount = equity * self.risk_per_trade_pct
        
        # Get features for stop loss calculation
        features = trading_state.get_features(symbol)
        if features and 'atr' in features:
            atr = features['atr']
            stop_distance = atr * settings.stop_loss_atr_mult
            risk_per_share = stop_distance
            max_qty = int(max_risk_amount / risk_per_share)
            
            if qty > max_qty:
                return False, f"Position size too large: max {max_qty} shares for {self.risk_per_trade_pct*100}% risk"
        
        # 8. Basic sanity checks
        if qty <= 0:
            return False, "Invalid quantity"
        
        if symbol not in settings.watchlist_symbols:
            return False, f"{symbol} not in watchlist"
        
        # All checks passed
        logger.info(f"Risk check PASSED: {side} {qty} {symbol}")
        return True, "Approved"
    
    def check_circuit_breaker(self):
        """Check and update circuit breaker status."""
        metrics = trading_state.get_metrics()
        
        if metrics.daily_pl_pct < -self.circuit_breaker_pct * 100:
            if not metrics.circuit_breaker_triggered:
                trading_state.update_metrics(circuit_breaker_triggered=True)
                logger.error(f"CIRCUIT BREAKER TRIGGERED: Daily loss {metrics.daily_pl_pct:.2f}%")
                return True
        
        return metrics.circuit_breaker_triggered
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker (use with caution)."""
        trading_state.update_metrics(circuit_breaker_triggered=False)
        logger.warning("Circuit breaker manually reset")
    
    def check_options_trade(self, symbol: str, cost: float, contracts: int) -> bool:
        """
        Check if an options trade is allowed.
        
        Args:
            symbol: Underlying symbol
            cost: Total cost of the options trade
            contracts: Number of contracts
            
        Returns:
            True if trade is allowed
        """
        try:
            # 1. Check if options trading is enabled
            if not settings.options_enabled:
                logger.warning("Options trading is disabled")
                return False
            
            # 2. Check circuit breaker
            if self.check_circuit_breaker():
                logger.warning("Circuit breaker active - options trade rejected")
                return False
            
            # 3. Check max options positions
            positions = trading_state.get_all_positions()
            options_positions = sum(
                1 for p in positions 
                if len(p.get('symbol', '')) > 10  # Options symbols are longer
            )
            
            if options_positions >= settings.max_options_positions:
                logger.warning(
                    f"Max options positions reached: {options_positions}/{settings.max_options_positions}"
                )
                return False
            
            # 4. Check buying power
            account = self.alpaca.get_account()
            if not account:
                logger.error("Failed to get account info")
                return False
            
            buying_power = float(account.buying_power)
            if cost > buying_power:
                logger.warning(
                    f"Insufficient buying power for options: need ${cost:.2f}, have ${buying_power:.2f}"
                )
                return False
            
            # 5. Check risk per trade
            equity = float(account.equity)
            max_risk = equity * settings.options_risk_per_trade_pct
            
            if cost > max_risk:
                logger.warning(
                    f"Options cost exceeds risk limit: ${cost:.2f} > ${max_risk:.2f}"
                )
                return False
            
            # 6. Sanity checks
            if contracts <= 0:
                logger.warning("Invalid number of contracts")
                return False
            
            if contracts > 100:  # Reasonable limit
                logger.warning(f"Too many contracts: {contracts}")
                return False
            
            logger.info(f"Options risk check PASSED: {contracts} contracts, cost ${cost:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error in options risk check: {e}", exc_info=True)
            return False
    
    def emergency_stop(self):
        """Emergency: disable trading and close all positions."""
        logger.error("EMERGENCY STOP TRIGGERED")
        trading_state.disable_trading()
        
        try:
            self.alpaca.close_all_positions()
            logger.info("All positions closed")
        except Exception as e:
            logger.error(f"Failed to close positions during emergency stop: {e}")
