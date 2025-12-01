"""Opportunity Scanner - Find and rank the best trading opportunities.

Scans the stock universe, calculates scores, and maintains a dynamic watchlist.
NOW WITH AI-POWERED DISCOVERY using Perplexity!
ALSO SUPPORTS: Momentum Wave Rider scanner as alternative to AI.
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from data.market_data import MarketDataManager
from data.features import FeatureEngine
from scanner.stock_universe import StockUniverse
from scanner.opportunity_scorer import OpportunityScorer
from scanner.ai_opportunity_finder import get_ai_opportunity_finder
from config import settings
from utils.logger import setup_logger

# Momentum Wave Rider imports
try:
    from scanner.momentum_scanner import MomentumScanner
    from scanner.momentum_scorer import MomentumScorer
    MOMENTUM_AVAILABLE = True
except ImportError:
    MOMENTUM_AVAILABLE = False

logger = setup_logger(__name__)


class OpportunityScanner:
    """Scan stocks and find best trading opportunities using AI or Momentum Scanner."""
    
    def __init__(self, market_data_manager: MarketDataManager, use_ai: bool = True, 
                 sentiment_analyzer=None, alpaca_client=None):
        self.market_data = market_data_manager
        self.scorer = OpportunityScorer(sentiment_analyzer=sentiment_analyzer)
        self.universe = StockUniverse()
        self.ai_finder = get_ai_opportunity_finder() if use_ai else None
        self.use_ai = use_ai
        self.sentiment_analyzer = sentiment_analyzer
        
        # Momentum Wave Rider scanner (alternative to AI)
        self.use_momentum_scanner = getattr(settings, 'USE_MOMENTUM_SCANNER', False)
        self.momentum_scanner = None
        self.momentum_scorer = None
        
        if self.use_momentum_scanner and MOMENTUM_AVAILABLE and alpaca_client:
            try:
                self.momentum_scanner = MomentumScanner(alpaca_client, market_data_manager)
                self.momentum_scorer = MomentumScorer()
                logger.info("✅ Momentum Wave Rider scanner initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize momentum scanner: {e}")
                self.use_momentum_scanner = False
        
        # Daily cache for enhanced scoring
        try:
            from data.daily_cache import get_daily_cache
            self.daily_cache = get_daily_cache()
            logger.info("✅ Daily cache available for enhanced scoring")
        except Exception as e:
            self.daily_cache = None
            logger.warning(f"Daily cache not available: {e}")
        
        # Cache
        self.last_scan_time = None
        self.last_scan_results = []
        self.scan_interval = timedelta(hours=1)  # Scan every hour
        
        mode = "Momentum" if self.use_momentum_scanner else ("AI-powered" if use_ai else "traditional")
        enhanced = " + daily data" if self.daily_cache else ""
        logger.info(f"OpportunityScanner initialized ({mode} mode{enhanced})")
    
    async def scan_universe_async(self, symbols: Optional[List[str]] = None, 
                                   min_score: float = 50.0) -> List[Dict]:
        """
        Scan stock universe for opportunities (async version with AI).
        
        Args:
            symbols: List of symbols to scan (None = use AI discovery)
            min_score: Minimum score threshold
            
        Returns:
            List of opportunities sorted by score
        """
        try:
            # Get current sentiment and strategy
            sentiment = None
            strategy = None
            if self.sentiment_analyzer:
                sentiment = self.sentiment_analyzer.get_sentiment()
                strategy = self.sentiment_analyzer.get_sentiment_strategy(sentiment['score'])
                
                logger.info(f"📊 Market Sentiment: {sentiment['score']}/100 ({sentiment['classification']})")
                logger.info(f"🎯 Strategy: {strategy['strategy']}")
                logger.info(f"📈 Allowed Caps: {', '.join([k.split('_')[0].upper() for k, v in strategy['allowed_caps'].items() if v])}")
            
            # Use AI to discover opportunities if enabled and no symbols provided
            if symbols is None and self.use_ai and self.ai_finder:
                logger.info("🤖 Using AI to discover opportunities...")
                
                # Request opportunities based on sentiment strategy
                if strategy:
                    # AI will filter based on allowed market caps
                    symbols = await self.ai_finder.discover_opportunities(
                        max_symbols=25,
                        allowed_caps=strategy['allowed_caps']
                    )
                else:
                    symbols = await self.ai_finder.discover_opportunities(max_symbols=25)
            elif symbols is None:
                symbols = StockUniverse.get_high_priority()
            
            logger.info(f"🔍 Scanning {len(symbols)} stocks for opportunities...")
            
            opportunities = []
            
            for symbol in symbols:
                try:
                    # Get market data (fetch 1 day of 5-min bars = ~78 bars)
                    bars_dict = self.market_data.fetch_historical_bars([symbol], days=1)
                    df = bars_dict.get(symbol) if bars_dict else None
                    
                    if df is None or len(df) < 30:
                        logger.debug(f"Insufficient data for {symbol}")
                        continue
                    
                    # Calculate features
                    features = FeatureEngine.calculate_features(df)
                    
                    if not features:
                        logger.debug(f"Failed to calculate features for {symbol}")
                        continue
                    
                    # Score opportunity (base score)
                    score_dict = self.scorer.calculate_total_score(features)
                    base_score = score_dict['total_score']
                    
                    # Calculate daily data bonus (Sprint 7+ enhancement)
                    daily_bonus = self.calculate_daily_data_bonus(symbol, features['price'])
                    enhanced_score = base_score + daily_bonus['total_bonus']
                    
                    # Filter by minimum score (using enhanced score)
                    if enhanced_score < min_score:
                        continue
                    
                    # Recalculate grade with enhanced score
                    if enhanced_score >= 90:
                        grade = 'A+'
                    elif enhanced_score >= 85:
                        grade = 'A'
                    elif enhanced_score >= 80:
                        grade = 'A-'
                    elif enhanced_score >= 75:
                        grade = 'B+'
                    elif enhanced_score >= 70:
                        grade = 'B'
                    elif enhanced_score >= 65:
                        grade = 'B-'
                    elif enhanced_score >= 60:
                        grade = 'C+'
                    elif enhanced_score >= 55:
                        grade = 'C'
                    else:
                        grade = 'C-'
                    
                    # Create opportunity record
                    opportunity = {
                        'symbol': symbol,
                        'score': enhanced_score,  # Enhanced score
                        'base_score': base_score,  # Original score
                        'daily_bonus': daily_bonus['total_bonus'],  # Bonus points
                        'grade': grade,  # Recalculated grade
                        'technical_score': score_dict['technical_score'],
                        'momentum_score': score_dict['momentum_score'],
                        'volume_score': score_dict['volume_score'],
                        'volatility_score': score_dict['volatility_score'],
                        'regime_score': score_dict['regime_score'],
                        'price': features['price'],
                        'rsi': features.get('rsi', 50),
                        'adx': features.get('adx', 0),
                        'volume_ratio': features.get('volume_ratio', 1.0),
                        'market_regime': features.get('market_regime', 'transitional'),
                        'confidence': features.get('confidence_score', 50),
                        'scanned_at': datetime.now().isoformat(),
                        'ai_discovered': self.use_ai,
                        'daily_data_details': daily_bonus['details']  # Enhancement details
                    }
                    
                    opportunities.append(opportunity)
                    
                except Exception as e:
                    logger.error(f"Error scanning {symbol}: {e}")
                    continue
            
            # Sort by score
            opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(
                f"✓ Scan complete: Found {len(opportunities)} opportunities "
                f"(min score: {min_score})"
            )
            
            # Cache results
            self.last_scan_time = datetime.now()
            self.last_scan_results = opportunities
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error scanning universe: {e}")
            return []
    
    def scan_universe(self, symbols: Optional[List[str]] = None, 
                          min_score: float = 50.0) -> List[Dict]:
        """
        Scan stock universe for opportunities (sync wrapper).
        
        Args:
            symbols: List of symbols to scan (None = use AI discovery)
            min_score: Minimum score threshold
            
        Returns:
            List of opportunities sorted by score
        """
        try:
            # Run async version in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create task
                return asyncio.create_task(self.scan_universe_async(symbols, min_score))
            else:
                # Run in new event loop
                return loop.run_until_complete(self.scan_universe_async(symbols, min_score))
        except Exception as e:
            logger.error(f"Error in scan_universe: {e}")
            # Fallback to synchronous scan
            return self._scan_universe_sync(symbols, min_score)
    
    def _scan_universe_sync(self, symbols: Optional[List[str]] = None, 
                            min_score: float = 50.0) -> List[Dict]:
        """Synchronous fallback scan without AI."""
        try:
            if symbols is None:
                symbols = StockUniverse.get_high_priority()
            
            logger.info(f"🔍 Scanning {len(symbols)} stocks for opportunities...")
            
            opportunities = []
            
            for symbol in symbols:
                try:
                    # Get market data (fetch 1 day of 5-min bars = ~78 bars)
                    bars_dict = self.market_data.fetch_historical_bars([symbol], days=1)
                    df = bars_dict.get(symbol) if bars_dict else None
                    
                    if df is None or len(df) < 30:
                        logger.debug(f"Insufficient data for {symbol}")
                        continue
                    
                    # Calculate features
                    features = FeatureEngine.calculate_features(df)
                    
                    if not features:
                        logger.debug(f"Failed to calculate features for {symbol}")
                        continue
                    
                    # Score opportunity (base score)
                    score_dict = self.scorer.calculate_total_score(features)
                    base_score = score_dict['total_score']
                    
                    # Calculate daily data bonus (Sprint 7+ enhancement)
                    daily_bonus = self.calculate_daily_data_bonus(symbol, features['price'])
                    enhanced_score = base_score + daily_bonus['total_bonus']
                    
                    # Filter by minimum score (using enhanced score)
                    if enhanced_score < min_score:
                        continue
                    
                    # Recalculate grade with enhanced score
                    if enhanced_score >= 90:
                        grade = 'A+'
                    elif enhanced_score >= 85:
                        grade = 'A'
                    elif enhanced_score >= 80:
                        grade = 'A-'
                    elif enhanced_score >= 75:
                        grade = 'B+'
                    elif enhanced_score >= 70:
                        grade = 'B'
                    elif enhanced_score >= 65:
                        grade = 'B-'
                    elif enhanced_score >= 60:
                        grade = 'C+'
                    elif enhanced_score >= 55:
                        grade = 'C'
                    else:
                        grade = 'C-'
                    
                    # Create opportunity record
                    opportunity = {
                        'symbol': symbol,
                        'score': enhanced_score,  # Enhanced score
                        'base_score': base_score,  # Original score
                        'daily_bonus': daily_bonus['total_bonus'],  # Bonus points
                        'grade': grade,  # Recalculated grade
                        'technical_score': score_dict['technical_score'],
                        'momentum_score': score_dict['momentum_score'],
                        'volume_score': score_dict['volume_score'],
                        'volatility_score': score_dict['volatility_score'],
                        'regime_score': score_dict['regime_score'],
                        'price': features['price'],
                        'rsi': features.get('rsi', 50),
                        'adx': features.get('adx', 0),
                        'volume_ratio': features.get('volume_ratio', 1.0),
                        'market_regime': features.get('market_regime', 'transitional'),
                        'confidence': features.get('confidence_score', 50),
                        'scanned_at': datetime.now().isoformat(),
                        'daily_data_details': daily_bonus['details']  # Enhancement details
                    }
                    
                    opportunities.append(opportunity)
                    
                except Exception as e:
                    logger.error(f"Error scanning {symbol}: {e}")
                    continue
            
            # Sort by score
            opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(
                f"✓ Scan complete: Found {len(opportunities)} opportunities "
                f"(min score: {min_score})"
            )
            
            # Cache results
            self.last_scan_time = datetime.now()
            self.last_scan_results = opportunities
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error scanning universe: {e}")
            return []
    
    def get_top_opportunities(self, n: int = 20) -> List[Dict]:
        """Get top N opportunities from last scan."""
        if not self.last_scan_results:
            logger.warning("No scan results available")
            return []
        
        return self.last_scan_results[:n]
    
    def get_watchlist_symbols(self, n: int = 20, min_score: float = 60.0) -> List[str]:
        """
        Get symbols for dynamic watchlist.
        
        Args:
            n: Maximum number of symbols
            min_score: Minimum score threshold
            
        Returns:
            List of symbols sorted by score
        """
        if not self.last_scan_results:
            logger.warning("No scan results, using default watchlist")
            return StockUniverse.get_high_priority()[:n]
        
        # Filter by minimum score
        qualified = [
            opp for opp in self.last_scan_results 
            if opp['score'] >= min_score
        ]
        
        # Get top N symbols
        symbols = [opp['symbol'] for opp in qualified[:n]]
        
        logger.info(
            f"Generated watchlist: {len(symbols)} symbols "
            f"(min score: {min_score})"
        )
        
        return symbols
    
    def should_rescan(self) -> bool:
        """Check if it's time to rescan."""
        if self.last_scan_time is None:
            return True
        
        time_since_scan = datetime.now() - self.last_scan_time
        return time_since_scan >= self.scan_interval
    
    def auto_scan_loop(self, interval_hours: int = 1):
        """
        Automatic scanning loop (runs in background).
        
        Args:
            interval_hours: Hours between scans
        """
        self.scan_interval = timedelta(hours=interval_hours)
        
        logger.info(f"🔄 Starting auto-scan loop (every {interval_hours}h)")
        
        while True:
            try:
                if self.should_rescan():
                    logger.info("⏰ Auto-scan triggered")
                    self.scan_universe()
                    
                    # Log top opportunities
                    top_5 = self.get_top_opportunities(5)
                    if top_5:
                        logger.info("📊 Top 5 Opportunities:")
                        for i, opp in enumerate(top_5, 1):
                            logger.info(
                                f"  {i}. {opp['symbol']}: {opp['score']:.1f} "
                                f"({opp['grade']}) - ${opp['price']:.2f}"
                            )
                
                # Sleep for 5 minutes, then check again
                import time
                time.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in auto-scan loop: {e}")
                import time
                time.sleep(60)  # Wait 1 minute on error
    
    def save_opportunities_to_db(self, opportunities: List[Dict], supabase_client=None):
        """Save opportunities to database for analysis."""
        try:
            if not opportunities or not supabase_client:
                return
            
            # Save to opportunities table
            for opp in opportunities:
                supabase_client.client.table("opportunities").upsert({
                    'symbol': opp['symbol'],
                    'score': opp['score'],
                    'grade': opp['grade'],
                    'technical_score': opp['technical_score'],
                    'momentum_score': opp['momentum_score'],
                    'volume_score': opp['volume_score'],
                    'volatility_score': opp['volatility_score'],
                    'regime_score': opp['regime_score'],
                    'price': opp['price'],
                    'rsi': opp['rsi'],
                    'adx': opp['adx'],
                    'volume_ratio': opp['volume_ratio'],
                    'market_regime': opp['market_regime'],
                    'confidence': opp['confidence'],
                    'scanned_at': opp['scanned_at']
                }, on_conflict='symbol,scanned_at').execute()
            
            logger.info(f"✓ Saved {len(opportunities)} opportunities to database")
            
        except Exception as e:
            logger.error(f"Error saving opportunities to database: {e}")
    
    def get_opportunity_summary(self) -> Dict:
        """Get summary of current opportunities."""
        if not self.last_scan_results:
            return {
                'total_opportunities': 0,
                'avg_score': 0,
                'top_grade': 'N/A',
                'last_scan': 'Never'
            }
        
        scores = [opp['score'] for opp in self.last_scan_results]
        
        return {
            'total_opportunities': len(self.last_scan_results),
            'avg_score': round(sum(scores) / len(scores), 1) if scores else 0,
            'top_grade': self.last_scan_results[0]['grade'] if self.last_scan_results else 'N/A',
            'top_symbol': self.last_scan_results[0]['symbol'] if self.last_scan_results else 'N/A',
            'top_score': self.last_scan_results[0]['score'] if self.last_scan_results else 0,
            'last_scan': self.last_scan_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_scan_time else 'Never',
            'grade_distribution': self._get_grade_distribution()
        }
    
    def _get_grade_distribution(self) -> Dict[str, int]:
        """Get distribution of grades."""
        if not self.last_scan_results:
            return {}
        
        distribution = {}
        for opp in self.last_scan_results:
            grade = opp['grade']
            distribution[grade] = distribution.get(grade, 0) + 1
        
        return distribution
    
    def calculate_daily_data_bonus(self, symbol: str, current_price: float, signal: str = 'long') -> Dict:
        """
        Calculate bonus points based on daily data AND signal direction (Sprint 7+ enhancement).
        
        NOW SUPPORTS BOTH LONG AND SHORT SIGNALS!
        
        Args:
            symbol: Stock symbol
            current_price: Current price
            signal: 'long' or 'short' - determines bonus logic
            
        Returns:
            Dict with bonus points and details
        """
        bonus = {
            'total_bonus': 0,
            'ema_200_bonus': 0,
            'daily_trend_bonus': 0,
            'trend_strength_bonus': 0,
            'details': []
        }
        
        if not self.daily_cache:
            return bonus
        
        try:
            daily_data = self.daily_cache.get_daily_data(symbol)
            
            if not daily_data:
                return bonus
            
            # Bonus 1: Price vs 200-EMA (0-8 points) - REDUCED to not dominate score
            # Being in an uptrend is good but shouldn't be the main factor
            ema_200 = daily_data.get('ema_200', 0)
            if ema_200 > 0:
                distance_pct = ((current_price - ema_200) / ema_200) * 100
                
                if signal == 'long':
                    # LONG: Small bonus for uptrends
                    if distance_pct > 15:  # >15% above - might be extended
                        bonus['ema_200_bonus'] = 5
                        bonus['details'].append(f"Extended uptrend: {distance_pct:.1f}% above 200-EMA")
                    elif distance_pct > 5:  # >5% above - healthy trend
                        bonus['ema_200_bonus'] = 8
                        bonus['details'].append(f"Healthy uptrend: {distance_pct:.1f}% above 200-EMA")
                    elif distance_pct > 0:  # Just above EMA - good entry
                        bonus['ema_200_bonus'] = 6
                        bonus['details'].append(f"Above 200-EMA: {distance_pct:.1f}%")
                
                elif signal == 'short':
                    # SHORT: Small bonus for downtrends
                    if distance_pct < -15:  # >15% below - might be oversold
                        bonus['ema_200_bonus'] = 5
                        bonus['details'].append(f"Extended downtrend: {abs(distance_pct):.1f}% below 200-EMA")
                    elif distance_pct < -5:  # >5% below - healthy downtrend
                        bonus['ema_200_bonus'] = 8
                        bonus['details'].append(f"Healthy downtrend: {abs(distance_pct):.1f}% below 200-EMA")
                    elif distance_pct < 0:  # Just below EMA
                        bonus['ema_200_bonus'] = 6
                        bonus['details'].append(f"Below 200-EMA: {abs(distance_pct):.1f}%")
            
            # Bonus 2: Daily trend (0-8 points) - REDUCED to not dominate score
            trend = daily_data.get('trend', 'neutral')
            ema_9 = daily_data.get('ema_9', 0)
            ema_21 = daily_data.get('ema_21', 0)
            
            if signal == 'long' and trend == 'bullish':
                # LONG: Small bonus for bullish trend
                if ema_9 > 0 and ema_21 > 0:
                    trend_strength = ((ema_9 - ema_21) / ema_21) * 100
                    
                    if trend_strength > 3:  # Strong bullish
                        bonus['daily_trend_bonus'] = 8
                        bonus['details'].append(f"Strong bullish trend: {trend_strength:.1f}%")
                    elif trend_strength > 1:  # Moderate bullish
                        bonus['daily_trend_bonus'] = 5
                        bonus['details'].append(f"Bullish trend: {trend_strength:.1f}%")
                    else:  # Weak bullish
                        bonus['daily_trend_bonus'] = 3
                        bonus['details'].append("Weak bullish trend")
            
            elif signal == 'short' and trend == 'bearish':
                # SHORT: Small bonus for bearish trend
                if ema_9 > 0 and ema_21 > 0:
                    trend_strength = ((ema_21 - ema_9) / ema_9) * 100
                    
                    if trend_strength > 3:  # Strong bearish
                        bonus['daily_trend_bonus'] = 8
                        bonus['details'].append(f"Strong bearish trend: {trend_strength:.1f}%")
                    elif trend_strength > 1:  # Moderate bearish
                        bonus['daily_trend_bonus'] = 5
                        bonus['details'].append(f"Bearish trend: {trend_strength:.1f}%")
                    else:  # Weak bearish
                        bonus['daily_trend_bonus'] = 3
                        bonus['details'].append("Weak bearish trend")
            
            # Bonus 3: Trend alignment (0-4 points) - REDUCED
            if bonus['ema_200_bonus'] >= 6 and bonus['daily_trend_bonus'] >= 5:
                bonus['trend_strength_bonus'] = 4
                direction = "bullish" if signal == 'long' else "bearish"
                bonus['details'].append(f"Good {direction} alignment")
            
            # Calculate total
            bonus['total_bonus'] = (
                bonus['ema_200_bonus'] + 
                bonus['daily_trend_bonus'] + 
                bonus['trend_strength_bonus']
            )
            
            if bonus['total_bonus'] > 0:
                logger.debug(f"{symbol}: Daily data bonus = +{bonus['total_bonus']} points")
            
        except Exception as e:
            logger.error(f"Error calculating daily bonus for {symbol}: {e}")
        
        return bonus
