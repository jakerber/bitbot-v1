"""BitBot Krakenex API wrapper module."""
import constants
import krakenex
import time

kraken = krakenex.API(key=constants.KRAKEN_KEY, secret=constants.KRAKEN_SECRET)

DEFAULT_LEVERAGE = "2"
ORDER_EXPIRATION = "+%i" % constants.ORDER_EXPIRATION_SECONDS
UNKNOWN_ASSET_PAIR_ERROR = "Unknown asset pair"

############################
##  Prices
############################

def getPrices(ticker):
    """Get all current prices of a cryptocurrency."""
    # execute kraken price request
    krakenTicker = constants.KRAKEN_CRYPTO_TICKERS[ticker]
    requestData = {"pair": "%sUSD" % krakenTicker}
    resp = _executeRequest(kraken.query_public, "Ticker", requestData=requestData)

    # determine price code used to interpret results
    priceCode = constants.KRAKEN_PRICE_CODE_TEMPLATE_TO_USD % krakenTicker
    if priceCode not in resp["result"]:
        priceCode = constants.KRAKEN_SECONDARY_PRICE_CODE_TEMPLATE_TO_USD % krakenTicker
    allPrices = resp["result"][priceCode]

    # convert all prices to floats and return
    for priceType in allPrices:
        if priceType == "open":  # open price is a single value, not an array
            allPrices[priceType] = float(allPrices[priceType])
        else:
            allPrices[priceType] = float(allPrices[priceType][0])
    return allPrices

############################
##  Account info
############################

def getAccountBalances():
    """Get all account balances."""
    resp = _executeRequest(kraken.query_private, "TradeBalance")
    for balance in resp["result"]:
        resp["result"][balance] = float(resp["result"][balance])
    return resp["result"]

def getAssetBalances():
    """Get all asset balances."""
    resp = _executeRequest(kraken.query_private, "Balance")
    for balance in resp["result"]:
        resp["result"][balance] = float(resp["result"][balance])
    return resp["result"]

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

def buy(ticker, amount, priceTarget):
    """Buy a cryptocurrency."""
    krakenTicker = constants.KRAKEN_CRYPTO_TICKERS[ticker]
    cryptoPair = constants.KRAKEN_PRICE_CODE_TEMPLATE_FROM_USD % krakenTicker
    requestData = {"pair": cryptoPair,
                   "type": "buy",
                   "ordertype": "market",
                   "volume": amount,
                   "expiretm": ORDER_EXPIRATION,
                   "close[ordertype]": "limit",
                   "close[price]": priceTarget}

    # verify target price is above ask price
    askPrice = getPrices(ticker)["a"]
    if not priceTarget > askPrice:
        raise RuntimeError("unable to buy %s: target price ($%.3f) must be above ask price ($%.3f)" % (ticker, priceTarget, askPrice))

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

def short(ticker, amount, priceTarget):
    """Short a cryptocurrency."""
    krakenTicker = constants.KRAKEN_CRYPTO_TICKERS[ticker]
    cryptoPair = constants.KRAKEN_PRICE_CODE_TEMPLATE_TO_USD % krakenTicker
    requestData = {"pair": cryptoPair,
                   "type": "sell",
                   "ordertype": "market",
                   "volume": amount,
                   "leverage": DEFAULT_LEVERAGE,
                   "expiretm": ORDER_EXPIRATION,
                   "close[ordertype]": "limit",
                   "close[price]": priceTarget}

    # verify target price is below bid price
    bidPrice = getPrices(ticker)["b"]
    if not priceTarget < bidPrice:
        raise RuntimeError("unable to short %s: target price ($%.3f) must be below bid price ($%.3f)" % (ticker, priceTarget, bidPrice))

    # ensure sufficient margin is available to open short position
    if not sufficientMargin(amount * bidPrice):
        raise RuntimeError("insufficient margin available: short would reduce margin level below %.2f%%" % constants.MARGIN_LEVEL_LIMIT)

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
    currentEquity = getAccountBalances()["e"]
    currentMarginUsed = getAccountBalances()["m"]
    usedMarginAfterShort = currentMarginUsed + shortAmountUSD
    marginLevelAfterShort = (currentEquity / usedMarginAfterShort) * 100
    return marginLevelAfterShort > constants.MARGIN_LEVEL_LIMIT

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
