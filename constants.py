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
KRAKEN_BALANCE_CONFIGS = KRAKEN_CONFIG["balances"]
KRAKEN_CRYPTO_CONFIGS = KRAKEN_CONFIG["cryptocurrencies"]
KRAKEN_PRICE_CONFIGS = KRAKEN_CONFIG["prices"]
SUPPORTED_BALANCES = KRAKEN_BALANCE_CONFIGS.keys()
SUPPORTED_TICKERS = KRAKEN_CRYPTO_CONFIGS.keys()
SUPPORTED_PRICE_TYPES = KRAKEN_PRICE_CONFIGS.keys()

# trading parameters
ALLOW_MARGIN_TRADING = os.environ.get("ALLOW_MARGIN_TRADING") == "True"
BASE_COST_USD = float(os.environ.get("BASE_COST_USD"))
DEFAULT_LEVERAGE = float(os.environ.get("DEFAULT_LEVERAGE"))
HISTORY_RETENTION_DAYS = int(os.environ.get("HISTORY_RETENTION_DAYS"))
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS"))
MARGIN_LEVEL_MINIMUM = int(os.environ.get("MARGIN_LEVEL_MINIMUM"))
PERCENT_DEVIATION_OPEN_THRESHOLD = float(os.environ.get("PERCENT_DEVIATION_OPEN_THRESHOLD"))
PERCENT_TRAILING_CLOSE_THRESHOLD = float(os.environ.get("PERCENT_TRAILING_CLOSE_THRESHOLD"))
PERCENT_TRAILING_REVERTED_CLOSE_THRESHOLD = float(os.environ.get("PERCENT_TRAILING_REVERTED_CLOSE_THRESHOLD"))
