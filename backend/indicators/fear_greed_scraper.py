"""
Fear & Greed Index Web Scraper
Multi-source with consensus scoring for reliability
"""

import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from statistics import median
from utils.logger import setup_logger

logger = setup_logger(__name__)


class FearGreedScraper:
    """
    Multi-source Fear & Greed Index scraper with consensus scoring
    """
    
    def __init__(self):
        self.sources = [
            ('cnn_graphdata', self._get_from_cnn_graphdata),  # Most reliable
            ('cnn_api', self._get_from_cnn_api),
            ('feargreedindex_org', self._get_from_feargreedindex_org),
            ('macromicro', self._get_from_macromicro),
        ]
    
    def get_fear_greed_index(self) -> Dict[str, Any]:
        """
        Get current Fear & Greed Index using consensus from multiple sources
        
        Returns:
            dict: {
                'score': int (0-100),
                'classification': str,
                'source': str,
                'sources_used': list,
                'timestamp': str,
                'success': bool
            }
        """
        scores = []
        sources_used = []
        
        # Try all sources
        for source_name, source_func in self.sources:
            try:
                result = source_func()
                if result and result.get('success'):
                    score = result['score']
                    scores.append(score)
                    sources_used.append(source_name)
                    logger.debug(f"✓ {source_name}: {score}/100")
            except Exception as e:
                logger.debug(f"{source_name} failed: {e}")
                continue
        
        # Use consensus if we have multiple sources
        if len(scores) >= 2:
            # Use median for robustness against outliers
            consensus_score = int(median(scores))
            logger.info(f"✓ Fear & Greed Index: {consensus_score}/100 ({self._classify_score(consensus_score)}) - consensus from {len(scores)} sources: {sources_used}")
            return {
                'score': consensus_score,
                'classification': self._classify_score(consensus_score),
                'source': 'consensus',
                'sources_used': sources_used,
                'all_scores': scores,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
        
        # Use single source if available
        elif len(scores) == 1:
            score = scores[0]
            logger.info(f"✓ Fear & Greed Index: {score}/100 ({self._classify_score(score)}) from {sources_used[0]}")
            return {
                'score': score,
                'classification': self._classify_score(score),
                'source': sources_used[0],
                'sources_used': sources_used,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
        
        # Default to neutral (50) - allows normal trading
        logger.info("⚠️  All sources failed - using default neutral (50/100)")
        return {
            'score': 50,
            'classification': 'neutral',
            'source': 'default_neutral',
            'sources_used': [],
            'timestamp': datetime.now().isoformat(),
            'success': True
        }
    
    def _get_from_cnn_api(self) -> Optional[Dict[str, Any]]:
        """
        Try CNN Fear & Greed API (primary endpoint)
        """
        try:
            url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'fear_and_greed' in data:
                current_data = data['fear_and_greed']
                if current_data and len(current_data) > 0:
                    latest = current_data[-1]
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
    
    def _get_from_cnn_graphdata(self) -> Optional[Dict[str, Any]]:
        """
        Try CNN Fear & Greed API (alternative endpoint with date)
        """
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{today}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Try different data structures
            if 'fear_and_greed' in data:
                fg_data = data['fear_and_greed']
                
                # Check for score field
                if isinstance(fg_data, dict) and 'score' in fg_data:
                    score = int(fg_data['score'])
                    return {
                        'score': score,
                        'classification': self._classify_score(score),
                        'source': 'cnn_graphdata',
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    }
                
                # Check for array format
                elif isinstance(fg_data, list) and len(fg_data) > 0:
                    latest = fg_data[-1]
                    if 'y' in latest:
                        score = int(latest['y'])
                        return {
                            'score': score,
                            'classification': self._classify_score(score),
                            'source': 'cnn_graphdata',
                            'timestamp': datetime.now().isoformat(),
                            'success': True
                        }
            
            return None
            
        except Exception as e:
            logger.debug(f"CNN graphdata failed: {e}")
            return None
    
    def _get_from_feargreedindex_org(self) -> Optional[Dict[str, Any]]:
        """
        Try feargreedindex.org (scraping approach)
        """
        try:
            url = "https://feargreedindex.org/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Look for score in HTML
            html = response.text
            
            # Try to find score patterns
            import re
            
            # Pattern 1: "score":34 or "score": 34
            pattern1 = r'"score"\s*:\s*(\d{1,3})'
            match = re.search(pattern1, html)
            if match:
                score = int(match.group(1))
                if 0 <= score <= 100:
                    return {
                        'score': score,
                        'classification': self._classify_score(score),
                        'source': 'feargreedindex_org',
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    }
            
            # Pattern 2: data-score="34"
            pattern2 = r'data-score="(\d{1,3})"'
            match = re.search(pattern2, html)
            if match:
                score = int(match.group(1))
                if 0 <= score <= 100:
                    return {
                        'score': score,
                        'classification': self._classify_score(score),
                        'source': 'feargreedindex_org',
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"feargreedindex.org failed: {e}")
            return None
    
    def _get_from_macromicro(self) -> Optional[Dict[str, Any]]:
        """
        Try MacroMicro (backup source)
        """
        try:
            url = "https://en.macromicro.me/charts/50108/cnn-fear-and-greed"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            html = response.text
            
            # Look for score in HTML/JSON
            import re
            
            # Try various patterns
            patterns = [
                r'"value"\s*:\s*(\d{1,3})',
                r'"score"\s*:\s*(\d{1,3})',
                r'Fear.*?Greed.*?(\d{1,3})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    score = int(match.group(1))
                    if 0 <= score <= 100:
                        return {
                            'score': score,
                            'classification': self._classify_score(score),
                            'source': 'macromicro',
                            'timestamp': datetime.now().isoformat(),
                            'success': True
                        }
            
            return None
            
        except Exception as e:
            logger.debug(f"MacroMicro failed: {e}")
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
