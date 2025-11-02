"""
Response formatter for copilot responses.

Formats execution results, LLM responses, and info queries into consistent structured output.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class CopilotResponse:
    """Standardized copilot response format."""
    
    content: str  # Main response text (markdown formatted)
    response_type: str  # "execution", "advice", "info", "error"
    details: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    citations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResponseFormatter:
    """Formats execution results and LLM responses into consistent output."""
    
    def format_execution(self, result: "ExecutionResult") -> CopilotResponse:
        """
        Format an execution result into a copilot response.
        
        Args:
            result: ExecutionResult from ActionExecutor
            
        Returns:
            CopilotResponse with formatted content
        """
        if result.success:
            response_type = "execution"
            content = self._format_success_message(result)
        else:
            response_type = "error"
            content = self._format_error_message(result)
        
        return CopilotResponse(
            content=content,
            response_type=response_type,
            details=result.details,
            confidence=1.0 if result.success else 0.0,
            metadata={
                "action": result.action,
                "success": result.success,
                "before_state": result.before_state,
                "after_state": result.after_state,
            }
        )
    
    def format_llm_response(
        self,
        llm_content: str,
        route: "QueryRoute",
        citations: List[Dict[str, Any]]
    ) -> CopilotResponse:
        """
        Format an LLM-generated response.
        
        Args:
            llm_content: Content from LLM provider
            route: Query routing information
            citations: List of citations from research
            
        Returns:
            CopilotResponse with formatted LLM content
        """
        return CopilotResponse(
            content=llm_content,
            response_type="advice",
            confidence=route.confidence,
            citations=citations,
            metadata={
                "category": route.category,
                "targets": route.targets,
                "symbols": route.symbols,
                "notes": route.notes,
            }
        )
    
    def format_info_response(
        self,
        data: Dict[str, Any],
        query: str
    ) -> CopilotResponse:
        """
        Format an information retrieval response.
        
        Args:
            data: Retrieved data
            query: Original query
            
        Returns:
            CopilotResponse with formatted info
        """
        content = self._format_info_data(data)
        
        return CopilotResponse(
            content=content,
            response_type="info",
            details=data,
            confidence=0.95,
            metadata={"query": query}
        )
    
    def _format_success_message(self, result: "ExecutionResult") -> str:
        """Format a success execution result."""
        # Use the message from the result if available
        if result.message:
            return result.message
        
        # Fallback formatting based on action type
        action_templates = {
            "check_market_status": self._format_market_status,
            "get_position_details": self._format_position_details,
            "get_account_summary": self._format_account_summary,
            "close_position": self._format_close_position,
            "close_all_positions": self._format_close_all,
            "cancel_order": self._format_cancel_order,
            "cancel_all_orders": self._format_cancel_all_orders,
            "modify_stop_loss": self._format_modify_stop,
            "modify_take_profit": self._format_modify_tp,
        }
        
        formatter = action_templates.get(result.action)
        if formatter:
            return formatter(result.details)
        
        return f"✅ {result.action} completed successfully"
    
    def _format_error_message(self, result: "ExecutionResult") -> str:
        """Format an error execution result."""
        if result.message:
            base_message = result.message
        else:
            base_message = f"❌ Failed to {result.action.replace('_', ' ')}"
        
        if result.error:
            base_message += f"\n\n**Error:** {result.error}"
        
        # Add recovery suggestions based on error type
        suggestions = self._get_recovery_suggestions(result)
        if suggestions:
            base_message += f"\n\n**Suggestion:** {suggestions}"
        
        return base_message
    
    def _get_recovery_suggestions(self, result: "ExecutionResult") -> str:
        """Get recovery suggestions based on error type."""
        error = result.error or ""
        action = result.action
        
        if "circuit breaker" in error.lower():
            return "Circuit breaker is active. Check your daily P/L and reset if needed."
        
        if "no position" in error.lower():
            return "Check your open positions with 'show positions' or 'status'."
        
        if "market closed" in error.lower():
            return "Market is currently closed. Try again during trading hours (9:30 AM - 4:00 PM ET)."
        
        if "buying power" in error.lower():
            return "Insufficient funds. Check your account balance and available buying power."
        
        if "invalid" in error.lower() and "stop" in action:
            return "Stop-loss must be below current price for long positions, above for short positions."
        
        if "invalid" in error.lower() and "take" in action:
            return "Take-profit must be above current price for long positions, below for short positions."
        
        return "Check the error details above and try again."
    
    def _format_info_data(self, data: Dict[str, Any]) -> str:
        """Format generic info data."""
        lines = ["📊 **Information**\n"]
        
        for key, value in data.items():
            if isinstance(value, (int, float)):
                if "pct" in key or "rate" in key:
                    lines.append(f"- **{key.replace('_', ' ').title()}:** {value:.2f}%")
                elif "price" in key or "pl" in key or "equity" in key:
                    lines.append(f"- **{key.replace('_', ' ').title()}:** ${value:,.2f}")
                else:
                    lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
            elif isinstance(value, bool):
                status = "✓" if value else "✗"
                lines.append(f"- **{key.replace('_', ' ').title()}:** {status}")
            elif isinstance(value, str):
                lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        
        return "\n".join(lines)
    
    # Action-specific formatters
    
    def _format_market_status(self, details: Dict[str, Any]) -> str:
        """Format market status response."""
        is_open = details.get("is_open", False)
        status = "🟢 **OPEN**" if is_open else "🔴 **CLOSED**"
        
        lines = [f"Market Status: {status}\n"]
        
        if is_open:
            next_close = details.get("next_close", "Unknown")
            lines.append(f"- **Closes at:** {next_close}")
        else:
            next_open = details.get("next_open", "Unknown")
            lines.append(f"- **Opens at:** {next_open}")
        
        return "\n".join(lines)
    
    def _format_position_details(self, details: Dict[str, Any]) -> str:
        """Format position details response."""
        symbol = details.get("symbol", "")
        side = details.get("side", "").upper()
        qty = details.get("qty", 0)
        entry = details.get("avg_entry_price", 0)
        current = details.get("current_price", 0)
        pl = details.get("unrealized_pl", 0)
        pl_pct = details.get("unrealized_pl_pct", 0)
        stop = details.get("stop_loss", 0)
        tp = details.get("take_profit", 0)
        exposure = details.get("exposure_pct", 0)
        
        pl_sign = "+" if pl >= 0 else ""
        pl_emoji = "📈" if pl >= 0 else "📉"
        
        lines = [
            f"{pl_emoji} **{symbol} Position**\n",
            f"- **Side:** {side}",
            f"- **Quantity:** {qty:,} shares",
            f"- **Entry Price:** ${entry:.2f}",
            f"- **Current Price:** ${current:.2f}",
            f"- **Unrealized P/L:** {pl_sign}${pl:,.2f} ({pl_sign}{pl_pct:.2f}%)",
            f"- **Stop Loss:** ${stop:.2f}",
            f"- **Take Profit:** ${tp:.2f}",
            f"- **Exposure:** {exposure:.1f}% of equity"
        ]
        
        # Add news if available
        news = details.get("news", [])
        if news:
            lines.append("\n**Recent News:**")
            for item in news[:3]:
                headline = item.get("headline", "")
                lines.append(f"- {headline}")
        
        return "\n".join(lines)
    
    def _format_account_summary(self, details: Dict[str, Any]) -> str:
        """Format account summary response."""
        equity = details.get("equity", 0)
        cash = details.get("cash", 0)
        buying_power = details.get("buying_power", 0)
        daily_pl = details.get("daily_pl", 0)
        daily_pl_pct = details.get("daily_pl_pct", 0)
        open_pos = details.get("open_positions", 0)
        max_pos = details.get("max_positions", 0)
        win_rate = details.get("win_rate", 0)
        pf = details.get("profit_factor", 0)
        cb = details.get("circuit_breaker", False)
        
        pl_sign = "+" if daily_pl >= 0 else ""
        pl_emoji = "📈" if daily_pl >= 0 else "📉"
        cb_status = "⚠️ **ACTIVE**" if cb else "✓ Clear"
        
        lines = [
            f"{pl_emoji} **Account Summary**\n",
            f"- **Equity:** ${equity:,.2f}",
            f"- **Cash:** ${cash:,.2f}",
            f"- **Buying Power:** ${buying_power:,.2f}",
            f"- **Daily P/L:** {pl_sign}${daily_pl:,.2f} ({pl_sign}{daily_pl_pct:.2f}%)",
            f"- **Open Positions:** {open_pos}/{max_pos}",
            f"- **Win Rate:** {win_rate:.1f}%",
            f"- **Profit Factor:** {pf:.2f}",
            f"- **Circuit Breaker:** {cb_status}"
        ]
        
        # Add top positions if available
        positions = details.get("positions", [])
        if positions:
            lines.append("\n**Top Positions:**")
            for pos in positions[:5]:
                symbol = pos.get("symbol", "")
                pl = pos.get("unrealized_pl", 0)
                pl_sign = "+" if pl >= 0 else ""
                lines.append(f"- {symbol}: {pl_sign}${pl:,.2f}")
        
        return "\n".join(lines)
    
    def _format_close_position(self, details: Dict[str, Any]) -> str:
        """Format close position response."""
        symbol = details.get("symbol", "")
        qty = details.get("qty", 0)
        exit_price = details.get("exit_price", 0)
        pl = details.get("realized_pl", 0)
        pl_pct = details.get("realized_pl_pct", 0)
        
        pl_sign = "+" if pl >= 0 else ""
        pl_emoji = "✅" if pl >= 0 else "❌"
        
        lines = [
            f"{pl_emoji} **Position Closed: {symbol}**\n",
            f"- **Quantity:** {qty:,} shares",
            f"- **Exit Price:** ${exit_price:.2f}",
            f"- **Realized P/L:** {pl_sign}${pl:,.2f} ({pl_sign}{pl_pct:.2f}%)"
        ]
        
        return "\n".join(lines)
    
    def _format_close_all(self, details: Dict[str, Any]) -> str:
        """Format close all positions response."""
        closed = details.get("closed_count", 0)
        total = details.get("total_positions", 0)
        total_pl = details.get("total_pl", 0)
        failed = details.get("failed_symbols", [])
        
        pl_sign = "+" if total_pl >= 0 else ""
        
        lines = [
            f"✅ **Closed {closed}/{total} Positions**\n",
            f"- **Total Realized P/L:** {pl_sign}${total_pl:,.2f}"
        ]
        
        if failed:
            lines.append(f"- **Failed to close:** {', '.join(failed)}")
        
        return "\n".join(lines)
    
    def _format_cancel_order(self, details: Dict[str, Any]) -> str:
        """Format cancel order response."""
        symbol = details.get("symbol", "")
        side = details.get("side", "").upper()
        qty = details.get("qty", 0)
        order_id = details.get("order_id", "")
        
        lines = [
            f"✅ **Order Cancelled**\n",
            f"- **Symbol:** {symbol}",
            f"- **Side:** {side}",
            f"- **Quantity:** {qty:,}",
            f"- **Order ID:** {order_id}"
        ]
        
        return "\n".join(lines)
    
    def _format_cancel_all_orders(self, details: Dict[str, Any]) -> str:
        """Format cancel all orders response."""
        cancelled = details.get("cancelled_count", 0)
        total = details.get("total_orders", 0)
        failed = details.get("failed_count", 0)
        
        lines = [f"✅ **Cancelled {cancelled}/{total} Orders**"]
        
        if failed > 0:
            lines.append(f"- **Failed:** {failed} orders")
        
        return "\n".join(lines)
    
    def _format_modify_stop(self, details: Dict[str, Any]) -> str:
        """Format modify stop-loss response."""
        symbol = details.get("symbol", "")
        old_stop = details.get("old_stop_loss", 0)
        new_stop = details.get("new_stop_loss", 0)
        current = details.get("current_price", 0)
        
        lines = [
            f"✅ **Stop-Loss Updated: {symbol}**\n",
            f"- **Old Stop:** ${old_stop:.2f}",
            f"- **New Stop:** ${new_stop:.2f}",
            f"- **Current Price:** ${current:.2f}"
        ]
        
        return "\n".join(lines)
    
    def _format_modify_tp(self, details: Dict[str, Any]) -> str:
        """Format modify take-profit response."""
        symbol = details.get("symbol", "")
        old_tp = details.get("old_take_profit", 0)
        new_tp = details.get("new_take_profit", 0)
        current = details.get("current_price", 0)
        
        lines = [
            f"✅ **Take-Profit Updated: {symbol}**\n",
            f"- **Old Target:** ${old_tp:.2f}",
            f"- **New Target:** ${new_tp:.2f}",
            f"- **Current Price:** ${current:.2f}"
        ]
        
        return "\n".join(lines)
