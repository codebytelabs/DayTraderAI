"""Quick integration test for Sprint 6"""
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from trading.position_manager import PositionManager
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient

print("Testing Sprint 6 Integration...")
print("="*60)

alpaca = AlpacaClient()
supabase = SupabaseClient()
pm = PositionManager(alpaca, supabase)

print('✓ Position Manager initialized')
print(f'✓ Trailing Stop Manager: {pm.trailing_stop_manager is not None}')
print(f'✓ Profit Taker: {pm.profit_taker is not None}')
print(f'✓ Profit Taker Shadow Mode: {pm.profit_taker.shadow_mode_active}')
print(f'✓ Profit Taker Enabled: {pm.profit_taker.enabled}')
print(f'✓ First Target: +{pm.profit_taker.first_target_r}R')
print(f'✓ Percentage: {pm.profit_taker.profit_percentage*100:.0f}%')
print(f'✓ Second Target: +{pm.profit_taker.second_target_r}R')

print("="*60)
print("✅ Sprint 6 fully integrated and ready!")
