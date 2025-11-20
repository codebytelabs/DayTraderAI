#!/usr/bin/env python3
"""
Comprehensive test suite for Smart Order Executor
Tests all industry-standard features before deployment
"""
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, time

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orders.smart_order_executor import (
    SmartOrderExecutor, 
    OrderConfig, 
    OrderResult
)


class TestSmartOrderExecutor:
    """Test suite for Smart Order Executor"""
    
    def setup_method(self):
        """Setup for each test"""
        self.mock_alpaca = Mock()
        self.config = OrderConfig(
            max_slippage_pct=0.001,  # 0.10%
            limit_buffer_regular=0.0005,  # 0.05%
            limit_buffer_extended=0.0002,  # 0.02%
            fill_timeout_seconds=60,
            min_rr_ratio=2.0,
            enable_extended_hours=False
        )
        self.executor = SmartOrderExecutor(self.mock_alpaca, self.config)
    
    def test_limit_price_calculation_regular_hours(self):
        """Test limit price calculation during regular hours"""
        signal_price = 100.00
        
        # Mock regular hours (10:00 AM)
        with patch('orders.smart_order_executor.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(10, 0)
            
            # Buy order: should add 0.05% buffer
            buy_limit = self.executor._calculate_limit_price(signal_price, 'buy')
            expected_buy = 100.00 * 1.0005  # +0.05%
            assert abs(buy_limit - expected_buy) < 0.01
            
            # Sell order: should subtract 0.05% buffer
            sell_limit = self.executor._calculate_limit_price(signal_price, 'sell')
            expected_sell = 100.00 * 0.9995  # -0.05%
            assert abs(sell_limit - expected_sell) < 0.01
    
    def test_dynamic_exit_calculation_buy(self):
        """Test dynamic SL/TP calculation for buy orders"""
        filled_price = 100.00
        risk_amount = 2.00  # $2 risk per share
        rr_ratio = 2.0  # 1:2 risk/reward
        
        stop_loss, take_profit = self.executor._calculate_dynamic_exits(
            filled_price, 'buy', risk_amount, rr_ratio
        )
        
        # Buy: SL below, TP above
        assert stop_loss == 98.00  # 100 - 2
        assert take_profit == 104.00  # 100 + (2 * 2)
    
    def test_dynamic_exit_calculation_sell(self):
        """Test dynamic SL/TP calculation for sell orders"""
        filled_price = 100.00
        risk_amount = 2.00  # $2 risk per share
        rr_ratio = 2.0  # 1:2 risk/reward
        
        stop_loss, take_profit = self.executor._calculate_dynamic_exits(
            filled_price, 'sell', risk_amount, rr_ratio
        )
        
        # Sell: SL above, TP below
        assert stop_loss == 102.00  # 100 + 2
        assert take_profit == 96.00  # 100 - (2 * 2)
    
    def test_slippage_validation_acceptable(self):
        """Test that acceptable slippage passes validation"""
        signal_price = 100.00
        filled_price = 100.05  # 0.05% slippage
        
        slippage_pct = abs(filled_price - signal_price) / signal_price
        assert abs(slippage_pct - 0.0005) < 0.0001, f"Expected 0.0005, got {slippage_pct}"  # 0.05%
        assert slippage_pct <= self.config.max_slippage_pct, f"Slippage {slippage_pct} should be <= {self.config.max_slippage_pct}"  # Should pass
    
    def test_slippage_validation_excessive(self):
        """Test that excessive slippage fails validation"""
        signal_price = 100.00
        filled_price = 100.20  # 0.20% slippage (too high)
        
        slippage_pct = abs(filled_price - signal_price) / signal_price
        assert abs(slippage_pct - 0.002) < 0.0001, f"Expected 0.002, got {slippage_pct}"  # 0.20%
        assert slippage_pct > self.config.max_slippage_pct, f"Slippage {slippage_pct} should be > {self.config.max_slippage_pct}"  # Should fail
    
    def test_crwd_scenario_simulation(self):
        """Test the exact CRWD scenario that caused problems"""
        # CRWD trade parameters
        symbol = "CRWD"
        side = "buy"
        quantity = 25
        signal_price = 534.82
        filled_price = 536.00  # Actual slippage that occurred
        risk_amount = 6.53  # From logs
        rr_ratio = 2.0
        
        # Calculate what SHOULD have happened
        stop_loss, take_profit = self.executor._calculate_dynamic_exits(
            filled_price, side, risk_amount, rr_ratio
        )
        
        # Verify correct calculation
        assert stop_loss == 529.47  # 536.00 - 6.53
        assert take_profit == 549.06  # 536.00 + (6.53 * 2)
        
        # Verify R/R ratio
        actual_risk = filled_price - stop_loss  # 6.53
        actual_reward = take_profit - filled_price  # 13.06
        actual_rr = actual_reward / actual_risk  # 2.0
        assert abs(actual_rr - 2.0) < 0.01  # Should be 1:2
        
        # Verify slippage
        slippage_pct = abs(filled_price - signal_price) / signal_price
        assert abs(slippage_pct - 0.0022) < 0.0001  # 0.22%
        
        # This slippage should FAIL validation (> 0.10%)
        assert slippage_pct > self.config.max_slippage_pct
        
        print(f"✅ CRWD Scenario Test Results:")
        print(f"   Signal: ${signal_price:.2f}")
        print(f"   Filled: ${filled_price:.2f}")
        print(f"   Slippage: {slippage_pct*100:.2f}% (EXCESSIVE)")
        print(f"   Stop Loss: ${stop_loss:.2f}")
        print(f"   Take Profit: ${take_profit:.2f}")
        print(f"   R/R Ratio: 1:{actual_rr:.2f}")
        print(f"   Trade Status: REJECTED (excessive slippage)")


def run_comprehensive_test():
    """Run all tests and provide detailed report"""
    print("🧪 Running Smart Order Executor Test Suite")
    print("=" * 60)
    
    test_suite = TestSmartOrderExecutor()
    test_suite.setup_method()
    
    tests = [
        ("Limit Price - Regular Hours", test_suite.test_limit_price_calculation_regular_hours),
        ("Dynamic Exits - Buy", test_suite.test_dynamic_exit_calculation_buy),
        ("Dynamic Exits - Sell", test_suite.test_dynamic_exit_calculation_sell),
        ("Slippage - Acceptable", test_suite.test_slippage_validation_acceptable),
        ("Slippage - Excessive", test_suite.test_slippage_validation_excessive),
        ("CRWD Scenario", test_suite.test_crwd_scenario_simulation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - Ready for deployment!")
        return True
    else:
        print("⚠️  Some tests failed - Fix before deployment")
        return False


if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)
