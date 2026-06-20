from abc import ABC, abstractmethod


class Broker(ABC):
    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        pass

    @abstractmethod
    def get_balance(self) -> dict:
        pass

    @abstractmethod
    def buy(self, symbol: str, quantity: int, price: float | None = None) -> dict:
        pass

    @abstractmethod
    def sell(self, symbol: str, quantity: int, price: float | None = None) -> dict:
        pass
