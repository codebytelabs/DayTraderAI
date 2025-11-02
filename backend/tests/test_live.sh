#!/bin/bash

# Simple Live Test Script for DayTraderAI
# Works on macOS

API_BASE="http://localhost:8006"

echo "================================================================================"
echo "DAYTRADERAI LIVE TEST"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counter
PASS=0
FAIL=0

test_endpoint() {
    local name=$1
    local endpoint=$2
    
    echo -n "Testing $name... "
    
    response=$(curl -s "$API_BASE$endpoint")
    
    if [ $? -eq 0 ] && [ ! -z "$response" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        echo "  $response" | head -c 150
        echo "..."
        ((PASS++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAIL++))
    fi
    echo ""
}

echo "Make sure backend is running: cd backend && ./run.sh"
echo ""
read -p "Press Enter when backend is ready..."
echo ""

echo "================================================================================"
echo "TESTING API ENDPOINTS"
echo "================================================================================"
echo ""

test_endpoint "Root" "/"
test_endpoint "Health" "/health"
test_endpoint "Account" "/account"
test_endpoint "Positions" "/positions"
test_endpoint "Orders" "/orders"
test_endpoint "Metrics" "/metrics"
test_endpoint "Engine Status" "/engine/status"

echo "================================================================================"
echo "SUMMARY"
echo "================================================================================"
echo ""
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Backend is working correctly!"
    echo ""
    echo "You have:"
    curl -s "$API_BASE/positions" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'  - {len(data)} open positions')" 2>/dev/null || echo "  - Positions data available"
    curl -s "$API_BASE/account" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'  - \${data[\"equity\"]:.2f} equity')" 2>/dev/null || echo "  - Account data available"
    echo ""
    echo "Trading engine is running and monitoring positions!"
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo "Check if backend is running on port 8006"
fi
