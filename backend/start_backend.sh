#!/bin/bash
# Start DayTraderAI Backend

echo "🚀 Starting DayTraderAI Backend..."
echo ""

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Start the backend
echo "✅ Starting server on http://0.0.0.0:8006"
echo ""
python main.py
