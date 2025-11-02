"""
Action classifier for copilot queries.

Classifies user queries into actionable intents (execute, advise, info) and extracts
parameters like symbols, prices, and quantities.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Intent detection keywords
EXECUTE_KEYWORDS = {
    "close", "exit", "sell", "cancel", "set", "move", "update", "modify",
    "change", "adjust", "stop", "liquidate", "dump", "cut"
}

EXECUTE_PHRASES = {
    "close position", "exit position", "sell all", "cancel order",
    "cancel all", "set stop", "move stop", "set take profit", "move tp",
    "update stop", "modify stop", "close all"
}

INFO_KEYWORDS = {
    "is", "are", "what", "show", "display", "get", "check", "status",
    "how", "when", "where", "tell", "give"
}

INFO_PHRASES = {
    "market open", "market closed", "trading hours", "is market",
    "show position", "show me", "what's my", "how is", "status of",
    "check market", "get position"
}

ADVISE_KEYWORDS = {
    "should", "would", "could", "recommend", "think", "suggest",
    "advice", "opinion", "analysis", "evaluate", "assess"
}

ADVISE_PHRASES = {
    "should i", "what do you think", "do you recommend", "is it good",
    "what about", "how about", "your opinion", "your thoughts"
}

# Action type keywords
CLOSE_KEYWORDS = {"close", "exit", "sell", "liquidate", "dump", "cut"}
CANCEL_KEYWORDS = {"cancel", "stop", "abort"}
MODIFY_SL_KEYWORDS = {"stop loss", "sl", "stop"}
MODIFY_TP_KEYWORDS = {"take profit", "tp", "target", "profit"}
MARKET_STATUS_KEYWORDS = {"market open", "market closed", "trading hours", "is market"}
POSITION_QUERY_KEYWORDS = {"show", "display", "status", "how is", "what's"}

# Quantifier keywords
ALL_QUANTIFIERS = {"all", "everything", "every", "entire"}

# Symbol pattern (1-6 uppercase letters)
SYMBOL_PATTERN = re.compile(r'\b([A-Z]{1,6})\b')

# Price pattern (dollar amounts or numbers)
PRICE_PATTERN = re.compile(r'\$?(\d+(?:\.\d{1,2})?)')

# Quantity pattern
QUANTITY_PATTERN = re.compile(r'\b(\d+)\s*(?:shares?|qty|quantity)?\b', re.IGNORECASE)


@dataclass
class ActionIntent:
    """Represents the classified intent of a user query."""
    
    intent_type: str  # "execute", "advise", "info"
    action: Optional[str] = None  # Specific action identifier
    confidence: float = 0.0  # 0.0 to 1.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    ambiguities: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate confidence is in valid range."""
        self.confidence = max(0.0, min(1.0, self.confidence))


class ActionClassifier:
    """Classifies user queries into actionable intents."""
    
    def __init__(self, watchlist: Optional[Set[str]] = None):
        """
        Initialize the action classifier.
        
        Args:
            watchlist: Set of valid ticker symbols. Defaults to settings.watchlist_symbols
        """
        self._watchlist = watchlist or set(settings.watchlist_symbols)
        logger.info(f"ActionClassifier initialized with {len(self._watchlist)} symbols in watchlist")
    
    def classify(self, query: str, context: Dict[str, Any]) -> ActionIntent:
        """
        Analyze query and return classified intent.
        
        Args:
            query: User's natural language query
            context: Trading context from ContextBuilder
            
        Returns:
            ActionIntent with classification and extracted parameters
        """
        if not query or not query.strip():
            return ActionIntent(
                intent_type="info",
                action="get_account_summary",
                confidence=0.5,
            )
        
        normalized = query.lower().strip()
        
        # Score each intent type
        execute_score = self._score_execute_intent(normalized)
        info_score = self._score_info_intent(normalized)
        advise_score = self._score_advise_intent(normalized)
        
        # Determine primary intent
        max_score = max(execute_score, info_score, advise_score)
        
        if max_score == 0:
            # Default to advise for unclear queries
            return ActionIntent(
                intent_type="advise",
                confidence=0.3,
                ambiguities=["Could not determine intent from query"]
            )
        
        # Classify based on highest score
        if execute_score == max_score:
            return self._classify_execute_action(normalized, query, context, execute_score)
        elif info_score == max_score:
            return self._classify_info_action(normalized, query, context, info_score)
        else:
            return ActionIntent(
                intent_type="advise",
                confidence=min(0.95, advise_score / 5.0),
            )
    
    def _score_execute_intent(self, query: str) -> float:
        """Score how likely the query is an execute intent."""
        score = 0.0
        
        # Check for execute phrases (higher weight)
        for phrase in EXECUTE_PHRASES:
            if phrase in query:
                score += 2.0
        
        # Check for execute keywords
        words = set(query.split())
        for keyword in EXECUTE_KEYWORDS:
            if keyword in words:
                score += 1.0
        
        # Boost for imperative structure (starts with verb)
        first_word = query.split()[0] if query.split() else ""
        if first_word in EXECUTE_KEYWORDS:
            score += 1.5
        
        return score
    
    def _score_info_intent(self, query: str) -> float:
        """Score how likely the query is an info intent."""
        score = 0.0
        
        # Check for info phrases
        for phrase in INFO_PHRASES:
            if phrase in query:
                score += 2.0
        
        # Check for info keywords
        words = set(query.split())
        for keyword in INFO_KEYWORDS:
            if keyword in words:
                score += 1.0
        
        # Boost for question structure
        if query.endswith('?'):
            score += 1.0
        
        # Boost if starts with question word
        first_word = query.split()[0] if query.split() else ""
        if first_word in INFO_KEYWORDS:
            score += 1.5
        
        return score
    
    def _score_advise_intent(self, query: str) -> float:
        """Score how likely the query is an advise intent."""
        score = 0.0
        
        # Check for advise phrases
        for phrase in ADVISE_PHRASES:
            if phrase in query:
                score += 2.5
        
        # Check for advise keywords
        words = set(query.split())
        for keyword in ADVISE_KEYWORDS:
            if keyword in words:
                score += 1.5
        
        return score
    
    def _classify_execute_action(
        self, 
        normalized: str, 
        original: str,
        context: Dict[str, Any],
        score: float
    ) -> ActionIntent:
        """Classify specific execute action and extract parameters."""
        
        # Detect action type
        action = None
        parameters: Dict[str, Any] = {}
        ambiguities: List[str] = []
        requires_confirmation = False
        
        # Check for close position
        if any(kw in normalized for kw in CLOSE_KEYWORDS):
            # Check for "all" quantifier
            if any(q in normalized for q in ALL_QUANTIFIERS):
                action = "close_all_positions"
                requires_confirmation = True
            else:
                action = "close_position"
                symbols = self._extract_symbols(original, context)
                if not symbols:
                    ambiguities.append("Could not determine which position to close")
                elif len(symbols) > 1:
                    ambiguities.append(f"Multiple symbols found: {', '.join(symbols)}")
                else:
                    parameters["symbol"] = symbols[0]
                    # Check if position value is high
                    position_value = self._get_position_value(symbols[0], context)
                    if position_value and position_value > 1000:
                        requires_confirmation = True
        
        # Check for cancel order
        elif any(kw in normalized for kw in CANCEL_KEYWORDS):
            if "order" in normalized:
                if any(q in normalized for q in ALL_QUANTIFIERS):
                    action = "cancel_all_orders"
                    requires_confirmation = True
                else:
                    action = "cancel_order"
                    symbols = self._extract_symbols(original, context)
                    if symbols:
                        parameters["symbol"] = symbols[0]
                    else:
                        ambiguities.append("Could not determine which order to cancel")
        
        # Check for stop-loss modification
        elif any(kw in normalized for kw in ["stop loss", "sl", "stop"]) and any(kw in normalized for kw in ["set", "move", "update", "modify", "change"]):
            action = "modify_stop_loss"
            symbols = self._extract_symbols(original, context)
            prices = self._extract_prices(original)
            
            if not symbols:
                ambiguities.append("Could not determine which position to modify")
            elif len(symbols) > 1:
                ambiguities.append(f"Multiple symbols found: {', '.join(symbols)}")
            else:
                parameters["symbol"] = symbols[0]
            
            if not prices:
                ambiguities.append("Could not determine stop-loss price")
            else:
                parameters["stop_loss"] = prices[0]
        
        # Check for take-profit modification
        elif any(kw in normalized for kw in ["take profit", "tp", "target"]) and any(kw in normalized for kw in ["set", "move", "update", "modify", "change"]):
            action = "modify_take_profit"
            symbols = self._extract_symbols(original, context)
            prices = self._extract_prices(original)
            
            if not symbols:
                ambiguities.append("Could not determine which position to modify")
            elif len(symbols) > 1:
                ambiguities.append(f"Multiple symbols found: {', '.join(symbols)}")
            else:
                parameters["symbol"] = symbols[0]
            
            if not prices:
                ambiguities.append("Could not determine take-profit price")
            else:
                parameters["take_profit"] = prices[0]
        
        if not action:
            ambiguities.append("Could not determine specific action to execute")
        
        # Calculate confidence
        confidence = min(0.95, score / 5.0)
        if ambiguities:
            confidence *= 0.6  # Reduce confidence for ambiguous queries
        
        return ActionIntent(
            intent_type="execute",
            action=action,
            confidence=confidence,
            parameters=parameters,
            requires_confirmation=requires_confirmation,
            ambiguities=ambiguities,
        )
    
    def _classify_info_action(
        self,
        normalized: str,
        original: str,
        context: Dict[str, Any],
        score: float
    ) -> ActionIntent:
        """Classify specific info action and extract parameters."""
        
        action = None
        parameters: Dict[str, Any] = {}
        ambiguities: List[str] = []
        
        # Check for market status query
        if any(kw in normalized for kw in ["market open", "market closed", "trading hours", "market"]):
            action = "check_market_status"
        
        # Check for position query
        elif any(kw in normalized for kw in ["show", "display", "status", "how is", "what's"]):
            symbols = self._extract_symbols(original, context)
            if symbols:
                action = "get_position_details"
                if len(symbols) > 1:
                    ambiguities.append(f"Multiple symbols found: {', '.join(symbols)}")
                else:
                    parameters["symbol"] = symbols[0]
            else:
                # Default to account summary if no symbol
                action = "get_account_summary"
        
        # Default to account summary
        if not action:
            action = "get_account_summary"
        
        confidence = min(0.95, score / 4.0)
        if ambiguities:
            confidence *= 0.7
        
        return ActionIntent(
            intent_type="info",
            action=action,
            confidence=confidence,
            parameters=parameters,
            ambiguities=ambiguities,
        )
    
    def _extract_symbols(self, query: str, context: Dict[str, Any]) -> List[str]:
        """Extract ticker symbols from query."""
        # Find all potential symbols (uppercase words)
        candidates = SYMBOL_PATTERN.findall(query.upper())
        
        # Filter to only valid watchlist symbols
        valid_symbols = [s for s in candidates if s in self._watchlist]
        
        # If no symbols found in query, check if query references open positions
        if not valid_symbols:
            positions = context.get("positions", [])
            if len(positions) == 1:
                # If only one position, assume that's the target
                valid_symbols = [positions[0]["symbol"]]
        
        return valid_symbols
    
    def _extract_prices(self, query: str) -> List[float]:
        """Extract price values from query."""
        matches = PRICE_PATTERN.findall(query)
        try:
            return [float(m) for m in matches]
        except ValueError:
            return []
    
    def _extract_quantities(self, query: str) -> List[int]:
        """Extract quantity values from query."""
        matches = QUANTITY_PATTERN.findall(query)
        try:
            return [int(m) for m in matches]
        except ValueError:
            return []
    
    def _get_position_value(self, symbol: str, context: Dict[str, Any]) -> Optional[float]:
        """Get the market value of a position from context."""
        positions = context.get("positions", [])
        for pos in positions:
            if pos.get("symbol") == symbol:
                return abs(pos.get("market_value", 0))
        return None
