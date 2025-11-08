"""
Exit Monitor
Monitors positions for early exit conditions
"""

import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ExitMonitor:
    """
    Monitors positions for early exit conditions
    
    Exit triggers:
    - Volume dried up (< 50% of entry volume)
    - Time limit (15 min with no profit)
    - Momentum reversal (MACD cross against position)
    """
    
    def __init__(self, alpaca_client, supabase_client, market_data):
        """
        Initialize exit monitor
        
        Args:
            alpaca_client: Alpaca API client
            supabase_client: Supabase database client
            market_data: Market data provider
        """
        self.alpaca = alpaca_client
        self.supabase = supabase_client
        self.market_data = market_data
        self.monitoring = False
        logger.info("Exit Monitor initialized")
    
    async def start_monitoring(self):
        """Start monitoring loop"""
        self.monitoring = True
        logger.info("Exit monitoring started")
        
        while self.monitoring:
            try:
                await self.monitor_positions()
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)
    
    def stop_monitoring(self):
        """Stop monitoring loop"""
        self.monitoring = False
        logger.info("Exit monitoring stopped")
    
    async def monitor_positions(self):
        """Main monitoring loop - checks all positions"""
        try:
            # Get all open positions
            positions = self.alpaca.get_all_positions()
            
            if not positions:
                return
            
            logger.debug(f"Monitoring {len(positions)} positions")
            
            for position in positions:
                # Check each exit condition
                if await self.check_volume_exit(position):
                    await self.execute_early_exit(position, 'volume')
                elif await self.check_time_exit(position):
                    await self.execute_early_exit(position, 'time')
                elif await self.check_momentum_exit(position):
                    await self.execute_early_exit(position, 'momentum')
                    
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
    
    async def check_volume_exit(self, position: Any) -> bool:
        """
        Check if volume has dried up
        
        Args:
            position: Alpaca position object
            
        Returns:
            bool: True if should exit due to low volume
        """
        try:
            symbol = position.symbol
            
            # Get current volume
            current_bar = await self.market_data.get_latest_bar(symbol)
            if not current_bar:
                return False
            
            current_volume = current_bar.get('volume', 0)
            
            # Get entry volume from database
            trade_result = self.supabase.table('trades').select('*').eq(
                'symbol', symbol
            ).order('entry_time', desc=True).limit(1).execute()
            
            if not trade_result.data:
                return False
            
            # For now, use average volume as proxy for entry volume
            # TODO: Store entry volume in trades table
            avg_volume = await self.market_data.get_average_volume(symbol, periods=20)
            
            if avg_volume and current_volume < (avg_volume * 0.5):
                logger.info(f"{symbol}: Volume dried up ({current_volume} < {avg_volume * 0.5})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking volume exit: {e}")
            return False
    
    async def check_time_exit(self, position: Any) -> bool:
        """
        Check if position should exit due to time
        
        Args:
            position: Alpaca position object
            
        Returns:
            bool: True if should exit due to time limit
        """
        try:
            # Check if position is profitable
            unrealized_plpc = float(position.unrealized_plpc)
            if unrealized_plpc > 0:
                return False  # Don't exit profitable positions
            
            # Get position entry time from database
            symbol = position.symbol
            trade_result = self.supabase.table('positions').select('entry_time').eq(
                'symbol', symbol
            ).execute()
            
            if not trade_result.data:
                return False
            
            entry_time = datetime.fromisoformat(trade_result.data[0]['entry_time'].replace('Z', '+00:00'))
            time_elapsed = datetime.now(entry_time.tzinfo) - entry_time
            
            # Exit if 15+ minutes and no profit
            if time_elapsed >= timedelta(minutes=15):
                logger.info(f"{symbol}: Time limit reached ({time_elapsed.seconds // 60} min, no profit)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking time exit: {e}")
            return False
    
    async def check_momentum_exit(self, position: Any) -> bool:
        """
        Check if momentum has reversed
        
        Args:
            position: Alpaca position object
            
        Returns:
            bool: True if should exit due to momentum reversal
        """
        try:
            symbol = position.symbol
            side = position.side
            
            # Get current MACD
            indicators = await self.market_data.get_indicators(symbol)
            if not indicators:
                return False
            
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            
            # Check for reversal
            if side == 'long' and macd < macd_signal:
                logger.info(f"{symbol}: Bearish MACD cross (long position)")
                return True
            elif side == 'short' and macd > macd_signal:
                logger.info(f"{symbol}: Bullish MACD cross (short position)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking momentum exit: {e}")
            return False
    
    async def execute_early_exit(self, position: Any, reason: str):
        """
        Execute early exit and log to database
        
        Args:
            position: Alpaca position object
            reason: Exit reason ('volume', 'time', 'momentum')
        """
        try:
            symbol = position.symbol
            logger.info(f"Executing early exit for {symbol}: {reason}")
            
            # Close position
            self.alpaca.close_position(symbol)
            
            # Get position details
            qty = int(position.qty)
            side = position.side
            entry_price = float(position.avg_entry_price)
            current_price = float(position.current_price)
            unrealized_pl = float(position.unrealized_pl)
            unrealized_plpc = float(position.unrealized_plpc)
            
            # Get entry time
            pos_result = self.supabase.table('positions').select('entry_time').eq(
                'symbol', symbol
            ).execute()
            
            entry_time = None
            if pos_result.data:
                entry_time = pos_result.data[0]['entry_time']
                time_elapsed = (datetime.now() - datetime.fromisoformat(
                    entry_time.replace('Z', '+00:00')
                )).seconds // 60
            else:
                time_elapsed = 0
            
            # Log exit to database
            self.supabase.table('position_exits').insert({
                'symbol': symbol,
                'side': side,
                'exit_type': reason,
                'exit_reason': f"Early exit: {reason}",
                'entry_price': entry_price,
                'exit_price': current_price,
                'quantity': qty,
                'hold_time_minutes': time_elapsed,
                'pnl_dollars': unrealized_pl,
                'pnl_percent': unrealized_plpc,
                'was_early_exit': True
            }).execute()
            
            logger.info(f"Early exit executed: {symbol} ({reason}), P/L: {unrealized_plpc:.2%}")
            
        except Exception as e:
            logger.error(f"Error executing early exit: {e}")
