#!/usr/bin/env python3
"""
Momentum Scorer - Score candidates based on momentum AND upside potential

This scorer rewards:
1. Volume surges (institutional interest)
2. Strong momentum (ADX > 25, RSI in zone)
3. Fresh breakouts (not extended moves)
4. Room to run (distance to resistance)
5. Multi-timeframe alignment

It penalizes:
- Overbought/oversold conditions (RSI > 75 or < 25)
- Extended moves (EMA diff > 1%)
- Insufficient room (<1% to resistance)
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass

from scanner.momentum_models import MomentumCandidate, MomentumScore

logger = logging.getLogger(__name__)


class MomentumScorer:
    """
    Momentum-focused scoring system.
    Rewards active momentum WITH room to run.
    
    Scoring breakdown (0-100 points):
    - Volume Score: 0-25 pts
    - Momentum Score: 0-20 pts (ADX + RSI)
    - Breakout Score: 0-20 pts
    - Upside Potential: 0-25 pts (KEY - room to run)
    - Trend Score: 0-10 pts
    - Penalties: up to -35 pts
    - Bonuses: up to +20 pts
    """
    
    def __init__(self):
        logger.info("✅ MomentumScorer initialized with upside analysis")
    
    def calculate_score(self, features: Dict) -> MomentumScore:
        """
        Calculate momentum score (0-100) based on technical indicators.
        
        Args:
            features: Dictionary with technical indicators
            
        Returns:
            MomentumScore with detailed breakdown
        """
        score = MomentumScore()
        
        # Extract features with defaults
        volume_ratio = features.get('volume_ratio', 1.0)
        adx = features.get('adx', 0.0)
        rsi = features.get('rsi', 50.0)
        ema_diff = features.get('ema_diff', 0.0)
        price = features.get('price', 0.0)
        resistance = features.get('resistance', 0.0)
        support = features.get('support', 0.0)
        vwap_distance = features.get('vwap_distance', 1.0)
        multi_tf_aligned = features.get('multi_tf_aligned', False)
        
        # Calculate component scores
        score.volume_score = self.calculate_volume_score(volume_ratio)
        score.momentum_score = self.calculate_momentum_score(adx, rsi)
        score.breakout_score = self.calculate_breakout_score(price, resistance, ema_diff)
        score.upside_score = self.calculate_upside_potential(price, resistance, support)
        score.trend_score = self.calculate_trend_score(multi_tf_aligned)
        
        # Apply penalties
        penalties = self.apply_penalties(rsi, ema_diff, price, resistance)
        score.overbought_penalty = penalties.get('overbought', 0)
        score.extended_penalty = penalties.get('extended', 0)
        score.insufficient_room_penalty = penalties.get('insufficient_room', 0)
        
        # Apply bonuses
        bonuses = self.apply_bonuses(price, resistance, support, vwap_distance, multi_tf_aligned)
        score.rr_bonus = bonuses.get('rr_bonus', 0)
        score.vwap_bonus = bonuses.get('vwap_bonus', 0)
        score.timeframe_bonus = bonuses.get('timeframe_bonus', 0)
        
        # Calculate total
        score.calculate_total()
        
        logger.debug(f"Score breakdown: vol={score.volume_score}, mom={score.momentum_score}, "
                    f"brk={score.breakout_score}, up={score.upside_score}, trend={score.trend_score}, "
                    f"penalties={score.overbought_penalty + score.extended_penalty + score.insufficient_room_penalty}, "
                    f"total={score.total_score}")
        
        return score

    def calculate_volume_score(self, volume_ratio: float) -> int:
        """
        Calculate volume score (0-25 points).
        
        Volume indicates institutional interest:
        - 200%+ volume: 25 points (strong institutional buying)
        - 150-200%: 20 points
        - 100-150%: 10 points
        - <100%: 0 points
        
        Args:
            volume_ratio: Current volume / 20-period average
            
        Returns:
            Volume score (0-25)
        """
        if volume_ratio >= 2.0:
            return 25
        elif volume_ratio >= 1.5:
            return 20
        elif volume_ratio >= 1.0:
            return 10
        else:
            return 0
    
    def calculate_momentum_score(self, adx: float, rsi: float) -> int:
        """
        Calculate momentum score (0-20 points).
        
        - ADX > 25: 12 points (strong trend)
        - RSI 40-70: 8 points (momentum zone, not overbought/oversold)
        
        Args:
            adx: Average Directional Index
            rsi: Relative Strength Index
            
        Returns:
            Momentum score (0-20)
        """
        score = 0
        
        # ADX component (0-12 pts)
        if adx > 25:
            score += 12
        elif adx > 20:
            score += 8
        elif adx > 15:
            score += 4
        
        # RSI component (0-8 pts) - momentum zone
        if 40 <= rsi <= 70:
            score += 8
        elif 30 <= rsi <= 75:
            score += 4
        
        return min(score, 20)
    
    def calculate_breakout_score(self, price: float, resistance: float, ema_diff: float) -> int:
        """
        Calculate breakout score (0-20 points).
        
        - Price above resistance: 12 points
        - Fresh EMA crossover (0.05-0.3%): 8 points
        
        Args:
            price: Current price
            resistance: Recent resistance level
            ema_diff: EMA9 - EMA21 as percentage
            
        Returns:
            Breakout score (0-20)
        """
        score = 0
        
        # Price vs resistance (0-12 pts)
        if resistance > 0 and price > resistance:
            score += 12
        elif resistance > 0 and price > resistance * 0.99:  # Within 1% of resistance
            score += 6
        
        # EMA crossover freshness (0-8 pts)
        ema_diff_abs = abs(ema_diff)
        if 0.05 <= ema_diff_abs <= 0.3:
            score += 8  # Fresh crossover - ideal
        elif 0.3 < ema_diff_abs <= 0.6:
            score += 5  # Developing
        elif 0.6 < ema_diff_abs <= 1.0:
            score += 2  # Getting extended
        
        return min(score, 20)

    def calculate_upside_potential(self, price: float, resistance: float, support: float) -> int:
        """
        Calculate upside potential score (0-25 points).
        
        This is the KEY addition - measures room to run!
        Prevents chasing stocks at the top.
        
        - Distance to resistance > 5%: 25 points (excellent room)
        - Distance to resistance 3-5%: 20 points (good room)
        - Distance to resistance 2-3%: 15 points (some room)
        - Distance to resistance 1-2%: 10 points (limited room)
        - Distance to resistance < 1%: 0 points (no room)
        
        Args:
            price: Current price
            resistance: Next resistance level
            support: Recent support level
            
        Returns:
            Upside potential score (0-25)
        """
        if price <= 0 or resistance <= 0:
            return 0
        
        # Calculate distance to resistance as percentage
        upside_pct = ((resistance - price) / price) * 100
        
        # Score based on room to run
        if upside_pct > 5.0:
            return 25  # Excellent room
        elif upside_pct > 3.0:
            return 20  # Good room
        elif upside_pct > 2.0:
            return 15  # Some room
        elif upside_pct > 1.0:
            return 10  # Limited room
        else:
            return 0   # No room - will also get penalty
    
    def calculate_trend_score(self, multi_tf_aligned: bool) -> int:
        """
        Calculate trend score (0-10 points).
        
        - Multi-timeframe alignment: 10 points
        - Single timeframe: 5 points
        
        Args:
            multi_tf_aligned: Whether multiple timeframes show same direction
            
        Returns:
            Trend score (0-10)
        """
        if multi_tf_aligned:
            return 10
        return 5  # Default for single timeframe
    
    def apply_penalties(self, rsi: float, ema_diff: float, price: float, resistance: float) -> Dict[str, int]:
        """
        Apply penalties for overbought/oversold, extended moves, and no room.
        
        - RSI > 75 or < 25: -20 points (overbought/oversold)
        - EMA diff > 1%: -15 points (extended move)
        - Upside < 1%: -15 points (no room to run)
        
        Args:
            rsi: Relative Strength Index
            ema_diff: EMA difference as percentage
            price: Current price
            resistance: Resistance level
            
        Returns:
            Dictionary of penalties
        """
        penalties = {
            'overbought': 0,
            'extended': 0,
            'insufficient_room': 0
        }
        
        # Overbought/oversold penalty
        if rsi > 75 or rsi < 25:
            penalties['overbought'] = 20
            logger.debug(f"Overbought/oversold penalty: RSI={rsi}")
        
        # Extended move penalty
        if abs(ema_diff) > 1.0:
            penalties['extended'] = 15
            logger.debug(f"Extended move penalty: EMA diff={ema_diff}%")
        
        # Insufficient room penalty
        if price > 0 and resistance > 0:
            upside_pct = ((resistance - price) / price) * 100
            if upside_pct < 1.0:
                penalties['insufficient_room'] = 15
                logger.debug(f"Insufficient room penalty: {upside_pct:.1f}% to resistance")
        
        return penalties

    def apply_bonuses(self, price: float, resistance: float, support: float, 
                      vwap_distance: float, multi_tf_aligned: bool) -> Dict[str, int]:
        """
        Apply bonuses for good risk/reward, VWAP proximity, and timeframe alignment.
        
        - R/R ratio > 3:1: +5 bonus points
        - R/R ratio > 2:1: +3 bonus points
        - Within 0.5% of VWAP: +5 points
        - Multi-timeframe aligned: +10 points (already in trend_score)
        
        Args:
            price: Current price
            resistance: Resistance level
            support: Support level
            vwap_distance: Distance from VWAP as percentage
            multi_tf_aligned: Whether multiple timeframes align
            
        Returns:
            Dictionary of bonuses
        """
        bonuses = {
            'rr_bonus': 0,
            'vwap_bonus': 0,
            'timeframe_bonus': 0
        }
        
        # Risk/Reward bonus
        if price > 0 and resistance > 0 and support > 0 and support < price:
            reward = resistance - price  # Potential upside
            risk = price - support       # Potential downside to stop
            
            if risk > 0:
                rr_ratio = reward / risk
                if rr_ratio > 3.0:
                    bonuses['rr_bonus'] = 5
                    logger.debug(f"R/R bonus +5: ratio={rr_ratio:.1f}")
                elif rr_ratio > 2.0:
                    bonuses['rr_bonus'] = 3
                    logger.debug(f"R/R bonus +3: ratio={rr_ratio:.1f}")
        
        # VWAP proximity bonus
        if abs(vwap_distance) <= 0.5:
            bonuses['vwap_bonus'] = 5
            logger.debug(f"VWAP bonus +5: distance={vwap_distance:.2f}%")
        
        # Timeframe alignment bonus (handled in trend_score, but can add extra)
        if multi_tf_aligned:
            bonuses['timeframe_bonus'] = 0  # Already counted in trend_score
        
        return bonuses
    
    def score_candidate(self, candidate: MomentumCandidate, features: Dict) -> MomentumCandidate:
        """
        Score a momentum candidate and update its scores.
        
        Args:
            candidate: MomentumCandidate to score
            features: Technical indicator features
            
        Returns:
            Updated MomentumCandidate with scores
        """
        score = self.calculate_score(features)
        
        # Update candidate with scores
        candidate.volume_score = score.volume_score
        candidate.trend_strength_score = score.momentum_score
        candidate.breakout_score = score.breakout_score
        candidate.upside_score = score.upside_score
        candidate.trend_score = score.trend_score
        candidate.momentum_score = score.total_score
        candidate.confidence = score.total_score
        
        # Update resistance analysis
        candidate.resistance_level = features.get('resistance', 0.0)
        candidate.support_level = features.get('support', 0.0)
        
        if candidate.price > 0 and candidate.resistance_level > 0:
            candidate.distance_to_resistance = (
                (candidate.resistance_level - candidate.price) / candidate.price * 100
            )
        
        if candidate.support_level > 0 and candidate.support_level < candidate.price:
            reward = candidate.resistance_level - candidate.price
            risk = candidate.price - candidate.support_level
            if risk > 0:
                candidate.risk_reward_ratio = reward / risk
        
        # Classify upside quality
        candidate.upside_quality = self._classify_upside(candidate.distance_to_resistance)
        
        return candidate
    
    def _classify_upside(self, distance_pct: float) -> str:
        """Classify upside quality based on distance to resistance."""
        if distance_pct > 5.0:
            return "excellent"
        elif distance_pct > 3.0:
            return "good"
        elif distance_pct > 2.0:
            return "some"
        elif distance_pct > 1.0:
            return "limited"
        else:
            return "poor"
