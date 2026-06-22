# KIS Paper Trading System

## 1. Submission Note

This project was developed as an educational assignment for building an automated trading system using the Korea Investment & Securities (KIS) Open API.

Early in development, KIS API access (app key/secret issuance and account setup) was still being worked out, so the project was built conservatively around a `PaperBroker` simulation engine that follows the same interface as a future KIS Open API broker, with the trade history clearly labeled as simulated and not an official KIS record.

That access has since been resolved. `KISBroker` is now verified end-to-end against the real KIS Open API on a live account, including an actual executed buy order (order no. `0010839900`) — see [Section 9](#9-live--mock-trading-with-kisbroker) and [Section 10](#10-limitations).

The `PaperBroker` simulation engine is kept in place for `main.py`/`Trader`-driven backtesting over CSV price history; `KISBroker` is used independently via `live_trade.py` for real-account interaction. The `PaperBroker` can be swapped for `KISBroker` without changing the strategy or risk-manager logic, since both implement the same `Broker` interface.

## 2. Project Overview

The system implements the core structure of an automated trading pipeline modeled after the Korea Investment & Securities Open API:

- Price data is read from a CSV source.
- A moving average strategy generates BUY / SELL / HOLD signals.
- A risk manager validates whether an order is allowed.
- A broker (currently `PaperBroker`) executes the order against a simulated account.
- A logger records every executed/rejected order to disk.

## 3. Architecture

```
Price Data
  -> MovingAverageStrategy
  -> RiskManager
  -> Broker (interface)
       -> PaperBroker   (used by main.py / Trader)
       -> KISBroker      (real KIS API, used manually via live_trade.py)
  -> TradeLogger
  -> logs/simulated_trade_history.csv
  -> logs/dry_run_order_log.jsonl
```

`Trader` (in `trading/trader.py`) wires `PaperBroker` together with the strategy/risk-manager/logger for each simulation step. `KISBroker` implements the same `Broker` interface independently and is driven by `live_trade.py` — see [Section 9](#9-live--mock-trading-with-kisbroker).

## 4. Broker Design

Both brokers implement the same abstract `Broker` interface (`broker/base.py`):

- `get_current_price(symbol)`
- `get_balance()`
- `buy(symbol, quantity, price=None)`
- `sell(symbol, quantity, price=None)`

### PaperBroker (`broker/paper_broker.py`)
- Tracks cash and positions in memory.
- Simulates market order execution at the current price.
- Rejects orders when cash or position is insufficient.
- Returns a structured order result for every call, tagged `"mode": "PAPER"`.

### KISBroker (`broker/kis_broker.py`)
- Full implementation against the real KIS Open API (domestic stock, cash orders).
- Reads `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO`, `KIS_BASE_URL` from environment variables.
- Whether it talks to the **mock** server (`openapivts.koreainvestment.com`) or the **live** server (`openapi.koreainvestment.com`, real money) is determined entirely by `KIS_BASE_URL`.
- Handles OAuth token issuance/caching, hashkey generation for orders, current price lookup, balance/holdings lookup, and buy/sell order submission.
- Raises `KISAPIError` on any non-success response from KIS (`rt_cd != "0"` or non-200 HTTP).
- **Not** wired into `main.py` / `Trader` — see [Section 9](#9-live--mock-trading-with-kisbroker) for why and how to use it instead.

## 5. Trading Strategy

`MovingAverageStrategy` (`strategy/moving_average.py`) compares a short-window and long-window moving average of closing prices:

- short MA > long MA -> `BUY`
- short MA < long MA -> `SELL`
- otherwise, or insufficient history -> `HOLD`

## 6. Risk Management

`RiskManager` (`trading/risk_manager.py`) enforces simple guardrails before an order reaches the broker:

- A buy order's total cost must not exceed available cash.
- A buy order's total cost must not exceed `max_trade_amount`.
- A sell order cannot exceed the currently held quantity (no short selling).

## 7. Trade Logs

Running `main.py` produces two log files in `logs/`:

- `simulated_trade_history.csv` — tabular trade history (timestamp, symbol, side, quantity, price, status, message, cash_after, mode).
- `dry_run_order_log.jsonl` — one JSON object per line with the full order result, including post-trade positions.

Both files are explicitly tagged as simulated paper trading output (`mode: PAPER`), not official KIS mock-trading records.

## 8. How to Run

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

Running tests:

```bash
pytest
```

Copy `.env.example` to `.env` and fill in real values only when KIS API access becomes available. No real API keys are included in this repository.

## 9. Live / Mock Trading with KISBroker

`KISBroker` is fully implemented, but it is intentionally **not** plugged into `main.py`'s `Trader` loop. Two reasons:

1. `Trader`/`PaperBroker` are built around simulated step-by-step prices from a CSV (`broker.update_price(...)`). `KISBroker` has no such method — it always asks KIS for the real current price — so the two are not drop-in compatible.
2. Auto-firing real orders off of `data/sample_prices.csv` (fake, hard-coded prices) would be meaningless at best and dangerous at worst if pointed at the live server.

Instead, use the separate `live_trade.py` CLI for manual, one-at-a-time interaction with the real KIS API:

```bash
# Read-only — safe to run anytime
python live_trade.py price --symbol 005930
python live_trade.py balance

# Orders are previewed only, unless --confirm is passed
python live_trade.py buy --symbol 005930 --quantity 1
python live_trade.py buy --symbol 005930 --quantity 1 --confirm

# Limit order (omit --price for a market order)
python live_trade.py sell --symbol 005930 --quantity 1 --price 73000 --confirm
```

Setup:

1. Copy `.env.example` to `.env`.
2. Fill in `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO` (format `12345678-01` — the 2-digit suffix is the product code; it's `01` for a regular brokerage account, `22` for 연금저축, `29` for IRP/퇴직연금, etc. Every KIS account has one even if your app/passbook doesn't show it explicitly).
3. If you only have a live-trading app key, you cannot test against the **mock** server (`openapivts.koreainvestment.com`) — KIS rejects account-specific calls (e.g. balance) with `EGW02007: 해당 앱키는 모의투자용 앱키가 아닙니다` if the key wasn't issued for mock trading. Mock trading requires a separate app-key/secret pair issued via "모의투자 신청" on the KIS developer portal.
4. `price`/`balance` are read-only and safe to run directly against the live server (`https://openapi.koreainvestment.com:9443`) to validate connectivity before ever calling `buy`/`sell`. Live orders use real money; `live_trade.py` will ask for an extra typed `yes` confirmation in that case.
5. KIS allows issuing a new access token at most once per minute (`EGW00133`); space out repeated runs of `live_trade.py` accordingly.

If you later want signal-driven (not manual) live trading, the strategy/risk-manager logic in `MovingAverageStrategy` and `RiskManager` can be reused as-is — what's missing is a `Trader`-like loop that pulls real historical prices from KIS (e.g. the daily-chart endpoint) instead of `update_price()`/CSV.

## 10. Limitations

- The trade history in `logs/` is generated by `PaperBroker` using locally simulated prices and order execution. It is **not** an official KIS mock-trading record.
- `KISBroker` talks to the real KIS API. The automated test suite (`tests/test_kis_broker.py`) only exercises it against mocked HTTP responses. It has additionally been manually verified end-to-end against the live KIS server: `live_trade.py price` and `live_trade.py balance` (real authentication, real account, read-only calls), and a real `buy` order that was filled (order no. `0010839900`). A second `buy` attempt on a different symbol was correctly rejected by KIS with `APBK0952` (order amount exceeds the available order amount for that account), confirming the broker also surfaces real order-validation failures rather than masking them.
- The moving average strategy is intentionally simple for teaching purposes and is not intended for production use.
- `KISBroker`'s access token is cached in memory only (not persisted across runs), and KIS rate-limits token issuance — avoid re-running `live_trade.py` in tight loops.
