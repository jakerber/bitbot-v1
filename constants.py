"""Application constants."""
import os

# database operations
DATABASE_URL = os.environ["DATABASE_URL"]

# kraken API constants
KRAKEN_API_BASE = "https://api.kraken.com/0/"
KRAKEN_CRYPTO_TICKERS = {"BTC": "XBT",
                         "ETH": "ETH",
                         "LTC": "LTC"}
KRAKEN_KEY_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               "kraken",
                               "keys",
                               ".kraken.key")
KRAKEN_PRICE_CODE_TEMPLATE = "X%sZ%s"
KRAKEN_PRICE_TYPES = {"ask": "a",
                      "bid": "b",
                      "low": "l",
                      "open": "o"}

# simulator constants
IS_SIMULATION = False
SIM_ACCOUNT_BALANCE = 1000.0
SIM_BALANCES = {ticker: 0 for ticker in KRAKEN_CRYPTO_TICKERS.keys()}

# delay between requests in seconds
SLEEP_INTERVAL = 10

# cryptos bitbot is allowed to trade with
SUPPORTED_CRYPTOS = KRAKEN_CRYPTO_TICKERS.keys()
