"""
Profit Protection Manager

Main integration point for the Intelligent Profit Protection System.
Coordinates position tracking, stop management, and profit taking.
"""

import threading
import time
from typing import Optional
from datetime import datetime

from .position_state_tracker import get_position_tracker
from .intelligent_stop_manager import get_stop_manager
from .profit_taking_engine import get_profit_engine
from core.alpaca_client import AlpacaClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ProfitProtectionManager:
    """
    Main manager that integrates profit protection with the trading system.
    Runs monitoring loop and coordinates all profit protection activities.
    """
    
    def __init__(self, alpaca_client: AlpacaClient):
        self.alpaca = alpaca_client
        self.tracker = get_position_tracker()
        self.stop_manager = get_stop_manager(alpaca_client)
        self.profit_engine = get_profit_engine(alpaca_client)
        
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        logger.info("✅ Profit Protection Manager initialized")
    
    def start(self):
        """Start the profit protection monitoring loop"""
        if self.running:
            logger.warning("Profit protection already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("🚀 Profit protection monitoring started")
    
    def stop(self):
        """Stop the profit protection monitoring loop"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("⏹️  Profit protection monitoring stopped")
    
    def track_new_position(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        quantity: int,
        side: str = 'long'
    ):
        """
        Start tracking a new position.
        
        Args:
            symbol: Stock symbol
            entry_price: Entry price
            stop_loss: Initial stop loss
            quantity: Number of shares
            side: 'long' or 'short'
        """
        try:
            position_state = self.tracker.track_position(
                symbol=symbol,
                entry_price=entry_price,
                stop_loss=stop_loss,
                quantity=quantity,
                side=side
            )
            
            logger.info(
                f"📊 Now tracking {symbol}: Entry ${entry_price:.2f}, "
                f"Stop ${stop_loss:.2f}, Qty {quantity}"
            )
            
            return position_state
            
        except Exception as e:
            logger.error(f"Error tracking position {symbol}: {e}")
            return None
    
    def remove_position(self, symbol: str):
        """Stop tracking a position"""
        try:
            self.tracker.remove_position(symbol)
            logger.info(f"Stopped tracking {symbol}")
        except Exception as e:
            logger.error(f"Error removing position {symbol}: {e}")
    
    def _monitoring_loop(self):
        """
        Main monitoring loop - runs every 1 second.
        Checks all positions for stop updates and profit milestones.
        """
        logger.info("🔄 Profit protection monitoring loop started")
        
        while self.running:
            try:
                # Get all tracked positions
                positions = self.tracker.get_all_positions()
                
                if not positions:
                    time.sleep(1)
                    continue
                
                # Update current prices for all positions
                self._update_position_prices(positions)
                
                # Check for stop updates needed
                self._check_stop_updates(positions)
                
                # Check for profit taking opportunities
                self._check_profit_milestones(positions)
                
                # Sleep for 1 second
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in profit protection monitoring loop: {e}")
                time.sleep(1)
    
    def _update_position_prices(self, positions: dict):
        """Update current prices for all positions"""
        try:
            # Get current prices from Alpaca
            for symbol in positions.keys():
                try:
                    # Get latest trade price
                    position = self.alpaca.get_position(symbol)
                    if position:
                        current_price = float(position.current_price)
                        self.tracker.update_current_price(symbol, current_price)
                except Exception as e:
                    logger.debug(f"Could not update price for {symbol}: {e}")
                    
        except Exception as e:
            logger.error(f"Error updating position prices: {e}")
    
    def _check_stop_updates(self, positions: dict):
        """Check if any positions need stop loss updates"""
        try:
            updates_needed = self.stop_manager.check_all_positions_for_updates()
            
            if updates_needed:
                logger.info(f"Found {len(updates_needed)} positions needing stop updates")
                
                for symbol, reason in updates_needed.items():
                    position_state = positions.get(symbol)
                    if position_state:
                        result = self.stop_manager.update_stop_for_position(position_state)
                        
                        if result.success:
                            logger.info(f"✅ {symbol}: {result.message}")
                        else:
                            logger.warning(f"⚠️  {symbol}: {result.message}")
                        
        except Exception as e:
            logger.error(f"Error checking stop updates: {e}")
    
    def _check_profit_milestones(self, positions: dict):
        """Check if any positions have reached profit milestones"""
        try:
            actions = self.profit_engine.check_all_positions_for_milestones()
            
            if actions:
                logger.info(f"Found {len(actions)} profit taking opportunities")
                
                for action in actions:
                    result = self.profit_engine.execute_partial_exit(
                        symbol=action.symbol,
                        quantity=action.quantity,
                        reason=action.reason
                    )
                    
                    if result.success:
                        logger.info(
                            f"💰 {action.symbol}: Took profit - {result.shares_sold} shares, "
                            f"${result.profit_realized:.2f} profit"
                        )
                    else:
                        logger.warning(f"⚠️  {action.symbol}: {result.message}")
                        
        except Exception as e:
            logger.error(f"Error checking profit milestones: {e}")
    
    def get_position_summary(self, symbol: str) -> dict:
        """Get complete summary for a position"""
        try:
            position_state = self.tracker.get_position_state(symbol)
            if not position_state:
                return {}
            
            profit_summary = self.profit_engine.get_profit_summary(symbol)
            
            return {
                'symbol': symbol,
                'entry_price': position_state.entry_price,
                'current_price': position_state.current_price,
                'stop_loss': position_state.stop_loss,
                'r_multiple': position_state.r_multiple,
                'unrealized_pl': position_state.unrealized_pl,
                'unrealized_pl_pct': position_state.unrealized_pl_pct,
                'protection_state': position_state.protection_state.state.value,
                'original_quantity': position_state.share_allocation.original_quantity,
                'remaining_quantity': position_state.share_allocation.remaining_quantity,
                'profit_summary': profit_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting position summary for {symbol}: {e}")
            return {}
    
    def sync_existing_positions(self):
        """
        Sync existing open positions from Alpaca.
        Call this on startup to track positions that are already open.
        """
        try:
            positions = self.alpaca.get_positions()
            
            for position in positions:
                symbol = position.symbol
                entry_price = float(position.avg_entry_price)
                current_price = float(position.current_price)
                quantity = int(position.qty)
                side = 'long' if int(position.qty) > 0 else 'short'
                
                # Try to find existing stop loss order
                orders = self.alpaca.get_orders(symbols=[symbol], status='open')
                stop_loss = None
                
                for order in orders:
                    if str(order.order_type).lower() == 'stop':
                        stop_loss = float(order.stop_price)
                        break
                
                # If no stop loss found, calculate a default one (2% risk)
                if stop_loss is None:
                    if side == 'long':
                        stop_loss = entry_price * 0.98
                    else:
                        stop_loss = entry_price * 1.02
                
                # Track the position
                self.track_new_position(
                    symbol=symbol,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    quantity=quantity,
                    side=side
                )
                
                # Update to current price
                self.tracker.update_current_price(symbol, current_price)
                
            logger.info(f"✅ Synced {len(positions)} existing positions")
            
        except Exception as e:
            logger.error(f"Error syncing existing positions: {e}")


# Global instance
_profit_protection_manager: Optional[ProfitProtectionManager] = None


def get_profit_protection_manager(alpaca_client: AlpacaClient) -> ProfitProtectionManager:
    """Get or create the global profit protection manager instance."""
    global _profit_protection_manager
    
    if _profit_protection_manager is None:
        _profit_protection_manager = ProfitProtectionManager(alpaca_client)
    
    return _profit_protection_manager
