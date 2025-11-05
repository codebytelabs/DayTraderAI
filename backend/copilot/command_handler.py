"""
Command Handler - Processes slash commands and portfolio actions.
"""

from typing import Any, Dict, List, Optional
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CommandHandler:
    """Handles slash commands and portfolio actions."""
    
    def __init__(self, alpaca_client):
        self.alpaca = alpaca_client
        self.watchlist = list(settings.watchlist_symbols)  # Runtime watchlist
        self.default_watchlist = list(settings.watchlist_symbols)  # Original from .env
    
    def is_command(self, query: str) -> bool:
        """Check if query is a command."""
        return query.strip().startswith('/') or query.strip().startswith('#')
    
    def parse_command(self, query: str) -> Dict[str, Any]:
        """Parse command from query."""
        query = query.strip()
        
        if query.startswith('/'):
            return self._parse_slash_command(query)
        elif query.startswith('#'):
            return self._parse_portfolio_action(query)
        
        return {"type": "unknown", "raw": query}
    
    def _parse_slash_command(self, query: str) -> Dict[str, Any]:
        """Parse slash command."""
        parts = query[1:].split()
        command = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        return {
            "type": "slash_command",
            "command": command,
            "args": args,
            "raw": query
        }
    
    def _parse_portfolio_action(self, query: str) -> Dict[str, Any]:
        """Parse portfolio action."""
        parts = query[1:].split()
        
        if not parts:
            return {"type": "portfolio_action", "action": "list", "raw": query}
        
        symbol_or_action = parts[0].upper()
        action = parts[1].lower() if len(parts) > 1 else "info"
        params = parts[2:] if len(parts) > 2 else []
        
        return {
            "type": "portfolio_action",
            "symbol": symbol_or_action,
            "action": action,
            "params": params,
            "raw": query
        }
    
    async def execute_portfolio_action(
        self, 
        parsed: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute portfolio action."""
        symbol = parsed.get("symbol")
        action = parsed.get("action")
        params = parsed.get("params", [])
        
        try:
            # Close position
            if action == "close":
                return await self._close_position(symbol, context)
            
            # Close all positions
            elif symbol == "CLOSE-ALL" and action == "info":
                return await self._close_all_positions(context)
            
            # Cancel all orders
            elif symbol == "CANCEL-ALL" and action == "info":
                return await self._cancel_all_orders(context)
            
            # Get position info
            elif action == "info":
                return self._get_position_info(symbol, context)
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown action: {action}",
                    "action": action
                }
        
        except Exception as e:
            logger.error(f"Error executing portfolio action: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
    
    async def _close_position(self, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Close a position."""
        positions = context.get("position_details", [])
        position = next((p for p in positions if p.get("symbol") == symbol), None)
        
        if not position:
            return {
                "success": False,
                "message": f"No position found for {symbol}"
            }
        
        qty = position.get("qty", 0)
        side = "sell" if qty > 0 else "buy"
        
        try:
            # Place market order to close
            order = self.alpaca.submit_order(
                symbol=symbol,
                qty=abs(qty),
                side=side,
                type="market",
                time_in_force="day"
            )
            
            return {
                "success": True,
                "message": f"Closing {qty} shares of {symbol}",
                "order_id": order.id,
                "symbol": symbol,
                "qty": qty,
                "side": side
            }
        
        except Exception as e:
            logger.error(f"Error closing position {symbol}: {e}")
            return {
                "success": False,
                "message": f"Failed to close {symbol}: {str(e)}",
                "error": str(e)
            }
    
    async def _close_all_positions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Close all positions."""
        positions = context.get("position_details", [])
        
        if not positions:
            return {
                "success": True,
                "message": "No positions to close"
            }
        
        results = []
        for position in positions:
            result = await self._close_position(position.get("symbol"), context)
            results.append(result)
        
        successful = sum(1 for r in results if r.get("success"))
        
        return {
            "success": True,
            "message": f"Closed {successful}/{len(positions)} positions",
            "results": results
        }
    
    async def _cancel_all_orders(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel all orders."""
        try:
            self.alpaca.cancel_all_orders()
            
            return {
                "success": True,
                "message": "All orders cancelled"
            }
        
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
            return {
                "success": False,
                "message": f"Failed to cancel orders: {str(e)}",
                "error": str(e)
            }
    
    def _get_position_info(self, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get position information."""
        positions = context.get("position_details", [])
        position = next((p for p in positions if p.get("symbol") == symbol), None)
        
        if not position:
            return {
                "success": False,
                "message": f"No position found for {symbol}"
            }
        
        return {
            "success": True,
            "message": f"Position info for {symbol}",
            "position": position
        }
    
    # Watchlist Management
    
    def get_watchlist(self) -> List[str]:
        """Get current watchlist."""
        return self.watchlist.copy()
    
    def view_watchlist(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """View watchlist with stats."""
        try:
            positions = context.get("position_details", [])
            position_symbols = {p.get("symbol") for p in positions}
            
            watchlist_data = []
            for symbol in self.watchlist:
                has_position = symbol in position_symbols
                watchlist_data.append({
                    "symbol": symbol,
                    "has_position": has_position
                })
            
            return {
                "success": True,
                "message": f"Current watchlist ({len(self.watchlist)} symbols)",
                "watchlist": watchlist_data,
                "total_symbols": len(self.watchlist),
                "active_positions": len(position_symbols & set(self.watchlist))
            }
        except Exception as e:
            logger.error(f"Error viewing watchlist: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def add_to_watchlist(self, symbols: List[str]) -> Dict[str, Any]:
        """Add symbols to watchlist."""
        try:
            added = []
            already_exists = []
            invalid = []
            
            for symbol in symbols:
                symbol = symbol.upper().strip()
                
                # Basic validation
                if not symbol.isalpha() or len(symbol) > 6:
                    invalid.append(symbol)
                    continue
                
                if symbol in self.watchlist:
                    already_exists.append(symbol)
                else:
                    self.watchlist.append(symbol)
                    added.append(symbol)
            
            message_parts = []
            if added:
                message_parts.append(f"✅ Added to watchlist: {', '.join(added)}")
            if already_exists:
                message_parts.append(f"ℹ️ Already in watchlist: {', '.join(already_exists)}")
            if invalid:
                message_parts.append(f"❌ Invalid symbols: {', '.join(invalid)}")
            
            message_parts.append(f"\nCurrent watchlist: {', '.join(self.watchlist)} ({len(self.watchlist)} symbols)")
            message_parts.append("\n⚠️ Note: Changes persist until backend restart. To make permanent, update .env file.")
            
            return {
                "success": True,
                "message": "\n".join(message_parts),
                "added": added,
                "already_exists": already_exists,
                "invalid": invalid,
                "watchlist": self.watchlist.copy()
            }
        except Exception as e:
            logger.error(f"Error adding to watchlist: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def remove_from_watchlist(self, symbols: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Remove symbols from watchlist."""
        try:
            removed = []
            not_found = []
            has_positions = []
            
            positions = context.get("position_details", [])
            position_symbols = {p.get("symbol") for p in positions}
            
            for symbol in symbols:
                symbol = symbol.upper().strip()
                
                if symbol not in self.watchlist:
                    not_found.append(symbol)
                else:
                    self.watchlist.remove(symbol)
                    removed.append(symbol)
                    
                    if symbol in position_symbols:
                        has_positions.append(symbol)
            
            message_parts = []
            if removed:
                message_parts.append(f"✅ Removed from watchlist: {', '.join(removed)}")
            if not_found:
                message_parts.append(f"ℹ️ Not in watchlist: {', '.join(not_found)}")
            if has_positions:
                message_parts.append(f"\n⚠️ Warning: You have open positions in {', '.join(has_positions)}. They will NOT be automatically closed.")
            
            message_parts.append(f"\nCurrent watchlist: {', '.join(self.watchlist)} ({len(self.watchlist)} symbols)")
            
            return {
                "success": True,
                "message": "\n".join(message_parts),
                "removed": removed,
                "not_found": not_found,
                "has_positions": has_positions,
                "watchlist": self.watchlist.copy()
            }
        except Exception as e:
            logger.error(f"Error removing from watchlist: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def reset_watchlist(self) -> Dict[str, Any]:
        """Reset watchlist to default from .env."""
        try:
            self.watchlist = self.default_watchlist.copy()
            
            return {
                "success": True,
                "message": f"✅ Watchlist reset to default\nCurrent watchlist: {', '.join(self.watchlist)} ({len(self.watchlist)} symbols)",
                "watchlist": self.watchlist.copy()
            }
        except Exception as e:
            logger.error(f"Error resetting watchlist: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
