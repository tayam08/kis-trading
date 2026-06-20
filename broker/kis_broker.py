import os
import time

import requests
from dotenv import load_dotenv

from broker.base import Broker

load_dotenv()


class KISAPIError(Exception):
    pass


class KISBroker(Broker):
    """
    Live/mock broker for the Korea Investment & Securities (KIS) Open API.

    Whether this hits the real trading server or the mock (paper) trading
    server is determined entirely by KIS_BASE_URL in .env:
      - https://openapivts.koreainvestment.com:29443  -> mock trading
      - https://openapi.koreainvestment.com:9443       -> live trading (real money)

    tr_id codes differ between mock and live, so they are selected based on
    whether "openapivts" appears in the base URL, not by a separate flag.
    """

    PRICE_TR_ID = "FHKST01010100"

    def __init__(self):
        self.app_key = os.getenv("KIS_APP_KEY")
        self.app_secret = os.getenv("KIS_APP_SECRET")
        self.base_url = os.getenv("KIS_BASE_URL")
        account_no = os.getenv("KIS_ACCOUNT_NO", "")

        if not (self.app_key and self.app_secret and self.base_url and account_no):
            raise ValueError(
                "KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT_NO, and KIS_BASE_URL "
                "must all be set in .env to use KISBroker."
            )

        if "-" in account_no:
            self.cano, self.acnt_prdt_cd = account_no.split("-", 1)
        else:
            self.cano, self.acnt_prdt_cd = account_no[:8], account_no[8:]

        self.is_mock = "openapivts" in self.base_url

        self._access_token = None
        self._token_expires_at = 0

    def authenticate(self) -> str:
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        response = requests.post(
            f"{self.base_url}/oauth2/tokenP",
            json={
                "grant_type": "client_credentials",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
            },
            timeout=10,
        )
        data = self._parse_response(response)

        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + int(data.get("expires_in", 86400)) - 60

        return self._access_token

    def get_current_price(self, symbol: str) -> float:
        response = requests.get(
            f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price",
            headers=self._headers(self.PRICE_TR_ID),
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
            },
            timeout=10,
        )
        data = self._parse_response(response)
        return float(data["output"]["stck_prpr"])

    def get_balance(self) -> dict:
        tr_id = "VTTC8434R" if self.is_mock else "TTTC8434R"

        response = requests.get(
            f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance",
            headers=self._headers(tr_id),
            params={
                "CANO": self.cano,
                "ACNT_PRDT_CD": self.acnt_prdt_cd,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
            timeout=10,
        )
        data = self._parse_response(response)

        holdings = {
            item["pdno"]: int(item["hldg_qty"])
            for item in data.get("output1", [])
            if int(item.get("hldg_qty", 0)) > 0
        }
        summary = data.get("output2", [{}])[0]

        return {
            "cash": float(summary.get("dnca_tot_amt", 0)),
            "positions": holdings,
            "position_value": float(summary.get("scts_evlu_amt", 0)),
            "total_equity": float(summary.get("tot_evlu_amt", 0)),
        }

    def buy(self, symbol: str, quantity: int, price: float | None = None) -> dict:
        tr_id = "VTTC0802U" if self.is_mock else "TTTC0802U"
        return self._place_order(tr_id, "BUY", symbol, quantity, price)

    def sell(self, symbol: str, quantity: int, price: float | None = None) -> dict:
        tr_id = "VTTC0801U" if self.is_mock else "TTTC0801U"
        return self._place_order(tr_id, "SELL", symbol, quantity, price)

    def _place_order(self, tr_id: str, side: str, symbol: str, quantity: int, price: float | None) -> dict:
        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "PDNO": symbol,
            "ORD_DVSN": "00" if price else "01",
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(int(price)) if price else "0",
        }

        headers = self._headers(tr_id)
        headers["hashkey"] = self._get_hashkey(body)

        response = requests.post(
            f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash",
            headers=headers,
            json=body,
            timeout=10,
        )
        data = self._parse_response(response)
        output = data.get("output", {})

        return {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "status": "FILLED" if data.get("rt_cd") == "0" else "REJECTED",
            "message": data.get("msg1"),
            "order_no": output.get("ODNO"),
            "order_time": output.get("ORD_TMD"),
            "mode": "MOCK" if self.is_mock else "LIVE",
        }

    def _get_hashkey(self, body: dict) -> str:
        response = requests.post(
            f"{self.base_url}/uapi/hashkey",
            headers={
                "content-type": "application/json",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
            },
            json=body,
            timeout=10,
        )
        data = self._parse_response(response)
        return data["HASH"]

    def _headers(self, tr_id: str) -> dict:
        return {
            "content-type": "application/json",
            "authorization": f"Bearer {self.authenticate()}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }

    @staticmethod
    def _parse_response(response: requests.Response) -> dict:
        if response.status_code != 200:
            raise KISAPIError(f"KIS API HTTP {response.status_code}: {response.text}")

        data = response.json()

        if "rt_cd" in data and data["rt_cd"] != "0":
            raise KISAPIError(f"KIS API error {data.get('msg_cd')}: {data.get('msg1')}")

        return data
