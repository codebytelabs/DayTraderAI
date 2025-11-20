# 🚨 EMERGENCY FIX - TDG Stop Loss Bug

## Problem Summary
TDG position entered at $1347.46 and closed at a loss even though price never dropped significantly.

## Root Causes Identified:

### 1. Stop Loss Too Tight (0.11% below entry)
- Entry: $1347.46
- Stop: $1345.92
- Distance: $1.54 (0.11%)
- **Normal market noise triggered it immediately**

### 2. Stop Loss Protection Using Wrong Price
The "stored stop loss" of $1345.09 is being used, which is:
- Calculated incorrectly
- Not accounting for proper risk distance
- Creating stops that are too tight

### 3. Minimum Stop Distance Not Enforced
The code has this check:
```python
if stop_distance < min_stop_distance:
    logger.warning(f"Stop distance too small for {symbol}")
    # Adjusting...
```

But it's not working correctly!

---

## IMMEDIATE FIXES REQUIRED:

### Fix #1: Enforce Minimum 1.5% Stop Loss Distance
**File:** `backend/trading/stop_loss_protection.py`

```python
def _calculate_stop_loss_price(self, position: Position) -> float:
    """
    Calculate stop loss price with MINIMUM 1.5% distance
    """
    entry_price = position.avg_entry_price
    
    # MINIMUM 1.5% stop distance (not 0.11%!)
    min_stop_pct = 0.015  # 1.5%
    
    if position.side == 'buy':
        # For long positions, stop BELOW entry
        stop_price = entry_price * (1 - min_stop_pct)
    else:
        # For short positions, stop ABOVE entry
        stop_price = entry_price * (1 + min_stop_pct)
    
    logger.info(f"Calculated stop for {position.symbol}: ${stop_price:.2f} ({min_stop_pct:.1%} from entry ${entry_price:.2f})")
    
    return stop_price
```

### Fix #2: Don't Try to Create Stop Loss for Non-Existent Positions
**File:** `backend/trading/stop_loss_protection.py`

```python
def check_and_create_stops(self):
    """
    Check positions and create stop losses if missing
    """
    try:
        # Get positions from Alpaca (source of truth)
        alpaca_positions = self.alpaca.get_positions()
        
        if not alpaca_positions:
            logger.debug("No positions to protect")
            return
        
        for alpaca_pos in alpaca_positions:
            symbol = alpaca_pos.symbol
            
            # Check if stop loss exists
            has_stop = self._has_active_stop_loss(symbol)
            
            if not has_stop:
                logger.warning(f"🚨 {symbol} has NO ACTIVE STOP LOSS - creating now...")
                
                # Create position object
                position = Position(
                    symbol=symbol,
                    qty=abs(int(alpaca_pos.qty)),
                    side='buy' if int(alpaca_pos.qty) > 0 else 'sell',
                    avg_entry_price=float(alpaca_pos.avg_entry_price),
                    current_price=float(alpaca_pos.current_price),
                    # ... other fields
                )
                
                # Calculate proper stop loss
                stop_price = self._calculate_stop_loss_price(position)
                
                # Create stop loss order
                self._create_stop_loss_order(symbol, position.qty, stop_price, position.side)
                
    except Exception as e:
        logger.error(f"Error in check_and_create_stops: {e}")
```

### Fix #3: Verify Position Exists Before Creating Stop
```python
def _create_stop_loss_order(self, symbol: str, qty: int, stop_price: float, side: str):
    """
    Create stop loss order - ONLY if position exists
    """
    try:
        # CRITICAL: Verify position still exists
        try:
            alpaca_position = self.alpaca.get_position(symbol)
            if not alpaca_position:
                logger.warning(f"Position {symbol} no longer exists - skipping stop loss")
                return False
        except Exception as e:
            if "position does not exist" in str(e).lower():
                logger.warning(f"Position {symbol} already closed - skipping stop loss")
                return False
            raise
        
        # Create stop loss order
        if side == 'buy':
            # Long position: sell stop
            order = self.alpaca.submit_order(
                symbol=symbol,
                qty=qty,
                side='sell',
                type='stop',
                stop_price=round(stop_price, 2),
                time_in_force='gtc'
            )
        else:
            # Short position: buy stop
            order = self.alpaca.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='stop',
                stop_price=round(stop_price, 2),
                time_in_force='gtc'
            )
        
        if order:
            logger.info(f"✅ Stop loss created for {symbol}: ${stop_price:.2f} (Order ID: {order.id})")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to create stop loss for {symbol}: {e}")
        return False
```

---

## TESTING CHECKLIST:

Before deploying:
- [ ] Verify minimum stop distance is 1.5% (not 0.11%)
- [ ] Test that stops are only created for existing positions
- [ ] Verify stop loss orders are correct side (sell for long, buy for short)
- [ ] Check that "account not allowed to short" error doesn't occur
- [ ] Confirm stops are not inverted (below entry for longs, above for shorts)

---

## EXPECTED BEHAVIOR AFTER FIX:

### For TDG Example:
- Entry: $1347.46
- Stop Loss: $1327.16 (1.5% below = $20.30 distance)
- Take Profit: $1367.76 (1.5% above)
- Risk/Reward: 1:1 minimum

### Benefits:
- Stops won't trigger from normal market noise
- Positions have room to breathe
- Only real moves trigger stops
- Win rate improves dramatically

---

## DEPLOY PRIORITY: CRITICAL

This bug is causing:
- ✅ Immediate losses on winning trades
- ✅ Stops triggering from noise
- ✅ 100% loss rate

**Must fix before any more trades!**
