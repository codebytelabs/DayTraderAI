import httpx
from typing import List, Dict, Optional
from datetime import datetime
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class OpenRouterClient:
    """
    OpenRouter client for AI fallback when primary Perplexity API fails.
    Supports models with online search capabilities.
    """
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_api_base_url
        # Default fallback model with strong reasoning or search
        self.model = settings.openrouter_model_sonar_pro 
        
        if not self.api_key:
            logger.warning("OpenRouter API key not configured")
        else:
            logger.info(f"OpenRouter initialized with fallback model: {self.model}")
    
    async def search(
        self,
        query: str,
        model: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Search using OpenRouter (Perplexity Sonar or other online models).
        
        Args:
            query: Search query
            model: Override default model
        
        Returns:
            Dict with 'content' and 'citations' (if available) or None
        """
        if not self.api_key:
            logger.error("OpenRouter API key not configured")
            return None
        
        model = model or self.model
        
        try:
            # Increase timeout for "reasoning" models which take longer
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://daytraderai.com", # Required by OpenRouter
                        "X-Title": "DayTraderAI", # Required by OpenRouter
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a financial news analyst. Provide factual, sourced information. If using a search-enabled model, cite your sources."
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
                    
                    # OpenRouter might not standardize citations across all models,
                    # but Perplexity models via OpenRouter often include them in text or metadata.
                    # We'll extract what we can.
                    citations = data.get("citations", []) 
                    
                    if content:
                        logger.info(f"OpenRouter search completed using {model}")
                        return {
                            "content": content,
                            "citations": citations,
                            "timestamp": datetime.utcnow().isoformat(),
                            "provider": "openrouter"
                        }
                    else:
                        logger.error("No content in OpenRouter response")
                        return None
                else:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"OpenRouter request failed: {e}")
            return None

    async def get_market_news(self, symbols: List[str]) -> Optional[Dict]:
        """Fallback for market news"""
        symbols_str = ", ".join(symbols)
        query = f"What are the key market developments today affecting these stocks: {symbols_str}? Provide actionable insights."
        return await self.search(query)
