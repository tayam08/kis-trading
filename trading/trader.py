class Trader:
    def __init__(self, broker, strategy, risk_manager, logger):
        self.broker = broker
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.logger = logger

    def run_step(self, symbol: str, price_history, quantity: int = 1):
        current_price = float(price_history.iloc[-1])
        self.broker.update_price(symbol, current_price)

        signal = self.strategy.generate_signal(price_history)
        balance = self.broker.get_balance()

        order_result = None

        if signal == "BUY":
            if self.risk_manager.can_buy(balance["cash"], current_price, quantity):
                order_result = self.broker.buy(symbol, quantity)
        elif signal == "SELL":
            if self.risk_manager.can_sell(balance["positions"], symbol, quantity):
                order_result = self.broker.sell(symbol, quantity)

        if order_result:
            self.logger.log_order(order_result)

        return {
            "symbol": symbol,
            "price": current_price,
            "signal": signal,
            "balance": self.broker.get_balance(),
            "order": order_result,
        }
