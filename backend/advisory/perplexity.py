import httpx
from typing import List, Dict, Optional
from datetime import datetime
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PerplexityClient:
    """
    Perplexity AI client for news and market research.
    Uses configurable model from .env with OpenRouter fallback.
    
    Fallback chain:
    1. Native Perplexity API (PERPLEXITY_DEFAULT_MODEL)
    2. OpenRouter Perplexity (OPENROUTER_PERPLEXITY_MODEL) - same model, different API path
    """
    
    def __init__(self):
        self.api_key = settings.perplexity_api_key
        self.base_url = settings.perplexity_api_base_url
        self.model = settings.perplexity_default_model
        
        # OpenRouter fallback configuration
        self.openrouter_api_key = settings.openrouter_api_key
        self.openrouter_base_url = settings.openrouter_api_base_url
        self.openrouter_perplexity_model = settings.openrouter_perplexity_model
        
        if not self.api_key:
            logger.warning("Perplexity API key not configured")
        else:
            logger.info(f"Perplexity initialized with model: {self.model}")
        
        if self.openrouter_api_key:
            logger.info(f"Perplexity fallback via OpenRouter: {self.openrouter_perplexity_model}")
    
    async def search(
        self,
        query: str,
        model: Optional[str] = None,
        use_fallback: bool = True
    ) -> Optional[Dict]:
        """
        Search using Perplexity with source citations.
        Falls back to OpenRouter if native Perplexity API fails.
        
        Args:
            query: Search query
            model: Override default model
            use_fallback: If True, try OpenRouter fallback on failure
        
        Returns:
            Dict with 'content' and 'citations' or None
        """
        # Try native Perplexity API first
        result = await self._search_native(query, model)
        if result:
            return result
        
        # Fallback to OpenRouter if enabled and configured
        if use_fallback and self.openrouter_api_key:
            logger.info("Native Perplexity failed, trying OpenRouter fallback...")
            result = await self._search_openrouter(query)
            if result:
                return result
        
        return None
    
    async def _search_native(
        self,
        query: str,
        model: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Search using native Perplexity API.
        """
        if not self.api_key:
            logger.warning("Perplexity API key not configured, skipping native API")
            return None
        
        model = model or self.model
        
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a financial news analyst. Provide factual, sourced information."
                            },
                            {
                                "role": "user",
                                "content": query
                            }
                        ]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    choice = data.get("choices", [{}])[0]
                    content = choice.get("message", {}).get("content")
                    citations = data.get("citations", [])
                    
                    if content:
                        logger.info(f"Perplexity (native) search completed: {len(citations)} citations")
                        return {
                            "content": content,
                            "citations": citations,
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": "perplexity_native"
                        }
                    else:
                        logger.error("No content in Perplexity response")
                        return None
                else:
                    logger.warning(f"Perplexity native API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.warning(f"Perplexity native request failed: {e}")
            return None
    
    async def _search_openrouter(self, query: str) -> Optional[Dict]:
        """
        Search using Perplexity model via OpenRouter (fallback).
        """
        if not self.openrouter_api_key:
            logger.error("OpenRouter API key not configured for fallback")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{self.openrouter_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.openrouter_perplexity_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a financial news analyst. Provide factual, sourced information."
                            },
                            {
                                "role": "user",
                                "content": query
                            }
                        ]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    choice = data.get("choices", [{}])[0]
                    content = choice.get("message", {}).get("content")
                    # OpenRouter may not return citations the same way
                    citations = data.get("citations", [])
                    
                    if content:
                        logger.info(f"Perplexity (OpenRouter fallback) search completed")
                        return {
                            "content": content,
                            "citations": citations,
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": "openrouter_fallback"
                        }
                    else:
                        logger.error("No content in OpenRouter Perplexity response")
                        return None
                else:
                    logger.error(f"OpenRouter Perplexity API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"OpenRouter Perplexity request failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    async def get_news(self, symbol: str) -> Optional[Dict]:
        """
        Get latest news for a symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            News summary with citations or None
        """
        query = f"""What are the latest news and developments for {symbol} stock today? 
Focus on:
- Recent price movements
- Company announcements
- Analyst ratings
- Market sentiment

Provide a concise summary with key points."""

        return await self.search(query)
    
    async def get_market_news(self, symbols: List[str]) -> Optional[Dict]:
        """
        Get market news affecting multiple symbols.
        
        Args:
            symbols: List of stock symbols
        
        Returns:
            Market news summary or None
        """
        symbols_str = ", ".join(symbols)
        query = f"""What are the key market developments today affecting these stocks: {symbols_str}?

Focus on:
- Overall market sentiment
- Sector trends
- Economic data releases
- Major news impacting these stocks

Provide actionable insights for day traders."""

        return await self.search(query)
    
    async def check_earnings(self, symbol: str) -> Optional[Dict]:
        """
        Check if symbol has earnings today or soon.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Earnings info or None
        """
        query = f"""When is the next earnings report for {symbol}? 
Is it today or within the next 2 days?
What are analyst expectations?"""

        return await self.search(query)
    
    async def analyze_sentiment(self, symbol: str) -> Optional[Dict]:
        """
        Analyze market sentiment for a symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Sentiment analysis or None
        """
        query = f"""What is the current market sentiment for {symbol}?

Analyze:
- Social media sentiment
- Analyst opinions
- Recent news tone
- Institutional activity

Provide a sentiment score (bullish/neutral/bearish) with reasoning."""

        return await self.search(query)
    
    async def research_symbol(self, symbol: str, question: str) -> Optional[Dict]:
        """
        Research specific question about a symbol.
        
        Args:
            symbol: Stock symbol
            question: Specific question
        
        Returns:
            Research results or None
        """
        query = f"For {symbol} stock: {question}"
        return await self.search(query)
