"""Low-level Binance Futures Testnet REST client."""

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import requests

from .logging_config import setup_logger

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000

logger = setup_logger("trading_bot.client")


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """Thin wrapper around the Binance Futures USDT-M REST API."""

    def __init__(self, api_key: str, api_secret: str, base_url: str = TESTNET_BASE_URL):
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: dict) -> str:
        """Return HMAC-SHA256 signature for the given parameter dict."""
        query = urlencode(params)
        return hmac.new(self.api_secret, query.encode(), hashlib.sha256).hexdigest()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        signed: bool = False,
    ) -> Any:
        params = params or {}
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = RECV_WINDOW
            params["signature"] = self._sign(params)

        url = f"{self.base_url}{endpoint}"

        # Don't log the signature (derived from the API secret).
        log_params = dict(params)
        if "signature" in log_params:
            log_params["signature"] = "<redacted>"

        logger.debug("REQUEST %s %s params=%s", method.upper(), url, log_params)

        try:
            resp = self.session.request(method, url, params=params, timeout=10)
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network failure: %s", exc)
            raise ConnectionError(f"Could not reach Binance API: {exc}") from exc
        except requests.exceptions.Timeout:
            logger.error("Request timed out for %s %s", method, url)
            raise TimeoutError("Request to Binance API timed out.")

        logger.debug("RESPONSE %s %s", resp.status_code, resp.text[:500])

        try:
            data = resp.json()
        except ValueError:
            logger.error("Non-JSON response: status=%s body=%s", resp.status_code, resp.text[:500])
            raise BinanceAPIError(resp.status_code, resp.text)

        # Binance typically returns a JSON body with {code, msg} on errors.
        if isinstance(data, dict) and "code" in data and data["code"] not in (0, 200):
            raise BinanceAPIError(int(data["code"]), str(data.get("msg", "Unknown error")))

        if not resp.ok:
            if isinstance(data, dict) and "msg" in data:
                raise BinanceAPIError(resp.status_code, str(data.get("msg")))
            raise BinanceAPIError(resp.status_code, str(data))

        return data

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_exchange_info(self) -> dict:
        """Fetch exchange info (symbol rules, filters, etc.)."""
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_account(self) -> dict:
        """Fetch account information (balances, positions)."""
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        stop_price: float | None = None,
        time_in_force: str = "GTC",
    ) -> dict:
        """
        Place a futures order.

        Parameters
        ----------
        symbol      : e.g. "BTCUSDT"
        side        : "BUY" or "SELL"
        order_type  : "MARKET", "LIMIT", "STOP_MARKET", "STOP_LIMIT"
        quantity    : order quantity
        price       : limit price (required for LIMIT / STOP_LIMIT)
        stop_price  : trigger price (required for STOP_MARKET / STOP_LIMIT)
        time_in_force: "GTC" (default), "IOC", "FOK"
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type in ("LIMIT", "STOP_LIMIT"):
            params["price"] = price
            params["timeInForce"] = time_in_force

        if order_type in ("STOP_MARKET", "STOP_LIMIT"):
            params["stopPrice"] = stop_price

        logger.info(
            "Placing order: symbol=%s side=%s type=%s qty=%s price=%s stopPrice=%s",
            symbol,
            side,
            order_type,
            quantity,
            price,
            stop_price,
        )

        result = self._request("POST", "/fapi/v1/order", params=params, signed=True)
        logger.info("Order placed successfully: orderId=%s status=%s", result.get("orderId"), result.get("status"))
        return result
