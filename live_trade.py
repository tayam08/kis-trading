"""
Manual CLI for talking to the real KIS Open API (live or mock server,
depending on KIS_BASE_URL in .env). This is intentionally separate from
main.py, which only ever drives the simulated PaperBroker.

Examples:
  python live_trade.py price --symbol 005930
  python live_trade.py balance
  python live_trade.py buy --symbol 005930 --quantity 1 --confirm
  python live_trade.py sell --symbol 005930 --quantity 1 --price 73000 --confirm

Orders are NOT sent unless --confirm is passed. Without it, the command
just prints what would be sent.
"""

import argparse

from broker.kis_broker import KISBroker


def main():
    parser = argparse.ArgumentParser(description="Manual KIS Open API order tool")
    parser.add_argument("action", choices=["price", "balance", "buy", "sell"])
    parser.add_argument("--symbol", help="6-digit stock code, e.g. 005930")
    parser.add_argument("--quantity", type=int, default=1)
    parser.add_argument("--price", type=float, default=None, help="Omit for a market order")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required to actually send a buy/sell order. Without it, the order is only previewed.",
    )
    args = parser.parse_args()

    broker = KISBroker()
    print(f"Connected to {'MOCK' if broker.is_mock else 'LIVE'} server: {broker.base_url}")

    if args.action == "price":
        price = broker.get_current_price(args.symbol)
        print(f"{args.symbol} current price: {price}")
        return

    if args.action == "balance":
        balance = broker.get_balance()
        print(balance)
        return

    if not args.symbol:
        parser.error(f"--symbol is required for {args.action}")

    order_type = "MARKET" if args.price is None else "LIMIT"
    print(
        f"Preview: {args.action.upper()} {args.quantity} of {args.symbol} "
        f"({order_type} order{'' if args.price is None else f' @ {args.price}'}) "
        f"on the {'MOCK' if broker.is_mock else 'LIVE (REAL MONEY)'} server."
    )

    if not args.confirm:
        print("Dry run only. Re-run with --confirm to actually send this order.")
        return

    if not broker.is_mock:
        typed = input(
            "This will send a REAL order with REAL money. Type 'yes' to proceed: "
        )
        if typed.strip().lower() != "yes":
            print("Aborted.")
            return

    order_fn = broker.buy if args.action == "buy" else broker.sell
    result = order_fn(args.symbol, args.quantity, args.price)
    print(result)


if __name__ == "__main__":
    main()
