#!/bin/bash

echo "============================================================"
echo "🚀 RESTARTING BEST BOT WITH ALL FIXES"
echo "============================================================"
echo ""

# Stop current bot
echo "🛑 Stopping current bot..."
pkill -f "python.*main.py"
sleep 2

# Verify it stopped
if pgrep -f "python.*main.py" > /dev/null; then
    echo "❌ Bot still running, force killing..."
    pkill -9 -f "python.*main.py"
    sleep 2
fi

echo "✅ Bot stopped"
echo ""

# Start the bot
echo "🚀 Starting BEST bot with all fixes..."
cd backend

# Activate virtual environment if it exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Start bot in background
nohup python main.py > ../bot.log 2>&1 &
BOT_PID=$!

echo "✅ Bot started (PID: $BOT_PID)"
echo ""

# Wait a moment for startup
sleep 3

# Check if it's running
if ps -p $BOT_PID > /dev/null; then
    echo "============================================================"
    echo "✅ BEST BOT IS RUNNING!"
    echo "============================================================"
    echo ""
    echo "📊 Monitor with:"
    echo "   tail -f bot.log"
    echo ""
    echo "🛑 Stop with:"
    echo "   pkill -f 'python.*main.py'"
    echo ""
    echo "💰 READY TO MAKE MONEY!"
else
    echo "❌ Bot failed to start. Check bot.log for errors:"
    echo "   tail -50 bot.log"
    exit 1
fi
