#!/bin/bash

echo "🚀 Setting up DayTraderAI Backend..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys!"
else
    echo ".env already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your Alpaca and Supabase keys"
echo "2. Run the Supabase schema: supabase_schema.sql"
echo "3. Start the backend: python main.py"
echo ""
echo "To activate the virtual environment later:"
echo "  source venv/bin/activate"
