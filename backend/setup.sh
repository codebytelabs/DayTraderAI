#!/bin/bash

echo "🚀 Setting up DayTraderAI Backend..."

# Check Python version
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    echo "✓ Python version: $python_version"
else
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Create virtual environment
if [ -d "venv" ]; then
    echo "✓ Virtual environment already exists"
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys!"
else
    echo "✓ .env already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys (if not done already)"
echo "2. Run the Supabase schema: supabase_schema.sql"
echo "3. Activate venv: source venv/bin/activate"
echo "4. Start the backend: python main.py"
echo ""
echo "Quick start:"
echo "  source venv/bin/activate"
echo "  python main.py"
