"""
Fear & Greed Index Web Scraper
Scrapes real-time Fear & Greed Index from reliable sources
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


class FearGreedScraper:
    """
    Scrapes Fear & Greed Index from multiple sources
    """
    
    def __init__(self):
        self.sources = [
            self._get_from_alternative_api,
            self._get_from_cnn_api,
        ]
    
    def get_fear_greed_index(self) -> Dict[str, Any]:
        """
        Get current Fear & Greed Index
        
        Returns:
            dict: {
                'score': int (0-100),
                'classification': str,
                'source': str,
                'timestamp': str,
                'success': bool
            }
        """
        for i, source_func in enumerate(self.sources, 1):
            try:
                logger.debug(f"Trying Fear & Greed source {i}...")
                result = source_func()
                if result and result.get('success'):
                    logger.info(f"✓ Fear & Greed Index: {result['score']}/100 ({result['classification']}) from {result['source']}")
                    return result
            except Exception as e:
                logger.debug(f"Source {i} failed: {e}")
                continue
        
        logger.warning("All Fear & Greed sources failed, using default")
        return {
            'score': 50,
            'classification': 'neutral',
            'source': 'default',
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
    
    def _get_from_alternative_api(self) -> Optional[Dict[str, Any]]:
        """
        Try alternative Fear & Greed API (crypto-focused but works)
        """
        try:
            # Alternative API endpoint
            url = "https://api.alternative.me/fng/"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                latest = data['data'][0]
                score = int(latest['value'])
                
                return {
                    'score': score,
                    'classification': latest['value_classification'].lower(),
                    'source': 'alternative_api',
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Alternative API failed: {e}")
            return None
    
    def _get_from_cnn_api(self) -> Optional[Dict[str, Any]]:
        """
        Try to get from CNN Fear & Greed API
        """
        try:
            # CNN's Fear & Greed Index API endpoint
            url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract current score
            if 'fear_and_greed' in data:
                current_data = data['fear_and_greed']
                if current_data and len(current_data) > 0:
                    latest = current_data[-1]  # Most recent
                    score = int(latest['y'])
                    
                    return {
                        'score': score,
                        'classification': self._classify_score(score),
                        'source': 'cnn_api',
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"CNN API failed: {e}")
            return None
    
    def _classify_score(self, score: int) -> str:
        """
        Classify Fear & Greed score
        
        Args:
            score: Score 0-100
            
        Returns:
            str: Classification
        """
        if score <= 25:
            return 'extreme_fear'
        elif score <= 45:
            return 'fear'
        elif score <= 55:
            return 'neutral'
        elif score <= 75:
            return 'greed'
        else:
            return 'extreme_greed'


# Test function
if __name__ == "__main__":
    scraper = FearGreedScraper()
    result = scraper.get_fear_greed_index()
    print(f"Fear & Greed Index: {result}")
