import pandas as pd

from strategy.base import Strategy


class MovingAverageStrategy(Strategy):
    def __init__(self, short_window: int = 3, long_window: int = 5):
        if short_window >= long_window:
            raise ValueError("short_window must be smaller than long_window.")

        self.short_window = short_window
        self.long_window = long_window

    def generate_signal(self, price_history: pd.Series) -> str:
        if len(price_history) < self.long_window:
            return "HOLD"

        short_ma = price_history.tail(self.short_window).mean()
        long_ma = price_history.tail(self.long_window).mean()

        if short_ma > long_ma:
            return "BUY"
        elif short_ma < long_ma:
            return "SELL"
        return "HOLD"
