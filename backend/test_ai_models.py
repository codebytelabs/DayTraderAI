#!/usr/bin/env python3
"""
AI Model Testing and Evaluation Module for DayTraderAI
Tests and compares different AI models for trading copilot functionality.

Models tested:
1. DeepSeek V3.2 Experimental (deepseek/deepseek-v3.2-exp)
2. DeepSeek Chat V3.1 (deepseek/deepseek-chat-v3.1)
3. Google Gemini 2.5 Flash Preview (google/gemini-2.5-flash-preview-09-2025)
4. Perplexity Sonar Pro (perplexity/sonar-pro)

Tests include:
- Trading analysis accuracy
- Response time
- Context understanding
- Financial reasoning
- Risk assessment
"""

import asyncio
import time
import json
import os
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx
from dotenv import load_dotenv
load_dotenv(override=True)


@dataclass
class ModelTestResult:
    """Result of a single model test"""
    model_name: str
    model_id: str
    test_name: str
    response_time: float
    response_quality: int  # 1-10
    accuracy: int  # 1-10
    context_understanding: int  # 1-10
    financial_reasoning: int  # 1-10
    response_length: int
    response_text: str
    error: Optional[str] = None


class AIModelTester:
    """Comprehensive AI model testing for trading copilot"""
    
    def __init__(self):
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        
        # Models to test
        self.models = {
            "deepseek-v3.2-exp": {
                "name": "DeepSeek V3.2 Experimental",
                "model_id": "deepseek/deepseek-v3.2-exp",
                "provider": "openrouter",
                "description": "Latest experimental model, strong reasoning"
            },
            "deepseek-chat-v3.1": {
                "name": "DeepSeek Chat V3.1",
                "model_id": "deepseek/deepseek-chat-v3.1",
                "provider": "openrouter",
                "description": "Stable production model, reliable"
            },
            "gemini-2.5-flash": {
                "name": "Gemini 2.5 Flash Preview",
                "model_id": "google/gemini-2.5-flash-preview",
                "provider": "openrouter",
                "description": "Fast inference, good for quick queries"
            },
            "perplexity-sonar": {
                "name": "Perplexity Sonar Pro",
                "model_id": "perplexity/sonar-pro",
                "provider": "openrouter",
                "description": "Real-time web search, current market data"
            }
        }
        
        # Test scenarios for trading copilot
        self.test_scenarios = self._create_test_scenarios()
    
    def _create_test_scenarios(self) -> List[Dict]:
        """Create comprehensive test scenarios"""
        return [
            {
                "name": "Portfolio Analysis",
                "category": "analysis",
                "prompt": """Analyze this trading portfolio:

Current Positions:
- AAPL: 100 shares @ $178.50, current $185.20 (+$670, +3.8%)
- NVDA: 50 shares @ $890.00, current $920.50 (+$1,525, +3.4%)
- TSLA: 30 shares @ $245.00, current $238.80 (-$186, -2.5%)
- SPY: 200 shares @ $445.00, current $448.50 (+$700, +0.8%)

Account: $125,000 equity, $45,000 buying power
Daily P/L: +$2,709 (+2.2%)
VIX: 18.5 (moderate volatility)

Provide specific insights on:
1. Portfolio risk assessment
2. Position sizing recommendations
3. Which positions to hold/trim/add
4. Overall strategy for today""",
                "expected_elements": ["risk", "diversification", "position", "recommendation"],
                "weight": 0.25
            },
            {
                "name": "Trade Entry Analysis",
                "category": "trading",
                "prompt": """Analyze this potential trade entry:

Symbol: AMD
Current Price: $158.45
Action: BUY

Technical Indicators:
- 9 EMA: $156.80 (price above)
- 21 EMA: $154.20 (price above)
- 200 EMA: $142.50 (price above - bullish)
- ATR(14): $4.85
- RSI(14): 62.5
- Volume: 45M (1.2x average)
- MACD: Bullish crossover 2 days ago

Market Context:
- SPY: +0.8% today
- Sector (XLK): +1.2% today
- VIX: 16.8 (low volatility)

Provide:
1. Trade quality score (1-10)
2. Recommended entry price
3. Stop loss level
4. Take profit targets
5. Position size recommendation (for $100k account)""",
                "expected_elements": ["entry", "stop", "target", "size", "risk"],
                "weight": 0.25
            },
            {
                "name": "Risk Management",
                "category": "risk",
                "prompt": """A trader has these positions with 8% portfolio drawdown today:

Losing Positions:
- META: -12% ($2,400 loss, 20% of portfolio)
- GOOGL: -8% ($1,200 loss, 15% of portfolio)
- AMZN: -6% ($900 loss, 15% of portfolio)

Winning Positions:
- NVDA: +5% ($750 gain, 15% of portfolio)
- MSFT: +3% ($450 gain, 15% of portfolio)

Cash: 20% of portfolio

The trader is considering:
1. Cutting all losses immediately
2. Averaging down on META
3. Adding to NVDA winner
4. Closing everything and waiting

What's the best risk management approach? Consider:
- Position sizing rules
- Correlation between positions
- Market conditions
- Psychological factors""",
                "expected_elements": ["cut loss", "position size", "correlation", "risk"],
                "weight": 0.20
            },
            {
                "name": "Market Sentiment",
                "category": "market",
                "prompt": """Current market conditions:

Indices:
- S&P 500: +0.6% (testing 4,500 resistance)
- NASDAQ: +0.9% (tech leading)
- Russell 2000: -0.3% (small caps lagging)

Volatility:
- VIX: 15.8 (-8% today, complacency)
- VIX term structure: Contango (normal)

Macro:
- 10Y Treasury: 4.35% (+3 bps)
- DXY: 104.2 (+0.2%)
- Fed meeting in 2 weeks

Sector Performance:
- Tech (XLK): +1.2%
- Financials (XLF): +0.4%
- Energy (XLE): -0.8%
- Healthcare (XLV): +0.2%

What's the market sentiment and recommended trading strategy for today?""",
                "expected_elements": ["sentiment", "sector", "strategy", "risk"],
                "weight": 0.15
            },
            {
                "name": "Quick Copilot Query",
                "category": "copilot",
                "prompt": """Current state:
- Account: $50,000
- Open positions: 3
- Daily P/L: +$450 (+0.9%)
- Trading enabled: Yes

User question: "Should I buy AAPL right now? It's up 2% today."

Provide a brief, actionable response.""",
                "expected_elements": ["recommendation", "reason", "risk"],
                "weight": 0.15
            }
        ]
    
    async def test_openrouter_model(
        self, 
        model_config: Dict, 
        prompt: str,
        system_prompt: str = None
    ) -> ModelTestResult:
        """Test an OpenRouter model"""
        start_time = time.time()
        
        if not self.openrouter_key:
            return ModelTestResult(
                model_name=model_config["name"],
                model_id=model_config["model_id"],
                test_name="",
                response_time=0,
                response_quality=0,
                accuracy=0,
                context_understanding=0,
                financial_reasoning=0,
                response_length=0,
                response_text="",
                error="OpenRouter API key not configured"
            )
        
        if not system_prompt:
            system_prompt = """You are an expert day trading assistant for DayTraderAI. 
Provide specific, actionable trading insights. Focus on:
- Risk management
- Technical analysis
- Position sizing
- Market context
Be concise but thorough."""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8006",
                "X-Title": "DayTraderAI Model Testing"
            }
            
            payload = {
                "model": model_config["model_id"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1500,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    return ModelTestResult(
                        model_name=model_config["name"],
                        model_id=model_config["model_id"],
                        test_name="",
                        response_time=response_time,
                        response_quality=0,
                        accuracy=0,
                        context_understanding=0,
                        financial_reasoning=0,
                        response_length=len(response_text),
                        response_text=response_text
                    )
                else:
                    return ModelTestResult(
                        model_name=model_config["name"],
                        model_id=model_config["model_id"],
                        test_name="",
                        response_time=response_time,
                        response_quality=0,
                        accuracy=0,
                        context_understanding=0,
                        financial_reasoning=0,
                        response_length=0,
                        response_text="",
                        error=f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
        except Exception as e:
            return ModelTestResult(
                model_name=model_config["name"],
                model_id=model_config["model_id"],
                test_name="",
                response_time=time.time() - start_time,
                response_quality=0,
                accuracy=0,
                context_understanding=0,
                financial_reasoning=0,
                response_length=0,
                response_text="",
                error=str(e)
            )
    
    def score_response(
        self, 
        response_text: str, 
        expected_elements: List[str],
        test_name: str
    ) -> Dict[str, int]:
        """Score response quality based on content analysis"""
        response_lower = response_text.lower()
        
        # Context Understanding (1-10)
        element_count = sum(1 for elem in expected_elements if elem.lower() in response_lower)
        context_score = min(10, int((element_count / len(expected_elements)) * 10))
        
        # Financial Reasoning (1-10)
        financial_keywords = [
            "risk", "return", "volatility", "support", "resistance",
            "stop loss", "take profit", "position size", "r/r", "risk/reward",
            "ema", "rsi", "atr", "volume", "momentum", "trend",
            "bullish", "bearish", "breakout", "pullback", "consolidation"
        ]
        financial_count = sum(1 for kw in financial_keywords if kw in response_lower)
        financial_score = min(10, int((financial_count / 6) * 10))
        
        # Response Quality (1-10)
        quality_factors = [
            len(response_text) > 200,  # Sufficient detail
            any(c in response_text for c in ['$', '%']),  # Specific numbers
            any(w in response_lower for w in ['recommend', 'suggest', 'consider']),  # Actionable
            any(w in response_lower for w in ['because', 'due to', 'since', 'given']),  # Reasoning
            response_text.count('.') >= 3,  # Multiple sentences
            any(w in response_lower for w in ['risk', 'caution', 'careful']),  # Risk awareness
        ]
        quality_score = int((sum(quality_factors) / len(quality_factors)) * 10)
        
        # Accuracy (based on test-specific criteria)
        accuracy_score = 7  # Base score
        
        if test_name == "Portfolio Analysis":
            if "diversif" in response_lower:
                accuracy_score += 1
            if any(w in response_lower for w in ["trim", "reduce", "add"]):
                accuracy_score += 1
            if "tsla" in response_lower and any(w in response_lower for w in ["loss", "negative", "down"]):
                accuracy_score += 1
                
        elif test_name == "Trade Entry Analysis":
            if any(w in response_lower for w in ["stop", "stop loss", "stop-loss"]):
                accuracy_score += 1
            if any(w in response_lower for w in ["target", "take profit", "profit target"]):
                accuracy_score += 1
            if any(c in response_text for c in ['$15', '$16', '158', '159', '160']):
                accuracy_score += 1
                
        elif test_name == "Risk Management":
            if any(w in response_lower for w in ["cut", "close", "exit"]):
                accuracy_score += 1
            if "meta" in response_lower:
                accuracy_score += 1
            if any(w in response_lower for w in ["correlation", "concentrated"]):
                accuracy_score += 1
        
        accuracy_score = min(10, accuracy_score)
        
        return {
            "response_quality": quality_score,
            "accuracy": accuracy_score,
            "context_understanding": context_score,
            "financial_reasoning": financial_score
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests on all models"""
        print("\n" + "=" * 60)
        print("🧪 DayTraderAI AI Model Evaluation")
        print("=" * 60)
        print(f"Testing {len(self.models)} models across {len(self.test_scenarios)} scenarios")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        all_results = []
        model_summaries = {}
        
        for model_key, model_config in self.models.items():
            print(f"\n📊 Testing: {model_config['name']}")
            print(f"   Model ID: {model_config['model_id']}")
            print("-" * 40)
            
            model_results = []
            
            for scenario in self.test_scenarios:
                print(f"   • {scenario['name']}...", end=" ", flush=True)
                
                result = await self.test_openrouter_model(model_config, scenario["prompt"])
                result.test_name = scenario["name"]
                
                if result.error:
                    print(f"❌ Error: {result.error[:50]}")
                    continue
                
                # Score the response
                scores = self.score_response(
                    result.response_text,
                    scenario["expected_elements"],
                    scenario["name"]
                )
                
                result.response_quality = scores["response_quality"]
                result.accuracy = scores["accuracy"]
                result.context_understanding = scores["context_understanding"]
                result.financial_reasoning = scores["financial_reasoning"]
                
                model_results.append(result)
                all_results.append(result)
                
                print(f"✅ {result.response_time:.2f}s (Q:{result.response_quality} A:{result.accuracy})")
                
                # Small delay between tests
                await asyncio.sleep(0.5)
            
            # Calculate model summary
            if model_results:
                successful = [r for r in model_results if not r.error]
                if successful:
                    model_summaries[model_key] = {
                        "name": model_config["name"],
                        "model_id": model_config["model_id"],
                        "description": model_config["description"],
                        "tests_passed": len(successful),
                        "tests_total": len(self.test_scenarios),
                        "avg_response_time": statistics.mean([r.response_time for r in successful]),
                        "avg_quality": statistics.mean([r.response_quality for r in successful]),
                        "avg_accuracy": statistics.mean([r.accuracy for r in successful]),
                        "avg_context": statistics.mean([r.context_understanding for r in successful]),
                        "avg_financial": statistics.mean([r.financial_reasoning for r in successful]),
                        "success_rate": len(successful) / len(self.test_scenarios),
                        "total_score": 0
                    }
                    
                    # Calculate weighted total score
                    s = model_summaries[model_key]
                    s["total_score"] = (
                        s["avg_quality"] * 0.20 +
                        s["avg_accuracy"] * 0.30 +
                        s["avg_context"] * 0.20 +
                        s["avg_financial"] * 0.20 +
                        (10 - min(10, s["avg_response_time"])) * 0.10  # Speed bonus
                    ) * s["success_rate"]
        
        return {
            "results": all_results,
            "summaries": model_summaries,
            "timestamp": datetime.now().isoformat(),
            "test_count": len(self.test_scenarios),
            "model_count": len(self.models)
        }
    
    def generate_report(self, test_data: Dict[str, Any]) -> str:
        """Generate comprehensive comparison report"""
        summaries = test_data["summaries"]
        
        # Sort by total score
        ranked = sorted(summaries.items(), key=lambda x: x[1]["total_score"], reverse=True)
        
        report = []
        report.append("\n" + "=" * 70)
        report.append("📊 AI MODEL COMPARISON REPORT - DayTraderAI")
        report.append("=" * 70)
        report.append(f"Generated: {test_data['timestamp']}")
        report.append(f"Models Tested: {test_data['model_count']}")
        report.append(f"Test Scenarios: {test_data['test_count']}")
        report.append("")
        
        # Comparison table
        report.append("┌" + "─" * 68 + "┐")
        report.append(f"│ {'Model':<28} │ {'Score':>6} │ {'Speed':>6} │ {'Quality':>7} │ {'Accuracy':>8} │")
        report.append("├" + "─" * 68 + "┤")
        
        for model_key, summary in ranked:
            report.append(
                f"│ {summary['name']:<28} │ "
                f"{summary['total_score']:>6.1f} │ "
                f"{summary['avg_response_time']:>5.1f}s │ "
                f"{summary['avg_quality']:>7.1f} │ "
                f"{summary['avg_accuracy']:>8.1f} │"
            )
        
        report.append("└" + "─" * 68 + "┘")
        report.append("")
        
        # Detailed rankings
        report.append("🏆 RANKINGS BY CATEGORY")
        report.append("-" * 40)
        
        # Speed ranking
        speed_ranked = sorted(summaries.items(), key=lambda x: x[1]["avg_response_time"])
        report.append(f"\n⚡ Fastest Response:")
        for i, (k, s) in enumerate(speed_ranked[:3], 1):
            report.append(f"   {i}. {s['name']}: {s['avg_response_time']:.2f}s")
        
        # Quality ranking
        quality_ranked = sorted(summaries.items(), key=lambda x: x[1]["avg_quality"], reverse=True)
        report.append(f"\n📝 Best Quality:")
        for i, (k, s) in enumerate(quality_ranked[:3], 1):
            report.append(f"   {i}. {s['name']}: {s['avg_quality']:.1f}/10")
        
        # Accuracy ranking
        accuracy_ranked = sorted(summaries.items(), key=lambda x: x[1]["avg_accuracy"], reverse=True)
        report.append(f"\n🎯 Most Accurate:")
        for i, (k, s) in enumerate(accuracy_ranked[:3], 1):
            report.append(f"   {i}. {s['name']}: {s['avg_accuracy']:.1f}/10")
        
        # Financial reasoning ranking
        financial_ranked = sorted(summaries.items(), key=lambda x: x[1]["avg_financial"], reverse=True)
        report.append(f"\n💰 Best Financial Reasoning:")
        for i, (k, s) in enumerate(financial_ranked[:3], 1):
            report.append(f"   {i}. {s['name']}: {s['avg_financial']:.1f}/10")
        
        # Recommendations
        report.append("\n" + "=" * 70)
        report.append("🎯 RECOMMENDATIONS FOR DayTraderAI")
        report.append("=" * 70)
        
        if len(ranked) >= 3:
            primary = ranked[0]
            secondary = ranked[1]
            tertiary = ranked[2]
            
            report.append(f"\n🥇 PRIMARY MODEL (Main Analysis):")
            report.append(f"   {primary[1]['name']}")
            report.append(f"   Model ID: {primary[1]['model_id']}")
            report.append(f"   Score: {primary[1]['total_score']:.1f}/10")
            report.append(f"   Best for: Trade analysis, portfolio review, risk assessment")
            
            report.append(f"\n🥈 SECONDARY MODEL (Copilot Chat):")
            report.append(f"   {secondary[1]['name']}")
            report.append(f"   Model ID: {secondary[1]['model_id']}")
            report.append(f"   Score: {secondary[1]['total_score']:.1f}/10")
            report.append(f"   Best for: Quick responses, user queries, fallback")
            
            report.append(f"\n🥉 TERTIARY MODEL (Quick Queries):")
            report.append(f"   {tertiary[1]['name']}")
            report.append(f"   Model ID: {tertiary[1]['model_id']}")
            report.append(f"   Score: {tertiary[1]['total_score']:.1f}/10")
            report.append(f"   Best for: Fast insights, simple queries, backup")
            
            if len(ranked) >= 4:
                backup = ranked[3]
                report.append(f"\n4️⃣ BACKUP MODEL:")
                report.append(f"   {backup[1]['name']}")
                report.append(f"   Model ID: {backup[1]['model_id']}")
        
        # Environment configuration
        report.append("\n" + "-" * 70)
        report.append("📝 RECOMMENDED .env CONFIGURATION:")
        report.append("-" * 70)
        
        if len(ranked) >= 3:
            report.append(f"OPENROUTER_PRIMARY_MODEL={ranked[0][1]['model_id']}")
            report.append(f"OPENROUTER_SECONDARY_MODEL={ranked[1][1]['model_id']}")
            report.append(f"OPENROUTER_TERTIARY_MODEL={ranked[2][1]['model_id']}")
            if len(ranked) >= 4:
                report.append(f"OPENROUTER_BACKUP_MODEL={ranked[3][1]['model_id']}")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)
    
    def update_env_file(self, test_data: Dict[str, Any]) -> bool:
        """Update .env file with recommended models"""
        summaries = test_data["summaries"]
        ranked = sorted(summaries.items(), key=lambda x: x[1]["total_score"], reverse=True)
        
        if len(ranked) < 3:
            print("❌ Not enough models tested to update configuration")
            return False
        
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        
        try:
            with open(env_path, "r") as f:
                env_content = f.read()
            
            # Update model configurations
            updates = {
                "OPENROUTER_PRIMARY_MODEL": ranked[0][1]["model_id"],
                "OPENROUTER_SECONDARY_MODEL": ranked[1][1]["model_id"],
                "OPENROUTER_TERTIARY_MODEL": ranked[2][1]["model_id"],
            }
            
            if len(ranked) >= 4:
                updates["OPENROUTER_BACKUP_MODEL"] = ranked[3][1]["model_id"]
            
            lines = env_content.split("\n")
            updated_lines = []
            
            for line in lines:
                updated = False
                for key, value in updates.items():
                    if line.startswith(f"{key}="):
                        updated_lines.append(f"{key}={value}")
                        updated = True
                        break
                
                if not updated:
                    updated_lines.append(line)
            
            with open(env_path, "w") as f:
                f.write("\n".join(updated_lines))
            
            print("\n✅ Updated .env with recommended models:")
            for key, value in updates.items():
                print(f"   {key}={value}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to update .env: {e}")
            return False
    
    async def save_results(self, test_data: Dict[str, Any], report: str):
        """Save test results to files"""
        # Save detailed JSON results
        results_path = os.path.join(os.path.dirname(__file__), "ai_model_test_results.json")
        
        # Convert results to serializable format
        serializable_data = {
            "summaries": test_data["summaries"],
            "timestamp": test_data["timestamp"],
            "test_count": test_data["test_count"],
            "model_count": test_data["model_count"]
        }
        
        with open(results_path, "w") as f:
            json.dump(serializable_data, f, indent=2)
        
        # Save report
        report_path = os.path.join(os.path.dirname(__file__), "ai_model_evaluation_report.txt")
        with open(report_path, "w") as f:
            f.write(report)
        
        print(f"\n💾 Results saved:")
        print(f"   • {results_path}")
        print(f"   • {report_path}")


async def main():
    """Run the AI model evaluation"""
    print("\n🚀 Starting DayTraderAI AI Model Evaluation...")
    
    # Check API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not found in environment")
        print("   Please set it in backend/.env")
        return
    
    tester = AIModelTester()
    
    # Run tests
    test_data = await tester.run_comprehensive_test()
    
    # Generate report
    report = tester.generate_report(test_data)
    print(report)
    
    # Save results
    await tester.save_results(test_data, report)
    
    # Update .env file
    tester.update_env_file(test_data)
    
    print("\n✅ AI Model evaluation complete!")


if __name__ == "__main__":
    asyncio.run(main())
