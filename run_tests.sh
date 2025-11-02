#!/bin/bash

# Wrapper script to run tests from root directory

echo "Running DayTraderAI Test Suite..."
echo ""

cd "$(dirname "$0")"

if [ ! -f "backend/test_suite.sh" ]; then
    echo "❌ Test suite not found"
    exit 1
fi

bash backend/test_suite.sh
