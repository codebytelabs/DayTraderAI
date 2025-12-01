#!/usr/bin/env python3
"""
Resistance Analyzer - Find resistance levels and calculate room to run

This analyzer prevents chasing stocks at the top by:
1. Finding next major resistance level
2. Calculating distance to resistance (upside potential)
3. Finding support level for stop placement
4. Calculating risk/reward ratio
5. Classifying upside quality

Key insight: A stock with great momentum but only 0.5% to resistance
is a BAD trade. We need ROOM TO RUN.
"""

import logging
from typing import List, Dict, Optional, Tuple
import statistics

logger = logging.getLogger(__name__)


class ResistanceAnalyzer:
    """
    Analyzes price levels to find resistance and calculate room to run.
    This prevents chasing stocks at the top.
    """
    
    def __init__(self):
        self.lookback_periods = 20
        logger.info("✅ ResistanceAnalyzer initialized - upside potential analysis ready")
    
    def find_resistance_level(self, bars: List[Dict], lookback: int = 20) -> float:
        """
        Find the next major resistance level using recent highs and pivot points.
        
        Methods:
        - Recent swing highs (local maxima)
        - Round number levels ($50, $100, etc.)
        - Previous day high
        
        Args:
            bars: List of OHLCV bars
            lookback: Number of bars to analyze
            
        Returns:
            Resistance level price
        """
        if not bars or len(bars) < 3:
            return 0.0
        
        current_price = bars[-1]['close']
        recent_bars = bars[-lookback:] if len(bars) >= lookback else bars
        
        # Method 1: Find swing highs (local maxima)
        swing_highs = self._find_swing_highs(recent_bars)
        
        # Method 2: Find round number resistance
        round_resistance = self._find_round_number_resistance(current_price)
        
        # Method 3: Recent high
        recent_high = max(bar['high'] for bar in recent_bars)
        
        # Combine methods - find nearest resistance ABOVE current price
        resistance_levels = []
        
        for high in swing_highs:
            if high > current_price * 1.001:  # At least 0.1% above
                resistance_levels.append(high)
        
        if round_resistance > current_price * 1.001:
            resistance_levels.append(round_resistance)
        
        if recent_high > current_price * 1.001:
            resistance_levels.append(recent_high)
        
        if not resistance_levels:
            # No clear resistance - use 5% above as default
            return current_price * 1.05
        
        # Return the nearest resistance above current price
        return min(resistance_levels)
    
    def _find_swing_highs(self, bars: List[Dict], window: int = 3) -> List[float]:
        """
        Find swing highs (local maxima) in price data.
        
        A swing high is a bar where the high is higher than
        the highs of the bars on either side.
        """
        swing_highs = []
        
        for i in range(window, len(bars) - window):
            current_high = bars[i]['high']
            is_swing_high = True
            
            # Check if current high is higher than surrounding bars
            for j in range(1, window + 1):
                if bars[i - j]['high'] >= current_high or bars[i + j]['high'] >= current_high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append(current_high)
        
        return swing_highs
    
    def _find_round_number_resistance(self, price: float) -> float:
        """
        Find the next round number resistance level.
        
        Round numbers act as psychological resistance:
        - $50, $100, $150, etc. for stocks
        - $10, $20, $30 for lower-priced stocks
        """
        if price < 10:
            increment = 1
        elif price < 50:
            increment = 5
        elif price < 100:
            increment = 10
        elif price < 500:
            increment = 25
        else:
            increment = 50
        
        # Find next round number above current price
        next_round = ((int(price) // increment) + 1) * increment
        return float(next_round)

    def find_support_level(self, bars: List[Dict], lookback: int = 20) -> float:
        """
        Find recent support level using recent lows.
        
        Methods:
        - Recent swing lows (local minima)
        - Previous day low
        - Round number support
        
        Args:
            bars: List of OHLCV bars
            lookback: Number of bars to analyze
            
        Returns:
            Support level price
        """
        if not bars or len(bars) < 3:
            return 0.0
        
        current_price = bars[-1]['close']
        recent_bars = bars[-lookback:] if len(bars) >= lookback else bars
        
        # Method 1: Find swing lows (local minima)
        swing_lows = self._find_swing_lows(recent_bars)
        
        # Method 2: Recent low
        recent_low = min(bar['low'] for bar in recent_bars)
        
        # Combine methods - find nearest support BELOW current price
        support_levels = []
        
        for low in swing_lows:
            if low < current_price * 0.999:  # At least 0.1% below
                support_levels.append(low)
        
        if recent_low < current_price * 0.999:
            support_levels.append(recent_low)
        
        if not support_levels:
            # No clear support - use 3% below as default (typical stop distance)
            return current_price * 0.97
        
        # Return the nearest support below current price
        return max(support_levels)
    
    def _find_swing_lows(self, bars: List[Dict], window: int = 3) -> List[float]:
        """
        Find swing lows (local minima) in price data.
        
        A swing low is a bar where the low is lower than
        the lows of the bars on either side.
        """
        swing_lows = []
        
        for i in range(window, len(bars) - window):
            current_low = bars[i]['low']
            is_swing_low = True
            
            # Check if current low is lower than surrounding bars
            for j in range(1, window + 1):
                if bars[i - j]['low'] <= current_low or bars[i + j]['low'] <= current_low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append(current_low)
        
        return swing_lows
    
    def calculate_upside_percentage(self, price: float, resistance: float) -> float:
        """
        Calculate percentage distance from current price to resistance.
        
        Args:
            price: Current price
            resistance: Resistance level
            
        Returns:
            Percentage distance to resistance
        """
        if price <= 0 or resistance <= 0:
            return 0.0
        
        return ((resistance - price) / price) * 100
    
    def calculate_risk_reward_ratio(self, price: float, resistance: float, support: float) -> float:
        """
        Calculate risk/reward ratio.
        
        Reward = resistance - price (potential upside)
        Risk = price - support (potential downside to stop)
        R/R = Reward / Risk
        
        Args:
            price: Current price
            resistance: Target/resistance level
            support: Stop/support level
            
        Returns:
            Risk/reward ratio (higher is better)
        """
        if price <= 0 or resistance <= 0 or support <= 0:
            return 0.0
        
        if support >= price:
            return 0.0  # Invalid - support should be below price
        
        reward = resistance - price  # Potential upside
        risk = price - support       # Potential downside
        
        if risk <= 0:
            return 0.0
        
        return reward / risk
    
    def classify_upside_quality(self, upside_pct: float) -> str:
        """
        Classify the upside quality based on distance to resistance.
        
        - >5%: 'excellent' - lots of room to run
        - 3-5%: 'good' - decent room
        - 2-3%: 'some' - limited but acceptable
        - 1-2%: 'limited' - tight, be careful
        - <1%: 'poor' - no room, avoid!
        
        Args:
            upside_pct: Percentage distance to resistance
            
        Returns:
            Quality classification string
        """
        if upside_pct > 5.0:
            return "excellent"
        elif upside_pct > 3.0:
            return "good"
        elif upside_pct > 2.0:
            return "some"
        elif upside_pct > 1.0:
            return "limited"
        else:
            return "poor"

    def analyze(self, bars: List[Dict]) -> Dict:
        """
        Full resistance/support analysis for a stock.
        
        Args:
            bars: List of OHLCV bars
            
        Returns:
            Dictionary with resistance, support, upside, R/R, and quality
        """
        if not bars:
            return {
                'resistance': 0.0,
                'support': 0.0,
                'price': 0.0,
                'upside_pct': 0.0,
                'risk_reward': 0.0,
                'quality': 'poor'
            }
        
        price = bars[-1]['close']
        resistance = self.find_resistance_level(bars)
        support = self.find_support_level(bars)
        upside_pct = self.calculate_upside_percentage(price, resistance)
        risk_reward = self.calculate_risk_reward_ratio(price, resistance, support)
        quality = self.classify_upside_quality(upside_pct)
        
        logger.debug(f"Resistance analysis: price=${price:.2f}, resistance=${resistance:.2f}, "
                    f"support=${support:.2f}, upside={upside_pct:.1f}%, R/R={risk_reward:.1f}, "
                    f"quality={quality}")
        
        return {
            'resistance': resistance,
            'support': support,
            'price': price,
            'upside_pct': upside_pct,
            'risk_reward': risk_reward,
            'quality': quality
        }
    
    def should_trade(self, bars: List[Dict], min_upside: float = 1.0, min_rr: float = 1.5) -> Tuple[bool, str]:
        """
        Determine if a stock should be traded based on upside potential.
        
        Args:
            bars: List of OHLCV bars
            min_upside: Minimum upside percentage required
            min_rr: Minimum risk/reward ratio required
            
        Returns:
            Tuple of (should_trade, reason)
        """
        analysis = self.analyze(bars)
        
        if analysis['upside_pct'] < min_upside:
            return False, f"Insufficient upside: {analysis['upside_pct']:.1f}% (need {min_upside}%)"
        
        if analysis['risk_reward'] < min_rr:
            return False, f"Poor R/R: {analysis['risk_reward']:.1f} (need {min_rr})"
        
        if analysis['quality'] == 'poor':
            return False, "Poor upside quality - too close to resistance"
        
        return True, f"Good setup: {analysis['upside_pct']:.1f}% upside, {analysis['risk_reward']:.1f} R/R"
