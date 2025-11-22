import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, time
import pytz
from config import settings



if __name__ == "__main__":
    # Manual verification script
    print("🧪 Testing EOD Logic...")
    
    # 1. Setup
    settings.force_eod_exit = True
    settings.eod_exit_time = "15:58"
    
    # 2. Mock Time Check
    eod_hour, eod_minute = 15, 58
    
    # Simulate 3:59 PM
    current_hour, current_minute = 15, 59
    
    print(f"⚙️  Config: Force Exit={settings.force_eod_exit}, Time={settings.eod_exit_time}")
    print(f"🕒 Current Time (Simulated): {current_hour}:{current_minute}")
    
    should_trigger = (current_hour > eod_hour or (current_hour == eod_hour and current_minute >= eod_minute)) and current_hour < 16
    
    if should_trigger:
        print("✅ EOD Trigger Condition MET")
    else:
        print("❌ EOD Trigger Condition FAILED")
        
    # Simulate 3:57 PM
    current_hour, current_minute = 15, 57
    print(f"🕒 Current Time (Simulated): {current_hour}:{current_minute}")
    should_trigger = (current_hour > eod_hour or (current_hour == eod_hour and current_minute >= eod_minute)) and current_hour < 16
    
    if not should_trigger:
        print("✅ Pre-EOD Condition Correct (Not Triggered)")
    else:
        print("❌ Pre-EOD Condition FAILED (Triggered Early)")
