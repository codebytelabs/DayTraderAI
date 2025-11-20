"""
Test AI-Enhanced Trading System
Tests how OpenRouter AI can improve trading decisions at key decision points
"""
import asyncio
import time
from typing import Dict, List
from advisory.openrouter import OpenRouterClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AIEnhancedTradingTest:
    """Test AI enhancement at various trading decision points"""
    
    def __init__(self):
        self.openrouter = OpenRouterClient()
        self.test_results = []
    
    async def test_signal_validation(self):
        """
        Test 1: AI validates technical signals before execution
        Current: Pure technical (EMA crossover + 4 confirmations)
        Enhanced: Technical + AI validation
        """
        logger.info("\n" + "="*80)
        logger.info("TEST 1: AI SIGNAL VALIDATION")
        logger.info("="*80)
        
        # Simulate a technical signal
        signal_data = {
            'symbol': 'NVDA',
            'signal': 'BUY',
            'price': 199.31,
            'confidence': 85,
            'confirmations': ['rsi', 'macd', 'vwap', 'volume'],
            'features': {
                'ema_9': 198.50,
                'ema_21': 195.20,
                'rsi': 51.7,
                'macd_histogram': 0.45,
                'adx': 28.3,
                'volume_ratio': 1.8,
                'atr': 4.20,
                'vwap': 197.80
            },
            'daily_data': {
                'ema_200': 158.68,
                'trend': 'bullish',
                'distance_from_ema': 25.6
            },
            'market_context': {
                'sentiment': 26,
                'regime': 'trending',
                'sector_performance': 0.8
            }
        }
        
        prompt = f"""Quick validation of this trade signal:

Symbol: {signal_data['symbol']}
Signal: {signal_data['signal']}
Price: ${signal_data['price']}
Technical Confidence: {signal_data['confidence']}%

Confirmations: {', '.join(signal_data['confirmations'])}
Daily Trend: {signal_data['daily_data']['trend']} (above 200-EMA)
Market Sentiment: {signal_data['market_context']['sentiment']}/100 (fear)

Should we take this trade? Answer in 2-3 sentences:
1. YES/NO/MAYBE
2. Key reason
3. Main risk"""

        start_time = time.time()
        
        # Test with primary model (DeepSeek V3.2-Exp)
        response = await self.openrouter.chat_completion(
            messages=[
                {"role": "system", "content": "You are a trading signal validator. Be concise."},
                {"role": "user", "content": prompt}
            ],
            model=self.openrouter.primary_model,
            max_tokens=200
        )
        
        elapsed = time.time() - start_time
        
        logger.info(f"\n📊 Signal: {signal_data['signal']} {signal_data['symbol']} @ ${signal_data['price']}")
        logger.info(f"⏱️  AI Response Time: {elapsed:.2f}s")
        logger.info(f"🤖 AI Validation:\n{response}")
        
        self.test_results.append({
            'test': 'Signal Validation',
            'response_time': elapsed,
            'response': response,
            'acceptable_time': elapsed < 5.0  # Must be under 5s for real-time
        })
        
        return response
    
    async def test_risk_assessment(self):
        """
        Test 2: AI assesses risk before position sizing
        Current: Rule-based risk checks
        Enhanced: Rule-based + AI risk assessment
        """
        logger.info("\n" + "="*80)
        logger.info("TEST 2: AI RISK ASSESSMENT")
        logger.info("="*80)
        
        risk_scenario = {
            'symbol': 'TSLA',
            'signal': 'SHORT',
            'price': 445.21,
            'position_size': 50,
            'position_value': 22260,
            'equity': 138619,
            'position_pct': 16.1,
            'stop_loss': 453.00,
            'take_profit': 429.00,
            'risk_reward': 2.08,
            'symbol_history': {
                'last_3_trades': [-180, -120, -86],
                'win_rate': 0.25,
                'in_cooldown': True,
                'cooldown_hours': 48
            },
            'market_context': {
                'sentiment': 26,
                'market_direction': 'up',
                'sector_performance': 0.8,
                'daily_trend': 'bullish'
            }
        }
        
        prompt = f"""Risk assessment for this trade:

{risk_scenario['signal']} {risk_scenario['symbol']} @ ${risk_scenario['price']}
Position: {risk_scenario['position_size']} shares (${risk_scenario['position_value']:,})
Position Size: {risk_scenario['position_pct']}% of equity

RED FLAGS:
- Symbol in 48h cooldown (3 consecutive losses)
- Win rate on this symbol: {risk_scenario['symbol_history']['win_rate']*100}%
- Shorting against bullish daily trend
- Market trending up today

Risk Score (1-10) and decision (YES/NO) in 2 sentences."""

        start_time = time.time()
        
        response = await self.openrouter.chat_completion(
            messages=[
                {"role": "system", "content": "You are a risk assessment expert. Be direct."},
                {"role": "user", "content": prompt}
            ],
            model=self.openrouter.primary_model,
            max_tokens=150
        )
        
        elapsed = time.time() - start_time
        
        logger.info(f"\n⚠️  Risk Scenario: {risk_scenario['signal']} {risk_scenario['symbol']}")
        logger.info(f"⏱️  AI Response Time: {elapsed:.2f}s")
        logger.info(f"🤖 AI Risk Assessment:\n{response}")
        
        self.test_results.append({
            'test': 'Risk Assessment',
            'response_time': elapsed,
            'response': response,
            'acceptable_time': elapsed < 3.0  # Must be under 3s
        })
        
        return response
    
    async def test_position_sizing_advice(self):
        """
        Test 3: AI advises on position sizing
        Current: Formula-based (confidence * regime * sentiment)
        Enhanced: Formula + AI adjustment
        """
        logger.info("\n" + "="*80)
        logger.info("TEST 3: AI POSITION SIZING ADVICE")
        logger.info("="*80)
        
        sizing_scenario = {
            'symbol': 'AMZN',
            'signal': 'BUY',
            'price': 248.37,
            'confidence': 82,
            'score': 134.6,
            'calculated_size': 55,  # shares
            'calculated_value': 13660,  # dollars
            'equity': 138619,
            'position_pct': 9.9,
            'market_context': {
                'sentiment': 26,  # fear
                'regime': 'trending',
                'volatility': 'moderate'
            }
        }
        
        prompt = f"""Position sizing check:

{sizing_scenario['signal']} {sizing_scenario['symbol']} @ ${sizing_scenario['price']}
Calculated: {sizing_scenario['calculated_size']} shares (${sizing_scenario['calculated_value']:,}, {sizing_scenario['position_pct']}%)
Confidence: {sizing_scenario['confidence']}%
Score: {sizing_scenario['score']} (A+)

Market: Fear (26/100), Trending regime

Is this position size appropriate? Answer: GOOD/REDUCE/INCREASE with 1 sentence why."""

        start_time = time.time()
        
        response = await self.openrouter.chat_completion(
            messages=[
                {"role": "system", "content": "You are a position sizing expert. Be concise."},
                {"role": "user", "content": prompt}
            ],
            model=self.openrouter.secondary_model,  # Use faster model
            max_tokens=100
        )
        
        elapsed = time.time() - start_time
        
        logger.info(f"\n💰 Position Sizing: {sizing_scenario['calculated_size']} shares")
        logger.info(f"⏱️  AI Response Time: {elapsed:.2f}s")
        logger.info(f"🤖 AI Advice:\n{response}")
        
        self.test_results.append({
            'test': 'Position Sizing',
            'response_time': elapsed,
            'response': response,
            'acceptable_time': elapsed < 2.0  # Must be under 2s
        })
        
        return response
    
    async def test_exit_strategy_optimization(self):
        """
        Test 4: AI optimizes exit strategy
        Current: Fixed ATR-based stops (2x ATR stop, 4x ATR target)
        Enhanced: ATR-based + AI optimization
        """
        logger.info("\n" + "="*80)
        logger.info("TEST 4: AI EXIT STRATEGY OPTIMIZATION")
        logger.info("="*80)
        
        exit_scenario = {
            'symbol': 'NVDA',
            'entry_price': 199.31,
            'current_price': 205.50,
            'unrealized_pnl': 309.50,
            'unrealized_pct': 3.1,
            'atr': 4.20,
            'calculated_stop': 195.20,  # entry - 2*ATR
            'calculated_target': 207.71,  # entry + 2*ATR
            'time_in_trade': '2 hours',
            'market_context': {
                'sentiment': 26,
                'volatility_increasing': True,
                'sector_momentum': 'strong'
            }
        }
        
        prompt = f"""Exit strategy for open position:

{exit_scenario['symbol']} @ ${exit_scenario['entry_price']} → ${exit_scenario['current_price']}
P&L: +${exit_scenario['unrealized_pnl']} (+{exit_scenario['unrealized_pct']}%)
Time: {exit_scenario['time_in_trade']}

Current stops:
- Stop Loss: ${exit_scenario['calculated_stop']}
- Take Profit: ${exit_scenario['calculated_target']}

Market: Volatility increasing, strong sector momentum

Should we: HOLD/TIGHTEN_STOP/TAKE_PROFIT? One sentence why."""

        start_time = time.time()
        
        response = await self.openrouter.chat_completion(
            messages=[
                {"role": "system", "content": "You are an exit strategy expert. Be concise."},
                {"role": "user", "content": prompt}
            ],
            model=self.openrouter.secondary_model,
            max_tokens=100
        )
        
        elapsed = time.time() - start_time
        
        logger.info(f"\n📈 Position: {exit_scenario['symbol']} +{exit_scenario['unrealized_pct']}%")
        logger.info(f"⏱️  AI Response Time: {elapsed:.2f}s")
        logger.info(f"🤖 AI Recommendation:\n{response}")
        
        self.test_results.append({
            'test': 'Exit Strategy',
            'response_time': elapsed,
            'response': response,
            'acceptable_time': elapsed < 2.0
        })
        
        return response
    
    async def test_market_regime_confirmation(self):
        """
        Test 5: AI confirms market regime assessment
        Current: ADX-based regime detection
        Enhanced: ADX + AI confirmation
        """
        logger.info("\n" + "="*80)
        logger.info("TEST 5: AI MARKET REGIME CONFIRMATION")
        logger.info("="*80)
        
        regime_data = {
            'detected_regime': 'trending',
            'adx': 28.3,
            'market_data': {
                'spy': {'price': 681.44, 'change': 0.3},
                'qqq': {'price': 623.23, 'change': 0.5},
                'vix': 18.5,
                'fear_greed': 26
            },
            'sector_performance': {
                'technology': 0.8,
                'healthcare': 0.3,
                'financials': -0.2,
                'energy': -0.5
            }
        }
        
        prompt = f"""Market regime check:

Detected: {regime_data['detected_regime'].upper()} (ADX: {regime_data['adx']})

Market Data:
- SPY: +{regime_data['market_data']['spy']['change']}%
- QQQ: +{regime_data['market_data']['qqq']['change']}%
- VIX: {regime_data['market_data']['vix']}
- Fear/Greed: {regime_data['market_data']['fear_greed']}/100

Confirm regime: TRENDING/RANGING/CHOPPY? One sentence."""

        start_time = time.time()
        
        response = await self.openrouter.chat_completion(
            messages=[
                {"role": "system", "content": "You are a market regime expert. Be concise."},
                {"role": "user", "content": prompt}
            ],
            model=self.openrouter.tertiary_model,  # Use fastest model
            max_tokens=50
        )
        
        elapsed = time.time() - start_time
        
        logger.info(f"\n🌊 Detected Regime: {regime_data['detected_regime']}")
        logger.info(f"⏱️  AI Response Time: {elapsed:.2f}s")
        logger.info(f"🤖 AI Confirmation:\n{response}")
        
        self.test_results.append({
            'test': 'Market Regime',
            'response_time': elapsed,
            'response': response,
            'acceptable_time': elapsed < 1.5
        })
        
        return response
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("\n" + "="*80)
        logger.info("🧪 AI-ENHANCED TRADING SYSTEM TEST")
        logger.info("="*80)
        logger.info("Testing how OpenRouter AI can enhance trading decisions")
        logger.info("")
        
        # Run all tests
        await self.test_signal_validation()
        await asyncio.sleep(2)  # Rate limiting
        
        await self.test_risk_assessment()
        await asyncio.sleep(2)
        
        await self.test_position_sizing_advice()
        await asyncio.sleep(2)
        
        await self.test_exit_strategy_optimization()
        await asyncio.sleep(2)
        
        await self.test_market_regime_confirmation()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary and recommendations"""
        logger.info("\n" + "="*80)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*80)
        
        total_tests = len(self.test_results)
        passed_time = sum(1 for r in self.test_results if r['acceptable_time'])
        avg_time = sum(r['response_time'] for r in self.test_results) / total_tests
        
        logger.info(f"\nTotal Tests: {total_tests}")
        logger.info(f"Time Requirements Met: {passed_time}/{total_tests}")
        logger.info(f"Average Response Time: {avg_time:.2f}s")
        logger.info("")
        
        for result in self.test_results:
            status = "✅" if result['acceptable_time'] else "❌"
            logger.info(f"{status} {result['test']}: {result['response_time']:.2f}s")
        
        logger.info("\n" + "="*80)
        logger.info("💡 RECOMMENDATIONS")
        logger.info("="*80)
        
        if passed_time == total_tests:
            logger.info("✅ All tests passed! AI enhancement is FEASIBLE for real-time trading")
            logger.info("")
            logger.info("Recommended Integration Points:")
            logger.info("1. Signal Validation: Add AI check before order submission")
            logger.info("2. Risk Assessment: AI validates high-risk trades")
            logger.info("3. Position Sizing: AI adjusts calculated sizes")
            logger.info("4. Exit Strategy: AI optimizes stop/target placement")
            logger.info("5. Market Regime: AI confirms regime detection")
        else:
            logger.info("⚠️  Some tests failed time requirements")
            logger.info("Consider using AI only for non-time-critical decisions")
        
        logger.info("\n" + "="*80)


async def main():
    tester = AIEnhancedTradingTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
