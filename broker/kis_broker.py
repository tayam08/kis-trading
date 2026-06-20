import os
from broker.base import Broker


class KISBroker(Broker):
    """
    Skeleton broker for future Korea Investment & Securities Open API integration.

    This class is intentionally not connected to live trading in the current
    submission because official KIS mock trading access is not available yet.
    """

    def __init__(self):
        self.app_key = os.getenv("KIS_APP_KEY")
        self.app_secret = os.getenv("KIS_APP_SECRET")
        self.account_no = os.getenv("KIS_ACCOUNT_NO")
        self.base_url = os.getenv("KIS_BASE_URL")

    def authenticate(self):
        raise NotImplementedError("KIS authentication will be implemented after API access is available.")

    def get_current_price(self, symbol: str) -> float:
        raise NotImplementedError("KIS market data API is not connected yet.")

    def get_balance(self) -> dict:
        raise NotImplementedError("KIS balance API is not connected yet.")

    def buy(self, symbol: str, quantity: int, price: float | None = None) -> dict:
        raise NotImplementedError("KIS order API is not connected yet.")

    def sell(self, symbol: str, quantity: int, price: float | None = None) -> dict:
        raise NotImplementedError("KIS order API is not connected yet.")
