#!/bin/bash

# Complete App Startup Script
# Starts backend and frontend with full integration

echo "================================================================================"
echo "🚀 STARTING DAYTRADERAI - COMPLETE INTEGRATION"
echo "================================================================================"
echo ""

# Check if backend is already running
if lsof -Pi :8006 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Backend already running on port 8006"
    read -p "Kill and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping existing backend..."
        lsof -ti:8006 | xargs kill -9 2>/dev/null
        sleep 2
    fi
fi

# Start backend
echo "================================================================================"
echo "STEP 1: STARTING BACKEND"
echo "================================================================================"
echo ""

cd backend

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Starting backend on port 8006..."
python main.py > ../backend.log 2>&1 &
BACKEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Waiting for backend to start..."
sleep 10

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "❌ Backend failed to start. Check backend.log"
    tail -50 ../backend.log
    exit 1
fi

# Test backend with retry logic
echo "Testing backend connection..."
MAX_RETRIES=6
RETRY_COUNT=0
BACKEND_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8006/health > /dev/null; then
        echo "✅ Backend is running!"
        BACKEND_READY=true
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "⏳ Backend not ready yet, retrying in 5 seconds... ($RETRY_COUNT/$MAX_RETRIES)"
            sleep 5
        fi
    fi
done

if [ "$BACKEND_READY" = false ]; then
    echo "❌ Backend not responding after $MAX_RETRIES attempts"
    echo "Last 50 lines of backend.log:"
    tail -50 ../backend.log
    exit 1
fi

cd ..

# Start frontend
echo ""
echo "================================================================================"
echo "STEP 2: STARTING FRONTEND"
echo "================================================================================"
echo ""

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "Starting frontend on port 5173..."
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!

echo "Frontend PID: $FRONTEND_PID"
echo ""

# Summary
echo "================================================================================"
echo "✅ APP STARTED SUCCESSFULLY!"
echo "================================================================================"
echo ""
echo "Backend:  http://localhost:8006"
echo "Frontend: http://localhost:5173"
echo ""
echo "Backend PID:  $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Logs:"
echo "  Backend:  tail -f backend.log"
echo "  Frontend: tail -f frontend.log"
echo ""
echo "To stop:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "================================================================================"
echo "🎉 READY FOR UAT TESTING!"
echo "================================================================================"
echo ""
echo "Open http://localhost:5173 in your browser"
echo ""
