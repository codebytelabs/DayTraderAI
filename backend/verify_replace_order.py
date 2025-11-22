import sys
import os
import time
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

def verify_replace_order():
    logger.info("🚀 Starting replace_order verification...")
    
    client = AlpacaClient()
    symbol = "SNAP"
    
    # 1. Get current price to place order far away
    quote = client.get_latest_quote(symbol)
    if not quote:
        logger.error("Failed to get quote")
        return
    
    current_price = quote['ask']
    limit_price = round(current_price * 0.8, 2)  # 20% below market
    
    logger.info(f"Current {symbol} price: ${current_price}")
    logger.info(f"Placing test limit buy at ${limit_price}")
    
    # 2. Submit test order
    try:
        req = LimitOrderRequest(
            symbol=symbol,
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price
        )
        order = client.submit_order_request(req)
        logger.info(f"✅ Order submitted: {order.id}")
        
        time.sleep(2)
        
        # 3. Replace order
        new_price = round(limit_price * 1.01, 2)  # Move up 1%
        logger.info(f"Attempting to replace order to ${new_price}...")
        
        replaced_order = client.replace_order(
            order_id=order.id,
            limit_price=new_price
        )
        
        if replaced_order:
            logger.info(f"✅ Order replaced successfully! New ID: {replaced_order.id}")
            logger.info(f"New Limit Price: ${replaced_order.limit_price}")
            
            if float(replaced_order.limit_price) == new_price:
                logger.info("✅ Price verification PASSED")
            else:
                logger.error(f"❌ Price verification FAILED: Expected {new_price}, got {replaced_order.limit_price}")
                
            # 4. Cleanup
            client.cancel_order(replaced_order.id)
            logger.info("✅ Cleanup: Order cancelled")
            
        else:
            logger.error("❌ Failed to replace order")
            client.cancel_order(order.id)
            
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    verify_replace_order()
