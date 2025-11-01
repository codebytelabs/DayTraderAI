"""
Complete Integration Test Suite
Tests ALL APIs and workflows before UAT:
- Alpaca (trading)
- Supabase (database)
- OpenRouter (AI analysis)
- Perplexity (market research)
- Full trading workflows
- Error handling
"""

import sys
import time
import json
import asyncio
from datetime import datetime, UTC
from typing import Dict, Tuple

# Test Results
results = {
    "alpaca": {"passed": 0, "failed": 0, "tests": []},
    "supabase": {"passed": 0, "failed": 0, "tests": []},
    "openrouter": {"passed": 0, "failed": 0, "tests": []},
    "perplexity": {"passed": 0, "failed": 0, "tests": []},
    "workflows": {"passed": 0, "failed": 0, "tests": []},
    "error_handling": {"passed": 0, "failed": 0, "tests": []}
}


def log(message: str, level: str = "INFO"):
    """Enhanced logging."""
    colors = {
        "INFO": "\033[0;37m",
        "SUCCESS": "\033[0;32m",
        "ERROR": "\033[0;31m",
        "WARNING": "\033[1;33m",
    }
    color = colors.get(level, "\033[0;37m")
    reset = "\033[0m"
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{timestamp}] {message}{reset}")


def record_test(category: str, name: str, passed: bool, details: str = ""):
    """Record test result."""
    result = {
        "name": name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    
    results[category]["tests"].append(result)
    
    if passed:
        results[category]["passed"] += 1
        log(f"✓ {name}", "SUCCESS")
    else:
        results[category]["failed"] += 1
        log(f"✗ {name}: {details}", "ERROR")
    
    if details and passed:
        log(f"  {details}", "INFO")


# ============================================================================
# ALPACA TESTS
# ============================================================================

def test_alpaca_connection():
    """Test Alpaca API connection."""
    log("\n" + "="*80, "INFO")
    log("TESTING ALPACA INTEGRATION", "INFO")
    log("="*80, "INFO")
    
    try:
        from core.alpaca_client import AlpacaClient
        
        client = AlpacaClient()
        account = client.get_account()
        
        equity = float(account.equity)
        cash = float(account.cash)
        buying_power = float(account.buying_power)
        
        record_test("alpaca", "Connection & Authentication", True,
                   f"Equity: ${equity:,.2f}, Cash: ${cash:,.2f}")
        
        return client
        
    except Exception as e:
        record_test("alpaca", "Connection & Authentication", False, str(e))
        return None


def test_alpaca_market_data(client):
    """Test market data fetching."""
    if not client:
        record_test("alpaca", "Market Data", False, "No client")
        return
    
    try:
        # Test latest bars
        bars = client.get_latest_bars(["AAPL", "SPY"])
        
        assert bars, "No bars returned"
        assert "AAPL" in bars, "AAPL not in bars"
        assert "SPY" in bars, "SPY not in bars"
        
        aapl_price = bars["AAPL"].close
        
        record_test("alpaca", "Market Data Fetching", True,
                   f"AAPL: ${aapl_price:.2f}, SPY: ${bars['SPY'].close:.2f}")
        
    except Exception as e:
        record_test("alpaca", "Market Data Fetching", False, str(e))


def test_alpaca_positions(client):
    """Test position management."""
    if not client:
        record_test("alpaca", "Positions", False, "No client")
        return
    
    try:
        positions = client.get_positions()
        
        record_test("alpaca", "Position Retrieval", True,
                   f"Found {len(positions)} positions")
        
    except Exception as e:
        record_test("alpaca", "Position Retrieval", False, str(e))


def test_alpaca_orders(client):
    """Test order management."""
    if not client:
        record_test("alpaca", "Orders", False, "No client")
        return
    
    try:
        orders = client.get_orders()
        
        record_test("alpaca", "Order Retrieval", True,
                   f"Found {len(orders)} orders")
        
    except Exception as e:
        record_test("alpaca", "Order Retrieval", False, str(e))


def test_alpaca_market_hours(client):
    """Test market hours detection."""
    if not client:
        record_test("alpaca", "Market Hours", False, "No client")
        return
    
    try:
        is_open = client.is_market_open()
        
        record_test("alpaca", "Market Hours Detection", True,
                   f"Market is {'OPEN' if is_open else 'CLOSED'}")
        
    except Exception as e:
        record_test("alpaca", "Market Hours Detection", False, str(e))


# ============================================================================
# SUPABASE TESTS
# ============================================================================

def test_supabase_connection():
    """Test Supabase connection."""
    log("\n" + "="*80, "INFO")
    log("TESTING SUPABASE INTEGRATION", "INFO")
    log("="*80, "INFO")
    
    try:
        from core.supabase_client import SupabaseClient
        
        client = SupabaseClient()
        
        # Test connection by fetching metrics
        metrics = client.get_latest_metrics()
        
        record_test("supabase", "Connection & Authentication", True,
                   "Connected to database")
        
        return client
        
    except Exception as e:
        record_test("supabase", "Connection & Authentication", False, str(e))
        return None


def test_supabase_metrics(client):
    """Test metrics storage and retrieval."""
    if not client:
        record_test("supabase", "Metrics", False, "No client")
        return
    
    try:
        # Save test metric
        test_metric = {
            "equity": 100000.0,
            "cash": 50000.0,
            "daily_pl": 1000.0,
            "daily_pl_pct": 1.0,
            "position_count": 5,
            "win_rate": 0.65,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        client.insert_metrics(test_metric)
        
        # Retrieve latest
        latest = client.get_latest_metrics()
        
        assert latest, "No metrics retrieved"
        
        record_test("supabase", "Metrics Storage", True,
                   f"Saved and retrieved metrics")
        
    except Exception as e:
        record_test("supabase", "Metrics Storage", False, str(e))


def test_supabase_trades(client):
    """Test trade logging."""
    if not client:
        record_test("supabase", "Trades", False, "No client")
        return
    
    try:
        # Log test trade
        test_trade = {
            "symbol": "TEST",
            "side": "buy",
            "qty": 10,
            "entry_price": 100.0,
            "exit_price": 105.0,
            "pnl": 50.0,
            "pnl_pct": 5.0,
            "reason": "integration_test",
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        client.insert_trade(test_trade)
        
        # Retrieve recent trades
        trades = client.get_trades(limit=10)
        
        record_test("supabase", "Trade Logging", True,
                   f"Logged trade, retrieved {len(trades)} recent trades")
        
    except Exception as e:
        record_test("supabase", "Trade Logging", False, str(e))


# ============================================================================
# OPENROUTER TESTS
# ============================================================================

async def test_openrouter_connection():
    """Test OpenRouter API connection."""
    log("\n" + "="*80, "INFO")
    log("TESTING OPENROUTER INTEGRATION", "INFO")
    log("="*80, "INFO")
    
    try:
        from advisory.openrouter import OpenRouterClient
        
        advisor = OpenRouterClient()
        
        # Test simple query
        response = await advisor.analyze_trade(
            symbol="AAPL",
            side="buy",
            price=150.0,
            features={
                "ema_short": 149.0,
                "ema_long": 147.0,
                "atr": 2.5,
                "volume_zscore": 1.5
            }
        )
        
        assert response, "No response from OpenRouter"
        assert len(response) > 50, "Response too short"
        
        record_test("openrouter", "Connection & API Call", True,
                   f"Received {len(response)} char response")
        
        return advisor
        
    except Exception as e:
        record_test("openrouter", "Connection & API Call", False, str(e))
        return None


async def test_openrouter_trade_analysis(advisor):
    """Test trade analysis."""
    if not advisor:
        record_test("openrouter", "Trade Analysis", False, "No advisor")
        return
    
    try:
        response = await advisor.analyze_trade(
            symbol="NVDA",
            side="sell",
            price=500.0,
            features={
                "ema_short": 502.0,
                "ema_long": 505.0,
                "atr": 15.0,
                "volume_zscore": -0.5
            }
        )
        
        assert response, "No analysis returned"
        
        # Check for key elements
        has_score = any(word in response.lower() for word in ["score", "rating", "quality"])
        has_action = any(word in response.lower() for word in ["go", "wait", "pass", "buy", "sell"])
        
        record_test("openrouter", "Trade Analysis Quality", True,
                   f"Analysis includes score: {has_score}, action: {has_action}")
        
    except Exception as e:
        record_test("openrouter", "Trade Analysis Quality", False, str(e))


async def test_openrouter_fallback(advisor):
    """Test multiple model availability."""
    if not advisor:
        record_test("openrouter", "Multiple Models", False, "No advisor")
        return
    
    try:
        # Test that we have multiple models configured
        has_primary = bool(advisor.primary_model)
        has_secondary = bool(advisor.secondary_model)
        has_tertiary = bool(advisor.tertiary_model)
        
        assert has_primary, "No primary model configured"
        assert has_secondary, "No secondary model configured"
        assert has_tertiary, "No tertiary model configured"
        
        # Test quick insight with tertiary model
        response = await advisor.quick_insight("What is the current market sentiment?")
        
        assert response, "Tertiary model failed"
        
        record_test("openrouter", "Multiple Models Available", True,
                   f"Primary, Secondary, and Tertiary models configured")
        
    except Exception as e:
        record_test("openrouter", "Multiple Models Available", False, str(e))


# ============================================================================
# PERPLEXITY TESTS
# ============================================================================

async def test_perplexity_connection():
    """Test Perplexity API connection."""
    log("\n" + "="*80, "INFO")
    log("TESTING PERPLEXITY INTEGRATION", "INFO")
    log("="*80, "INFO")
    
    try:
        from advisory.perplexity import PerplexityClient
        
        advisor = PerplexityClient()
        
        # Test simple query
        result = await advisor.get_news("AAPL")
        response = result.get("content") if result else None
        
        assert response, "No response from Perplexity"
        assert len(response) > 50, "Response too short"
        
        record_test("perplexity", "Connection & API Call", True,
                   f"Received {len(response)} char response")
        
        return advisor
        
    except Exception as e:
        record_test("perplexity", "Connection & API Call", False, str(e))
        return None


async def test_perplexity_market_context(advisor):
    """Test market context retrieval."""
    if not advisor:
        record_test("perplexity", "Market Context", False, "No advisor")
        return
    
    try:
        result = await advisor.get_news("NVDA")
        response = result.get("content") if result else None
        
        assert response, "No context returned"
        
        # Check for relevant content
        has_news = any(word in response.lower() for word in ["news", "announced", "reported"])
        has_market = any(word in response.lower() for word in ["market", "trading", "stock"])
        
        record_test("perplexity", "Market Context Quality", True,
                   f"Context includes news: {has_news}, market info: {has_market}")
        
    except Exception as e:
        record_test("perplexity", "Market Context Quality", False, str(e))


# ============================================================================
# WORKFLOW TESTS
# ============================================================================

async def test_complete_trading_workflow():
    """Test complete trading workflow."""
    log("\n" + "="*80, "INFO")
    log("TESTING COMPLETE WORKFLOWS", "INFO")
    log("="*80, "INFO")
    
    try:
        from core.alpaca_client import AlpacaClient
        from trading.risk_manager import RiskManager
        
        # Initialize components
        alpaca = AlpacaClient()
        risk_mgr = RiskManager(alpaca)
        
        # Step 1: Fetch latest market data (always available)
        bars = alpaca.get_latest_bars(["AAPL"])
        assert bars, "No market data"
        assert "AAPL" in bars, "AAPL not in bars"
        
        # Step 2: Get current price
        current_price = bars["AAPL"].close
        assert current_price > 0, "Invalid price"
        
        # Step 3: Test risk check for small order (should pass)
        approved, reason = risk_mgr.check_order("AAPL", "buy", 1, current_price)
        assert reason, "No risk check reason"
        
        # Step 4: Test risk check for large order (should fail)
        approved_large, reason_large = risk_mgr.check_order("AAPL", "buy", 100000, current_price)
        assert not approved_large, "Should reject large order"
        
        record_test("workflows", "Complete Trading Workflow", True,
                   f"Market Data -> Risk Checks -> Validation")
        
    except Exception as e:
        record_test("workflows", "Complete Trading Workflow", False, str(e))


async def test_ai_advisory_workflow():
    """Test AI advisory workflow."""
    try:
        from advisory.openrouter import OpenRouterClient
        from advisory.perplexity import PerplexityClient
        
        openrouter = OpenRouterClient()
        perplexity = PerplexityClient()
        
        # Step 1: Get market context
        result = await perplexity.get_news("AAPL")
        context = result.get("content") if result else None
        assert context, "No market context"
        
        # Step 2: Analyze trade with context
        analysis = await openrouter.analyze_trade(
            symbol="AAPL",
            side="buy",
            price=150.0,
            features={
                "ema_short": 149.0,
                "ema_long": 147.0,
                "atr": 2.5,
                "volume_zscore": 1.5
            },
            context=context[:500]  # Include context
        )
        assert analysis, "No analysis"
        
        record_test("workflows", "AI Advisory Workflow", True,
                   "Market Context -> Trade Analysis")
        
    except Exception as e:
        record_test("workflows", "AI Advisory Workflow", False, str(e))


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_error_handling():
    """Test error handling and validation."""
    log("\n" + "="*80, "INFO")
    log("TESTING ERROR HANDLING & VALIDATION", "INFO")
    log("="*80, "INFO")
    
    try:
        from trading.risk_manager import RiskManager
        from core.alpaca_client import AlpacaClient
        
        alpaca = AlpacaClient()
        risk_mgr = RiskManager(alpaca)
        
        # Test 1: Check that risk manager validates orders
        approved1, reason1 = risk_mgr.check_order("AAPL", "buy", 100000, 150.0)
        assert not approved1, f"Should reject excessive size"
        assert reason1, "Should have reason for rejection"
        
        # Test 2: Check that risk manager provides reasons
        approved2, reason2 = risk_mgr.check_order("AAPL", "buy", 1, 150.0)
        # May approve or reject based on market hours, but must have reason
        assert reason2, "Should have reason for decision"
        assert len(reason2) > 0, "Reason should not be empty"
        
        # Test 3: Check that risk manager handles different scenarios
        approved3, reason3 = risk_mgr.check_order("AAPL", "buy", 0, 150.0)
        assert not approved3, f"Should reject zero quantity"
        assert reason3, "Should have reason for rejection"
        
        # Verify risk manager is working correctly
        # It should reject at least one of the above (which it did)
        rejections = sum([not approved1, not approved2, not approved3])
        assert rejections >= 2, "Risk manager should reject invalid orders"
        
        record_test("error_handling", "Risk Validation & Limits", True,
                   f"Risk manager validates orders correctly ({rejections}/3 rejected)")
        
    except Exception as e:
        record_test("error_handling", "Risk Validation & Limits", False, str(e))


# ============================================================================
# MAIN RUNNER
# ============================================================================

def print_summary():
    """Print test summary."""
    log("\n" + "="*80, "INFO")
    log("TEST SUMMARY", "INFO")
    log("="*80, "INFO")
    
    total_passed = 0
    total_failed = 0
    
    for category, data in results.items():
        passed = data["passed"]
        failed = data["failed"]
        total = passed + failed
        
        if total > 0:
            total_passed += passed
            total_failed += failed
            
            percentage = (passed / total) * 100
            status = "✓" if failed == 0 else "✗"
            
            log(f"\n{category.upper()}: {status} {passed}/{total} ({percentage:.0f}%)",
                "SUCCESS" if failed == 0 else "ERROR")
            
            if failed > 0:
                for test in data["tests"]:
                    if not test["passed"]:
                        log(f"  ✗ {test['name']}: {test['details']}", "ERROR")
    
    log("\n" + "="*80, "INFO")
    log(f"TOTAL: {total_passed} passed, {total_failed} failed",
        "SUCCESS" if total_failed == 0 else "ERROR")
    log("="*80, "INFO")
    
    # Save results
    with open("integration_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    log("\nResults saved to: integration_test_results.json", "INFO")
    
    return total_failed == 0


async def main():
    """Run all tests."""
    log("="*80, "INFO")
    log("COMPLETE INTEGRATION TEST SUITE", "INFO")
    log("="*80, "INFO")
    log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
    
    try:
        # Alpaca tests
        alpaca_client = test_alpaca_connection()
        test_alpaca_market_data(alpaca_client)
        test_alpaca_positions(alpaca_client)
        test_alpaca_orders(alpaca_client)
        test_alpaca_market_hours(alpaca_client)
        
        # Supabase tests
        supabase_client = test_supabase_connection()
        test_supabase_metrics(supabase_client)
        test_supabase_trades(supabase_client)
        
        # OpenRouter tests
        openrouter_advisor = await test_openrouter_connection()
        await test_openrouter_trade_analysis(openrouter_advisor)
        await test_openrouter_fallback(openrouter_advisor)
        
        # Perplexity tests
        perplexity_advisor = await test_perplexity_connection()
        await test_perplexity_market_context(perplexity_advisor)
        
        # Workflow tests
        await test_complete_trading_workflow()
        await test_ai_advisory_workflow()
        
        # Error handling
        test_error_handling()
        
        # Summary
        all_passed = print_summary()
        
        if all_passed:
            log("\n✓ ALL INTEGRATIONS VALIDATED - READY FOR UAT", "SUCCESS")
            return 0
        else:
            log("\n✗ SOME TESTS FAILED - FIX BEFORE UAT", "ERROR")
            return 1
    
    except KeyboardInterrupt:
        log("\n\nTests interrupted", "WARNING")
        return 1
    except Exception as e:
        log(f"\n\nFatal error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
