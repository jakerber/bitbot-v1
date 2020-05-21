"""Application constants."""
import os

# bitbot constants
CONFIDENCE_DECIMALS = 10
DEVIATION_THRESHOLD = float(os.environ.get("DEVIATION_THRESHOLD"))
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS"))
MAX_CONFIDENCE = float("0." + ("9" * CONFIDENCE_DECIMALS))

# database operations
MONGODB_NAME = "bitbot"
MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_URI_DEV = "mongodb://127.0.0.1:27017/%s" % MONGODB_NAME
if not MONGODB_URI:
    MONGODB_URI = MONGODB_URI_DEV

# kraken API constants
KRAKEN_API_BASE = "https://api.kraken.com/0/"
KRAKEN_CRYPTO_TICKERS = {"BTC": "XBT",
                         "ETH": "ETH",
                         "LTC": "LTC"}
KRAKEN_KEY = os.environ.get("KRAKEN_KEY")
KRAKEN_SECRET = os.environ.get("KRAKEN_SECRET")
KRAKEN_PRICE_BALANCE_TEMPLATE = "X%s"
KRAKEN_PRICE_CODE_TEMPLATE = "X%sZ%s"
KRAKEN_PRICE_TYPES = {"ask": "a",
                      "bid": "b",
                      "low": "l",
                      "open": "o"}

# delay between requests in seconds
SLEEP_INTERVAL = 10

# cryptos bitbot is allowed to trade with
SUPPORTED_CRYPTOS = KRAKEN_CRYPTO_TICKERS.keys()
