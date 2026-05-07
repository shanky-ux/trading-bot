"""Input validation for trading bot CLI parameters."""

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET", "STOP_LIMIT"}


class ValidationError(ValueError):
    """Raised when user-supplied input fails validation."""


def validate_symbol(symbol: str) -> str:
    """Normalise and validate a trading symbol."""
    symbol = symbol.strip().upper()
    if not symbol.isalnum() or len(symbol) < 3:
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Expected alphanumeric, e.g. BTCUSDT."
        )
    return symbol


def validate_side(side: str) -> str:
    """Validate order side (BUY / SELL)."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(VALID_SIDES)}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type (MARKET / LIMIT / STOP_MARKET / STOP_LIMIT)."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(VALID_ORDER_TYPES)}."
        )
    return order_type


def validate_quantity(quantity: str | float) -> float:
    """Validate and convert quantity to a positive float."""
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Invalid quantity '{quantity}'. Must be a number.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be positive, got {qty}.")
    return qty


def validate_price(price: str | float | None, order_type: str) -> float | None:
    """Validate price; required for LIMIT and STOP_LIMIT orders."""
    if order_type in ("LIMIT", "STOP_LIMIT"):
        if price is None:
            raise ValidationError(
                f"Price is required for {order_type} orders."
            )
        try:
            p = float(price)
        except (TypeError, ValueError):
            raise ValidationError(f"Invalid price '{price}'. Must be a number.")
        if p <= 0:
            raise ValidationError(f"Price must be positive, got {p}.")
        return p
    return None  # price not used for MARKET / STOP_MARKET


def validate_stop_price(stop_price: str | float | None, order_type: str) -> float | None:
    """Validate stop price; required for STOP_MARKET and STOP_LIMIT orders."""
    if order_type in ("STOP_MARKET", "STOP_LIMIT"):
        if stop_price is None:
            raise ValidationError(
                f"Stop price is required for {order_type} orders."
            )
        try:
            sp = float(stop_price)
        except (TypeError, ValueError):
            raise ValidationError(f"Invalid stop price '{stop_price}'. Must be a number.")
        if sp <= 0:
            raise ValidationError(f"Stop price must be positive, got {sp}.")
        return sp
    return None
