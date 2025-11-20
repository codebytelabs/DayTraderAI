#!/bin/bash
echo "======================================================================"
echo "LONG-ONLY MODE & TRAILING STOPS CONFIGURATION CHECK"
echo "======================================================================"
echo ""
echo "Checking config.py for long_only_mode setting..."
if grep -q "long_only_mode.*True" backend/config.py; then
    echo "✅ long_only_mode: True (ENABLED)"
else
    echo "❌ long_only_mode: NOT FOUND or False"
fi

echo ""
echo "Checking trading_engine.py for long-only filter..."
if grep -q "long_only_mode.*SELL signal rejected" backend/trading/trading_engine.py; then
    echo "✅ Long-only filter: IMPLEMENTED in trading_engine.py"
else
    echo "❌ Long-only filter: NOT FOUND in trading_engine.py"
fi

echo ""
echo "Checking trailing stops configuration..."
if grep -q "trailing_stops_enabled.*True" backend/config.py; then
    echo "✅ trailing_stops_enabled: True (ENABLED)"
else
    echo "❌ trailing_stops_enabled: NOT FOUND or False"
fi

echo ""
echo "======================================================================"
echo "CONFIGURATION STATUS"
echo "======================================================================"
