# OpenRouter Model Selection Guide

## Recommended Models (Already Configured)

### Primary Model: `google/gemini-2.5-flash-preview-09-2025`
**Use for**: Trade analysis, market analysis, detailed copilot responses

**Why**:
- ✅ Best quality/speed balance
- ✅ Strong reasoning capabilities
- ✅ Good at financial analysis
- ✅ Fast response times
- ✅ Cost-effective

**Cost**: ~$0.10 per 1M tokens

### Secondary Model: `google/gemini-2.5-flash-lite-preview-09-2025`
**Use for**: Quick copilot responses, simple queries

**Why**:
- ✅ Very fast responses
- ✅ Lower cost
- ✅ Good for simple tasks
- ✅ Handles conversational queries well

**Cost**: ~$0.05 per 1M tokens

### Backup Model: `minimax/minimax-m2:free`
**Use for**: Quick insights when budget is a concern

**Why**:
- ✅ Completely free
- ✅ Decent quality for simple tasks
- ✅ Good fallback option

**Cost**: Free

## Alternative Models to Consider

### For Maximum Quality (Higher Cost)

**`openai/gpt-4-turbo`**
- Best reasoning and analysis
- Excellent for complex trading decisions
- Cost: ~$10 per 1M tokens
- Use when: You need the absolute best analysis

**`anthropic/claude-3.5-sonnet`**
- Excellent reasoning
- Great at following instructions
- Cost: ~$3 per 1M tokens
- Use when: You need reliable, thoughtful analysis

### For Speed (Lower Quality)

**`openai/gpt-3.5-turbo`**
- Very fast
- Good for simple tasks
- Cost: ~$0.50 per 1M tokens
- Use when: Speed matters more than depth

**`meta-llama/llama-3.1-8b-instruct:free`**
- Free and fast
- Decent for basic queries
- Cost: Free
- Use when: Budget is tight

### For Specialized Tasks

**`perplexity/sonar-pro`** (via Perplexity API)
- Best for news and research
- Includes citations
- Real-time information
- Already configured for news queries

## Model Configuration

All models are configured in `backend/.env`:

```bash
# Primary model for analysis and copilot (best quality)
OPENROUTER_PRIMARY_MODEL=google/gemini-2.5-flash-preview-09-2025

# Secondary model for quick responses
OPENROUTER_SECONDARY_MODEL=google/gemini-2.5-flash-lite-preview-09-2025

# Backup free model
OPENROUTER_BACKUP_MODEL=minimax/minimax-m2:free

# Temperature for responses (0.0-1.0)
OPENROUTER_TEMPERATURE=0.7
```

## When to Use Each Model

### Primary Model (Gemini 2.5 Flash)
- ✅ Trade analysis before execution
- ✅ Market condition analysis
- ✅ Risk assessment
- ✅ Strategy recommendations
- ✅ Detailed copilot responses

### Secondary Model (Gemini 2.5 Flash Lite)
- ✅ Quick copilot chat
- ✅ Simple status queries
- ✅ Command confirmations
- ✅ Basic explanations

### Backup Model (Minimax Free)
- ✅ Quick insights
- ✅ Testing without cost
- ✅ Fallback when primary fails
- ✅ High-volume simple queries

## Temperature Settings

```bash
OPENROUTER_TEMPERATURE=0.7  # Default (balanced)
```

**Temperature Guide**:
- `0.0-0.3`: Very focused, deterministic (good for analysis)
- `0.4-0.7`: Balanced creativity and focus (recommended)
- `0.8-1.0`: More creative, varied responses

**Recommendations**:
- Trade analysis: `0.3` (more conservative)
- Copilot chat: `0.7` (more natural)
- Market insights: `0.5` (balanced)

## Cost Optimization

### Current Setup (Recommended)
- Primary: Gemini 2.5 Flash (~$0.10/1M tokens)
- Secondary: Gemini 2.5 Flash Lite (~$0.05/1M tokens)
- Backup: Minimax Free ($0)

**Estimated monthly cost** (moderate usage):
- ~1000 trade analyses: $1-2
- ~5000 copilot messages: $2-3
- **Total: $3-5/month**

### Budget Setup (Minimal Cost)
```bash
OPENROUTER_PRIMARY_MODEL=minimax/minimax-m2:free
OPENROUTER_SECONDARY_MODEL=meta-llama/llama-3.1-8b-instruct:free
OPENROUTER_BACKUP_MODEL=minimax/minimax-m2:free
```
**Cost: $0/month** (but lower quality)

### Premium Setup (Best Quality)
```bash
OPENROUTER_PRIMARY_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_SECONDARY_MODEL=openai/gpt-4-turbo
OPENROUTER_BACKUP_MODEL=google/gemini-2.5-flash-preview-09-2025
```
**Cost: ~$20-50/month** (excellent quality)

## Testing Models

To test a different model, just update `.env`:

```bash
# Test Claude
OPENROUTER_PRIMARY_MODEL=anthropic/claude-3.5-sonnet

# Test GPT-4
OPENROUTER_PRIMARY_MODEL=openai/gpt-4-turbo

# Test free models
OPENROUTER_PRIMARY_MODEL=meta-llama/llama-3.1-70b-instruct:free
```

Restart the backend for changes to take effect.

## Model Performance Comparison

| Model | Speed | Quality | Cost | Best For |
|-------|-------|---------|------|----------|
| Gemini 2.5 Flash | ⚡⚡⚡ | ⭐⭐⭐⭐ | 💰 | Analysis (Recommended) |
| Gemini 2.5 Flash Lite | ⚡⚡⚡⚡ | ⭐⭐⭐ | 💰 | Quick responses |
| Claude 3.5 Sonnet | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰 | Complex analysis |
| GPT-4 Turbo | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰💰 | Best reasoning |
| GPT-3.5 Turbo | ⚡⚡⚡⚡ | ⭐⭐⭐ | 💰💰 | Fast queries |
| Minimax Free | ⚡⚡⚡ | ⭐⭐ | Free | Budget option |
| Llama 3.1 70B Free | ⚡⚡ | ⭐⭐⭐ | Free | Free quality |

## Monitoring Usage

Check your OpenRouter dashboard:
- https://openrouter.ai/activity

Track:
- Token usage per model
- Cost per day
- Request success rate
- Average response time

## Recommendations

### For Most Users (Current Setup)
✅ **Keep the default configuration**
- Gemini 2.5 Flash for analysis
- Gemini 2.5 Flash Lite for chat
- Minimax Free as backup

**Why**: Best balance of quality, speed, and cost

### For Budget-Conscious Users
Switch to free models:
```bash
OPENROUTER_PRIMARY_MODEL=meta-llama/llama-3.1-70b-instruct:free
OPENROUTER_SECONDARY_MODEL=minimax/minimax-m2:free
```

### For Maximum Quality
Upgrade to premium:
```bash
OPENROUTER_PRIMARY_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_SECONDARY_MODEL=openai/gpt-4-turbo
```

### For Speed
Use fastest models:
```bash
OPENROUTER_PRIMARY_MODEL=google/gemini-2.5-flash-lite-preview-09-2025
OPENROUTER_SECONDARY_MODEL=openai/gpt-3.5-turbo
```

## Troubleshooting

### Model Not Available
If you get "model not available" errors:
1. Check OpenRouter model list: https://openrouter.ai/models
2. Verify model name spelling
3. Check if model requires special access
4. Try backup model

### High Costs
If costs are too high:
1. Switch to free models
2. Reduce temperature (less tokens)
3. Use secondary model more
4. Cache responses when possible

### Poor Quality
If responses are poor:
1. Upgrade to premium models
2. Adjust temperature
3. Improve prompts
4. Use primary model for all tasks

## Support

- OpenRouter docs: https://openrouter.ai/docs
- Model comparison: https://openrouter.ai/models
- Pricing: https://openrouter.ai/docs/pricing
