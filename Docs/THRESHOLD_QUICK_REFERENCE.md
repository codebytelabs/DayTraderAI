# Adaptive Thresholds Quick Reference
**Industry-Standard Day Trading Configuration**

## 🎯 Base Thresholds
```
Long:  50% (was 60%)
Short: 55% (was 65%)
Max:   70/75% (was 75/80%)
```

## 📊 Adjustment Ranges

### Regime (Primary Factor)
```
Extreme Chop (≤0.4):  +15%  (was +25%)
Very Choppy (0.4-0.5): +12%  (was +20%)
Mod Choppy (0.5-0.6):  +8%   (was +15%)
Slight Chop (0.6-0.7): +5%   (was +10%)
Transitional (0.7-0.8): +2%   (was +5%)
Trending (0.8-0.9):    0%    (same)
Strong Trend (0.9-1.0): -5%   (same)
Very Strong (>1.0):    -10%  (was -5%)
```

### Time of Day (Minor Factor)
```
9:00-10:00 (Open):      +2%  (was -3%)
10:00-11:00 (Morning):  -2%  (was -3%)
11:00-14:00 (Midday):   +3%  (was +5%)
14:00-15:00 (Afternoon): 0%  (same)
15:00-16:00 (Power):    -2%  (was 0%)
Outside Hours:          +8%  (was +10%)
```

### Sentiment (Balanced Factor)
```
Extreme Fear (<15):     L+5% S+8%  (was L+8% S+10%)
Strong Fear (15-25):    L+2% S+5%  (was L+3% S+5%)
Fear (25-40):           L+0% S+3%  (same)
Neutral (40-60):        L+0% S+0%  (same)
Greed (60-75):          L+3% S+0%  (same)
Strong Greed (75-85):   L+5% S+2%  (was L+5% S+3%)
Extreme Greed (>85):    L+8% S+5%  (was L+10% S+8%)
```

## 🛑 Pause Conditions
```
Extreme Choppy:         Mult ≤ 0.25  (was ≤ 0.35)
Extreme Sentiment:      <10/>90 + Mult ≤0.35  (was <15/>85 + ≤0.5)
Triple Threat:          REMOVED
```

## 💡 Quick Examples

### Current Market (Fear 24, Chop 0.5, Midday)
```
Before: 88/95% ❌
After:  67/75% ✅
```

### Strong Trend (Neutral 50, Trend 1.1, Morning)
```
Before: 52/57% ✅
After:  38/43% ✅✅ (More opportunities)
```

### Moderate Chop (Neutral 45, Chop 0.6, Midday)
```
Before: 80/85% ❌
After:  61/66% ✅
```

## ✅ Key Principles

1. **Base 50/55%** - Industry standard for day trading
2. **Max 70/75%** - Never exceed professional limits
3. **Regime Primary** - Market structure matters most
4. **Time Minor** - Volume filters handle this better
5. **Sentiment Balanced** - Extremes = opportunities
6. **Rare Pausing** - Trade most conditions

## 🎓 Industry Standards

- ✅ Confidence: 50-60% base, 70-75% max
- ✅ Regime: +10-15% for choppy
- ✅ Time: 2-5% adjustments
- ✅ Sentiment: 5-10% adjustments
- ✅ Pausing: < 5% of trading days
