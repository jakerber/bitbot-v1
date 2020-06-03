"""Application constants."""
import os

# api
API_ROOT = "/api"

# notifications
MY_EMAIL = os.environ.get("MY_EMAIL")
MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN")
MAILGUN_API_URL = "https://api.mailgun.net/v3/%s" % MAILGUN_DOMAIN

# database operations
MONGODB_NAME = "bitbot"
MONGODB_EXCLUDE_PROPS = ["id", "_id"]
MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_URI_DEV = "mongodb://127.0.0.1:27017/%s" % MONGODB_NAME
if not MONGODB_URI:
    MONGODB_URI = MONGODB_URI_DEV

# kraken API constants
KRAKEN_API_BASE = "https://api.kraken.com/0/"
KRAKEN_CRYPTO_TICKERS = {"ADA": "ADA",
                         "BTC": "XBT",
                         "ETH": "ETH",
                         "EOS": "EOS",
                         "LTC": "LTC",
                         "XMR": "XMR",
                         "XRP": "XRP"}
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

# bitbot constants
ALLOW_MARGIN_TRADING = os.environ.get("ALLOW_MARGIN_TRADING") == "True"
BASE_BUY_USD = float(os.environ.get("BASE_BUY_USD"))
CONFIDENCE_DECIMALS = 10
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS"))
MAX_CONFIDENCE = float("0." + ("9" * CONFIDENCE_DECIMALS))
PERCENT_DEVIATION_THRESHOLD_MAX = float(os.environ.get("PERCENT_DEVIATION_THRESHOLD_MAX"))
PERCENT_DEVIATION_THRESHOLD_MIN = float(os.environ.get("PERCENT_DEVIATION_THRESHOLD_MIN"))
SUPPORTED_CRYPTOS = KRAKEN_CRYPTO_TICKERS.keys()
