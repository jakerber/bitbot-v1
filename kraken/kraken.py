"""Wrapper around Krakenex API."""
import krakenex

import constants

kraken = krakenex.API()
kraken.load_key(constants.KRAKEN_KEY_PATH)

def buy(ticker, amount):
    """Buy a cryptocurrency."""
    raise NotImplementedError  # returns sell price

def getAccountBalance():
    """Get current account monetary balance."""
    raise NotImplementedError

    # # execute kraken account balance request
    # krakenTicker = constants.KRAKEN_CRYPTO_TICKERS[ticker]
    # requestData = {"pair": "%sUSD" % krakenTicker}
    # resp = _executeRequest(kraken.query_private, "TradeBalance", requestData=requestData)
    #
    # # return account balance
    # balance = resp["result"]
    # return balance

def getBalance(ticker):
    """Get the current balance of a cryptocurrency."""
    raise NotImplementedError

    # # execute kraken cryptocurrency balance request
    # resp = _executeRequest(kraken.query_private, "Balance")
    #
    # # return cryptocurrency balance
    # balance = resp["result"]
    # return balance

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
    return float(price)

def sell(ticker, amount):
    """Sell a cryptocurrency."""
    raise NotImplementedError  # returns sell price

def _executeRequest(api, requestName, requestData={}):
    """Execute a request to the Kraken API."""
    resp = api(requestName, requestData)

    # raise error if necessary
    error = resp["error"]
    if error:
        raise RuntimeError("unable to execute Kraken %s request. Err: %s" % (requestName, error))

    # return response
    return resp
