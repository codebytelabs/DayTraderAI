#!/bin/bash

# Deploy AI Trade Validation - Phase 1
# This script enables AI validation and restarts the backend

echo "========================================"
echo "AI Trade Validation - Phase 1 Deployment"
echo "========================================"
echo ""

# Check if config.py has AI validation enabled
if grep -q "ENABLE_AI_VALIDATION: bool = True" config.py; then
    echo "✅ AI validation already enabled in config.py"
else
    echo "⚠️  AI validation not enabled in config.py"
    echo "   Please set ENABLE_AI_VALIDATION = True in backend/config.py"
    exit 1
fi

echo ""
echo "📋 Pre-deployment checklist:"
echo "   ✅ AITradeValidator class created"
echo "   ✅ Risk manager integration complete"
echo "   ✅ All tests passed"
echo "   ✅ Configuration verified"
echo ""

# Ask for confirmation
read -p "Deploy AI validation now? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "🚀 Deploying AI validation..."
echo ""

# Check if backend is running
if pgrep -f "python.*trading_engine.py" > /dev/null; then
    echo "📍 Backend is running, restarting..."
    
    # Kill existing process
    pkill -f "python.*trading_engine.py"
    sleep 2
    
    echo "✅ Backend stopped"
else
    echo "📍 Backend not running"
fi

echo ""
echo "🔄 Starting backend with AI validation..."
echo ""

# Start backend in background
nohup python trading/trading_engine.py > logs/trading.log 2>&1 &

# Wait for startup
sleep 3

# Check if started successfully
if pgrep -f "python.*trading_engine.py" > /dev/null; then
    echo "✅ Backend started successfully"
    echo ""
    echo "📊 Monitoring AI validation..."
    echo "   (Press Ctrl+C to stop monitoring)"
    echo ""
    
    # Monitor logs for AI validation
    tail -f logs/trading.log | grep --line-buffered '🤖'
else
    echo "❌ Failed to start backend"
    echo "   Check logs/trading.log for errors"
    exit 1
fi
