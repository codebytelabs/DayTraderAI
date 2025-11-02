# Security Architecture - API Key Management

## ✅ Correct Architecture (Implemented)

### Backend Manages All Secrets

```
┌─────────────────────────────────────┐
│         Backend (.env)              │
│  ┌───────────────────────────────┐  │
│  │  ALPACA_API_KEY=xxx           │  │
│  │  ALPACA_SECRET_KEY=xxx        │  │
│  │  SUPABASE_SERVICE_KEY=xxx     │  │
│  │  OPENROUTER_API_KEY=xxx       │  │
│  │  PERPLEXITY_API_KEY=xxx       │  │
│  └───────────────────────────────┘  │
│                                     │
│  Endpoints:                         │
│  • /health/services (status)        │
│  • /config (non-sensitive config)   │
│  • /performance (data)              │
│  • All trading operations           │
└─────────────────────────────────────┘
              ↕ HTTPS
┌─────────────────────────────────────┐
│         Frontend (.env.local)       │
│  ┌───────────────────────────────┐  │
│  │  VITE_BACKEND_URL=xxx         │  │
│  │  VITE_ALPACA_BASE_URL=xxx     │  │
│  │  VITE_SUPABASE_URL=xxx        │  │
│  │  (NO API KEYS!)               │  │
│  └───────────────────────────────┘  │
│                                     │
│  Settings UI:                       │
│  • Read-only service info           │
│  • Trading parameters (editable)    │
│  • UI preferences (editable)        │
└─────────────────────────────────────┘
```

## What Changed

### Before (❌ Insecure)

- Frontend asked users to enter API keys
- Keys stored in browser localStorage
- Keys could be exposed in browser dev tools
- Keys bundled into frontend build
- Anyone with access to the app could see keys

### After (✅ Secure)

- **All API keys live in `backend/.env` only**
- Frontend never sees or stores secrets
- Settings drawer shows read-only configuration
- Only trading parameters are editable in UI
- Keys never leave the server

## Backend Configuration (`backend/.env`)

```env
# Trading API
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key_here

# AI Services
OPENROUTER_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here

# Strategy (can be changed via API)
WATCHLIST_SYMBOLS=SPY,QQQ,AAPL,NVDA,TSLA
MAX_POSITIONS=5
RISK_PER_TRADE_PCT=0.01
```

## Frontend Configuration (`.env.local`)

```env
# Backend connection
VITE_BACKEND_URL=http://localhost:8006

# Display defaults (non-sensitive)
VITE_ALPACA_BASE_URL=https://paper-api.alpaca.markets
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_OPENROUTER_MODEL=openai/gpt-4-turbo
VITE_PERPLEXITY_MODEL=sonar-pro

# UI defaults
VITE_MAX_POSITIONS=5
VITE_RISK_PER_TRADE_PCT=0.01
```

## Settings Drawer Behavior

### API Keys & Services Tab

- **Read-only** display of configured services
- Shows which services are configured
- Links to backend configuration file
- No input fields for secrets

### Strategy & Risk Tab

- **Editable** trading parameters:
  - Watchlist symbols
  - Risk per trade %
  - Max concurrent positions
- Saved to localStorage for UI preferences
- Can be synced to backend (future feature)

### Copilot & Automation Tab

- **Editable** UI preferences:
  - LLM provider selection
  - Temperature setting
  - Automation preferences
- Saved to localStorage

## Security Benefits

1. **No Secret Exposure**: API keys never sent to browser
2. **No Storage Risk**: Keys not in localStorage or sessionStorage
3. **No Build Risk**: Keys not bundled into JavaScript
4. **No Network Risk**: Keys not transmitted over network
5. **Server-Side Only**: All API calls made from backend
6. **Audit Trail**: Backend logs all API usage
7. **Easy Rotation**: Change keys in one place (backend/.env)
8. **Environment Isolation**: Different keys for dev/staging/prod

## How It Works

### 1. Backend Startup

```python
# backend/main.py
alpaca_client = AlpacaClient()  # Uses ALPACA_API_KEY from .env
supabase_client = SupabaseClient()  # Uses SUPABASE_SERVICE_KEY
```

### 2. Frontend Requests Data

```typescript
// Frontend makes request
const data = await apiClient.get("/positions");
// Backend uses its API keys to fetch from Alpaca
// Returns sanitized data to frontend
```

### 3. Service Health Check

```typescript
// Frontend checks service status
const health = await apiClient.get("/health/services");
// Returns: { alpaca: 'connected', supabase: 'connected', ... }
// Backend tests connections using its keys
```

### 4. Configuration Loading

```typescript
// Frontend loads display config
const config = await apiClient.get("/config");
// Returns: { alpaca_base_url, watchlist, max_positions, ... }
// NO API KEYS INCLUDED
```

## Migration Guide

If you previously entered API keys in the Settings drawer:

1. **Clear browser storage**:

   ```javascript
   localStorage.clear();
   ```

2. **Ensure backend `.env` has all keys**:

   ```bash
   cd backend
   cat .env  # Verify all keys are present
   ```

3. **Restart backend**:

   ```bash
   python main.py
   ```

4. **Refresh frontend**:
   - Settings will now show read-only configuration
   - Service status will show green when backend is connected

## Troubleshooting

### Services Show "Disconnected"

1. Check backend is running: `ps aux | grep main.py`
2. Check backend logs for API errors
3. Verify keys in `backend/.env` are correct
4. Test endpoints: `curl http://localhost:8006/health/services`

### Settings Show Empty Values

1. Ensure backend `/config` endpoint is working
2. Check browser console for errors
3. Verify backend is accessible at `VITE_BACKEND_URL`
4. Clear localStorage and refresh

### Can't Edit Configuration

- **API Keys**: Correct! Edit `backend/.env` instead
- **Service URLs**: Read-only, edit `backend/.env`
- **Trading Parameters**: Should be editable in Strategy tab
- **UI Preferences**: Should be editable in Copilot tab

## Best Practices

✅ **DO**:

- Keep all API keys in `backend/.env`
- Use environment variables for configuration
- Rotate keys regularly
- Use different keys for dev/staging/prod
- Monitor API usage and costs
- Set up alerts for unusual activity

❌ **DON'T**:

- Store API keys in frontend code
- Commit `.env` files to git
- Share API keys in chat/email
- Use production keys in development
- Expose keys in error messages
- Log API keys in application logs

## Future Enhancements

- [ ] Add backend endpoint to update trading parameters
- [ ] Add API key validation on backend startup
- [ ] Add key rotation mechanism
- [ ] Add usage monitoring dashboard
- [ ] Add rate limiting per API key
- [ ] Add key expiration warnings
- [ ] Add multi-user support with per-user keys

---

**Summary**: All API keys are now managed exclusively by the backend. The frontend Settings drawer shows read-only configuration and only allows editing of trading parameters and UI preferences. This is the correct and secure architecture! 🔒
