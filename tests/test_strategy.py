import pandas as pd

from strategy.moving_average import MovingAverageStrategy


def test_moving_average_buy_signal():
    strategy = MovingAverageStrategy(short_window=2, long_window=3)
    prices = pd.Series([100, 101, 105])

    signal = strategy.generate_signal(prices)

    assert signal == "BUY"


def test_moving_average_sell_signal():
    strategy = MovingAverageStrategy(short_window=2, long_window=3)
    prices = pd.Series([105, 101, 100])

    signal = strategy.generate_signal(prices)

    assert signal == "SELL"
