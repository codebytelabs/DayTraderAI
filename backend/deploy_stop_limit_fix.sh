#!/bin/bash

echo "🚀 Deploying Stop-Limit Fix..."
echo ""

# Check if fix is in place
if grep -q "StopLimitOrderRequest" trading/stop_loss_protection.py; then
    echo "✅ Stop-limit fix detected in code"
else
    echo "❌ Fix not found! Check trading/stop_loss_protection.py"
    exit 1
fi

echo ""
echo "📋 Current bot status:"
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Bot is running (PID: $(pgrep -f 'python.*main.py'))"
    echo ""
    echo "🔄 Restarting bot to apply fix..."
    pkill -f "python.*main.py"
    sleep 2
    echo "✅ Bot stopped"
else
    echo "⚠️  Bot is not running"
fi

echo ""
echo "🎯 Fix Summary:"
echo "   - Changed stop orders to stop-limit orders"
echo "   - Eliminates 'wash trade detected' errors"
echo "   - All positions will get protection"
echo ""
echo "📖 See STOP_LIMIT_FIX_DEPLOYED.md for details"
echo ""
echo "✅ Ready to restart bot with: python main.py"
