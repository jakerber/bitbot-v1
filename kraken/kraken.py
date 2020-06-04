"""BitBot Krakenex API wrapper module."""
import constants
import krakenex
import time

kraken = krakenex.API(key=constants.KRAKEN_KEY, secret=constants.KRAKEN_SECRET)

DEFAULT_LEVERAGE = "2"
UNKNOWN_ASSET_PAIR_ERROR = "Unknown asset pair"

############################
##  Prices
############################

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
    priceCode = constants.KRAKEN_PRICE_CODE_TEMPLATE_TO_USD % krakenTicker
    if priceCode not in resp["result"]:
        priceCode = constants.KRAKEN_SECONDARY_PRICE_CODE_TEMPLATE_TO_USD % krakenTicker
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
    priceCode = constants.KRAKEN_PRICE_CODE_TEMPLATE_TO_USD % krakenTicker
    if priceCode not in resp["result"]:
        priceCode = constants.KRAKEN_SECONDARY_PRICE_CODE_TEMPLATE_TO_USD % krakenTicker
    price = resp["result"][priceCode][priceTypeCode][0]
    if priceType == "open":  # open price is a single value, not an array
        price = resp["result"][priceCode][priceTypeCode]
    return float(price)

############################
##  Account info
############################

def getAccountBalances():
    """Get all account balances."""
    resp = _executeRequest(kraken.query_private, "Balance")
    for balance in resp["result"]:
        resp["result"][balance] = float(resp["result"][balance])
    return resp["result"]

def getAccountValue():
    """Get total value of account in USD."""
    resp = _executeRequest(kraken.query_private, "TradeBalance")
    return float(resp["result"]["e"])

def getBalance(ticker):
    """Get the current balance of a cryptocurrency."""
    balances = getAccountBalances()
    krakenTicker = constants.KRAKEN_CRYPTO_TICKERS[ticker]
    priceBalanceKey = constants.KRAKEN_PRICE_BALANCE_TEMPLATE % krakenTicker
    if priceBalanceKey in balances:
        return balances[priceBalanceKey]
    return 0.0

def getMarginUsed():
    """Get the current margin used for all open positions."""
    resp = _executeRequest(kraken.query_private, "TradeBalance")
    return float(resp["result"]["m"])

def getTradeHistory(startDatetime=None, endDatetime=None):
    """Get trade history for this account."""
    requestData = {}
    if startDatetime:
        requestData["start"] = startDatetime.timestamp()
    if endDatetime:
        requestData["end"] = endDatetime.timestamp()
    resp = _executeRequest(kraken.query_private, "TradesHistory", requestData=requestData)
    return resp["result"]

############################
##  Trading
############################

def buy(ticker, amount, priceLimit, priceTarget):
    """Buy a cryptocurrency."""
    krakenTicker = constants.KRAKEN_CRYPTO_TICKERS[ticker]
    cryptoPair = constants.KRAKEN_PRICE_CODE_TEMPLATE_FROM_USD % krakenTicker
    requestData = {"pair": cryptoPair,
                   "type": "buy",
                   "ordertype": "limit",
                   "price": priceLimit,
                   "volume": amount,
                   "close[ordertype]": "limit",
                   "close[price]": priceTarget}

    # add kraken buy order
    try:
        resp = _executeRequest(kraken.query_private, "AddOrder", requestData=requestData)
    except RuntimeError as err:
        if UNKNOWN_ASSET_PAIR_ERROR not in str(err):
            raise

        # retry with secondary pairing if asset pair is unknown
        else:
            requestData["pair"] = constants.KRAKEN_SECONDARY_PRICE_CODE_TEMPLATE_TO_USD % krakenTicker
            resp = _executeRequest(kraken.query_private, "AddOrder", requestData=requestData)

    return resp["result"]["descr"]

def short(ticker, amount, priceLimit, priceTarget):
    """Short a cryptocurrency."""
    krakenTicker = constants.KRAKEN_CRYPTO_TICKERS[ticker]
    cryptoPair = constants.KRAKEN_PRICE_CODE_TEMPLATE_TO_USD % krakenTicker
    requestData = {"pair": cryptoPair,
                   "type": "sell",
                   "ordertype": "limit",
                   "price": priceLimit,
                   "volume": amount,
                   "leverage": DEFAULT_LEVERAGE,
                   "close[ordertype]": "limit",
                   "close[price]": priceTarget}

    # ensure sufficient margin is available to open short position
    if not sufficientMargin(amount * priceLimit):
        raise RuntimeError("insufficient margin available: short would reduce margin level below %.f%%" % constants.KRAKEN_MARGIN_LEVEL_LIMIT)

    # add kraken sell order
    try:
        resp = _executeRequest(kraken.query_private, "AddOrder", requestData=requestData)
    except RuntimeError as err:
        if UNKNOWN_ASSET_PAIR_ERROR not in str(err):
            raise

        # retry with secondary pairing if asset pair is unknown
        else:
            requestData["pair"] = constants.KRAKEN_SECONDARY_PRICE_CODE_TEMPLATE_TO_USD % krakenTicker
            resp = _executeRequest(kraken.query_private, "AddOrder", requestData=requestData)

    return resp["result"]["descr"]

############################
##  Helper methods
############################

def sufficientMargin(shortAmountUSD):
    """Determine if there is enough margin available to open a short position."""
    currentEquity = getAccountValue()
    currentMarginUsed = getMarginUsed()
    usedMarginAfterShort = currentMarginUsed + shortAmountUSD
    marginLevelAfterShort = (currentEquity / usedMarginAfterShort) * 100
    return marginLevelAfterShort > constants.KRAKEN_MARGIN_LEVEL_LIMIT

def _executeRequest(api, requestName, requestData={}):
    """Execute a request to the Kraken API."""
    resp = api(requestName, requestData)

    # raise error if necessary
    if resp["error"] or "result" not in resp:
        raise RuntimeError("unable to execute Kraken %s request: %s" % (requestName, resp["error"]))

    # pause to avoid spamming exchange
    time.sleep(constants.KRAKEN_API_CALL_INTERVAL_SEC)

    # return response
    return resp
