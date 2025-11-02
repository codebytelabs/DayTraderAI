#!/bin/bash

# Test OpenRouter models with curl
API_KEY="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"
BASE_URL="https://openrouter.ai/api/v1/chat/completions"

# Test prompt
PROMPT='{"model":"MODEL_NAME","messages":[{"role":"system","content":"You are an expert day trading analyst. Provide concise, actionable analysis."},{"role":"user","content":"Analyze this trade:\n\nSymbol: AAPL\nAction: BUY\nPrice: $178.50\n\nTechnical Indicators:\n- EMA Short (9): $177.20\n- EMA Long (21): $175.80\n- ATR: $2.40\n- Volume Z-Score: 1.8\n\nThe short EMA just crossed above the long EMA with strong volume.\n\nProvide:\n1. Trade quality score (1-10)\n2. Key risks (2-3 points)\n3. Recommended action (GO/WAIT/PASS)\n\nBe concise and actionable."}],"temperature":0.7,"max_tokens":1000}'

# Models to test
MODELS=(
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
echo "OPENROUTER MODEL TESTING WITH CURL"
echo "================================================================================"
echo ""

for MODEL in "${MODELS[@]}"; do
    echo "Testing: $MODEL"
    echo "--------------------------------------------------------------------------------"
    
    # Replace MODEL_NAME in prompt
    TEST_PROMPT="${PROMPT//MODEL_NAME/$MODEL}"
    
    # Time the request
    START=$(date +%s.%N)
    
    # Make request
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$BASE_URL" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d "$TEST_PROMPT")
    
    END=$(date +%s.%N)
    ELAPSED=$(echo "$END - $START" | bc)
    
    # Extract HTTP code (last line)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    BODY=$(echo "$RESPONSE" | head -n -1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        # Extract content and tokens
        CONTENT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['choices'][0]['message']['content'][:200] if 'choices' in data else 'No content')" 2>/dev/null)
        TOKENS=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('usage', {}).get('total_tokens', 0))" 2>/dev/null)
        
        echo "✓ Success - ${ELAPSED}s - ${TOKENS} tokens"
        echo "  Response: $CONTENT..."
    else
        ERROR=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('error', {}).get('message', 'Unknown error'))" 2>/dev/null)
        echo "✗ Failed - HTTP $HTTP_CODE - $ERROR"
    fi
    
    echo ""
    sleep 2  # Rate limiting
done

echo "================================================================================"
echo "TESTING COMPLETE"
echo "================================================================================"
