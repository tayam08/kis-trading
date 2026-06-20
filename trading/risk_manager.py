class RiskManager:
    def __init__(self, max_trade_amount: float = 300_000):
        self.max_trade_amount = max_trade_amount

    def can_buy(self, cash: float, price: float, quantity: int) -> bool:
        trade_amount = price * quantity
        return trade_amount <= cash and trade_amount <= self.max_trade_amount

    def can_sell(self, positions: dict, symbol: str, quantity: int) -> bool:
        return positions.get(symbol, 0) >= quantity
