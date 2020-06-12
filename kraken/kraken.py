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
##  Order info
############################

def getOrder(transactionId):
    """Get order information.

    Response format: (https://www.kraken.com/en-us/features/api#query-orders-info)
        {
            "refid": None,
            "userref": 0,
            "status": "closed",
            "reason": None,
            "opentm": 1591986580.2079,
            "closetm": 1591986584.3492,
            "starttm": 0,
            "expiretm": 1591986600,
            "descr": {
                "pair": "ADAUSD",
                "type": "sell",
                "ordertype": "limit",
                "price": "0.078864",
                "price2": "0",
                "leverage": "2:1",
                "order": "sell 126.80056807 ADAUSD @ limit 0.078864 with 2:1 leverage",
                "close": ""
            },
            "vol": "126.80056807",
            "vol_exec": "126.80056807",
            "cost": "10.000000",
            "fee": "0.018000",
            "price": "0.078864",
            "stopprice": "0.000000",
            "limitprice": "0.000000",
            "misc": "",
            "oflags": "fciq"
        }
    """
    requestData = {"txid": transactionId}
    resp = _executeRequest(kraken.query_private, "QueryOrders", requestData=requestData)
    return resp.get("result").get(transactionId)

############################
##  Trading
############################

def buy(ticker, amount, price=None, useMargin=False):
    """Buy a cryptocurrency."""
    krakenConfig = constants.KRAKEN_CRYPTO_CONFIGS.get(ticker)
    assetPair = krakenConfig.get("usd_pair")
    pricePrecision = krakenConfig.get("price_decimal_precision")
    volumePrecision = krakenConfig.get("volume_decimal_precision")

    # construct kraken order request
    requestData = {"pair": assetPair,
                   "type": "buy",
                   "ordertype": "market",
                   "volume": TRADE_VALUE_TEMPLATE.format(precision=volumePrecision) % amount,
                   "expiretm": ORDER_EXPIRATION}

    # specify limit if price provided
    if price:
        pricePrecision = krakenConfig.get("price_decimal_precision")
        requestData["price"] = TRADE_VALUE_TEMPLATE.format(precision=pricePrecision) % price
        requestData["ordertype"] = "limit"

    # add leverage if buying on margin
    if useMargin:
        price = price or float(getPrices(ticker).get("a")[0])
        if not sufficientMargin(amount * price):
            raise RuntimeError("insufficient margin available: buy would reduce margin level below %.2f%%" % constants.MARGIN_LEVEL_LIMIT)
        requestData["leverage"] = DEFAULT_LEVERAGE

    # execute buy order
    resp = _executeRequest(kraken.query_private, "AddOrder", requestData=requestData)
    return resp.get("result")

def sell(ticker, amount, price=None, useMargin=False):
    """Sell a cryptocurrency."""
    krakenConfig = constants.KRAKEN_CRYPTO_CONFIGS.get(ticker)
    assetPair = krakenConfig.get("usd_pair")
    volumePrecision = krakenConfig.get("volume_decimal_precision")

    # construct kraken order request
    requestData = {"pair": assetPair,
                   "type": "sell",
                   "ordertype": "market",
                   "volume": TRADE_VALUE_TEMPLATE.format(precision=volumePrecision) % amount,
                   "expiretm": ORDER_EXPIRATION}

    # specify limit if price provided
    if price:
        pricePrecision = krakenConfig.get("price_decimal_precision")
        requestData["price"] = TRADE_VALUE_TEMPLATE.format(precision=pricePrecision) % price
        requestData["ordertype"] = "limit"

    # add leverage if selling on margin
    if useMargin:
        price = price or float(getPrices(ticker).get("b")[0])
        if not sufficientMargin(amount * price):
            raise RuntimeError("insufficient margin available: sell would reduce margin level below %.2f%%" % constants.MARGIN_LEVEL_LIMIT)
        requestData["leverage"] = DEFAULT_LEVERAGE

    # execute sell order
    resp = _executeRequest(kraken.query_private, "AddOrder", requestData=requestData)
    return resp.get("result")

############################
##  Helper methods
############################

def sufficientMargin(tradeAmountUSD):
    """Determine if there is enough margin available to open a position."""
    equity = getAccountBalances().get("e")
    marginUsed = getAccountBalances().get("m")
    marginUsed += tradeAmountUSD / DEFAULT_LEVERAGE  # estimated margin cost
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
