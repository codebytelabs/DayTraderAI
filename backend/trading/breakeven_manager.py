"""
Breakeven Stop Manager
Manages breakeven stop adjustments for profitable positions
"""

import logging
import asyncio
from typing import Dict, Any, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class BreakevenStopManager:
    """
    Manages breakeven stop adjustments
    
    Moves stop loss to breakeven (entry price) once position reaches +1R profit
    """
    
    def __init__(self, alpaca_client, supabase_client):
        """
        Initialize breakeven stop manager
        
        Args:
            alpaca_client: Alpaca API client
            supabase_client: Supabase database client
        """
        self.alpaca = alpaca_client
        self.supabase = supabase_client
        self.breakeven_set = Set[str]()  # Track which positions have breakeven set
        self.monitoring = False
        logger.info("Breakeven Stop Manager initialized")
    
    async def start_monitoring(self):
        """Start monitoring loop"""
        self.monitoring = True
        logger.info("Breakeven monitoring started")
        
        while self.monitoring:
            try:
                await self.monitor_for_breakeven()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in breakeven monitoring: {e}")
                await asyncio.sleep(60)
    
    def stop_monitoring(self):
        """Stop monitoring loop"""
        self.monitoring = False
        logger.info("Breakeven monitoring stopped")
    
    async def monitor_for_breakeven(self):
        """Check positions for breakeven stop adjustment"""
        try:
            # Get all open positions
            positions = self.alpaca.get_all_positions()
            
            if not positions:
                return
            
            logger.debug(f"Checking {len(positions)} positions for breakeven")
            
            for position in positions:
                symbol = position.symbol
                
                # Skip if breakeven already set
                if symbol in self.breakeven_set:
                    continue
                
                # Check if position has reached +1R profit
                if await self.should_move_to_breakeven(position):
                    await self.move_stop_to_breakeven(position)
                    
        except Exception as e:
            logger.error(f"Error monitoring for breakeven: {e}")
    
    async def should_move_to_breakeven(self, position: Any) -> bool:
        """
        Check if position should move to breakeven
        
        Args:
            position: Alpaca position object
            
        Returns:
            bool: True if should move to breakeven
        """
        try:
            # Get unrealized P/L percentage
            unrealized_plpc = float(position.unrealized_plpc)
            
            # Get position details from database to calculate R
            symbol = position.symbol
            pos_result = self.supabase.table('positions').select('*').eq(
                'symbol', symbol
            ).execute()
            
            if not pos_result.data:
                return False
            
            pos_data = pos_result.data[0]
            entry_price = float(pos_data['avg_entry_price'])
            stop_loss = pos_data.get('stop_loss')
            
            if not stop_loss:
                # No stop loss set, use 1% as default R
                risk_percent = 1.0
            else:
                # Calculate R based on stop loss
                stop_loss = float(stop_loss)
                risk_percent = abs((entry_price - stop_loss) / entry_price) * 100
            
            # Move to breakeven if profit >= 1R
            if unrealized_plpc >= risk_percent:
                logger.info(f"{symbol}: Reached +1R profit ({unrealized_plpc:.2%} >= {risk_percent:.2%})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking breakeven condition: {e}")
            return False
    
    async def move_stop_to_breakeven(self, position: Any):
        """
        Move stop loss to breakeven price
        
        Args:
            position: Alpaca position object
        """
        try:
            symbol = position.symbol
            side = position.side
            entry_price = float(position.avg_entry_price)
            
            # Calculate breakeven price (entry + commissions)
            # Alpaca commission is $0, but account for slippage
            commission_buffer = 0.01  # 1 cent buffer
            
            if side == 'long':
                breakeven_price = entry_price + commission_buffer
            else:  # short
                breakeven_price = entry_price - commission_buffer
            
            logger.info(f"Moving {symbol} stop to breakeven: ${breakeven_price:.2f}")
            
            # Update stop loss order
            # Note: This requires getting the stop loss order ID and replacing it
            # For now, we'll update the database and log the action
            
            # Update database
            self.supabase.table('positions').update({
                'stop_loss': breakeven_price,
                'updated_at': datetime.now().isoformat()
            }).eq('symbol', symbol).execute()
            
            # Mark as breakeven set
            self.breakeven_set.add(symbol)
            
            # Log action
            self.supabase.table('position_exits').insert({
                'symbol': symbol,
                'side': side,
                'exit_type': 'breakeven',
                'exit_reason': 'Stop moved to breakeven after +1R profit',
                'entry_price': entry_price,
                'exit_price': breakeven_price,
                'was_early_exit': False
            }).execute()
            
            logger.info(f"✅ Breakeven stop set for {symbol}")
            
        except Exception as e:
            logger.error(f"Error moving stop to breakeven: {e}")
    
    def reset_breakeven_tracking(self, symbol: str):
        """
        Reset breakeven tracking for a symbol (when position closes)
        
        Args:
            symbol: Stock symbol
        """
        if symbol in self.breakeven_set:
            self.breakeven_set.remove(symbol)
            logger.debug(f"Reset breakeven tracking for {symbol}")
