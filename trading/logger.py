import csv
import json
import os


class TradeLogger:
    def __init__(
        self,
        csv_path: str = "logs/simulated_trade_history.csv",
        jsonl_path: str = "logs/dry_run_order_log.jsonl",
    ):
        self.csv_path = csv_path
        self.jsonl_path = jsonl_path
        os.makedirs("logs", exist_ok=True)

    def log_order(self, order_result: dict):
        self._write_csv(order_result)
        self._write_jsonl(order_result)

    def _write_csv(self, order_result: dict):
        file_exists = os.path.exists(self.csv_path)

        fieldnames = [
            "timestamp",
            "symbol",
            "side",
            "quantity",
            "price",
            "status",
            "message",
            "cash_after",
            "mode",
        ]

        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                key: order_result.get(key)
                for key in fieldnames
            })

    def _write_jsonl(self, order_result: dict):
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(order_result, ensure_ascii=False) + "\n")
