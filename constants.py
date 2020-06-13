"""BitBot constants module."""
import os
import json

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
KRAKEN_API_CALL_INTERVAL_SEC = 0.5
KRAKEN_KEY = os.environ.get("KRAKEN_KEY")
KRAKEN_SECRET = os.environ.get("KRAKEN_SECRET")

# kraken API configuration
KRAKEN_CONFIG = {}
with open("kraken/config.json") as config:
    KRAKEN_CONFIG = json.loads(config.read())
KRAKEN_CRYPTO_CONFIGS = KRAKEN_CONFIG["cryptocurrencies"]
KRAKEN_PRICE_CONFIGS = KRAKEN_CONFIG["prices"]

# trading constants
ALLOW_MARGIN_TRADING = os.environ.get("ALLOW_MARGIN_TRADING") == "True"
BASE_BUY_USD = float(os.environ.get("BASE_BUY_USD"))
DEFAULT_LEVERAGE = float(os.environ.get("DEFAULT_LEVERAGE"))
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS"))
MARGIN_LEVEL_LIMIT = float(os.environ.get("MARGIN_LEVEL_LIMIT"))
MAXIMUM_TRADE_VOLUME_MULTIPLIER = float(os.environ.get("MAXIMUM_TRADE_VOLUME_MULTIPLIER"))
ORDER_EXPIRATION_SECONDS = int(os.environ.get("ORDER_EXPIRATION_SECONDS"))
PERCENT_DEVIATION_TRADE_THRESHOLD = float(os.environ.get("PERCENT_DEVIATION_TRADE_THRESHOLD"))
PERCENT_TRAILING_CLOSE_THRESHOLD = float(os.environ.get("PERCENT_TRAILING_CLOSE_THRESHOLD"))
SUPPORTED_CRYPTOS = KRAKEN_CRYPTO_CONFIGS.keys()
SUPPORTED_PRICE_TYPES = KRAKEN_PRICE_CONFIGS.keys()
