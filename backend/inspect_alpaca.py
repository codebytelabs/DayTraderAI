import inspect
from alpaca.trading.client import TradingClient

print("Inspecting TradingClient.replace_order_by_id signature:")
try:
    sig = inspect.signature(TradingClient.replace_order_by_id)
    print(sig)
except Exception as e:
    print(f"Error: {e}")
