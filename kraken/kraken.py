"""Wrapper around Krakenex API."""
import constants
import krakenex

kraken = krakenex.API(key=constants.KRAKEN_KEY, secret=constants.KRAKEN_SECRET)

def buy(ticker, amount):
    """Buy a cryptocurrency."""
    raise NotImplementedError  # returns sell price

def getAccountBalance():
    """Get current account monetary balance."""
    resp = _executeRequest(kraken.query_private, "Balance")
    balance = resp["result"]
    return balance

def getBalance(ticker):
    """Get the current balance of a cryptocurrency."""
    # execute kraken balance request
    krakenTicker = constants.KRAKEN_CRYPTO_TICKERS[ticker]
    requestData = {"pair": "%sUSD" % krakenTicker}
    resp = _executeRequest(kraken.query_private, "TradeBalance", requestData=requestData)

    # return crypto balance
    balance = resp["result"]
    return balance

def getAllPrices(ticker):
    """Get all current prices of a cryptocurrency.

    Format: (https://www.kraken.com/en-us/features/api#get-ticker-info)
        {
            "a": ["9718.50000", "1", "1.000"],
            "b": ["9715.60000", "4", "4.000"],
            "c": ["9712.70000", "0.03238337"],
            "v": ["22.15109020", "6976.84439690"],
            "p": ["9709.27880", "9687.91860"],
            "t": [70, 22174],
            "l": ["9675.60000", "9331.70000"],
            "h": ["9722.70000", "9888.00000"],
            "o": "9675.60000"
        }
    """
    # execute kraken price request
    krakenTicker = constants.KRAKEN_CRYPTO_TICKERS[ticker]
    requestData = {"pair": "%sUSD" % krakenTicker}
    resp = _executeRequest(kraken.query_public, "Ticker", requestData=requestData)

    # return crypto price
    priceCode = constants.KRAKEN_PRICE_CODE_TEMPLATE % (krakenTicker, "USD")
    allPrices = resp["result"][priceCode]
    return allPrices

def getPrice(ticker, priceType):
    """Get the current price of a cryptocurrency."""
    # execute kraken price request
    krakenTicker = constants.KRAKEN_CRYPTO_TICKERS[ticker]
    requestData = {"pair": "%sUSD" % krakenTicker}
    resp = _executeRequest(kraken.query_public, "Ticker", requestData=requestData)

    # return crypto price
    priceTypeCode = constants.KRAKEN_PRICE_TYPES[priceType]
    priceCode = constants.KRAKEN_PRICE_CODE_TEMPLATE % (krakenTicker, "USD")
    price = resp["result"][priceCode][priceTypeCode][0]
    if priceType == "open":  # open price is a single value, not an array
        price = resp["result"][priceCode][priceTypeCode]
    return float(price)

def sell(ticker, amount):
    """Sell a cryptocurrency."""
    raise NotImplementedError  # returns sell price

def _executeRequest(api, requestName, requestData={}):
    """Execute a request to the Kraken API."""
    resp = api(requestName, requestData)

    # raise error if necessary
    if resp["error"] or "result" not in resp:
        raise RuntimeError("unable to execute Kraken %s request: %s" % (requestName, resp["error"]))

    # return response
    return resp
