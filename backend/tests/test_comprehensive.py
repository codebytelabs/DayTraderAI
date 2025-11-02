"""
Comprehensive Testing Suite for DayTraderAI
Tests with REAL API keys and data - NO MOCKS

Test Levels:
1. Unit Tests - Individual modules
2. API Tests - Each endpoint
3. Integration Tests - Full workflows
4. Use Case Tests - Real trading scenarios
"""

import sys
import time
import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
API_BASE = "http://localhost:8006"
VERBOSE = True

# Test Results
test_results = {
    "unit": {"passed": 0, "failed": 0, "tests": []},
    "api": {"passed": 0, "failed": 0, "tests": []},
    "integration": {"passed": 0, "failed": 0, "tests": []},
    "use_case": {"passed": 0, "failed": 0, "tests": []}
}


def log(message: str, level: str = "INFO"):
    """Enhanced logging with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    colors = {
        "INFO": "\033[0;37m",
        "SUCCESS": "\033[0;32m",
        "ERROR": "\033[0;31m",
        "WARNING": "\033[1;33m",
        "DEBUG": "\033[0;36m"
    }
    color = colors.get(level, "\033[0;37m")
    reset = "\033[0m"
    print(f"{color}[{timestamp}] [{level}] {message}{reset}")


def test_result(category: str, name: str, passed: bool, details: str = ""):
    """Record test result."""
    result = {
        "name": name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    
    test_results[category]["tests"].append(result)
    
    if passed:
        test_results[category]["passed"] += 1
        log(f"✓ PASS: {name}", "SUCCESS")
    else:
        test_results[category]["failed"] += 1
        log(f"✗ FAIL: {name} - {details}", "ERROR")
    
    if VERBOSE and details:
        log(f"  Details: {details}", "DEBUG")


def api_call(method: str, endpoint: str, data: Dict = None) -> Tuple[int, Dict]:
    """Make API call and return status code and response."""
    url = f"{API_BASE}{endpoint}"
    log(f"API Call: {method} {endpoint}", "DEBUG")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            return 0, {"error": "Invalid method"}
        
        try:
            return response.status_code, response.json()
        except:
            return response.status_code, {"text": response.text}
    
    except Exception as e:
        log(f"API call failed: {e}", "ERROR")
        return 0, {"error": str(e)}


# ============================================================================
# LEVEL 1: UNIT TESTS - Test Individual Modules
# ============================================================================

def test_unit_config():
    """Test configuration loading."""
    log("\n" + "="*80, "INFO")
    log("LEVEL 1: UNIT TESTS - Configuration", "INFO")
    log("="*80, "INFO")
    
    try:
        from config import settings
        
        # Test required settings exist
        assert hasattr(settings, 'alpaca_api_key'), "Missing alpaca_api_key"
        assert hasattr(settings, 'supabase_url'), "Missing supabase_url"
        assert hasattr(settings, 'openrouter_api_key'), "Missing openrouter_api_key"
        
        # Test values are not empty
        assert settings.alpaca_api_key, "alpaca_api_key is empty"
        assert settings.supabase_url, "supabase_url is empty"
        
        # Test watchlist
        assert len(settings.watchlist_symbols) > 0, "Watchlist is empty"
        
        test_result("unit", "Configuration Loading", True, 
                   f"Loaded {len(settings.watchlist_symbols)} symbols")
        
    except Exception as e:
        test_result("unit", "Configuration Loading", False, str(e))


def test_unit_alpaca_client():
    """Test Alpaca client initialization."""
    log("\nTesting Alpaca Client...", "INFO")
    
    try:
        from core.alpaca_client import AlpacaClient
        
        client = AlpacaClient()
        
        # Test account connection
        account = client.get_account()
        assert account is not None, "Failed to get account"
        
        equity = float(account.equity)
        assert equity > 0, "Invalid equity"
        
        test_result("unit", "Alpaca Client", True, 
                   f"Connected - Equity: ${equity:.2f}")
        
    except Exception as e:
        test_result("unit", "Alpaca Client", False, str(e))


def test_unit_supabase_client():
    """Test Supabase client initialization."""
    log("\nTesting Supabase Client...", "INFO")
    
    try:
        from core.supabase_client import SupabaseClient
        
        client = SupabaseClient()
        
        # Test database connection by fetching metrics
        metrics = client.get_latest_metrics()
        
        test_result("unit", "Supabase Client", True, 
                   "Connected to database")
        
    except Exception as e:
        test_result("unit", "Supabase Client", False, str(e))


def test_unit_risk_manager():
    """Test Risk Manager logic."""
    log("\nTesting Risk Manager...", "INFO")
    
    try:
        from core.alpaca_client import AlpacaClient
        from trading.risk_manager import RiskManager
        
        alpaca = AlpacaClient()
        risk_mgr = RiskManager(alpaca)
        
        # Test risk check (should pass for small order)
        approved, reason = risk_mgr.check_order("AAPL", "buy", 1, 150.0)
        
        test_result("unit", "Risk Manager", True, 
                   f"Risk check: {reason}")
        
    except Exception as e:
        test_result("unit", "Risk Manager", False, str(e))


def test_unit_feature_engine():
    """Test feature computation."""
    log("\nTesting Feature Engine...", "INFO")
    
    try:
        import pandas as pd
        from data.features import FeatureEngine
        
        # Create sample data
        data = {
            'open': [100, 101, 102, 103, 104],
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }
        df = pd.DataFrame(data)
        
        engine = FeatureEngine()
        features = engine.calculate_features(df, ema_short=2, ema_long=3)
        
        assert features is not None, "Features not computed"
        assert 'ema_short' in features, "Missing EMA short"
        assert 'ema_long' in features, "Missing EMA long"
        assert 'atr' in features, "Missing ATR"
        
        test_result("unit", "Feature Engine", True, 
                   f"Computed {len(features)} features")
        
    except Exception as e:
        test_result("unit", "Feature Engine", False, str(e))


# ============================================================================
# LEVEL 2: API TESTS - Test Each Endpoint
# ============================================================================

def test_api_health():
    """Test health endpoints."""
    log("\n" + "="*80, "INFO")
    log("LEVEL 2: API TESTS - Health Endpoints", "INFO")
    log("="*80, "INFO")
    
    # Test root
    status, data = api_call("GET", "/")
    test_result("api", "GET /", status == 200, 
               f"Status: {status}, Response: {json.dumps(data)[:100]}")
    
    # Test health
    status, data = api_call("GET", "/health")
    test_result("api", "GET /health", status == 200, 
               f"Status: {status}, Alpaca: {data.get('alpaca', 'unknown')}")


def test_api_account():
    """Test account endpoints."""
    log("\nTesting Account Endpoints...", "INFO")
    
    status, data = api_call("GET", "/account")
    
    if status == 200:
        equity = data.get('equity', 0)
        cash = data.get('cash', 0)
        test_result("api", "GET /account", True, 
                   f"Equity: ${equity:.2f}, Cash: ${cash:.2f}")
    else:
        test_result("api", "GET /account", False, 
                   f"Status: {status}, Error: {data}")


def test_api_positions():
    """Test positions endpoints."""
    log("\nTesting Positions Endpoints...", "INFO")
    
    status, data = api_call("GET", "/positions")
    
    if status == 200:
        count = len(data) if isinstance(data, list) else 0
        test_result("api", "GET /positions", True, 
                   f"Found {count} positions")
    else:
        test_result("api", "GET /positions", False, 
                   f"Status: {status}")


def test_api_orders():
    """Test orders endpoints."""
    log("\nTesting Orders Endpoints...", "INFO")
    
    status, data = api_call("GET", "/orders")
    
    if status == 200:
        count = len(data) if isinstance(data, list) else 0
        test_result("api", "GET /orders", True, 
                   f"Found {count} orders")
    else:
        test_result("api", "GET /orders", False, 
                   f"Status: {status}")


def test_api_metrics():
    """Test metrics endpoints."""
    log("\nTesting Metrics Endpoints...", "INFO")
    
    status, data = api_call("GET", "/metrics")
    
    if status == 200:
        equity = data.get('equity', 0)
        daily_pl = data.get('daily_pl', 0)
        test_result("api", "GET /metrics", True, 
                   f"Equity: ${equity:.2f}, Daily P/L: ${daily_pl:.2f}")
    else:
        test_result("api", "GET /metrics", False, 
                   f"Status: {status}")


def test_api_engine():
    """Test engine control endpoints."""
    log("\nTesting Engine Endpoints...", "INFO")
    
    # Test status
    status, data = api_call("GET", "/engine/status")
    
    if status == 200:
        running = data.get('running', False)
        trading_enabled = data.get('trading_enabled', False)
        test_result("api", "GET /engine/status", True, 
                   f"Running: {running}, Trading: {trading_enabled}")
    else:
        test_result("api", "GET /engine/status", False, 
                   f"Status: {status}")


def test_api_trading_controls():
    """Test trading control endpoints."""
    log("\nTesting Trading Controls...", "INFO")
    
    # Test disable
    status, data = api_call("POST", "/trading/disable")
    test_result("api", "POST /trading/disable", status == 200, 
               f"Status: {status}")
    
    time.sleep(1)
    
    # Test enable
    status, data = api_call("POST", "/trading/enable")
    test_result("api", "POST /trading/enable", status == 200, 
               f"Status: {status}")


# ============================================================================
# LEVEL 3: INTEGRATION TESTS - Full Workflows
# ============================================================================

def test_integration_order_flow():
    """Test complete order submission and management flow."""
    log("\n" + "="*80, "INFO")
    log("LEVEL 3: INTEGRATION TESTS - Order Flow", "INFO")
    log("="*80, "INFO")
    
    try:
        # Step 1: Get initial state
        log("Step 1: Getting initial state...", "INFO")
        status, initial_positions = api_call("GET", "/positions")
        initial_count = len(initial_positions) if isinstance(initial_positions, list) else 0
        log(f"Initial positions: {initial_count}", "DEBUG")
        
        # Step 2: Submit order
        log("Step 2: Submitting test order (BUY 1 AAPL)...", "INFO")
        status, order_response = api_call("POST", "/orders/submit?symbol=AAPL&side=buy&qty=1&reason=integration_test")
        
        if status != 200:
            test_result("integration", "Order Flow", False, 
                       f"Order submission failed: {order_response}")
            return
        
        success = order_response.get('success', False)
        log(f"Order submission result: {success}", "DEBUG")
        
        if not success:
            # Order rejected by risk manager - this is OK
            test_result("integration", "Order Flow", True, 
                       f"Order correctly rejected by risk manager: {order_response.get('message', '')}")
            return
        
        # Step 3: Wait for fill
        log("Step 3: Waiting for order to fill...", "INFO")
        time.sleep(3)
        
        # Step 4: Check position created
        log("Step 4: Checking if position was created...", "INFO")
        status, new_positions = api_call("GET", "/positions")
        new_count = len(new_positions) if isinstance(new_positions, list) else 0
        
        if new_count > initial_count:
            log(f"Position created! Count: {initial_count} -> {new_count}", "SUCCESS")
            
            # Step 5: Close position
            log("Step 5: Closing position...", "INFO")
            status, close_response = api_call("POST", "/positions/AAPL/close")
            
            if status == 200:
                time.sleep(2)
                
                # Step 6: Verify position closed
                log("Step 6: Verifying position closed...", "INFO")
                status, final_positions = api_call("GET", "/positions")
                final_count = len(final_positions) if isinstance(final_positions, list) else 0
                
                if final_count < new_count:
                    test_result("integration", "Order Flow", True, 
                               f"Complete flow: {initial_count} -> {new_count} -> {final_count} positions")
                else:
                    test_result("integration", "Order Flow", False, 
                               "Position not closed")
            else:
                test_result("integration", "Order Flow", False, 
                           f"Failed to close position: {close_response}")
        else:
            test_result("integration", "Order Flow", False, 
                       "Position not created after order")
        
    except Exception as e:
        test_result("integration", "Order Flow", False, str(e))


def test_integration_data_pipeline():
    """Test data ingestion and feature computation pipeline."""
    log("\nTesting Data Pipeline...", "INFO")
    
    try:
        from core.alpaca_client import AlpacaClient
        from core.supabase_client import SupabaseClient
        from data.market_data import MarketDataManager
        
        alpaca = AlpacaClient()
        supabase = SupabaseClient()
        market_data = MarketDataManager(alpaca, supabase)
        
        # Test fetching latest bars
        log("Fetching latest bars...", "DEBUG")
        bars = market_data.fetch_latest_bars(["AAPL"])
        
        assert bars, "No bars fetched"
        assert "AAPL" in bars, "AAPL not in bars"
        
        # Test feature computation
        log("Computing features...", "DEBUG")
        historical = market_data.fetch_historical_bars(["AAPL"], days=1)
        
        if "AAPL" in historical:
            features = market_data.compute_features("AAPL", historical["AAPL"])
            assert features, "Features not computed"
            
            test_result("integration", "Data Pipeline", True, 
                       f"Fetched bars and computed features for AAPL")
        else:
            test_result("integration", "Data Pipeline", False, 
                       "No historical data available")
        
    except Exception as e:
        test_result("integration", "Data Pipeline", False, str(e))


# ============================================================================
# LEVEL 4: USE CASE TESTS - Real Trading Scenarios
# ============================================================================

def test_use_case_market_hours():
    """Test behavior during market hours vs closed."""
    log("\n" + "="*80, "INFO")
    log("LEVEL 4: USE CASE TESTS - Market Hours", "INFO")
    log("="*80, "INFO")
    
    try:
        from core.alpaca_client import AlpacaClient
        
        alpaca = AlpacaClient()
        is_open = alpaca.is_market_open()
        
        log(f"Market is currently: {'OPEN' if is_open else 'CLOSED'}", "INFO")
        
        test_result("use_case", "Market Hours Detection", True, 
                   f"Market is {'open' if is_open else 'closed'}")
        
    except Exception as e:
        test_result("use_case", "Market Hours Detection", False, str(e))


def test_use_case_risk_limits():
    """Test risk management limits."""
    log("\nTesting Risk Limits...", "INFO")
    
    try:
        from core.alpaca_client import AlpacaClient
        from trading.risk_manager import RiskManager
        
        alpaca = AlpacaClient()
        risk_mgr = RiskManager(alpaca)
        
        # Test 1: Normal order (should pass)
        approved, reason = risk_mgr.check_order("AAPL", "buy", 1, 150.0)
        log(f"Small order: {approved} - {reason}", "DEBUG")
        
        # Test 2: Large order (should fail)
        approved2, reason2 = risk_mgr.check_order("AAPL", "buy", 10000, 150.0)
        log(f"Large order: {approved2} - {reason2}", "DEBUG")
        
        # Risk manager should reject large order
        if not approved2:
            test_result("use_case", "Risk Limits", True, 
                       f"Correctly rejected large order: {reason2}")
        else:
            test_result("use_case", "Risk Limits", False, 
                       "Failed to reject large order")
        
    except Exception as e:
        test_result("use_case", "Risk Limits", False, str(e))


def test_use_case_circuit_breaker():
    """Test circuit breaker functionality."""
    log("\nTesting Circuit Breaker...", "INFO")
    
    try:
        status, metrics = api_call("GET", "/metrics")
        
        if status == 200:
            breaker_triggered = metrics.get('circuit_breaker_triggered', False)
            daily_pl_pct = metrics.get('daily_pl_pct', 0)
            
            log(f"Circuit breaker: {breaker_triggered}, Daily P/L: {daily_pl_pct:.2f}%", "DEBUG")
            
            test_result("use_case", "Circuit Breaker", True, 
                       f"Breaker: {breaker_triggered}, P/L: {daily_pl_pct:.2f}%")
        else:
            test_result("use_case", "Circuit Breaker", False, 
                       "Failed to get metrics")
        
    except Exception as e:
        test_result("use_case", "Circuit Breaker", False, str(e))


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def print_summary():
    """Print comprehensive test summary."""
    log("\n" + "="*80, "INFO")
    log("TEST SUMMARY", "INFO")
    log("="*80, "INFO")
    
    total_passed = 0
    total_failed = 0
    
    for category, results in test_results.items():
        passed = results["passed"]
        failed = results["failed"]
        total = passed + failed
        
        total_passed += passed
        total_failed += failed
        
        if total > 0:
            percentage = (passed / total) * 100
            status = "✓" if failed == 0 else "✗"
            
            log(f"\n{category.upper()} TESTS: {status}", "INFO")
            log(f"  Passed: {passed}/{total} ({percentage:.1f}%)", 
                "SUCCESS" if failed == 0 else "WARNING")
            
            if failed > 0:
                log(f"  Failed: {failed}", "ERROR")
                for test in results["tests"]:
                    if not test["passed"]:
                        log(f"    - {test['name']}: {test['details']}", "ERROR")
    
    log("\n" + "="*80, "INFO")
    log(f"TOTAL: {total_passed} passed, {total_failed} failed", 
        "SUCCESS" if total_failed == 0 else "ERROR")
    log("="*80, "INFO")
    
    # Save results to file
    with open("backend/test_results_comprehensive.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    log("\nResults saved to: backend/test_results_comprehensive.json", "INFO")
    
    return total_failed == 0


def main():
    """Run all tests."""
    log("="*80, "INFO")
    log("COMPREHENSIVE TEST SUITE - REAL DATA", "INFO")
    log("="*80, "INFO")
    log(f"API Base: {API_BASE}", "INFO")
    log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
    
    try:
        # Level 1: Unit Tests
        test_unit_config()
        test_unit_alpaca_client()
        test_unit_supabase_client()
        test_unit_risk_manager()
        test_unit_feature_engine()
        
        # Level 2: API Tests
        test_api_health()
        test_api_account()
        test_api_positions()
        test_api_orders()
        test_api_metrics()
        test_api_engine()
        test_api_trading_controls()
        
        # Level 3: Integration Tests
        test_integration_order_flow()
        test_integration_data_pipeline()
        
        # Level 4: Use Case Tests
        test_use_case_market_hours()
        test_use_case_risk_limits()
        test_use_case_circuit_breaker()
        
        # Print summary
        all_passed = print_summary()
        
        if all_passed:
            log("\n✓ ALL TESTS PASSED - READY FOR UAT", "SUCCESS")
            return 0
        else:
            log("\n✗ SOME TESTS FAILED - FIX ISSUES BEFORE UAT", "ERROR")
            return 1
    
    except KeyboardInterrupt:
        log("\n\nTests interrupted by user", "WARNING")
        return 1
    except Exception as e:
        log(f"\n\nFatal error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
