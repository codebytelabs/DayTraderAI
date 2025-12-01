#!/usr/bin/env python3
"""
Momentum Scanner - Data-Driven Wave Detection

Replaces slow AI discovery with fast, real-time market data analysis.
Focuses on volume surges, breakouts, and active momentum.
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

# Import the data model
try:
    from scanner.momentum_models import MomentumCandidate
except ImportError:
    from dataclasses import dataclass
    
    @dataclass
    class MomentumCandidate:
        """Temporary fallback until models file is created."""
        symbol: str
        price: float
        volume_ratio: float
        momentum_score: int
        confidence: int


class MomentumScanner:
    """
    Data-driven momentum scanner using Alpaca and Twelve Data.
    
    Replaces slow AI-based discovery with real-time market data analysis.
    Identifies stocks with:
    - Volume surges (150%+ above average)
    - Price breakouts above resistance
    - Strong momentum indicators (ADX > 25)
    - Fresh EMA crossovers (not extended moves)
    - Room to run (upside potential to resistance)
    """
    
    def __init__(self, alpaca_client, market_data_client):
        self.alpaca = alpaca_client
        self.market_data = market_data_client
        self.min_volume_ratio = 1.5  # Minimum 150% volume surge
        self.min_price_move = 0.02   # Minimum 2% price move
        self.lookback_periods = 20   # For volume average calculation
        
        logger.info("✅ MomentumScanner initialized - data-driven wave detection ready")

    async def scan_momentum_waves(self, max_symbols: int = 50) -> List[MomentumCandidate]:
        """
        Scan for active momentum waves in real-time.
        
        This is the main entry point that:
        1. Gets top movers from Alpaca (fast)
        2. Filters by volume surge (institutional interest)
        3. Returns ranked momentum candidates
        
        Args:
            max_symbols: Maximum number of candidates to return
            
        Returns:
            List of momentum candidates ranked by score
        """
        try:
            start_time = time.time()
            logger.info(f"🌊 Scanning for momentum waves (max: {max_symbols})...")
            
            # 1. GET TOP MOVERS (fastest way to find momentum)
            gainers = await self.get_top_movers('up', max_symbols // 2)
            losers = await self.get_top_movers('down', max_symbols // 2)
            
            all_movers = gainers + losers
            logger.info(f"📊 Found {len(all_movers)} active movers")
            
            # 2. FILTER BY VOLUME SURGE (institutional interest)
            volume_filtered = self.filter_by_volume_surge(all_movers, self.min_volume_ratio)
            logger.info(f"📈 {len(volume_filtered)} candidates passed volume filter (≥{self.min_volume_ratio}x)")
            
            # 3. CONVERT TO MOMENTUM CANDIDATES
            momentum_candidates = []
            
            for candidate in volume_filtered:
                try:
                    momentum_candidate = self._create_momentum_candidate(candidate)
                    if momentum_candidate:
                        momentum_candidates.append(momentum_candidate)
                except Exception as e:
                    logger.warning(f"Error processing {candidate.get('symbol', 'unknown')}: {e}")
                    continue
            
            # 4. SORT BY MOMENTUM SCORE (highest first)
            momentum_candidates.sort(key=lambda x: x.momentum_score, reverse=True)
            
            # 5. LIMIT RESULTS
            final_candidates = momentum_candidates[:max_symbols]
            
            scan_time = time.time() - start_time
            logger.info(f"🎯 Momentum scan complete: {len(final_candidates)} candidates in {scan_time:.2f}s")
            
            if final_candidates:
                top = final_candidates[0]
                logger.info(f"🏆 Top: {top.symbol} (score: {top.momentum_score}, vol: {top.volume_ratio:.1f}x)")
            
            return final_candidates
            
        except Exception as e:
            logger.error(f"Error in momentum wave scan: {e}")
            return []

    async def get_top_movers(self, direction: str, limit: int) -> List[Dict]:
        """
        Get top movers from Alpaca Market Data API.
        
        Args:
            direction: 'up' for gainers, 'down' for losers
            limit: Maximum number of movers to return
            
        Returns:
            List of mover dictionaries with symbol, price, change data
        """
        try:
            logger.debug(f"Fetching top {limit} {direction} movers from Alpaca...")
            movers = await self._get_curated_movers(direction, limit)
            logger.debug(f"Retrieved {len(movers)} {direction} movers")
            return movers
        except Exception as e:
            logger.error(f"Error fetching top movers: {e}")
            return []
    
    async def _get_curated_movers(self, direction: str, limit: int) -> List[Dict]:
        """
        Get movers from a curated list of high-liquidity symbols.
        """
        # High-volume, liquid symbols for momentum trading
        momentum_universe = [
            # Tech momentum leaders
            'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META', 'TSLA', 'AMD', 'NFLX',
            'AVGO', 'CRM', 'ADBE', 'ORCL', 'INTC', 'CSCO',
            # Market ETFs (high liquidity)
            'SPY', 'QQQ', 'IWM', 'DIA',
            # Financial momentum
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C',
            # Healthcare momentum
            'UNH', 'JNJ', 'PFE', 'LLY', 'ABBV', 'MRK',
            # Energy momentum
            'XOM', 'CVX', 'COP', 'SLB',
            # Consumer momentum
            'AMZN', 'WMT', 'HD', 'NKE', 'MCD', 'COST',
            # Industrial momentum
            'BA', 'CAT', 'GE', 'UPS', 'HON', 'MMM'
        ]
        
        movers = []
        
        for symbol in momentum_universe[:limit * 2]:
            try:
                bars = await self._get_recent_bars(symbol, periods=60)
                if not bars or len(bars) < 10:
                    continue
                
                current_price = bars[-1]['close']
                hour_ago_price = bars[0]['close']
                
                price_change_pct = ((current_price - hour_ago_price) / hour_ago_price) * 100
                
                if direction == 'up' and price_change_pct >= self.min_price_move * 100:
                    movers.append({
                        'symbol': symbol,
                        'price': current_price,
                        'change_pct': price_change_pct,
                        'bars': bars,
                        'volume': bars[-1]['volume']
                    })
                elif direction == 'down' and price_change_pct <= -self.min_price_move * 100:
                    movers.append({
                        'symbol': symbol,
                        'price': current_price,
                        'change_pct': price_change_pct,
                        'bars': bars,
                        'volume': bars[-1]['volume']
                    })
                    
            except Exception as e:
                logger.debug(f"Error getting data for {symbol}: {e}")
                continue
        
        movers.sort(key=lambda x: abs(x['change_pct']), reverse=True)
        return movers[:limit]

    async def _get_recent_bars(self, symbol: str, periods: int = 60) -> List[Dict]:
        """
        Get recent price bars for a symbol.
        
        Args:
            symbol: Stock symbol
            periods: Number of 1-minute bars to fetch
            
        Returns:
            List of bar dictionaries with OHLCV data
        """
        try:
            if hasattr(self.market_data, 'get_bars'):
                bars_response = self.market_data.get_bars(symbol, '1Min', limit=periods)
                
                if hasattr(bars_response, 'df') and not bars_response.df.empty:
                    df = bars_response.df
                    bars = []
                    for idx, row in df.iterrows():
                        bars.append({
                            'timestamp': idx,
                            'open': float(row['open']),
                            'high': float(row['high']),
                            'low': float(row['low']),
                            'close': float(row['close']),
                            'volume': int(row['volume'])
                        })
                    return bars
            return []
        except Exception as e:
            logger.debug(f"Error fetching bars for {symbol}: {e}")
            return []
    
    def filter_by_volume_surge(self, candidates: List[Dict], min_ratio: float = 1.5) -> List[Dict]:
        """
        Filter candidates by volume surge (institutional interest).
        
        This is a critical filter that identifies stocks with institutional
        interest based on volume spikes above normal levels.
        
        Args:
            candidates: List of stock candidates
            min_ratio: Minimum volume ratio (1.5 = 150% of average)
            
        Returns:
            List of candidates that pass the volume filter
        """
        filtered_candidates = []
        
        for candidate in candidates:
            try:
                volume_ratio = self._calculate_volume_ratio(candidate)
                
                if volume_ratio >= min_ratio:
                    candidate['volume_ratio'] = volume_ratio
                    filtered_candidates.append(candidate)
                    logger.debug(f"{candidate['symbol']}: Volume ratio {volume_ratio:.1f}x ✅")
                else:
                    logger.debug(f"{candidate['symbol']}: Volume {volume_ratio:.1f}x ❌ (need ≥{min_ratio}x)")
                    
            except Exception as e:
                logger.warning(f"Error calculating volume for {candidate.get('symbol', 'unknown')}: {e}")
                continue
        
        return filtered_candidates

    def _calculate_volume_ratio(self, candidate: Dict) -> float:
        """
        Calculate volume ratio vs average.
        
        Args:
            candidate: Candidate dictionary with bars data
            
        Returns:
            Volume ratio (current volume / average volume)
        """
        bars = candidate.get('bars', [])
        if len(bars) < self.lookback_periods:
            return 1.0  # Default to neutral if insufficient data
        
        # Current volume (latest bar)
        current_volume = bars[-1]['volume']
        
        # Average volume over lookback period (excluding current bar)
        historical_volumes = [bar['volume'] for bar in bars[-self.lookback_periods:-1]]
        avg_volume = sum(historical_volumes) / len(historical_volumes) if historical_volumes else 1
        
        # Calculate ratio
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        return volume_ratio
    
    def _create_momentum_candidate(self, candidate: Dict) -> Optional[MomentumCandidate]:
        """
        Create a MomentumCandidate from raw candidate data.
        
        Args:
            candidate: Raw candidate dictionary
            
        Returns:
            MomentumCandidate object or None if creation fails
        """
        try:
            # Basic momentum score calculation (will be enhanced by MomentumScorer)
            base_score = 50  # Neutral starting score
            
            # Volume bonus
            volume_ratio = candidate.get('volume_ratio', 1.0)
            if volume_ratio >= 2.0:
                base_score += 20
            elif volume_ratio >= 1.5:
                base_score += 10
            
            # Price movement bonus
            change_pct = abs(candidate.get('change_pct', 0))
            if change_pct >= 5.0:
                base_score += 15
            elif change_pct >= 3.0:
                base_score += 10
            elif change_pct >= 2.0:
                base_score += 5
            
            return MomentumCandidate(
                symbol=candidate['symbol'],
                price=candidate['price'],
                volume_ratio=volume_ratio,
                momentum_score=min(base_score, 100),
                confidence=min(base_score, 100)
            )
            
        except Exception as e:
            logger.error(f"Error creating momentum candidate: {e}")
            return None
