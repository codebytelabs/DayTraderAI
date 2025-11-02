#!/bin/bash

# Complete Integration Test Runner
# Tests ALL APIs before UAT

set -e

echo "================================================================================"
echo "COMPLETE INTEGRATION TEST SUITE"
echo "================================================================================"
echo ""
echo "This will test:"
echo "  ✓ Alpaca API (trading)"
echo "  ✓ Supabase (database)"
echo "  ✓ OpenRouter (AI analysis)"
echo "  ✓ Perplexity (market research)"
echo "  ✓ Complete workflows"
echo "  ✓ Error handling"
echo ""
read -p "Press Enter to continue..."
echo ""

# Navigate to backend
cd backend

# Activate venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

source venv/bin/activate

# Run tests
echo "Running integration tests..."
python test_all_integrations.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "================================================================================"
    echo "✓ ALL INTEGRATIONS VALIDATED!"
    echo "================================================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Connect frontend to backend"
    echo "  2. Run UAT testing"
    echo ""
else
    echo ""
    echo "================================================================================"
    echo "✗ SOME TESTS FAILED"
    echo "================================================================================"
    echo ""
    echo "Fix issues before proceeding to UAT"
    echo ""
fi

exit $exit_code
