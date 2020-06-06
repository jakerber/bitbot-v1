"""BitBot constants module."""
import os

# api
API_ROOT = "/api/v1"

# notifications
MY_EMAIL = os.environ.get("MY_EMAIL")
MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN")
MAILGUN_API_URL = "https://api.mailgun.net/v3/%s" % MAILGUN_DOMAIN

# database operations
MONGODB_NAME = "bitbot"
MONGODB_EXCLUDE_PROPS = ["id", "_id"]
MONGODB_SORT_ASC = 1
MONGODB_SORT_DESC = -1
MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_URI_DEV = "mongodb://127.0.0.1:27017/%s" % MONGODB_NAME
if not MONGODB_URI:
    MONGODB_URI = MONGODB_URI_DEV

# kraken API constants
KRAKEN_API_BASE = "https://api.kraken.com/0/"
KRAKEN_API_CALL_INTERVAL_SEC = 0.1
KRAKEN_CRYPTO_TICKERS = {"ADA": "ADA",
                         "BTC": "XBT",
                         "ETH": "ETH",
                         "EOS": "EOS",
                         "LTC": "LTC",
                         "TRX": "TRX",
                         "XLM": "XLM",
                         "XMR": "XMR",
                         "XRP": "XRP",
                         "XTZ": "XTZ"}
KRAKEN_KEY = os.environ.get("KRAKEN_KEY")
KRAKEN_SECRET = os.environ.get("KRAKEN_SECRET")
KRAKEN_PRICE_BALANCE_TEMPLATE = "X%s"
KRAKEN_PRICE_CODE_TEMPLATE_TO_USD = "X%sZUSD"
KRAKEN_PRICE_CODE_TEMPLATE_FROM_USD = "ZUSDX%s"
KRAKEN_SECONDARY_PRICE_CODE_TEMPLATE_TO_USD = "%sUSD"
KRAKEN_SECONDARY_PRICE_CODE_TEMPLATE_FROM_USD = "USD%s"
KRAKEN_PRICE_TYPES = {"ask": "a",
                      "bid": "b",
                      "low": "l",
                      "open": "o"}

# trading constants
ALLOW_MARGIN_TRADING = os.environ.get("ALLOW_MARGIN_TRADING") == "True"
BASE_BUY_USD = float(os.environ.get("BASE_BUY_USD"))
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS"))
MARGIN_LEVEL_LIMIT = float(os.environ.get("MARGIN_LEVEL_LIMIT"))
TRADE_MULTIPLIER_MAX = float(os.environ.get("TRADE_MULTIPLIER_MAX"))
PERCENT_DEVIATION_THRESHOLD = float(os.environ.get("PERCENT_DEVIATION_THRESHOLD"))
SUPPORTED_CRYPTOS = KRAKEN_CRYPTO_TICKERS.keys()
SUPPORTED_PRICE_TYPES = ["open", "high", "low"]
