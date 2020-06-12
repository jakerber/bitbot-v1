"""BitBot Krakenex API wrapper module."""
import constants
import krakenex
import time

kraken = krakenex.API(key=constants.KRAKEN_KEY, secret=constants.KRAKEN_SECRET)

DEFAULT_LEVERAGE = 2
ORDER_EXPIRATION = "+%i" % constants.ORDER_EXPIRATION_SECONDS
TRADE_VALUE_TEMPLATE = "%.{precision}f"

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
    krakenAssetPair = constants.KRAKEN_CRYPTO_CONFIGS.get(ticker).get("usd_pair")
    requestData = {"pair": krakenAssetPair}
    resp = _executeRequest(kraken.query_public, "Ticker", requestData=requestData)

    # return all current prices
    return resp.get("result").get(krakenAssetPair)

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

def buy(ticker, amount, price, useMargin=False):
    """Buy a cryptocurrency."""
    krakenConfig = constants.KRAKEN_CRYPTO_CONFIGS.get(ticker)
    assetPair = krakenConfig.get("usd_pair")
    pricePrecision = krakenConfig.get("price_decimal_precision")
    volumePrecision = krakenConfig.get("volume_decimal_precision")

    # construct kraken order request
    requestData = {"pair": assetPair,
                   "type": "buy",
                   "ordertype": "limit",
                   "price": TRADE_VALUE_TEMPLATE.format(precision=pricePrecision) % price,
                   "volume": TRADE_VALUE_TEMPLATE.format(precision=volumePrecision) % amount,
                   "expiretm": ORDER_EXPIRATION}

    # add leverage if buying on margin
    if useMargin:
        if not sufficientMargin(amount * price):
            raise RuntimeError("insufficient margin available: buy would reduce margin level below %.2f%%" % constants.MARGIN_LEVEL_LIMIT)
        requestData["leverage"] = DEFAULT_LEVERAGE

    # execute buy order
    resp = _executeRequest(kraken.query_private, "AddOrder", requestData=requestData)
    return resp.get("result").get("descr")

def short(ticker, amount, price, useMargin=False):
    """Short a cryptocurrency."""
    krakenConfig = constants.KRAKEN_CRYPTO_CONFIGS.get(ticker)
    assetPair = krakenConfig.get("usd_pair")
    pricePrecision = krakenConfig.get("price_decimal_precision")
    volumePrecision = krakenConfig.get("volume_decimal_precision")

    # construct kraken order request
    requestData = {"pair": assetPair,
                   "type": "sell",
                   "ordertype": "limit",
                   "price": TRADE_VALUE_TEMPLATE.format(precision=pricePrecision) % price,
                   "volume": TRADE_VALUE_TEMPLATE.format(precision=volumePrecision) % amount,
                   "expiretm": ORDER_EXPIRATION}

    # add leverage if shorting on margin
    if useMargin:
        if not sufficientMargin(amount * price):
            raise RuntimeError("insufficient margin available: short would reduce margin level below %.2f%%" % constants.MARGIN_LEVEL_LIMIT)
        requestData["leverage"] = DEFAULT_LEVERAGE

    # execute sell order
    resp = _executeRequest(kraken.query_private, "AddOrder", requestData=requestData)
    return resp.get("result")

############################
##  Helper methods
############################

def sufficientMargin(shortAmountUSD):
    """Determine if there is enough margin available to open a short position."""
    equity = getAccountBalances().get("e")
    marginUsed = getAccountBalances().get("m")
    marginUsed += shortAmountUSD / DEFAULT_LEVERAGE  # estimated margin cost
    marginLevel = (equity / marginUsed) * 100
    return marginLevel > constants.MARGIN_LEVEL_LIMIT

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
