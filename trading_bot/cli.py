#!/usr/bin/env python3
"""
Trading Bot CLI — Binance Futures Testnet (USDT-M)

Usage examples
--------------
# Market BUY
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit SELL
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70000

# Stop-Market BUY
python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 60000

# Stop-Limit BUY
python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.001 --price 60500 --stop-price 60000
"""

import argparse
import os
import sys

from bot.client import BinanceClient, TESTNET_BASE_URL
from bot.logging_config import setup_logger
from bot.orders import format_order_response, place_order

logger = setup_logger("trading_bot.cli")

SEPARATOR = "─" * 60


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M)",
    )

    # API credentials from environment variables
    parser.add_argument(
        "--api-key",
        default=os.getenv("BINANCE_TESTNET_API_KEY"),
        help="Binance Testnet API key",
    )

    parser.add_argument(
        "--api-secret",
        default=os.getenv("BINANCE_TESTNET_API_SECRET"),
        help="Binance Testnet API secret",
    )

    # Order parameters
    parser.add_argument(
        "--symbol",
        required=True,
        help="Trading symbol, e.g. BTCUSDT",
    )

    parser.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        type=str.upper,
        help="Order side",
    )

    parser.add_argument(
        "--type",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET", "STOP_LIMIT"],
        type=str.upper,
        help="Order type",
    )

    parser.add_argument(
        "--quantity",
        required=True,
        type=float,
        help="Order quantity",
    )

    parser.add_argument(
        "--price",
        type=float,
        default=None,
        help="Limit price",
    )

    parser.add_argument(
        "--stop-price",
        type=float,
        default=None,
        dest="stop_price",
        help="Stop trigger price",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Validate API credentials
    if not args.api_key or not args.api_secret:
        parser.error(
            "API credentials are required.\n"
            "Set BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_API_SECRET"
        )

    logger.info("Starting trading bot CLI")

    client = BinanceClient(
        api_key=args.api_key,
        api_secret=args.api_secret,
        base_url=TESTNET_BASE_URL,
    )

    print(SEPARATOR)
    print("ORDER REQUEST")
    print(SEPARATOR)

    result = place_order(
        client=client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        quantity=args.quantity,
        price=args.price,
        stop_price=args.stop_price,
    )

    if result["summary"]:
        print(result["summary"])

    print(SEPARATOR)

    if result["success"]:
        print("ORDER PLACED SUCCESSFULLY")
        print(SEPARATOR)
        print("ORDER RESPONSE")
        print(SEPARATOR)
        print(format_order_response(result["order"]))
        print(SEPARATOR)
        logger.info("Order completed successfully.")

    else:
        print(f"ORDER FAILED: {result['error']}")
        print(SEPARATOR)
        logger.error("Order failed: %s", result["error"])
        sys.exit(1)


if __name__ == "__main__":
    main()