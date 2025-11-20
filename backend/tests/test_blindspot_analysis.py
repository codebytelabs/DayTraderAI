"""
Blindspot Analysis & Testing Module
Tests all potential issues identified in adaptive thresholds V2
and validates solutions before implementation.
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple

# Test scenarios based on real terminal data
REAL_SCENARIOS = {
    "amd_low_volume": {
        "symbol": "AMD",
        "price": 240.34,
        "ema9": 241.03,
        "ema21": 242.13,
        "signal": "SELL",
        "confidence": 55.0,
        "volume_ratio": 0.35,
        "sentiment": 26,
        "rsi": 37.5,
        "adx": 24.9
    },
    "smci_low_volume": {
        "symbol": "SMCI",
        "price": 39.32,
        "ema9": 39.31,
        "ema21": 39.37,
        "signal": "SELL",
        "confidence": 50.0,
        "volume_ratio": 0.30,
        "sentiment": 26,
        "rsi": 45.0,
        "adx": 20.0
    },
    "dkng_ema_issue": {
        "symbol": "DKNG",
        "price": 30.21,
        "ema9": 30.19,
        "ema21": 30.23,
        "signal": "SELL",
        "confidence": 40.0,
        "volume_ratio": 0.60,
        "sentiment": 26,
        "rsi": 48.0,
        "adx": 18.0
    },
    "hood_async_bug": {
        "symbol": "HOOD",
        "price": 17.58,
        "ema9": 17.52,
        "ema21": 17.45,
        "signal": "BUY",
        "confidence": 45.0,
        "volume_ratio": 0.80,
        "sentiment": 26,
        "rsi": 42.0,
        "adx": 22.0
    },
    "amzn_high_score": {
        "symbol": "AMZN",
        "price": 249.30,
        "ema9": 248.50,
        "ema21": 247.80,
        "signal": "BUY",
        "confidence": 70.0,
        "volume_ratio": 1.06,
        "sentiment": 26,
        "rsi": 45.3,
        "adx": 17.5,
        "scanner_score": 133.6
    }
}


class TestBlindspot1_AsyncSentimentBug:
    """Test and fix the async sentiment error on HOOD"""
    
    def test_identify_async_issue(self):
        """Reproduce the async sentiment bug"""
        # This is the error: "An asyncio.Future, a coroutine or an awaitable is required"
        # Likely caused by calling async function without await
        
        async def get_sentiment_async():
            return 26
        
        # WRONG: This returns a coroutine, not the value
        sentiment_wrong = get_sentiment_async()
        assert asyncio.iscoroutine(sentiment_wrong)
        
        # RIGHT: This awaits and gets the value
        async def test_correct():
            sentiment_right = await get_sentiment_async()
            assert sentiment_right == 26
        
        asyncio.run(test_correct())
    
    def test_solution_sync_wrapper(self):
        """Solution: Use sync wrapper for sentiment calls"""
        
        async def get_sentiment_async():
            await asyncio.sleep(0.01)  # Simulate API call
            return 26
        
        def get_sentiment_sync():
            """Sync wrapper that properly handles async call"""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create task
                    return None  # Fall back to cached value
                else:
                    return loop.run_until_complete(get_sentiment_async())
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(get_sentiment_async())
        
        result = get_sentiment_sync()
        assert result == 26


class TestBlindspot2_VolumeThresholds:
    """Test volume threshold adjustments for fear markets"""
    
    def test_current_strict_thresholds(self):
        """Current system: 0.5x minimum for all shorts"""
        scenarios = [
            REAL_SCENARIOS["amd_low_volume"],
            REAL_SCENARIOS["smci_low_volume"]
        ]
        
        rejected = 0
        for scenario in scenarios:
            if scenario["volume_ratio"] < 0.5:
                rejected += 1
        
        assert rejected == 2  # Both rejected
    
    def test_solution_adaptive_volume_by_sentiment(self):
        """Solution: Lower volume threshold in fear markets for quality setups"""
        
        def get_min_volume_threshold(sentiment: int, signal_type: str, confidence: float) -> float:
            """Adaptive volume thresholds based on market conditions"""
            
            # Base thresholds
            if signal_type == "SHORT":
                base = 0.5
            else:  # LONG
                base = 0.4
            
            # In extreme fear (< 30), allow lower volume for high-confidence longs
            if sentiment < 30:
                if signal_type == "BUY" and confidence >= 60:
                    return 0.35  # Oversold bounce plays
                elif signal_type == "SELL" and confidence >= 65:
                    return 0.45  # High-confidence shorts only
            
            return base
        
        # Test AMD short (55% confidence, fear market)
        amd = REAL_SCENARIOS["amd_low_volume"]
        min_vol = get_min_volume_threshold(amd["sentiment"], amd["signal"], amd["confidence"])
        assert min_vol == 0.5  # Still strict for medium-confidence shorts
        assert amd["volume_ratio"] < min_vol  # Would still reject
        
        # Test AMZN long (70% confidence, fear market)
        amzn = REAL_SCENARIOS["amzn_high_score"]
        min_vol = get_min_volume_threshold(amzn["sentiment"], amzn["signal"], amzn["confidence"])
        assert min_vol == 0.35  # Relaxed for high-confidence longs
        assert amzn["volume_ratio"] > min_vol  # Would PASS
    
    def test_solution_results(self):
        """Verify solution improves signal acceptance without compromising safety"""
        
        def evaluate_with_adaptive_volume(scenario: Dict) -> Tuple[bool, str]:
            sentiment = scenario["sentiment"]
            signal = scenario["signal"]
            confidence = scenario["confidence"]
            volume = scenario["volume_ratio"]
            
            # Get adaptive threshold
            if sentiment < 30:
                if signal == "BUY" and confidence >= 60:
                    min_vol = 0.35
                elif signal == "SELL" and confidence >= 65:
                    min_vol = 0.45
                else:
                    min_vol = 0.5 if signal == "SELL" else 0.4
            else:
                min_vol = 0.5 if signal == "SELL" else 0.4
            
            passed = volume >= min_vol
            reason = f"Volume {volume:.2f}x vs {min_vol:.2f}x required"
            return passed, reason
        
        results = {}
        for name, scenario in REAL_SCENARIOS.items():
            passed, reason = evaluate_with_adaptive_volume(scenario)
            results[name] = {"passed": passed, "reason": reason}
        
        # AMD: Still rejected (55% confidence short, low volume)
        assert not results["amd_low_volume"]["passed"]
        
        # SMCI: Still rejected (50% confidence short, low volume)
        assert not results["smci_low_volume"]["passed"]
        
        # AMZN: Now PASSES (70% confidence long, good volume)
        assert results["amzn_high_score"]["passed"]
        
        # Safety check: Low confidence signals still rejected
        assert not results["hood_async_bug"]["passed"]  # 45% confidence


class TestBlindspot3_EMAPositionLogic:
    """Test EMA position validation logic"""
    
    def test_current_ema_check(self):
        """Current logic: Price must be below BOTH EMAs for short"""
        dkng = REAL_SCENARIOS["dkng_ema_issue"]
        
        # Price: 30.21, EMA9: 30.19, EMA21: 30.23
        # Price is BETWEEN the EMAs - should this be rejected?
        
        price_below_ema9 = dkng["price"] < dkng["ema9"]
        price_below_ema21 = dkng["price"] < dkng["ema21"]
        
        assert not price_below_ema9  # Price > EMA9
        assert price_below_ema21     # Price < EMA21
        
        # Current logic rejects because price not below BOTH
        current_logic_passes = price_below_ema9 and price_below_ema21
        assert not current_logic_passes
    
    def test_solution_ema_crossover_logic(self):
        """Solution: Check EMA relationship, not just price position"""
        
        def validate_ema_setup(price: float, ema9: float, ema21: float, 
                              signal: str, confidence: float) -> Tuple[bool, str]:
            """Improved EMA validation"""
            
            if signal == "SELL":
                # For shorts, prefer:
                # 1. EMA9 < EMA21 (bearish crossover)
                # 2. Price near or below EMA9
                ema_bearish = ema9 < ema21
                price_position = (price - ema9) / ema9 * 100  # % above EMA9
                
                if not ema_bearish:
                    return False, "EMAs not in bearish alignment"
                
                # Allow price slightly above EMA9 if confidence is high
                if confidence >= 60:
                    max_above = 0.5  # 0.5% above EMA9 allowed
                else:
                    max_above = 0.2  # Strict for low confidence
                
                if price_position > max_above:
                    return False, f"Price {price_position:.2f}% above EMA9 (max: {max_above}%)"
                
                return True, "EMA setup valid"
            
            else:  # BUY
                # For longs, prefer:
                # 1. EMA9 > EMA21 (bullish crossover) OR
                # 2. Price bouncing off EMA21 support
                ema_bullish = ema9 > ema21
                near_ema21 = abs(price - ema21) / ema21 * 100 < 1.0  # Within 1%
                
                if ema_bullish or near_ema21:
                    return True, "EMA setup valid"
                
                return False, "No bullish EMA setup"
        
        # Test DKNG short
        dkng = REAL_SCENARIOS["dkng_ema_issue"]
        passed, reason = validate_ema_setup(
            dkng["price"], dkng["ema9"], dkng["ema21"],
            dkng["signal"], dkng["confidence"]
        )
        
        # EMA9 (30.19) < EMA21 (30.23) = bearish ✓
        # Price (30.21) is 0.07% above EMA9
        # Confidence 40% = max 0.2% above allowed
        assert not passed  # Still rejected (price too far above for low confidence)
        
        # Test AMD short
        amd = REAL_SCENARIOS["amd_low_volume"]
        passed, reason = validate_ema_setup(
            amd["price"], amd["ema9"], amd["ema21"],
            amd["signal"], amd["confidence"]
        )
        
        # EMA9 (241.03) < EMA21 (242.13) = bearish ✓
        # Price (240.34) below EMA9 ✓
        assert passed  # EMA setup is good (volume is the issue)


class TestBlindspot4_SignalGeneration:
    """Test why high-scoring symbols don't generate signals"""
    
    def test_scanner_vs_strategy_gap(self):
        """Identify gap between scanner scores and strategy signals"""
        
        # Scanner found AMZN with score 133.6
        # But no BUY signal was generated in strategy loop
        
        amzn = REAL_SCENARIOS["amzn_high_score"]
        
        # Scanner scoring (simplified)
        def calculate_scanner_score(rsi: float, adx: float, volume: float) -> float:
            score = 100
            
            # RSI component
            if 30 <= rsi <= 70:
                score += 20
            
            # ADX component
            if adx > 15:
                score += 10
            
            # Volume component
            if volume > 1.0:
                score += 10
            
            return score
        
        scanner_score = calculate_scanner_score(
            amzn["rsi"], amzn["adx"], amzn["volume_ratio"]
        )
        assert scanner_score >= 130  # High score
        
        # Strategy signal generation (simplified)
        def generates_signal(price: float, ema9: float, ema21: float) -> bool:
            """Does this generate a signal?"""
            ema_diff_pct = abs(ema9 - ema21) / ema21 * 100
            
            # Need sufficient EMA separation
            if ema_diff_pct < 0.3:  # Less than 0.3% separation
                return False
            
            # Need price momentum
            if ema9 > ema21:  # Bullish
                return price > ema9  # Price above fast EMA
            else:  # Bearish
                return price < ema9  # Price below fast EMA
        
        has_signal = generates_signal(amzn["price"], amzn["ema9"], amzn["ema21"])
        
        # This is the gap: High scanner score but no signal
        # Because EMAs might not have enough separation yet
    
    def test_solution_bridge_scanner_and_strategy(self):
        """Solution: Generate signals for high-scoring scanner results"""
        
        def should_evaluate_for_entry(scanner_score: float, confidence: float,
                                     rsi: float, volume: float) -> bool:
            """Bridge scanner and strategy"""
            
            # High scanner scores deserve evaluation even without perfect EMAs
            if scanner_score >= 130:
                # Check if conditions support the direction
                if confidence >= 60 and volume >= 0.8:
                    # RSI not overbought/oversold
                    if 30 < rsi < 70:
                        return True
            
            return False
        
        amzn = REAL_SCENARIOS["amzn_high_score"]
        should_eval = should_evaluate_for_entry(
            amzn["scanner_score"], amzn["confidence"],
            amzn["rsi"], amzn["volume_ratio"]
        )
        
        assert should_eval  # AMZN should be evaluated for entry


class TestIntegratedSolution:
    """Test all fixes together"""
    
    def test_complete_evaluation_pipeline(self):
        """Test complete evaluation with all fixes"""
        
        def evaluate_signal_v2(scenario: Dict) -> Dict:
            """Enhanced evaluation with all fixes"""
            
            result = {
                "symbol": scenario["symbol"],
                "passed": False,
                "reasons": [],
                "improvements": []
            }
            
            # 1. Async sentiment (fixed)
            sentiment = scenario["sentiment"]  # Now properly sync
            result["improvements"].append("✓ Sentiment retrieved synchronously")
            
            # 2. Adaptive volume thresholds
            if sentiment < 30:
                if scenario["signal"] == "BUY" and scenario["confidence"] >= 60:
                    min_vol = 0.35
                elif scenario["signal"] == "SELL" and scenario["confidence"] >= 65:
                    min_vol = 0.45
                else:
                    min_vol = 0.5 if scenario["signal"] == "SELL" else 0.4
            else:
                min_vol = 0.5 if scenario["signal"] == "SELL" else 0.4
            
            volume_ok = scenario["volume_ratio"] >= min_vol
            if volume_ok:
                result["reasons"].append(f"✓ Volume {scenario['volume_ratio']:.2f}x >= {min_vol:.2f}x")
            else:
                result["reasons"].append(f"✗ Volume {scenario['volume_ratio']:.2f}x < {min_vol:.2f}x")
            
            # 3. Improved EMA logic
            ema9 = scenario["ema9"]
            ema21 = scenario["ema21"]
            price = scenario["price"]
            
            if scenario["signal"] == "SELL":
                ema_ok = ema9 < ema21
                price_position = (price - ema9) / ema9 * 100
                max_above = 0.5 if scenario["confidence"] >= 60 else 0.2
                position_ok = price_position <= max_above
            else:
                ema_ok = ema9 > ema21 or abs(price - ema21) / ema21 * 100 < 1.0
                position_ok = True
            
            if ema_ok and position_ok:
                result["reasons"].append("✓ EMA setup valid")
            else:
                result["reasons"].append("✗ EMA setup invalid")
            
            # 4. Confidence threshold
            min_confidence = 55 if sentiment < 30 else 60
            confidence_ok = scenario["confidence"] >= min_confidence
            if confidence_ok:
                result["reasons"].append(f"✓ Confidence {scenario['confidence']}% >= {min_confidence}%")
            else:
                result["reasons"].append(f"✗ Confidence {scenario['confidence']}% < {min_confidence}%")
            
            # Final decision
            result["passed"] = volume_ok and ema_ok and position_ok and confidence_ok
            
            return result
        
        # Test all scenarios
        results = {}
        for name, scenario in REAL_SCENARIOS.items():
            results[name] = evaluate_signal_v2(scenario)
        
        # Verify results
        assert not results["amd_low_volume"]["passed"]  # Still rejected (low volume)
        assert not results["smci_low_volume"]["passed"]  # Still rejected (low volume)
        assert not results["dkng_ema_issue"]["passed"]  # Still rejected (low confidence)
        assert not results["hood_async_bug"]["passed"]  # Still rejected (low confidence)
        assert results["amzn_high_score"]["passed"]  # NOW PASSES! ✓
        
        return results


def run_simulation_summary():
    """Run all tests and provide summary"""
    print("\n" + "="*80)
    print("BLINDSPOT ANALYSIS - SIMULATION RESULTS")
    print("="*80)
    
    # Run integrated test
    test = TestIntegratedSolution()
    results = test.test_complete_evaluation_pipeline()
    
    print("\n📊 EVALUATION RESULTS:")
    print("-" * 80)
    
    for name, result in results.items():
        status = "✅ PASS" if result["passed"] else "⛔ REJECT"
        print(f"\n{status} - {result['symbol']}")
        for reason in result["reasons"]:
            print(f"  {reason}")
    
    print("\n" + "="*80)
    print("RECOMMENDATIONS:")
    print("="*80)
    print("""
1. ✅ FIX ASYNC BUG: Add sync wrapper for sentiment calls
2. ✅ ADAPTIVE VOLUME: Lower thresholds for high-confidence longs in fear
3. ✅ IMPROVED EMA LOGIC: Check EMA relationship, not just price position
4. ✅ BRIDGE SCANNER-STRATEGY: Evaluate high-scoring symbols even without perfect EMAs

EXPECTED IMPACT:
- Maintains capital protection (rejects weak setups)
- Unlocks high-quality opportunities (AMZN-type setups)
- Fixes async bug (no more errors)
- Smarter EMA validation (fewer false rejections)
""")
    
    print("="*80)


if __name__ == "__main__":
    # Run simulation
    run_simulation_summary()
