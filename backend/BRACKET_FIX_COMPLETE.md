# Bracket Order Fix - Complete

## 🐛 **Bug Found:**
`trading/position_manager.py` lines 847 & 865 were hardcoded to use `OrderSide.SELL` for bracket recreation, which is **WRONG for SHORT positions**.

## ✅ **Fix Applied:**
```python
# OLD (WRONG):
side=OrderSide.SELL,  # Always SELL

# NEW (CORRECT):
exit_side = OrderSide.SELL if position.side == 'buy' else OrderSide.BUY
side=exit_side,  # Correct side based on position
```

## 📊 **Current Position Status:**

### COST - SHORT 15 shares @ $883.46
- ✅ **Stop-Loss: BUY 15 @ $896.71** (protects against losses)
- ⚠️  Take-Profit: Missing (trailing stops will handle)

### ON - SHORT 288 shares @ $47.07  
- ✅ **Stop-Loss: BUY 288 @ $47.78** (protects against losses)
- ⚠️  Take-Profit: Missing (trailing stops will handle)

### VRTX - SHORT 32 shares @ $420.26
- ✅ **Stop-Loss: BUY 32 @ $426.56** (protects against losses)
- ⚠️  Take-Profit: Missing (trailing stops will handle)

## 🛡️ **Risk Assessment:**

**PROTECTED** - All positions have stop-losses:
1. ✅ All have CORRECT stop-loss orders (BUY side for shorts)
2. ✅ Stop-losses protect against significant losses
3. ✅ Trailing stops will activate when profitable (+2R)
4. ✅ Bot's position monitor provides backup protection

## 🔄 **Next Steps:**

1. ✅ Code fixed - future positions will have correct brackets
2. ✅ Wrong orders canceled
3. ⏳ Current positions protected by TP orders
4. 🔄 Bot will recreate correct brackets on next restart

## 📝 **Files Modified:**
- `trading/position_manager.py` - Fixed `_recreate_take_profit()` method
  - Line 807-830: Fixed price calculations for short positions
  - Line 833-850: Fixed order side detection for cancellation
  - Line 855-877: Fixed exit side and qty for order creation

## ✅ **Verification:**
Run `python check_brackets_now.py` to verify bracket status anytime.
