#!/bin/bash
# Quick check for stop loss protection status in logs

echo "=================================="
echo "STOP LOSS PROTECTION STATUS CHECK"
echo "=================================="
echo ""

# Check if trading engine is running
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Trading engine is running"
else
    echo "❌ Trading engine is NOT running"
    exit 1
fi

echo ""
echo "Recent Protection Manager Activity:"
echo "-----------------------------------"

# Check for protection manager initialization
if tail -100 backend.log 2>/dev/null | grep -q "Stop Loss Protection Manager initialized"; then
    echo "✅ Protection manager initialized"
else
    echo "⚠️  Protection manager not found in recent logs"
fi

# Check for stop loss creation
CREATED=$(tail -500 backend.log 2>/dev/null | grep -c "Created stop loss for")
if [ "$CREATED" -gt 0 ]; then
    echo "✅ Created $CREATED stop losses recently"
    tail -500 backend.log 2>/dev/null | grep "Created stop loss for" | tail -5
fi

# Check for protection warnings
WARNINGS=$(tail -500 backend.log 2>/dev/null | grep -c "NO ACTIVE STOP LOSS")
if [ "$WARNINGS" -gt 0 ]; then
    echo "⚠️  $WARNINGS positions without stop loss detected"
    tail -500 backend.log 2>/dev/null | grep "NO ACTIVE STOP LOSS" | tail -5
else
    echo "✅ No unprotected positions detected"
fi

# Check for protection manager errors
ERRORS=$(tail -500 backend.log 2>/dev/null | grep -c "Failed to create stop loss")
if [ "$ERRORS" -gt 0 ]; then
    echo "❌ $ERRORS stop loss creation failures"
    tail -500 backend.log 2>/dev/null | grep "Failed to create stop loss" | tail -5
fi

echo ""
echo "=================================="
echo "Check complete. Review Alpaca dashboard to verify stops are active."
echo "=================================="
