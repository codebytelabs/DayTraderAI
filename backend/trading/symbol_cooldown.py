"""
Symbol Cooldown Manager - Sprint 6 Enhancement

Implements industry-standard cooldown periods after consecutive losses
to prevent overtrading and whipsaws on problematic symbols.

Research-backed thresholds:
- 2 consecutive losses → 24-hour cooldown
- 3+ consecutive losses → 48-hour cooldown
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from core.supabase_client import SupabaseClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SymbolCooldownManager:
    """
    Manages symbol-level cooldowns after consecutive losses.
    
    Features:
    - Tracks consecutive losses per symbol
    - Enforces 24-48 hour cooldowns
    - Reduces position sizes after cooldown expires
    - Increases confidence thresholds for re-entry
    """
    
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client
        self.cooldowns: Dict[str, dict] = {}  # In-memory cache
        self._load_cooldowns()
    
    def _load_cooldowns(self):
        """Load active cooldowns from database on startup."""
        try:
            # Get recent trades to calculate consecutive losses
            trades = self.supabase.get_trades(limit=200)
            
            # Group by symbol and check for consecutive losses
            symbol_trades = {}
            for trade in trades:
                symbol = trade.get('symbol')
                if not symbol:
                    continue
                
                if symbol not in symbol_trades:
                    symbol_trades[symbol] = []
                
                symbol_trades[symbol].append({
                    'timestamp': trade.get('exit_time', trade.get('timestamp')),
                    'pnl': trade.get('pnl', 0),
                    'reason': trade.get('reason', '')
                })
            
            # Check each symbol for consecutive losses
            for symbol, trades_list in symbol_trades.items():
                # Sort by timestamp (most recent first)
                sorted_trades = sorted(trades_list, key=lambda x: x['timestamp'], reverse=True)
                
                # Count consecutive losses from most recent
                consecutive_losses = 0
                for trade in sorted_trades:
                    if trade['pnl'] < 0 and 'stop_loss' in trade['reason']:
                        consecutive_losses += 1
                    else:
                        break  # Stop at first win
                
                # Apply cooldown if needed
                if consecutive_losses >= 2:
                    self._apply_cooldown(symbol, consecutive_losses, from_startup=True)
            
            logger.info(f"✓ Cooldown manager initialized: {len(self.cooldowns)} active cooldowns")
            
        except Exception as e:
            logger.error(f"Failed to load cooldowns: {e}")
    
    def _apply_cooldown(self, symbol: str, consecutive_losses: int, from_startup: bool = False):
        """Apply cooldown to a symbol."""
        # Determine cooldown duration
        if consecutive_losses >= 3:
            cooldown_hours = 48
        else:
            cooldown_hours = 24
        
        cooldown_until = datetime.utcnow() + timedelta(hours=cooldown_hours)
        
        self.cooldowns[symbol] = {
            'consecutive_losses': consecutive_losses,
            'cooldown_until': cooldown_until,
            'cooldown_hours': cooldown_hours,
            'applied_at': datetime.utcnow()
        }
        
        if not from_startup:
            logger.warning(
                f"🚫 COOLDOWN APPLIED: {symbol} frozen for {cooldown_hours}h "
                f"after {consecutive_losses} consecutive losses"
            )
    
    def record_trade_result(self, symbol: str, pnl: float, reason: str):
        """
        Record a trade result and update cooldown status.
        
        Args:
            symbol: Stock symbol
            pnl: Profit/loss amount
            reason: Exit reason (stop_loss, take_profit, etc.)
        """
        try:
            # Get recent trades for this symbol
            all_trades = self.supabase.get_trades(limit=100)
            symbol_trades = [t for t in all_trades if t.get('symbol') == symbol]
            
            # Sort by timestamp (most recent first)
            sorted_trades = sorted(
                symbol_trades,
                key=lambda x: x.get('exit_time', x.get('timestamp', '')),
                reverse=True
            )
            
            # Count consecutive losses (including this one)
            consecutive_losses = 0
            for trade in sorted_trades:
                if trade.get('pnl', 0) < 0 and 'stop_loss' in trade.get('reason', ''):
                    consecutive_losses += 1
                else:
                    break
            
            # If this trade was a loss, check if we need cooldown
            if pnl < 0 and 'stop_loss' in reason:
                if consecutive_losses >= 2:
                    self._apply_cooldown(symbol, consecutive_losses)
            
            # If this trade was a win, clear cooldown
            elif pnl > 0:
                if symbol in self.cooldowns:
                    logger.info(f"✅ Cooldown cleared for {symbol} after winning trade")
                    del self.cooldowns[symbol]
            
        except Exception as e:
            logger.error(f"Failed to record trade result for {symbol}: {e}")
    
    def is_symbol_allowed(self, symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a symbol is allowed to trade (not in cooldown).
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            Tuple of (is_allowed, reason_if_blocked)
        """
        if symbol not in self.cooldowns:
            return True, None
        
        cooldown_info = self.cooldowns[symbol]
        cooldown_until = cooldown_info['cooldown_until']
        
        # Check if cooldown has expired
        if datetime.utcnow() >= cooldown_until:
            logger.info(f"✅ Cooldown expired for {symbol}")
            del self.cooldowns[symbol]
            return True, None
        
        # Still in cooldown
        time_remaining = cooldown_until - datetime.utcnow()
        hours_remaining = time_remaining.total_seconds() / 3600
        
        reason = (
            f"Symbol in cooldown for {hours_remaining:.1f}h more "
            f"({cooldown_info['consecutive_losses']} consecutive losses)"
        )
        
        return False, reason
    
    def get_position_size_multiplier(self, symbol: str) -> float:
        """
        Get position size multiplier for a symbol after cooldown expires.
        
        Returns:
            1.0 = normal size
            0.5 = 50% size (after 2 losses)
            0.25 = 25% size (after 3+ losses)
        """
        if symbol not in self.cooldowns:
            return 1.0
        
        consecutive_losses = self.cooldowns[symbol]['consecutive_losses']
        
        if consecutive_losses >= 3:
            return 0.25  # 75% reduction
        elif consecutive_losses >= 2:
            return 0.5   # 50% reduction
        
        return 1.0
    
    def get_confidence_boost_required(self, symbol: str) -> float:
        """
        Get additional confidence score required for a symbol after cooldown.
        
        Returns:
            0 = no boost required
            10 = +10 points required (after 2 losses)
            20 = +20 points required (after 3+ losses)
        """
        if symbol not in self.cooldowns:
            return 0.0
        
        consecutive_losses = self.cooldowns[symbol]['consecutive_losses']
        
        if consecutive_losses >= 3:
            return 20.0
        elif consecutive_losses >= 2:
            return 10.0
        
        return 0.0
    
    def get_active_cooldowns(self) -> Dict[str, dict]:
        """Get all active cooldowns for monitoring."""
        active = {}
        now = datetime.utcnow()
        
        for symbol, info in list(self.cooldowns.items()):
            if now < info['cooldown_until']:
                time_remaining = info['cooldown_until'] - now
                active[symbol] = {
                    'consecutive_losses': info['consecutive_losses'],
                    'hours_remaining': time_remaining.total_seconds() / 3600,
                    'cooldown_until': info['cooldown_until'].isoformat()
                }
            else:
                # Expired, remove it
                del self.cooldowns[symbol]
        
        return active
    
    def clear_cooldown(self, symbol: str):
        """Manually clear a cooldown (for testing or manual intervention)."""
        if symbol in self.cooldowns:
            logger.info(f"🔓 Manually cleared cooldown for {symbol}")
            del self.cooldowns[symbol]
            return True
        return False
