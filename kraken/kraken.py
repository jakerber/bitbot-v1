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
    """Get all current prices of a cryptocurrency.

    Response format: (https://www.kraken.com/en-us/features/api#get-ticker-info)
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
    krakenTicker = constants.KRAKEN_CRYPTO_TICKERS.get(ticker)
    requestData = {"pair": constants.KRAKEN_ASSET_PAIR_TEMPLATE % krakenTicker}
    resp = _executeRequest(kraken.query_public, "Ticker", requestData=requestData)

    # return all current prices
    priceCode = constants.KRAKEN_PRICE_CODE_TEMPLATE_TO_USD % krakenTicker
    if priceCode not in resp.get("result"):
        priceCode = constants.KRAKEN_SECONDARY_PRICE_CODE_TEMPLATE_TO_USD % krakenTicker
    return resp.get("result").get(priceCode)

############################
##  Account info
############################

def getAccountBalances():
    """Get all account balances."""
    resp = _executeRequest(kraken.query_private, "TradeBalance")
    for balance in resp.get("result"):
        resp["result"][balance] = float(resp.get("result").get(balance))
    return resp.get("result")

def getAssetBalances():
    """Get all asset balances."""
    resp = _executeRequest(kraken.query_private, "Balance")
    for balance in resp.get("result"):
        resp["result"][balance] = float(resp.get("result").get(balance))
    return resp.get("result")

def getTradeHistory(startDatetime=None, endDatetime=None):
    """Get trade history for this account."""
    requestData = {}
    if startDatetime:
        requestData["start"] = startDatetime.timestamp()
    if endDatetime:
        requestData["end"] = endDatetime.timestamp()
    resp = _executeRequest(kraken.query_private, "TradesHistory", requestData=requestData)
    return resp.get("result")

############################
##  Trading
############################

def buy(ticker, amount, priceTarget):
    """Buy a cryptocurrency."""
    krakenTicker = constants.KRAKEN_CRYPTO_TICKERS.get(ticker)
    cryptoPair = constants.KRAKEN_PRICE_CODE_TEMPLATE_FROM_USD % krakenTicker
    requestData = {"pair": cryptoPair,
                   "type": "buy",
                   "ordertype": "market",
                   "volume": amount,
                   "expiretm": ORDER_EXPIRATION,
                   "close[ordertype]": "limit",
                   "close[price]": priceTarget}

    # verify target price is above ask price
    askPrice = float(getPrices(ticker).get("a")[0])
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

    return resp.get("result").get("descr")

def short(ticker, amount, priceTarget):
    """Short a cryptocurrency."""
    krakenTicker = constants.KRAKEN_CRYPTO_TICKERS.get(ticker)
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
    bidPrice = float(getPrices(ticker).get("b")[0])
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

    return resp.get("result").get("descr")

############################
##  Helper methods
############################

def sufficientMargin(shortAmountUSD):
    """Determine if there is enough margin available to open a short position."""
    currentEquity = getAccountBalances().get("e")
    currentMarginUsed = getAccountBalances().get("m")
    usedMarginAfterShort = currentMarginUsed + shortAmountUSD
    marginLevelAfterShort = (currentEquity / usedMarginAfterShort) * 100
    return marginLevelAfterShort > constants.MARGIN_LEVEL_LIMIT

def _executeRequest(api, requestName, requestData={}):
    """Execute a request to the Kraken API."""
    resp = api(requestName, requestData)

    # raise error if necessary
    if resp.get("error") or "result" not in resp:
        raise RuntimeError("unable to execute Kraken %s request: %s" % (requestName, resp.get("error")))

    # pause to avoid spamming exchange
    time.sleep(constants.KRAKEN_API_CALL_INTERVAL_SEC)

    # return response
    return resp
