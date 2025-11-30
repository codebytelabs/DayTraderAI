import httpx
from typing import Dict, List, Optional
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


# Model cost tiers (approximate cost per 1M tokens)
MODEL_COSTS = {
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28, "tier": "budget"},
    "deepseek/deepseek-v3.2-exp": {"input": 0.50, "output": 1.00, "tier": "standard"},
    "google/gemini-2.5-flash-preview": {"input": 0.0, "output": 0.0, "tier": "free"},
    "google/gemini-2.5-flash-preview:free": {"input": 0.0, "output": 0.0, "tier": "free"},
    "perplexity/sonar-pro": {"input": 3.0, "output": 15.0, "tier": "premium"},
    "perplexity/sonar": {"input": 1.0, "output": 1.0, "tier": "standard"},
}


def estimate_query_complexity(query: str, max_tokens: int = 500) -> str:
    """
    Estimate query complexity to select appropriate model tier.
    
    Returns: 'simple', 'medium', or 'complex'
    """
    query_lower = query.lower()
    
    # Simple queries - use free/budget models
    simple_patterns = [
        "status", "balance", "equity", "positions", "how much",
        "what is", "show me", "list", "current", "today"
    ]
    if any(p in query_lower for p in simple_patterns) and len(query) < 100:
        return "simple"
    
    # Complex queries - use quality models
    complex_patterns = [
        "analyze", "analysis", "strategy", "recommend", "should i",
        "opportunities", "deep dive", "compare", "evaluate", "risk assessment"
    ]
    if any(p in query_lower for p in complex_patterns) or max_tokens > 1000:
        return "complex"
    
    return "medium"


class OpenRouterClient:
    """
    OpenRouter LLM client for trading analysis and copilot.
    Uses configurable models from .env
    """
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_api_base_url
        self.primary_model = settings.openrouter_primary_model
        self.secondary_model = settings.openrouter_secondary_model
        self.tertiary_model = settings.openrouter_tertiary_model
        self.backup_model = settings.openrouter_backup_model
        self.temperature = settings.openrouter_temperature
        
        if not self.api_key:
            logger.warning("OpenRouter API key not configured")
        else:
            logger.info(f"OpenRouter initialized:")
            logger.info(f"  Primary (analysis): {self.primary_model}")
            logger.info(f"  Secondary (chat): {self.secondary_model}")
            logger.info(f"  Tertiary (quick): {self.tertiary_model}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 2000,
        use_fallback: bool = True
    ) -> Optional[str]:
        """
        Send chat completion request to OpenRouter with automatic fallback.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Override default model (uses primary if not specified)
            temperature: Override default temperature
            max_tokens: Maximum tokens in response
            use_fallback: If True, try fallback models on failure
        
        Returns:
            Response content or None if all models failed
        """
        if not self.api_key:
            logger.error("OpenRouter API key not configured")
            return None
        
        # Build model fallback chain from .env configuration
        models_to_try = []
        if model:
            models_to_try.append(model)
        else:
            models_to_try.append(self.primary_model)
        
        if use_fallback:
            # Add fallback models from .env (not hardcoded!)
            for fallback in [self.secondary_model, self.tertiary_model, self.backup_model]:
                if fallback and fallback not in models_to_try:
                    models_to_try.append(fallback)
        
        temperature = temperature if temperature is not None else self.temperature
        
        for i, current_model in enumerate(models_to_try):
            try:
                timeout = 30.0 if i == 0 else 20.0  # Shorter timeout for fallbacks
                
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": current_model,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content")
                        if content:
                            if i > 0:
                                logger.info(f"OpenRouter fallback success (model: {current_model})")
                            else:
                                logger.info(f"OpenRouter response received (model: {current_model})")
                            return content
                        else:
                            logger.warning(f"No content from {current_model}, trying fallback...")
                    else:
                        logger.warning(f"Model {current_model} failed: {response.status_code}")
                        
            except Exception as e:
                logger.warning(f"Model {current_model} error: {e}")
                continue
        
        logger.error("All OpenRouter models failed")
        return None
    
    async def analyze_trade(
        self,
        symbol: str,
        side: str,
        price: float,
        features: Dict,
        context: str = ""
    ) -> Optional[str]:
        """
        Analyze a potential trade using primary model.
        
        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            price: Current price
            features: Technical indicators
            context: Additional context
        
        Returns:
            Analysis text or None
        """
        system_prompt = """You are an expert day trading analyst. Analyze trades based on:
- Technical indicators (EMAs, ATR, volume)
- Market context
- Risk/reward ratio
- Entry/exit timing

Provide concise, actionable analysis. Focus on risks and opportunities."""

        user_prompt = f"""Analyze this trade:

Symbol: {symbol}
Action: {side.upper()}
Price: ${price:.2f}

Technical Indicators:
- EMA Short: ${features.get('ema_short', 0):.2f}
- EMA Long: ${features.get('ema_long', 0):.2f}
- ATR: ${features.get('atr', 0):.2f}
- Volume Z-Score: {features.get('volume_zscore', 0):.2f}

{context}

Provide:
1. Trade quality assessment (1-10)
2. Key risks
3. Recommended action
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.chat_completion(messages, model=self.primary_model)
    
    async def copilot_response(
        self,
        user_message: str,
        trading_context: Dict,
        conversation_history: List[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Generate copilot response using secondary model (faster).
        
        Args:
            user_message: User's question/command
            trading_context: Current trading state
            conversation_history: Previous messages
        
        Returns:
            Response text or None
        """
        system_prompt = """You are the DayTraderAI copilot assistant. You help traders:
- Understand current positions and performance
- Execute trading commands
- Analyze market conditions
- Manage risk

Be concise, actionable, and risk-aware. Always prioritize capital preservation."""

        context_summary = f"""Current Trading State:
- Equity: ${trading_context.get('equity', 0):.2f}
- Daily P/L: ${trading_context.get('daily_pl', 0):.2f} ({trading_context.get('daily_pl_pct', 0):.2f}%)
- Open Positions: {trading_context.get('open_positions', 0)}
- Win Rate: {trading_context.get('win_rate', 0)*100:.1f}%
- Trading Enabled: {trading_context.get('trading_enabled', False)}
"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history[-4:])  # Last 4 messages
        
        messages.append({
            "role": "user",
            "content": f"{context_summary}\n\nUser: {user_message}"
        })
        
        # Use secondary model for faster responses
        return await self.chat_completion(messages, model=self.secondary_model)
    
    async def market_analysis(
        self,
        symbols: List[str],
        market_data: Dict
    ) -> Optional[str]:
        """
        Generate market analysis using primary model.
        
        Args:
            symbols: List of symbols to analyze
            market_data: Market data and indicators
        
        Returns:
            Analysis text or None
        """
        system_prompt = """You are a market analyst specializing in day trading.
Analyze market conditions and identify opportunities/risks.
Focus on actionable insights for intraday trading."""

        user_prompt = f"""Analyze current market conditions for these symbols:
{', '.join(symbols)}

Market Data:
{market_data}

Provide:
1. Overall market sentiment
2. Best opportunities
3. Symbols to avoid
4. Key risks today
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.chat_completion(messages, model=self.primary_model)
    
    async def quick_insight(self, query: str) -> Optional[str]:
        """
        Quick insight using tertiary model (extremely fast).
        
        Args:
            query: Quick question
        
        Returns:
            Response text or None
        """
        messages = [
            {"role": "system", "content": "You are a helpful trading assistant. Be brief."},
            {"role": "user", "content": query}
        ]
        
        # Use tertiary model for quick queries (Gemini Flash Lite - extremely fast)
        return await self.chat_completion(messages, model=self.tertiary_model, max_tokens=500)
