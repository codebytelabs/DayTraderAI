"""
News client for fetching market news and integrating with AI analysis.
Uses Alpaca News API and Perplexity for sentiment analysis.
"""

from alpaca.data.historical.news import NewsClient as AlpacaNewsClient
from alpaca.data.requests import NewsRequest
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class NewsClient:
    """Client for fetching and analyzing market news."""
    
    def __init__(self):
        # Alpaca News API doesn't require authentication
        self.client = AlpacaNewsClient()
        logger.info("News client initialized")
    
    def get_news(
        self,
        symbols: Optional[List[str]] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Fetch news articles.
        
        Args:
            symbols: List of symbols to filter by (None for all)
            start: Start datetime (default: 24 hours ago)
            end: End datetime (default: now)
            limit: Maximum number of articles
            
        Returns:
            List of news articles
        """
        try:
            if start is None:
                start = datetime.now() - timedelta(days=1)
            if end is None:
                end = datetime.now()
            
            request = NewsRequest(
                symbols=symbols,
                start=start,
                end=end,
                limit=limit
            )
            
            news = self.client.get_news(request)
            
            articles = []
            for article in news.data:
                articles.append({
                    "id": article.id,
                    "headline": article.headline,
                    "summary": article.summary if hasattr(article, 'summary') else "",
                    "author": article.author,
                    "created_at": article.created_at,
                    "updated_at": article.updated_at,
                    "url": article.url,
                    "symbols": article.symbols if hasattr(article, 'symbols') else [],
                    "source": article.source if hasattr(article, 'source') else ""
                })
            
            logger.info(f"Fetched {len(articles)} news articles")
            return articles
            
        except Exception as e:
            logger.error(f"Failed to fetch news: {e}")
            return []
    
    def get_symbol_news(
        self,
        symbol: str,
        hours: int = 24,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent news for a specific symbol.
        
        Args:
            symbol: Stock symbol
            hours: Hours of history to fetch
            limit: Maximum number of articles
            
        Returns:
            List of news articles for the symbol
        """
        start = datetime.now() - timedelta(hours=hours)
        return self.get_news(symbols=[symbol], start=start, limit=limit)
    
    def get_market_news(
        self,
        hours: int = 24,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get general market news (not symbol-specific).
        
        Args:
            hours: Hours of history to fetch
            limit: Maximum number of articles
            
        Returns:
            List of market news articles
        """
        start = datetime.now() - timedelta(hours=hours)
        return self.get_news(symbols=None, start=start, limit=limit)
    
    def analyze_sentiment(self, article: Dict) -> Dict:
        """
        Analyze sentiment of a news article.
        This is a placeholder - integrate with Perplexity or other AI for real analysis.
        
        Args:
            article: News article dict
            
        Returns:
            Sentiment analysis result
        """
        # TODO: Integrate with Perplexity for real sentiment analysis
        # For now, return neutral sentiment
        return {
            "sentiment": "neutral",
            "score": 0.0,
            "confidence": 0.5,
            "summary": article.get("headline", "")
        }
    
    def get_trending_symbols(self, hours: int = 24, min_mentions: int = 3) -> List[Dict]:
        """
        Find symbols with increased news coverage.
        
        Args:
            hours: Hours of history to analyze
            min_mentions: Minimum mentions to be considered trending
            
        Returns:
            List of trending symbols with mention counts
        """
        try:
            news = self.get_market_news(hours=hours, limit=200)
            
            # Count symbol mentions
            symbol_counts = {}
            for article in news:
                for symbol in article.get("symbols", []):
                    symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
            # Filter and sort
            trending = [
                {"symbol": symbol, "mentions": count}
                for symbol, count in symbol_counts.items()
                if count >= min_mentions
            ]
            trending.sort(key=lambda x: x["mentions"], reverse=True)
            
            logger.info(f"Found {len(trending)} trending symbols")
            return trending
            
        except Exception as e:
            logger.error(f"Failed to get trending symbols: {e}")
            return []
