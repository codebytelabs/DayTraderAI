#!/usr/bin/env python3
"""
Test script for command system.
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from copilot.command_handler import CommandHandler
from copilot.query_router import QueryRouter
from copilot.config import CopilotConfig


def test_command_parsing():
    """Test command parsing."""
    print("🧪 Testing Command Parsing...")
    
    handler = CommandHandler(None)
    
    # Test slash commands
    tests = [
        ("/market-summary", "slash_command", "market-summary"),
        ("/news", "slash_command", "news"),
        ("#AAPL close", "portfolio_action", "AAPL"),
        ("#close-all", "portfolio_action", "CLOSE-ALL"),
        ("what happened yesterday?", "unknown", None),
    ]
    
    for query, expected_type, expected_value in tests:
        parsed = handler.parse_command(query)
        assert parsed["type"] == expected_type, f"Failed for {query}: expected {expected_type}, got {parsed['type']}"
        
        if expected_type == "slash_command":
            assert parsed["command"] == expected_value, f"Failed command parsing for {query}"
        elif expected_type == "portfolio_action":
            assert parsed["symbol"] == expected_value, f"Failed symbol parsing for {query}"
        
        print(f"   ✅ {query} -> {parsed['type']}")
    
    print("✅ Command parsing tests passed!\n")


def test_query_routing():
    """Test query routing with commands."""
    print("🧪 Testing Query Routing...")
    
    config = CopilotConfig()
    router = QueryRouter(config)
    
    # Test command routing
    tests = [
        ("/market-summary", "command"),
        ("#AAPL close", "command"),
        ("what happened yesterday?", "news"),
        ("should I buy AAPL?", "analysis"),
    ]
    
    for query, expected_category in tests:
        route = router.route(query, {}, [])
        assert route.category == expected_category, f"Failed for {query}: expected {expected_category}, got {route.category}"
        print(f"   ✅ {query} -> {route.category}")
    
    print("✅ Query routing tests passed!\n")


def test_command_detection():
    """Test command detection."""
    print("🧪 Testing Command Detection...")
    
    handler = CommandHandler(None)
    
    tests = [
        ("/market-summary", True),
        ("#AAPL close", True),
        ("what happened?", False),
        ("/", True),
        ("#", True),
    ]
    
    for query, expected in tests:
        result = handler.is_command(query)
        assert result == expected, f"Failed for {query}: expected {expected}, got {result}"
        print(f"   ✅ {query} -> {result}")
    
    print("✅ Command detection tests passed!\n")


def main():
    """Run all tests."""
    print("🚀 Testing Command System\n")
    
    try:
        test_command_parsing()
        test_query_routing()
        test_command_detection()
        
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Command System is ready!")
        print("\nNext steps:")
        print("1. Start your trading system: ./start_app.sh")
        print("2. Test the command palette in the UI")
        print("3. Try commands like:")
        print("   - Type '/' to see all slash commands")
        print("   - Type '#' to see portfolio actions")
        print("   - Type '/market-summary' for market overview")
        print("   - Type '#AAPL close' to close a position")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
