"""
Real AI Model Comparison Test
Tests actual API calls to compare model performance for trading analysis
"""
import asyncio
import time
import json
from typing import Dict, List
from advisory.openrouter import OpenRouterClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Test scenarios focused on trading
TRADE_ANALYSIS_PROMPT = """Analyze this trade setup:

Symbol: NVDA
Action: BUY
Price: $199.31
Confidence: 85%

Technical Indicators:
- EMA(9): $198.50 (bullish crossover)
- EMA(21): $195.20
- RSI: 51.7 (neutral, room to run)
- MACD Histogram: +0.45 (positive momentum)
- ADX: 28.3 (trending market)
- Volume Ratio: 1.8x (above average)
- ATR: $4.20 (volatility measure)
- VWAP: $197.80 (price above VWAP)

Daily Data:
- 200-EMA: $158.68
- Trend: Bullish (price 25.6% above 200-EMA)
- Distance from 200-EMA: Strong uptrend

Market Context:
- Sentiment: 26/100 (fear - contrarian opportunity)
- Market Regime: Trending
- Sector: Technology (+0.8% today)

Provide:
1. Trade quality score (1-10) with reasoning
2. Top 3 risks
3. Top 3 opportunities
4. Position size recommendation (conservative/normal/aggressive)
5. Exit strategy (stop loss and take profit levels)

Be concise but thorough. Focus on actionable insights."""

RISK_ASSESSMENT_PROMPT = """Assess risk for this proposed trade:

Symbol: TSLA
Action: SHORT
Price: $445.21
Shares: 50
Position Value: $22,260 (16.1% of equity)

Stop Loss: $453.00 (+1.75%)
Take Profit: $429.00 (-3.64%)
Risk/Reward: 1:2.08

Account Context:
- Equity: $138,619
- Daily P/L: +$2,300 (+1.69%)
- Open Positions: 8/20
- Available Buying Power: $45,000

Symbol History:
- TSLA in 48h cooldown (3 consecutive losses)
- Last 3 trades: -$180, -$120, -$86
- Win rate on TSLA: 25% (1/4 trades)

Market Context:
- Sentiment: 26/100 (fear)
- Market trending up today
- Tech sector: +0.8%
- TSLA daily trend: Bullish (above 200-EMA)

Technical Analysis:
- RSI: 51.5 (neutral)
- MACD: Slightly bearish divergence
- Volume: 4.4x average (high activity)
- ADX: 9.9 (weak trend, choppy)

Should this trade be taken?
1. Risk score (1-10, 10=highest risk)
2. Decision: Yes/No/Maybe with reasoning
3. Top 3 risk factors
4. Recommended adjustments if taking
5. Alternative strategy if rejecting

Be direct and risk-focused."""

MARKET_ANALYSIS_PROMPT = """Analyze current market conditions and provide trading strategy:

Market Data:
- S&P 500 (SPY): $681.44 (+0.3%)
- Nasdaq (QQQ): $623.23 (+0.5%)
- VIX: 18.5 (moderate volatility)
- Fear & Greed Index: 26/100 (fear)

Top Opportunities (AI-discovered):
1. AMZN: Score 134.6 (A+) - Bullish, above 200-EMA, strong momentum
2. AMD: Score 128.6 (A+) - Bullish, breakout pattern
3. AAPL: Score 126.6 (A+) - Bullish, trend aligned
4. NVDA: Score 125.6 (A+) - Bullish, high volume
5. TSLA: Score 123.6 (A+) - Bullish, but risky

Sector Performance:
- Technology: +0.8%
- Healthcare: +0.3%
- Financials: -0.2%
- Energy: -0.5%

Provide:
1. Overall market sentiment (bullish/bearish/neutral) with reasoning
2. Best sectors to trade today
3. Risk level (1-10) for day trading
4. Recommended strategy (aggressive/balanced/defensive)
5. Top 3 opportunities to focus on
6. Top 3 risks to watch

Be strategic and actionable."""

MULTI_STEP_REASONING_PROMPT = """Complex trading scenario requiring multi-step reasoning:

I have $50,000 buying power and want to optimize today's trades.

Current Portfolio:
- 8 positions (60% tech, 20% healthcare, 20% financials)
- Daily P/L: +$2,300 (+1.69%)
- All positions green except TSLA (-$80)

Available Opportunities (Top 5):
1. AMZN: $248.37, Score 134.6, Confidence 82%, Bullish
2. AMD: $244.03, Score 128.6, Confidence 78%, Bullish
3. DKNG: $30.54, Score 113.6, Confidence 75%, Bullish
4. SNOW: $268.56, Score 112.6, Confidence 74%, Bullish
5. COIN: $98.60, Score 110.2, Confidence 72%, Bullish

Constraints:
- Max 20 positions total (currently 8)
- Max 10% per position ($13,862)
- Max 30 trades/day (used 12 so far)
- Risk per trade: 1% ($1,386)

Market Conditions:
- Sentiment: 26/100 (fear)
- Regime: Trending
- Tech sector: +0.8%

Questions:
1. Which 3 symbols should I trade and why?
2. What position size for each (shares and $)?
3. What's my total risk exposure?
4. Should I close TSLA first?
5. What's my profit target for the day?

Provide a complete trading plan with step-by-step reasoning."""


async def test_model(model_name: str, prompt: str, scenario_name: str) -> Dict:
    """Test a single model with a prompt"""
    client = OpenRouterClient()
    
    start_time = time.time()
    
    try:
        response = await client.chat_completion(
            messages=[
                {"role": "system", "content": "You are an expert day trading analyst. Provide concise, actionable analysis."},
                {"role": "user", "content": prompt}
            ],
            model=model_name,
            temperature=0.7,
            max_tokens=1500
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response:
            return {
                "model": model_name,
                "scenario": scenario_name,
                "success": True,
                "response": response,
                "response_time": response_time,
                "response_length": len(response),
                "tokens_estimate": len(response.split()) * 1.3  # Rough estimate
            }
        else:
            return {
                "model": model_name,
                "scenario": scenario_name,
                "success": False,
                "error": "No response received",
                "response_time": response_time
            }
            
    except Exception as e:
        end_time = time.time()
        return {
            "model": model_name,
            "scenario": scenario_name,
            "success": False,
            "error": str(e),
            "response_time": end_time - start_time
        }


async def run_comparison():
    """Run comprehensive model comparison"""
    
    # Models to test
    models = [
        "openai/gpt-oss-safeguard-20b",  # Current primary
        "google/gemini-2.5-flash-preview-09-2025",  # Current secondary
        "openai/gpt-oss-120b",  # Current tertiary
        "deepseek/deepseek-v3.2-exp",  # New candidate
        "deepseek/deepseek-chat-v3.1",  # New candidate
        "qwen/qwen3-max"  # New candidate
    ]
    
    # Test scenarios
    scenarios = [
        ("Trade Analysis", TRADE_ANALYSIS_PROMPT),
        ("Risk Assessment", RISK_ASSESSMENT_PROMPT),
        ("Market Analysis", MARKET_ANALYSIS_PROMPT),
        ("Multi-Step Reasoning", MULTI_STEP_REASONING_PROMPT)
    ]
    
    results = []
    
    logger.info("=" * 80)
    logger.info("🧪 STARTING REAL MODEL COMPARISON TEST")
    logger.info("=" * 80)
    logger.info(f"Testing {len(models)} models across {len(scenarios)} scenarios")
    logger.info(f"Total tests: {len(models) * len(scenarios)}")
    logger.info("")
    
    # Test each model on each scenario
    for scenario_name, prompt in scenarios:
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 SCENARIO: {scenario_name}")
        logger.info(f"{'='*80}\n")
        
        for model in models:
            logger.info(f"Testing {model}...")
            result = await test_model(model, prompt, scenario_name)
            results.append(result)
            
            if result['success']:
                logger.info(f"✅ Success - {result['response_time']:.2f}s - {result['response_length']} chars")
                logger.info(f"Response preview: {result['response'][:200]}...")
            else:
                logger.error(f"❌ Failed - {result.get('error', 'Unknown error')}")
            
            logger.info("")
            
            # Rate limiting - wait between requests
            await asyncio.sleep(2)
    
    # Generate summary report
    logger.info("\n" + "=" * 80)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 80)
    
    # Group by model
    model_stats = {}
    for result in results:
        model = result['model']
        if model not in model_stats:
            model_stats[model] = {
                'total_tests': 0,
                'successful': 0,
                'failed': 0,
                'total_time': 0,
                'total_length': 0,
                'scenarios': []
            }
        
        stats = model_stats[model]
        stats['total_tests'] += 1
        stats['scenarios'].append(result['scenario'])
        
        if result['success']:
            stats['successful'] += 1
            stats['total_time'] += result['response_time']
            stats['total_length'] += result['response_length']
        else:
            stats['failed'] += 1
    
    # Print summary
    logger.info("\n" + "-" * 80)
    for model, stats in model_stats.items():
        logger.info(f"\n{model}:")
        logger.info(f"  Success Rate: {stats['successful']}/{stats['total_tests']} ({stats['successful']/stats['total_tests']*100:.1f}%)")
        
        if stats['successful'] > 0:
            avg_time = stats['total_time'] / stats['successful']
            avg_length = stats['total_length'] / stats['successful']
            logger.info(f"  Avg Response Time: {avg_time:.2f}s")
            logger.info(f"  Avg Response Length: {avg_length:.0f} chars")
        
        if stats['failed'] > 0:
            logger.info(f"  ❌ Failed Tests: {stats['failed']}")
    
    # Save detailed results
    output_file = "model_comparison_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n✅ Detailed results saved to: {output_file}")
    logger.info("\n" + "=" * 80)
    logger.info("🎯 COMPARISON TEST COMPLETE")
    logger.info("=" * 80)
    
    return results


if __name__ == "__main__":
    asyncio.run(run_comparison())
