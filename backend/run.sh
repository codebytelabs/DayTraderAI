#!/bin/bash

# Quick run script for DayTraderAI backend

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

echo "🚀 Starting DayTraderAI Backend..."
source venv/bin/activate
python main.py
