"""Order placement logic — sits between the CLI and the Binance client."""

from .client import BinanceClient, BinanceAPIError
from .logging_config import setup_logger
from .validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = setup_logger("trading_bot.orders")


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: str | float | None = None,
    stop_price: str | float | None = None,
) -> dict:
    """
    Validate inputs, place an order, and return a structured result dict.

    Returns a dict with keys:
      success    : bool
      order      : dict | None  (raw Binance response on success)
      summary    : str          (human-readable request summary)
      error      : str | None   (error message on failure)
    """
    # ---- Validate -------------------------------------------------------
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        order_type = validate_order_type(order_type)
        quantity = validate_quantity(quantity)
        price = validate_price(price, order_type)
        stop_price = validate_stop_price(stop_price, order_type)
    except ValidationError as exc:
        logger.warning("Validation failed: %s", exc)
        return {"success": False, "order": None, "summary": "", "error": str(exc)}

    # ---- Build human-readable request summary ---------------------------
    summary_parts = [
        f"  Symbol    : {symbol}",
        f"  Side      : {side}",
        f"  Type      : {order_type}",
        f"  Quantity  : {quantity}",
    ]
    if price is not None:
        summary_parts.append(f"  Price     : {price}")
    if stop_price is not None:
        summary_parts.append(f"  Stop Price: {stop_price}")
    summary = "\n".join(summary_parts)

    # ---- Place order -----------------------------------------------------
    try:
        order = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except (BinanceAPIError, ConnectionError, TimeoutError) as exc:
        logger.error("Order placement failed: %s", exc)
        return {"success": False, "order": None, "summary": summary, "error": str(exc)}
    except Exception as exc:
        logger.exception("Unexpected error during order placement")
        return {
            "success": False,
            "order": None,
            "summary": summary,
            "error": f"Unexpected error: {exc}",
        }

    return {"success": True, "order": order, "summary": summary, "error": None}


def format_order_response(order: dict) -> str:
    """Format a Binance order response for CLI display."""
    lines = [
        f"  Order ID      : {order.get('orderId', 'N/A')}",
        f"  Client Order  : {order.get('clientOrderId', 'N/A')}",
        f"  Symbol        : {order.get('symbol', 'N/A')}",
        f"  Status        : {order.get('status', 'N/A')}",
        f"  Side          : {order.get('side', 'N/A')}",
        f"  Type          : {order.get('type', 'N/A')}",
        f"  Orig Qty      : {order.get('origQty', 'N/A')}",
        f"  Executed Qty  : {order.get('executedQty', 'N/A')}",
        f"  Avg Price     : {order.get('avgPrice', 'N/A')}",
        f"  Price         : {order.get('price', 'N/A')}",
        f"  Time in Force : {order.get('timeInForce', 'N/A')}",
        f"  Update Time   : {order.get('updateTime', 'N/A')}",
    ]
    return "\n".join(lines)
