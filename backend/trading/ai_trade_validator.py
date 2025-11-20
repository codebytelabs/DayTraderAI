"""
AI Trade Validator
Validates high-risk trades before execution using DeepSeek AI
"""
import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime
from advisory.openrouter import OpenRouterClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AITradeValidator:
    """
    Validates high-risk trades using AI before execution.
    Only validates trades that meet high-risk criteria to minimize latency.
    """
    
    def __init__(self):
        self.openrouter = OpenRouterClient()
        self.validation_count = 0
        self.rejection_count = 0
        self.approval_count = 0
        self.error_count = 0
        self.total_validation_time = 0.0
        
        logger.info("🤖 AI Trade Validator initialized (DeepSeek V3.2-Exp)")
    
    def is_high_risk(self, symbol: str, signal: str, context: Dict) -> Tuple[bool, str]:
        """
        Determine if trade is high-risk and needs AI validation.
        
        Returns:
            (is_high_risk, reason)
        """
        reasons = []
        
        # Check 1: Symbol in cooldown
        if context.get('in_cooldown', False):
            reasons.append(f"in {context.get('cooldown_hours', 0)}h cooldown")
        
        # Check 2: Low win rate on symbol
        win_rate = context.get('symbol_win_rate', 1.0)
        if win_rate < 0.40:
            reasons.append(f"low win rate ({win_rate*100:.0f}%)")
        
        # Check 3: Large position size
        position_pct = context.get('position_pct', 0)
        if position_pct > 8.0:
            reasons.append(f"large position ({position_pct:.1f}%)")
        
        # Check 4: Counter-trend trade
        if context.get('counter_trend', False):
            reasons.append("counter-trend")
        
        # Check 5: Low confidence
        confidence = context.get('confidence', 100)
        if confidence < 75:
            reasons.append(f"low confidence ({confidence}%)")
        
        # Check 6: Consecutive losses
        consecutive_losses = context.get('consecutive_losses', 0)
        if consecutive_losses >= 2:
            reasons.append(f"{consecutive_losses} consecutive losses")
        
        if reasons:
            return True, ", ".join(reasons)
        
        return False, ""
    
    async def validate(
        self,
        symbol: str,
        signal: str,
        features: Dict,
        context: Dict,
        timeout: float = 3.5
    ) -> Tuple[bool, str]:
        """
        Validate trade with AI.
        
        Args:
            symbol: Stock symbol
            signal: 'buy' or 'sell'
            features: Technical indicators
            context: Risk context (cooldown, win rate, etc.)
            timeout: Max time to wait for AI response
        
        Returns:
            (approved, reason)
        """
        self.validation_count += 1
        start_time = datetime.now()
        
        try:
            # Build concise prompt
            prompt = self._build_validation_prompt(symbol, signal, features, context)
            
            # Quick AI validation with timeout
            response = await asyncio.wait_for(
                self.openrouter.chat_completion(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a trade risk validator. Answer YES or NO with one brief sentence explaining why."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=self.openrouter.primary_model,
                    max_tokens=100
                ),
                timeout=timeout
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            self.total_validation_time += elapsed
            
            if not response:
                logger.warning("🤖 AI validation returned no response, failing open")
                self.error_count += 1
                return True, "AI no response"
            
            # Parse decision
            response_upper = response.upper()
            
            if "NO" in response_upper and "NO" in response_upper[:20]:
                # AI rejected
                self.rejection_count += 1
                logger.warning(f"🤖 AI REJECTED {signal.upper()} {symbol} ({elapsed:.2f}s): {response}")
                return False, response
            else:
                # AI approved
                self.approval_count += 1
                logger.info(f"🤖 AI APPROVED {signal.upper()} {symbol} ({elapsed:.2f}s)")
                return True, response
        
        except asyncio.TimeoutError:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.warning(f"🤖 AI validation timeout ({elapsed:.2f}s), failing open")
            self.error_count += 1
            return True, "Timeout - failed open"
        
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"🤖 AI validation error ({elapsed:.2f}s): {e}")
            self.error_count += 1
            # Fail open - allow trade if AI fails
            return True, f"Error: {str(e)}"
    
    def _build_validation_prompt(
        self,
        symbol: str,
        signal: str,
        features: Dict,
        context: Dict
    ) -> str:
        """Build concise validation prompt"""
        
        # Extract key data
        price = features.get('price', 0)
        confidence = context.get('confidence', 0)
        position_pct = context.get('position_pct', 0)
        
        # Build risk factors list
        risk_factors = []
        
        if context.get('in_cooldown'):
            cooldown_hours = context.get('cooldown_hours', 0)
            consecutive_losses = context.get('consecutive_losses', 0)
            risk_factors.append(f"In {cooldown_hours}h cooldown ({consecutive_losses} losses)")
        
        if context.get('symbol_win_rate', 1.0) < 0.40:
            win_rate = context.get('symbol_win_rate', 0) * 100
            risk_factors.append(f"Low win rate: {win_rate:.0f}%")
        
        if position_pct > 8.0:
            risk_factors.append(f"Large position: {position_pct:.1f}% of equity")
        
        if context.get('counter_trend'):
            daily_trend = context.get('daily_trend', 'unknown')
            risk_factors.append(f"Counter-trend: {signal} against {daily_trend} daily trend")
        
        if confidence < 75:
            risk_factors.append(f"Low confidence: {confidence}%")
        
        # Format risk factors
        risk_text = "\n".join(f"- {rf}" for rf in risk_factors) if risk_factors else "- None"
        
        # Build prompt
        prompt = f"""Validate this HIGH-RISK trade:

{signal.upper()} {symbol} @ ${price:.2f}
Confidence: {confidence}%
Position Size: {position_pct:.1f}% of equity

Risk Factors:
{risk_text}

Should we take this trade? Answer YES or NO with one sentence explaining the key reason."""
        
        return prompt
    
    def get_stats(self) -> Dict:
        """Get validation statistics"""
        avg_time = (
            self.total_validation_time / self.validation_count
            if self.validation_count > 0
            else 0
        )
        
        return {
            'total_validations': self.validation_count,
            'approvals': self.approval_count,
            'rejections': self.rejection_count,
            'errors': self.error_count,
            'rejection_rate': (
                self.rejection_count / self.validation_count
                if self.validation_count > 0
                else 0
            ),
            'avg_validation_time': avg_time
        }
    
    def log_stats(self):
        """Log validation statistics"""
        stats = self.get_stats()
        
        logger.info("🤖 AI Trade Validator Statistics:")
        logger.info(f"   Total Validations: {stats['total_validations']}")
        logger.info(f"   Approvals: {stats['approvals']}")
        logger.info(f"   Rejections: {stats['rejections']}")
        logger.info(f"   Errors: {stats['errors']}")
        logger.info(f"   Rejection Rate: {stats['rejection_rate']*100:.1f}%")
        logger.info(f"   Avg Time: {stats['avg_validation_time']:.2f}s")
