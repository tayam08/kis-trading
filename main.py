import pandas as pd

from broker.paper_broker import PaperBroker
from strategy.moving_average import MovingAverageStrategy
from trading.risk_manager import RiskManager
from trading.logger import TradeLogger
from trading.trader import Trader


def main():
    symbol = "005930"

    df = pd.read_csv("data/sample_prices.csv", dtype={"symbol": str})
    df = df[df["symbol"] == symbol].reset_index(drop=True)

    broker = PaperBroker(initial_cash=1_000_000)
    strategy = MovingAverageStrategy(short_window=3, long_window=5)
    risk_manager = RiskManager(max_trade_amount=300_000)
    logger = TradeLogger()

    trader = Trader(
        broker=broker,
        strategy=strategy,
        risk_manager=risk_manager,
        logger=logger,
    )

    for i in range(1, len(df) + 1):
        price_history = df["close"].iloc[:i]
        result = trader.run_step(symbol=symbol, price_history=price_history, quantity=1)

        print(
            f"{df['date'].iloc[i-1]} | "
            f"price={result['price']} | "
            f"signal={result['signal']} | "
            f"cash={result['balance']['cash']} | "
            f"positions={result['balance']['positions']}"
        )

    print("\nPaper trading simulation complete.")
    print("Logs saved to logs/simulated_trade_history.csv and logs/dry_run_order_log.jsonl")


if __name__ == "__main__":
    main()
