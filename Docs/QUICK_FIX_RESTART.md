# 🔧 Quick Fix - How to Restart Backend

**Issue:** Backend can't find `.env` file when run from project root.

**Solution:** Run from backend directory.

---

## ✅ Correct Way to Start Backend

### Option 1: Change to Backend Directory First
```bash
cd backend
python main.py
```

### Option 2: Use the Restart Script
```bash
./restart_backend.sh
```

### Option 3: Check if restart_backend.sh exists
```bash
ls -la restart_backend.sh
```

If it doesn't exist, create it:
```bash
cat > restart_backend.sh << 'EOF'
#!/bin/bash
cd backend
python main.py
EOF

chmod +x restart_backend.sh
```

---

## 🎯 What Was Fixed

Added Twelve Data API keys to `config.py`:
```python
# Twelve Data Configuration (Sprint 7 - Daily Cache)
twelvedata_api_key: str = ""
twelvedata_secondary_api_key: str = ""
```

Also added `extra = "ignore"` to Config class to ignore extra fields in `.env`.

---

## 📊 What to Look For After Starting

### Immediate (In Logs)
```
✅ "Daily cache initialized"
✅ "AI Scanner: Daily cache available"  
✅ "Risk Manager: Daily cache available"
```

### At 9:30 AM ET Tomorrow
```
🔄 "Refreshing daily cache..."
📊 "Calculated 200-EMA for [X] symbols"
✅ "Daily cache refresh complete"
```

---

## 🚀 Start Now

```bash
cd backend
python main.py
```

That's it! All enhancements are active and ready to go.
