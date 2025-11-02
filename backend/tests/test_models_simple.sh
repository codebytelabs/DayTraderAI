#!/bin/bash

# Simple model testing with curl
API_KEY="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"
BASE_URL="https://openrouter.ai/api/v1/chat/completions"

# Test prompt
read -r -d '' PROMPT << 'EOF'
{
  "model": "MODEL_NAME",
  "messages": [
    {"role": "system", "content": "You are an expert day trading analyst. Provide concise, actionable analysis."},
    {"role": "user", "content": "Analyze this trade:\n\nSymbol: AAPL\nAction: BUY\nPrice: $178.50\n\nTechnical Indicators:\n- EMA Short (9): $177.20\n- EMA Long (21): $175.80\n- ATR: $2.40\n- Volume Z-Score: 1.8\n\nThe short EMA just crossed above the long EMA with strong volume.\n\nProvide:\n1. Trade quality score (1-10)\n2. Key risks (2-3 points)\n3. Recommended action (GO/WAIT/PASS)\n\nBe concise and actionable."}
  ],
  "temperature": 0.7,
  "max_tokens": 1000
}
EOF

# Models to test
declare -a MODELS=(
    "anthropic/claude-sonnet-4.5"
    "anthropic/claude-haiku-4.5"
    "anthropic/claude-3.5-haiku"
    "google/gemini-2.5-flash-preview-09-2025"
    "google/gemini-2.5-flash-lite-preview-09-2025"
    "openai/gpt-5-mini"
    "openai/gpt-oss-120b"
    "openai/gpt-oss-safeguard-20b"
)

echo "================================================================================"
echo "OPENROUTER MODEL TESTING - TRADE ANALYSIS"
echo "================================================================================"
echo ""
echo "Testing ${#MODELS[@]} models for quality and speed..."
echo ""

# Results file
RESULTS_FILE="backend/test_results.txt"
> "$RESULTS_FILE"

for MODEL in "${MODELS[@]}"; do
    echo "Testing: $MODEL"
    echo "--------------------------------------------------------------------------------"
    
    # Replace MODEL_NAME
    TEST_PROMPT="${PROMPT//MODEL_NAME/$MODEL}"
    
    # Time the request
    START=$(perl -MTime::HiRes=time -e 'print time')
    
    # Make request and save to temp file
    TEMP_FILE=$(mktemp)
    HTTP_CODE=$(curl -s -w "%{http_code}" -o "$TEMP_FILE" \
        -X POST "$BASE_URL" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d "$TEST_PROMPT")
    
    END=$(perl -MTime::HiRes=time -e 'print time')
    ELAPSED=$(perl -e "print $END - $START")
    
    if [ "$HTTP_CODE" = "200" ]; then
        # Parse JSON response
        CONTENT_LENGTH=$(cat "$TEMP_FILE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['choices'][0]['message']['content']) if 'choices' in data else 0)" 2>/dev/null)
        TOKENS=$(cat "$TEMP_FILE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('usage', {}).get('total_tokens', 0))" 2>/dev/null)
        PREVIEW=$(cat "$TEMP_FILE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['choices'][0]['message']['content'][:150] if 'choices' in data else '')" 2>/dev/null)
        
        # Calculate quality score (content length / time)
        QUALITY_SCORE=$(perl -e "print int($CONTENT_LENGTH / $ELAPSED)")
        
        echo "✓ Success"
        echo "  Time: ${ELAPSED}s"
        echo "  Tokens: $TOKENS"
        echo "  Content Length: $CONTENT_LENGTH chars"
        echo "  Quality Score: $QUALITY_SCORE"
        echo "  Preview: $PREVIEW..."
        
        # Save to results
        echo "$MODEL|$ELAPSED|$TOKENS|$CONTENT_LENGTH|$QUALITY_SCORE" >> "$RESULTS_FILE"
    else
        ERROR=$(cat "$TEMP_FILE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('error', {}).get('message', 'Unknown'))" 2>/dev/null)
        echo "✗ Failed - HTTP $HTTP_CODE"
        echo "  Error: $ERROR"
    fi
    
    rm -f "$TEMP_FILE"
    echo ""
    sleep 2  # Rate limiting
done

echo "================================================================================"
echo "RESULTS SUMMARY"
echo "================================================================================"
echo ""
echo "Sorted by Quality Score (content length / response time):"
echo ""
printf "%-50s %10s %10s %15s %12s\n" "Model" "Time (s)" "Tokens" "Content (chars)" "Quality"
echo "--------------------------------------------------------------------------------"

# Sort by quality score (5th column) descending
sort -t'|' -k5 -rn "$RESULTS_FILE" | while IFS='|' read -r model time tokens content quality; do
    printf "%-50s %10s %10s %15s %12s\n" "$model" "$time" "$tokens" "$content" "$quality"
done

echo ""
echo "================================================================================"
echo "RECOMMENDATIONS"
echo "================================================================================"
echo ""

# Get top 3
TOP1=$(sort -t'|' -k5 -rn "$RESULTS_FILE" | head -1 | cut -d'|' -f1)
TOP2=$(sort -t'|' -k5 -rn "$RESULTS_FILE" | head -2 | tail -1 | cut -d'|' -f1)
TOP3=$(sort -t'|' -k5 -rn "$RESULTS_FILE" | head -3 | tail -1 | cut -d'|' -f1)

echo "Based on actual testing (Quality + Speed):"
echo ""
echo "PRIMARY MODEL (Trade/Market Analysis):"
echo "  $TOP1"
echo ""
echo "SECONDARY MODEL (Copilot Chat):"
echo "  $TOP2"
echo ""
echo "TERTIARY MODEL (Quick Insights):"
echo "  $TOP3"
echo ""
echo "Update backend/.env with these models!"
echo ""
