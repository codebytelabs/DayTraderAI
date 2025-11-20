#!/usr/bin/env python3
"""Debug script to see actual order structure"""

from core.alpaca_client import AlpacaClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

alpaca = AlpacaClient()

# Get all orders
orders = alpaca.get_orders(status='all')

# Focus on KO
ko_orders = [o for o in orders if o.symbol == 'KO']

logger.info(f"Found {len(ko_orders)} orders for KO:")
for order in ko_orders:
    logger.info(f"\n  Order ID: {order.id}")
    logger.info(f"  Type: {order.type.value}")
    logger.info(f"  Side: {order.side.value}")
    logger.info(f"  Status: {order.status.value}")
    logger.info(f"  Qty: {order.qty}")
    if hasattr(order, 'limit_price') and order.limit_price:
        logger.info(f"  Limit Price: ${order.limit_price}")
    if hasattr(order, 'stop_price') and order.stop_price:
        logger.info(f"  Stop Price: ${order.stop_price}")
