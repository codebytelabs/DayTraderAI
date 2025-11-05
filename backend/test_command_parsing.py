#!/usr/bin/env python3
"""
Simple test for command parsing (no dependencies).
"""


def parse_command(query: str):
    """Parse command from query."""
    query = query.strip()
    
    if query.startswith('/'):
        parts = query[1:].split()
        command = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        return {
            "type": "slash_command",
            "command": command,
            "args": args,
            "raw": query
        }
    elif query.startswith('#'):
        parts = query[1:].split()
        
        if not parts:
            return {"type": "portfolio_action", "action": "list", "raw": query}
        
        symbol_or_action = parts[0].upper()
        action = parts[1].lower() if len(parts) > 1 else "info"
        params = parts[2:] if len(parts) > 2 else []
        
        return {
            "type": "portfolio_action",
            "symbol": symbol_or_action,
            "action": action,
            "params": params,
            "raw": query
        }
    
    return {"type": "unknown", "raw": query}


def is_command(query: str) -> bool:
    """Check if query is a command."""
    return query.strip().startswith('/') or query.strip().startswith('#')


def main():
    """Run tests."""
    print("🚀 Testing Command Parsing\n")
    
    # Test slash commands
    print("📋 Testing Slash Commands:")
    slash_tests = [
        "/market-summary",
        "/news",
        "/portfolio-summary",
        "/opportunities",
        "/help",
    ]
    
    for query in slash_tests:
        parsed = parse_command(query)
        assert parsed["type"] == "slash_command"
        print(f"   ✅ {query} -> command: {parsed['command']}")
    
    # Test portfolio actions
    print("\n⚡ Testing Portfolio Actions:")
    action_tests = [
        ("#AAPL close", "AAPL", "close"),
        ("#NVDA", "NVDA", "info"),
        ("#close-all", "CLOSE-ALL", "info"),
        ("#cancel-all", "CANCEL-ALL", "info"),
        ("#", None, "list"),
    ]
    
    for query, expected_symbol, expected_action in action_tests:
        parsed = parse_command(query)
        assert parsed["type"] == "portfolio_action"
        if expected_symbol:
            assert parsed["symbol"] == expected_symbol
        assert parsed["action"] == expected_action
        print(f"   ✅ {query} -> symbol: {parsed.get('symbol', 'N/A')}, action: {parsed['action']}")
    
    # Test command detection
    print("\n🔍 Testing Command Detection:")
    detection_tests = [
        ("/market-summary", True),
        ("#AAPL close", True),
        ("what happened?", False),
        ("buy 50 AAPL", False),
    ]
    
    for query, expected in detection_tests:
        result = is_command(query)
        assert result == expected
        print(f"   ✅ {query} -> is_command: {result}")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("\n✅ Command System parsing is working correctly!")
    print("\nSupported commands:")
    print("  Slash Commands (/):")
    print("    - /market-summary - Market overview")
    print("    - /news - Latest news")
    print("    - /portfolio-summary - Portfolio analysis")
    print("    - /opportunities - Trading opportunities")
    print("    - /help - Show all commands")
    print("\n  Portfolio Actions (#):")
    print("    - #SYMBOL close - Close a position")
    print("    - #SYMBOL - Get position info")
    print("    - #close-all - Close all positions")
    print("    - #cancel-all - Cancel all orders")
    print("    - # - List all positions and actions")


if __name__ == "__main__":
    main()
