"""Application constants."""
import os

import errors

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
                      "bid": "b"}

# simulator constants
SIM_ACCOUNT_BALANCE = 1000.0

# cryptos bitbot is allowed to trade with
SUPPORTED_CRYPTOS = KRAKEN_CRYPTO_TICKERS.keys()

# ensure a cryptocurrency is supported before continuing
def validateCrypto(ticker):
    """Ensure a cryptocurrency is supported."""
    if ticker not in SUPPORTED_CRYPTOS:
        raise UnsupportedCryptoError(ticker)
