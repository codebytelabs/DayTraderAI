import re
from dataclasses import dataclass
from typing import Dict, List, Sequence

from copilot.config import CopilotConfig

NEWS_KEYWORDS = {
    "news",
    "headline",
    "happened",
    "rumor",
    "catalyst",
    "earnings",
    "report",
    "release",
    "press",
    "conference",
}

ANALYSIS_KEYWORDS = {
    "buy",
    "sell",
    "short",
    "long",
    "enter",
    "exit",
    "analysis",
    "recommend",
    "should i",
    "what do you think",
    "risk",
    "exposure",
    "position",
    "target",
    "stop",
    "take profit",
    "strategy",
    "setup",
}

STATUS_KEYWORDS = {
    "status",
    "summary",
    "update",
    "overview",
    "performance",
    "metrics",
    "how are we doing",
}


@dataclass(slots=True)
class QueryRoute:
    """Represents routing decision for a user query."""

    category: str
    targets: List[str]
    confidence: float
    symbols: List[str]
    notes: List[str]


class QueryRouter:
    """Hybrid router selecting the best AI backends for a user query."""

    def __init__(self, config: CopilotConfig):
        self._config = config

    def route(self, query: str, context: Dict[str, object], symbols: Sequence[str]) -> QueryRoute:
        cleaned = query.lower().strip()
        notes: List[str] = []

        if not cleaned:
            return QueryRoute(
                category="status",
                targets=["openrouter"],
                confidence=0.4,
                symbols=list(symbols),
                notes=["Empty query routed to system summary."],
            )
        
        # Check for commands
        if cleaned.startswith('/') or cleaned.startswith('#'):
            # Check for /analyze command
            if cleaned.startswith('/analyze'):
                # Extract symbols from command
                analyze_symbols = self._extract_analyze_symbols(cleaned)
                return QueryRoute(
                    category="deep_analysis",
                    targets=["perplexity", "openrouter"],
                    confidence=1.0,
                    symbols=analyze_symbols,
                    notes=[f"Deep analysis requested for {len(analyze_symbols)} symbol(s)"],
                )
            
            # Check for /opportunities command
            if cleaned.startswith('/opportunities') or cleaned.startswith('/opportunity'):
                return QueryRoute(
                    category="opportunities",
                    targets=["perplexity", "openrouter"] if self._config.hybrid_routing else ["openrouter"],
                    confidence=0.95,
                    symbols=list(symbols),
                    notes=["Opportunities research requested - using market research + analysis."],
                )
            
            return QueryRoute(
                category="command",
                targets=["command_handler"],
                confidence=1.0,
                symbols=list(symbols),
                notes=["Command detected."],
            )

        news_score = self._keyword_score(cleaned, NEWS_KEYWORDS)
        analysis_score = self._keyword_score(cleaned, ANALYSIS_KEYWORDS)
        status_score = self._keyword_score(cleaned, STATUS_KEYWORDS)

        # Check for opportunities/research queries
        opportunities_keywords = {"opportunities", "opportunity", "ideas", "signals", "setups", "trades"}
        is_opportunities_query = any(kw in cleaned for kw in opportunities_keywords)

        # increase analysis weight if user references open positions
        if symbols and any(sym in (s.lower() for s in symbols) for sym in cleaned.split()):
            analysis_score += 1.0

        top_category = "analysis"
        targets = ["openrouter"]
        confidence = 0.6 + 0.1 * max(analysis_score, news_score, status_score)

        # Special handling for opportunities queries - use BOTH Perplexity and OpenRouter
        if is_opportunities_query:
            top_category = "opportunities"
            targets = ["perplexity", "openrouter"] if self._config.hybrid_routing else ["openrouter"]
            confidence = 0.85
            notes.append("Detected opportunities query - using market research + analysis.")
        elif news_score > analysis_score and news_score > status_score:
            top_category = "news"
            targets = ["perplexity"]
            notes.append("Detected news-focused intent.")
        elif status_score >= max(news_score, analysis_score) and status_score > 0:
            top_category = "status"
            targets = ["openrouter"]
            confidence = min(0.9, 0.5 + 0.1 * status_score)
            notes.append("Detected status/overview intent.")
        elif news_score > 0 and analysis_score > 0:
            top_category = "hybrid"
            targets = ["perplexity", "openrouter"] if self._config.hybrid_routing else ["openrouter"]
            confidence = 0.7
            notes.append("Detected mixed news + analysis intent.")
        else:
            notes.append("Defaulted to trade analysis.")

        if not self._config.hybrid_routing and "perplexity" in targets and len(targets) > 1:
            targets = ["openrouter"]
            notes.append("Hybrid routing disabled; using OpenRouter only.")

        return QueryRoute(
            category=top_category,
            targets=targets,
            confidence=max(0.3, min(confidence, 0.95)),
            symbols=list(symbols),
            notes=notes,
        )

    @staticmethod
    def _keyword_score(text: str, keywords: Sequence[str]) -> float:
        score = 0.0
        for keyword in keywords:
            if keyword in text:
                score += 1.0
            elif " " not in keyword:
                occurrences = len(re.findall(rf"\b{re.escape(keyword)}\b", text))
                score += occurrences * 0.5
        return score
    
    @staticmethod
    def _extract_analyze_symbols(query: str) -> List[str]:
        """Extract symbols from /analyze command."""
        # Remove /analyze command
        query = query.replace('/analyze', '').strip()
        # Split by spaces and filter valid symbols (1-6 uppercase letters)
        symbols = []
        for word in query.split():
            word = word.upper().strip()
            if word.isalpha() and 1 <= len(word) <= 6:
                symbols.append(word)
        return symbols[:3]  # Max 3 symbols
