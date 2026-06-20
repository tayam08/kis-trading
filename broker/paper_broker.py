from datetime import datetime
from broker.base import Broker


class PaperBroker(Broker):
    def __init__(self, initial_cash: float = 1_000_000):
        self.cash = initial_cash
        self.positions = {}
        self.current_prices = {}
        self.trade_history = []

    def update_price(self, symbol: str, price: float):
        self.current_prices[symbol] = price

    def get_current_price(self, symbol: str) -> float:
        if symbol not in self.current_prices:
            raise ValueError(f"No current price available for symbol: {symbol}")
        return self.current_prices[symbol]

    def get_balance(self) -> dict:
        position_value = sum(
            qty * self.current_prices.get(symbol, 0)
            for symbol, qty in self.positions.items()
        )
        return {
            "cash": self.cash,
            "positions": self.positions.copy(),
            "position_value": position_value,
            "total_equity": self.cash + position_value,
        }

    def buy(self, symbol: str, quantity: int, price: float | None = None) -> dict:
        execution_price = price or self.get_current_price(symbol)
        total_cost = execution_price * quantity

        if total_cost > self.cash:
            return self._make_order_result(
                symbol, "BUY", quantity, execution_price, "REJECTED", "Insufficient cash"
            )

        self.cash -= total_cost
        self.positions[symbol] = self.positions.get(symbol, 0) + quantity

        return self._make_order_result(
            symbol, "BUY", quantity, execution_price, "FILLED", "Paper order filled"
        )

    def sell(self, symbol: str, quantity: int, price: float | None = None) -> dict:
        execution_price = price or self.get_current_price(symbol)
        current_qty = self.positions.get(symbol, 0)

        if quantity > current_qty:
            return self._make_order_result(
                symbol, "SELL", quantity, execution_price, "REJECTED", "Insufficient position"
            )

        self.cash += execution_price * quantity
        self.positions[symbol] = current_qty - quantity

        if self.positions[symbol] == 0:
            del self.positions[symbol]

        return self._make_order_result(
            symbol, "SELL", quantity, execution_price, "FILLED", "Paper order filled"
        )

    def _make_order_result(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        status: str,
        message: str,
    ) -> dict:
        result = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "status": status,
            "message": message,
            "cash_after": self.cash,
            "positions_after": self.positions.copy(),
            "mode": "PAPER",
        }

        self.trade_history.append(result)
        return result
