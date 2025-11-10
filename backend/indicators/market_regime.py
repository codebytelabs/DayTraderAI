"""Market Regime Detection - Identify market conditions for adaptive trading."""

from typing import Dict, Optional
from datetime import datetime, timedelta
from core.alpaca_client import AlpacaClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MarketRegimeDetector:
    """Detect market regime to adapt trading strategy."""
    
    def __init__(self, alpaca_client: AlpacaClient):
        self.alpaca = alpaca_client
        self.current_regime = None
        self.last_update = None
    
    def detect_regime(self) -> Dict:
        """
        Detect current market regime.
        
        Returns:
            dict: {
                'regime': 'broad_bullish' | 'narrow_bullish' | 'broad_bearish' | 'narrow_bearish' | 'choppy',
                'breadth_score': 0-100,
                'trend_strength': 0-100,
                'volatility_level': 'low' | 'normal' | 'high',
                'position_size_multiplier': 0.5-1.5,
                'should_trade': bool
            }
        """
        try:
            # Get market breadth indicators
            breadth = self._calculate_market_breadth()
            
            # Get trend strength
            trend = self._calculate_trend_strength()
            
            # Get volatility level
            volatility = self._calculate_volatility()
            
            # Determine regime
            regime = self._determine_regime(breadth, trend, volatility)
            
            # Calculate position size multiplier (pass volatility for choppy regime)
            multiplier = self._calculate_position_multiplier(regime, volatility)
            
            # Determine if we should trade
            should_trade = self._should_trade(regime)
            
            result = {
                'regime': regime,
                'breadth_score': breadth['score'],
                'trend_strength': trend['strength'],
                'volatility_level': volatility['level'],
                'position_size_multiplier': multiplier,
                'should_trade': should_trade,
                'details': {
                    'breadth': breadth,
                    'trend': trend,
                    'volatility': volatility
                }
            }
            
            self.current_regime = result
            self.last_update = datetime.now()
            
            logger.info(f"📊 Market Regime: {regime} | Breadth: {breadth['score']:.0f} | Multiplier: {multiplier:.2f}x")
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return self._get_default_regime()
    
    def _calculate_market_breadth(self) -> Dict:
        """
        Calculate market breadth indicators.
        
        Returns:
            dict: {
                'score': 0-100,
                'advancing': int,
                'declining': int,
                'ratio': float
            }
        """
        try:
            # Get major indices and sector ETFs
            symbols = ['SPY', 'QQQ', 'DIA', 'IWM', 'XLF', 'XLE', 'XLK', 'XLV', 'XLI', 'XLP']
            
            # Get latest bars
            bars = self.alpaca.get_latest_bars(symbols)
            
            if not bars:
                return {'score': 50, 'advancing': 5, 'declining': 5, 'ratio': 1.0}
            
            advancing = 0
            declining = 0
            
            for symbol, bar in bars.items():
                # Compare close to open
                if bar.close > bar.open:
                    advancing += 1
                else:
                    declining += 1
            
            total = advancing + declining
            ratio = advancing / declining if declining > 0 else 2.0
            
            # Score: 0-100 based on ratio
            # Ratio > 2.0 = 100 (very broad)
            # Ratio = 1.0 = 50 (neutral)
            # Ratio < 0.5 = 0 (very narrow/bearish)
            if ratio >= 2.0:
                score = 100
            elif ratio >= 1.5:
                score = 75
            elif ratio >= 1.0:
                score = 50
            elif ratio >= 0.67:
                score = 25
            else:
                score = 0
            
            return {
                'score': score,
                'advancing': advancing,
                'declining': declining,
                'ratio': ratio
            }
            
        except Exception as e:
            logger.error(f"Error calculating breadth: {e}")
            return {'score': 50, 'advancing': 5, 'declining': 5, 'ratio': 1.0}
    
    def _calculate_trend_strength(self) -> Dict:
        """
        Calculate overall market trend strength.
        
        Returns:
            dict: {
                'strength': 0-100,
                'direction': 'bullish' | 'bearish' | 'neutral'
            }
        """
        try:
            # Use SPY as market proxy
            from data.market_data import MarketDataManager
            from core.supabase_client import get_client as get_supabase_client
            
            market_data = MarketDataManager(self.alpaca, get_supabase_client())
            features = market_data.get_latest_features('SPY')
            
            if not features:
                return {'strength': 50, 'direction': 'neutral'}
            
            adx = features.get('adx', 20)
            ema9 = features.get('ema9', 0)
            ema21 = features.get('ema21', 0)
            
            # Determine direction
            if ema9 > ema21:
                direction = 'bullish'
            elif ema9 < ema21:
                direction = 'bearish'
            else:
                direction = 'neutral'
            
            # Strength based on ADX
            # ADX > 40 = very strong trend (100)
            # ADX 25-40 = strong trend (75)
            # ADX 20-25 = moderate trend (50)
            # ADX < 20 = weak/no trend (25)
            if adx >= 40:
                strength = 100
            elif adx >= 25:
                strength = 75
            elif adx >= 20:
                strength = 50
            else:
                strength = 25
            
            return {
                'strength': strength,
                'direction': direction,
                'adx': adx
            }
            
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return {'strength': 50, 'direction': 'neutral'}
    
    def _calculate_volatility(self) -> Dict:
        """
        Calculate market volatility level using real VIX data.
        
        Returns:
            dict: {
                'level': 'low' | 'normal' | 'high',
                'vix': float
            }
        """
        try:
            # Get real VIX from Yahoo Finance
            from indicators.vix_fetcher import get_vix_fetcher
            
            vix_fetcher = get_vix_fetcher()
            vix = vix_fetcher.get_vix()
            
            if vix is None:
                vix = 20.0  # Fallback to historical average
            
            # Classify volatility based on VIX levels
            # VIX < 15: Low volatility (calm market)
            # VIX 15-25: Normal volatility
            # VIX > 25: High volatility (fearful market)
            if vix < 15:
                level = 'low'
            elif vix < 25:
                level = 'normal'
            else:
                level = 'high'
            
            return {
                'level': level,
                'vix': vix
            }
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return {'level': 'normal', 'vix': 20.0}
    
    def _determine_regime(self, breadth: Dict, trend: Dict, volatility: Dict) -> str:
        """Determine overall market regime."""
        
        breadth_score = breadth['score']
        trend_dir = trend['direction']
        trend_str = trend['strength']
        
        # Broad market (good breadth)
        if breadth_score >= 60:
            if trend_dir == 'bullish' and trend_str >= 50:
                return 'broad_bullish'
            elif trend_dir == 'bearish' and trend_str >= 50:
                return 'broad_bearish'
            else:
                return 'broad_neutral'
        
        # Narrow market (poor breadth)
        elif breadth_score >= 40:
            if trend_dir == 'bullish':
                return 'narrow_bullish'
            elif trend_dir == 'bearish':
                return 'narrow_bearish'
            else:
                return 'choppy'
        
        # Very narrow or choppy
        else:
            return 'choppy'
    
    def _calculate_position_multiplier(self, regime: str, volatility: Dict = None) -> float:
        """
        Calculate position size multiplier based on regime and volatility.
        
        For choppy regimes, multiplier varies with VIX:
        - VIX < 20 (low vol): 0.75x
        - VIX 20-30 (medium vol): 0.5x
        - VIX > 30 (high vol): 0.25x
        
        Returns:
            float: 0.25-1.5 multiplier for position sizing
        """
        # Base multipliers for non-choppy regimes
        base_multipliers = {
            'broad_bullish': 1.5,   # Best conditions - trade bigger
            'broad_bearish': 1.5,   # Good for shorts - trade bigger
            'broad_neutral': 1.0,   # Normal conditions
            'narrow_bullish': 0.7,  # Risky - trade smaller
            'narrow_bearish': 0.7,  # Risky - trade smaller
        }
        
        # For choppy regime, use dynamic VIX-based multiplier
        if regime == 'choppy':
            if volatility is None:
                # Fallback to conservative default
                return 0.5
            
            vix = volatility.get('vix', 20.0)
            
            if vix < 20:
                # Low volatility choppy - less risky
                multiplier = 0.75
                logger.info(f"📊 Choppy + Low VIX ({vix:.1f}) → {multiplier}x multiplier")
            elif vix <= 30:
                # Medium volatility choppy - moderate risk
                multiplier = 0.5
                logger.info(f"📊 Choppy + Medium VIX ({vix:.1f}) → {multiplier}x multiplier")
            else:
                # High volatility choppy - very risky
                multiplier = 0.25
                logger.info(f"📊 Choppy + High VIX ({vix:.1f}) → {multiplier}x multiplier")
            
            return multiplier
        
        return base_multipliers.get(regime, 1.0)
    
    def _should_trade(self, regime: str) -> bool:
        """
        Determine if we should trade in current regime.
        
        Returns:
            bool: Always True - use position_size_multiplier for risk adjustment
        
        Note: Professional algo trading uses graduated scaling, not binary blocking.
        We trade in all regimes but with appropriate position sizing:
        - Choppy: 0.5x (reduced risk)
        - Normal: 1.0x (standard risk)
        - Trending: 1.5x (increased risk)
        """
        # Always allow trading - let position_size_multiplier handle risk adjustment
        return True
    
    def _get_default_regime(self) -> Dict:
        """Get default regime when detection fails."""
        return {
            'regime': 'broad_neutral',
            'breadth_score': 50,
            'trend_strength': 50,
            'volatility_level': 'normal',
            'position_size_multiplier': 1.0,
            'should_trade': True,
            'details': {}
        }
    
    def get_current_regime(self) -> Optional[Dict]:
        """Get the current regime (cached)."""
        return self.current_regime


# Singleton instance
_regime_detector = None

def get_regime_detector(alpaca_client: AlpacaClient) -> MarketRegimeDetector:
    """Get singleton regime detector instance."""
    global _regime_detector
    if _regime_detector is None:
        _regime_detector = MarketRegimeDetector(alpaca_client)
    return _regime_detector
