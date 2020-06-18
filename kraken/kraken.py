"""BitBot Krakenex API wrapper module."""
import constants
import krakenex
import math
import time

kraken = krakenex.API(key=constants.KRAKEN_KEY, secret=constants.KRAKEN_SECRET)

DEFAULT_LEVERAGE = 2
MAXIMUM_TRANSACTION_IDS = 50
ORDER_EXPIRATION = "+%i" % constants.ORDER_EXPIRATION_SECONDS
TRADE_VALUE_TEMPLATE = "%.{precision}f"

############################
##  Prices
############################

def getPrices():
    """Get all current prices of all supported cryptocurrencies.

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
    # gather support crypto asset pairs
    assetPairs = []
    for ticker in constants.SUPPORTED_TICKERS:
        assetPair = constants.KRAKEN_CRYPTO_CONFIGS.get(ticker).get("usd_pair")
        assetPairs.append(assetPair)

    # execute kraken price request
    requestData = {"pair": ",".join(assetPairs)}
    resp = _executeRequest(kraken.query_public, "Ticker", requestData=requestData)

    # convert results from asset pairs back to tickers
    prices = {}
    for ticker in constants.SUPPORTED_TICKERS:
        assetPair = constants.KRAKEN_CRYPTO_CONFIGS.get(ticker).get("usd_pair")
        prices[ticker] = resp.get("result").get(assetPair)

    # return all current prices
    return prices

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
    for asset in resp.get("result"):
        resp["result"][asset] = float(resp.get("result").get(asset))
    return resp.get("result")

############################
##  Order info
############################

def getOrders(transactionIds):
    """Get information on previously executed orders.

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
    orders = {}

    # split up into seperate queries if maximum orders exceeded
    queriesRequired = math.ceil(len(transactionIds) / MAXIMUM_TRANSACTION_IDS)
    for query in range(queriesRequired):
        startIndex = query * MAXIMUM_TRANSACTION_IDS
        endIndex = (query + 1) * MAXIMUM_TRANSACTION_IDS

        # query orders and combine results
        requestData = {"txid": ",".join(transactionIds[startIndex:endIndex])}
        resp = _executeRequest(kraken.query_private, "QueryOrders", requestData=requestData)
        orders.update(resp.get("result"))

    # return combined results
    return orders

############################
##  Trading
############################

def buy(ticker, volume, price=None, leverage=None):
    """Buy a cryptocurrency."""
    krakenConfig = constants.KRAKEN_CRYPTO_CONFIGS.get(ticker)
    assetPair = krakenConfig.get("usd_pair")
    pricePrecision = krakenConfig.get("price_decimal_precision")
    volumePrecision = krakenConfig.get("volume_decimal_precision")

    # construct kraken order request
    requestData = {"pair": assetPair,
                   "type": "buy",
                   "ordertype": "market",
                   "volume": TRADE_VALUE_TEMPLATE.format(precision=volumePrecision) % volume,
                   "expiretm": ORDER_EXPIRATION}

    # specify limit if price provided
    if price:
        pricePrecision = krakenConfig.get("price_decimal_precision")
        requestData["price"] = TRADE_VALUE_TEMPLATE.format(precision=pricePrecision) % price
        requestData["ordertype"] = "limit"

    # add leverage if buying on margin
    if leverage:
        requestData["leverage"] = leverage

    # execute buy order
    resp = _executeRequest(kraken.query_private, "AddOrder", requestData=requestData)
    return resp.get("result")

def sell(ticker, volume, price=None, leverage=None):
    """Sell a cryptocurrency."""
    krakenConfig = constants.KRAKEN_CRYPTO_CONFIGS.get(ticker)
    assetPair = krakenConfig.get("usd_pair")
    volumePrecision = krakenConfig.get("volume_decimal_precision")

    # construct kraken order request
    requestData = {"pair": assetPair,
                   "type": "sell",
                   "ordertype": "market",
                   "volume": TRADE_VALUE_TEMPLATE.format(precision=volumePrecision) % volume,
                   "expiretm": ORDER_EXPIRATION}

    # specify limit if price provided
    if price:
        pricePrecision = krakenConfig.get("price_decimal_precision")
        requestData["price"] = TRADE_VALUE_TEMPLATE.format(precision=pricePrecision) % price
        requestData["ordertype"] = "limit"

    # add leverage if selling on margin
    if leverage:
        requestData["leverage"] = leverage

    # execute sell order
    resp = _executeRequest(kraken.query_private, "AddOrder", requestData=requestData)
    return resp.get("result")

############################
##  Helper methods
############################

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
