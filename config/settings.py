import os

from dotenv import load_dotenv

load_dotenv()

TRADING_MODE = os.getenv("TRADING_MODE", "PAPER")
INITIAL_CASH = float(os.getenv("INITIAL_CASH", "1000000"))

KIS_APP_KEY = os.getenv("KIS_APP_KEY")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")
KIS_ACCOUNT_NO = os.getenv("KIS_ACCOUNT_NO")
KIS_BASE_URL = os.getenv("KIS_BASE_URL")
