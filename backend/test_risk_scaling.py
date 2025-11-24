#!/usr/bin/env python3
"""
Test script to validate Confidence-Based Risk Scaling logic.
Simulates various market conditions and confidence levels to verify position sizing.
"""

import sys
import os
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from trading.risk_manager import RiskManager
from core.alpaca_client import AlpacaClient
from config import settings

def test_risk_scaling():
    print("\n🧪 Testing Confidence-Based Risk Scaling Logic...\n")
    
    # Mock dependencies
    mock_alpaca = MagicMock(spec=AlpacaClient)
    mock_supabase = MagicMock()
    
    # Initialize RiskManager
    risk_manager = RiskManager(mock_alpaca, mock_supabase)
    
    # Test Cases
    scenarios = [
        {
            "name": "🚀 High Confidence (90%) + Bull Market",
            "confidence": 90,
            "regime": {"regime": "trending", "volatility_level": "normal"},
            "expected_conf_mult": 2.0,
            "expected_regime_mult": 1.0,
            "expected_risk_factor": 2.0  # 2.0 * 1.0
        },
        {
            "name": "⚠️ Medium Confidence (80%) + Choppy Market",
            "confidence": 80,
            "regime": {"regime": "choppy", "volatility_level": "normal"},
            "expected_conf_mult": 1.5,
            "expected_regime_mult": 0.75,
            "expected_risk_factor": 1.125  # 1.5 * 0.75
        },
        {
            "name": "🛡️ Normal Confidence (70%) + High Volatility",
            "confidence": 70,
            "regime": {"regime": "neutral", "volatility_level": "high"},
            "expected_conf_mult": 1.0,
            "expected_regime_mult": 0.85,
            "expected_risk_factor": 0.85  # 1.0 * 0.85
        },
        {
            "name": "🐻 High Confidence (95%) + Bear Market",
            "confidence": 95,
            "regime": {"regime": "bear", "volatility_level": "high"},
            "expected_conf_mult": 2.0,
            "expected_regime_mult": 0.50,
            "expected_risk_factor": 1.0  # 2.0 * 0.50
        }
    ]
    
    passed = 0
    
    for scenario in scenarios:
        print(f"Testing: {scenario['name']}")
        
        # Test Confidence Multiplier
        conf_mult = risk_manager._get_confidence_multiplier(scenario['confidence'])
        
        # Test Regime Safety Multiplier
        regime_mult = risk_manager._get_regime_safety_multiplier(scenario['regime'])
        
        # Calculate combined risk factor (ignoring other multipliers for this test)
        risk_factor = conf_mult * regime_mult
        
        # Validation
        conf_ok = conf_mult == scenario['expected_conf_mult']
        regime_ok = regime_mult == scenario['expected_regime_mult']
        risk_ok = abs(risk_factor - scenario['expected_risk_factor']) < 0.01
        
        print(f"  Confidence Mult: {conf_mult} (Expected: {scenario['expected_conf_mult']}) {'✅' if conf_ok else '❌'}")
        print(f"  Regime Mult:     {regime_mult} (Expected: {scenario['expected_regime_mult']}) {'✅' if regime_ok else '❌'}")
        print(f"  Total Risk Factor: {risk_factor:.3f}x (Expected: {scenario['expected_risk_factor']}x) {'✅' if risk_ok else '❌'}")
        
        if conf_ok and regime_ok and risk_ok:
            passed += 1
        print("-" * 50)
        
    print(f"\nResults: {passed}/{len(scenarios)} scenarios passed.")
    
    if passed == len(scenarios):
        print("\n✅ ALL TESTS PASSED - Logic is safe to deploy!")
        return True
    else:
        print("\n❌ SOME TESTS FAILED - Do not deploy.")
        return False

if __name__ == "__main__":
    success = test_risk_scaling()
    sys.exit(0 if success else 1)
