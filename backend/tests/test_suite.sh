#!/bin/bash

# Comprehensive Test Suite for DayTraderAI Backend
# Tests with REAL API keys and data

set -e  # Exit on error

API_BASE="http://localhost:8006"
BACKEND_PID=""

echo "================================================================================"
echo "DAYTRADERAI BACKEND TEST SUITE"
echo "================================================================================"
echo ""
echo "⚠️  WARNING: This uses REAL API keys and paper trading"
echo "⚠️  Make sure backend/.env is configured correctly"
echo ""
read -p "Press Enter to continue..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test result
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

# Function to test API endpoint
test_api() {
    local method=$1
    local endpoint=$2
    local expected_code=$3
    local description=$4
    
    echo -n "Testing: $description... "
    
    # Use temp file to avoid head/tail issues on macOS
    local temp_file=$(mktemp)
    
    if [ "$method" = "GET" ]; then
        curl -s -w "\n%{http_code}" "$API_BASE$endpoint" > "$temp_file"
    else
        curl -s -w "\n%{http_code}" -X "$method" "$API_BASE$endpoint" > "$temp_file"
    fi
    
    http_code=$(tail -n 1 "$temp_file")
    body=$(sed '$d' "$temp_file")
    
    if [ "$http_code" = "$expected_code" ]; then
        test_result 0 "$description"
        echo "  Response: $(echo $body | cut -c1-100)..."
    else
        test_result 1 "$description (Expected $expected_code, got $http_code)"
        echo "  Response: $body"
    fi
    
    rm -f "$temp_file"
    echo ""
}

# Start backend
echo "================================================================================"
echo "STEP 1: START BACKEND"
echo "================================================================================"
echo ""

# Detect if we're in backend directory or root
if [ -f "main.py" ]; then
    # Already in backend directory
    BACKEND_DIR="."
    LOG_FILE="backend_test.log"
else
    # In root directory
    BACKEND_DIR="backend"
    LOG_FILE="backend_test.log"
    cd backend
fi

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

echo "Starting backend..."
source venv/bin/activate
python main.py > $LOG_FILE 2>&1 &
BACKEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Waiting for backend to start..."
sleep 10

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "❌ Backend failed to start. Check backend_test.log"
    cat backend_test.log | tail -50
    exit 1
fi

echo "✓ Backend started"
echo ""

# Test 1: Health Check
echo "================================================================================"
echo "STEP 2: HEALTH & CONNECTIVITY TESTS"
echo "================================================================================"
echo ""

test_api "GET" "/" "200" "Root endpoint"
test_api "GET" "/health" "200" "Health check"
test_api "GET" "/account" "200" "Account info (Alpaca connection)"

# Test 2: State Endpoints
echo "================================================================================"
echo "STEP 3: STATE & DATA TESTS"
echo "================================================================================"
echo ""

test_api "GET" "/positions" "200" "Get positions"
test_api "GET" "/orders" "200" "Get orders"
test_api "GET" "/metrics" "200" "Get metrics"
test_api "GET" "/engine/status" "200" "Engine status"

# Test 3: Trading Controls
echo "================================================================================"
echo "STEP 4: TRADING CONTROL TESTS"
echo "================================================================================"
echo ""

test_api "POST" "/trading/disable" "200" "Disable trading"
test_api "POST" "/trading/enable" "200" "Enable trading"
test_api "POST" "/sync" "200" "Manual sync"

# Test 4: Order Submission (Real Test!)
echo "================================================================================"
echo "STEP 5: ORDER SUBMISSION TEST (REAL PAPER TRADING)"
echo "================================================================================"
echo ""

echo "⚠️  This will submit a REAL paper trading order!"
read -p "Press Enter to continue or Ctrl+C to skip..."
echo ""

echo "Submitting test order: BUY 1 AAPL..."
response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/orders/submit?symbol=AAPL&side=buy&qty=1&reason=test")
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" = "200" ]; then
    success=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
    if [ "$success" = "True" ]; then
        test_result 0 "Order submission"
        echo "  Order submitted successfully!"
    else
        test_result 1 "Order submission (rejected by risk manager)"
        echo "  Reason: $body"
    fi
else
    test_result 1 "Order submission (HTTP error)"
    echo "  Response: $body"
fi

echo ""
sleep 2

# Check if position was created
echo "Checking for position..."
positions=$(curl -s "$API_BASE/positions")
position_count=$(echo "$positions" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
echo "  Current positions: $position_count"
echo ""

# Test 5: Position Management
if [ "$position_count" -gt "0" ]; then
    echo "================================================================================"
    echo "STEP 6: POSITION MANAGEMENT TEST"
    echo "================================================================================"
    echo ""
    
    echo "Closing AAPL position..."
    test_api "POST" "/positions/AAPL/close" "200" "Close position"
    
    sleep 2
    
    # Verify position closed
    positions=$(curl -s "$API_BASE/positions")
    new_count=$(echo "$positions" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
    
    if [ "$new_count" -lt "$position_count" ]; then
        test_result 0 "Position closed successfully"
    else
        test_result 1 "Position not closed"
    fi
    echo ""
fi

# Test 6: Engine Control
echo "================================================================================"
echo "STEP 7: ENGINE CONTROL TESTS"
echo "================================================================================"
echo ""

# Engine should be running by default
status=$(curl -s "$API_BASE/engine/status")
is_running=$(echo "$status" | python3 -c "import sys, json; print(json.load(sys.stdin).get('running', False))" 2>/dev/null)

if [ "$is_running" = "True" ]; then
    test_result 0 "Engine is running"
else
    test_result 1 "Engine not running"
fi

echo ""

# Test 7: Data Validation
echo "================================================================================"
echo "STEP 8: DATA VALIDATION"
echo "================================================================================"
echo ""

echo "Validating account data..."
account=$(curl -s "$API_BASE/account")
equity=$(echo "$account" | python3 -c "import sys, json; print(json.load(sys.stdin).get('equity', 0))" 2>/dev/null)

if [ "$(echo "$equity > 0" | bc)" -eq 1 ]; then
    test_result 0 "Account has equity: \$$equity"
else
    test_result 1 "Invalid account equity"
fi

echo ""

echo "Validating metrics..."
metrics=$(curl -s "$API_BASE/metrics")
equity_metric=$(echo "$metrics" | python3 -c "import sys, json; print(json.load(sys.stdin).get('equity', 0))" 2>/dev/null)

if [ "$(echo "$equity_metric > 0" | bc)" -eq 1 ]; then
    test_result 0 "Metrics equity: \$$equity_metric"
else
    test_result 1 "Invalid metrics"
fi

echo ""

# Cleanup
echo "================================================================================"
echo "CLEANUP"
echo "================================================================================"
echo ""

echo "Stopping backend (PID: $BACKEND_PID)..."
kill $BACKEND_PID 2>/dev/null || true
sleep 2

# Force kill if still running
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "Force killing backend..."
    kill -9 $BACKEND_PID 2>/dev/null || true
fi

echo "✓ Backend stopped"
echo ""

# Summary
echo "================================================================================"
echo "TEST SUMMARY"
echo "================================================================================"
echo ""
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Backend is ready for UAT testing!"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo ""
    echo "Check backend_test.log for details"
    echo "Fix issues before UAT testing"
    exit 1
fi
