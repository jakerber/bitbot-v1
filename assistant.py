"""BitBot assistant information retrieval module."""
import constants
import datetime
import logger
from kraken import kraken

MINIMUM_ASSET_BALANCE = 0.0001

class Assistant:
    """Object to retrieve information for BitBot."""
    def __init__(self, mongodb):
        self.mongodb = mongodb
        self.logger = logger.Logger("Assistant")

    ############################
    ##  Prices
    ############################

    def getPrices(self):
        """Get all current prices of all supported cryptocurrencies."""
        self.logger.log("fetching current prices")
        _prices = kraken.getPrices()

        # parse supported price types out of response
        prices = {}
        for ticker in _prices:
            prices[ticker] = {}
            for priceType in constants.KRAKEN_PRICE_CONFIGS:
                config = constants.KRAKEN_PRICE_CONFIGS.get(priceType)
                price = _prices.get(ticker).get(config.get("code"))[config.get("api_index")]
                prices[ticker][priceType] = float(price)

        # return all converted prices
        return prices

    def getPriceHistory(self, ticker, startingDatetime=None, verify=True):
        """Get the historical price data of a cryptocurrency."""
        if ticker not in constants.SUPPORTED_TICKERS:
            raise RuntimeError("ticker not supported: %s" % ticker)

        # get starting datetime based on lookback days if none provided
        if not startingDatetime:
            self.logger.log("fetching %s price history" % ticker)
            now = datetime.datetime.utcnow()
            delta = datetime.timedelta(days=constants.LOOKBACK_DAYS)
            startingDatetime = now - delta
        else:
            self.logger.log("fetching %s price since %s UTC" % (ticker, startingDatetime.strftime("%Y-%m-%d %H:%M")))

        # fetch price history
        queryFilter = {"ticker": ticker, "utc_datetime": {"$gte": startingDatetime}}
        querySort = ("utc_datetime", constants.MONGODB_SORT_ASC)
        priceHistory = self.mongodb.find("price", filter=queryFilter, sort=querySort)

        # verify history exists
        if not priceHistory and verify:
            raise RuntimeError("%s price history is empty" % ticker)

        # return price history
        return priceHistory

    ############################
    ##  Account info
    ############################

    def getAccountBalances(self):
        """Get current account balances."""
        self.logger.log("fetching account balances")
        accountBalances = kraken.getAccountBalances()

        # parse relevant balances from response
        balances = {}
        for balanceType in constants.SUPPORTED_BALANCES:
            balanceCode = constants.KRAKEN_BALANCE_CONFIGS.get(balanceType)
            balances[balanceType] = accountBalances.get(balanceCode)
        return balances

    def getAssetBalances(self):
        """Get current balance of all assets."""
        self.logger.log("fetching asset balances")
        assetBalances = kraken.getAssetBalances()

        # convert assets to tickers and omit balances under minimum
        tickerBalances = {}
        for ticker in constants.SUPPORTED_TICKERS:
            asset = constants.KRAKEN_CRYPTO_CONFIGS.get(ticker).get("asset")
            balance = assetBalances.get(asset)
            balance = 0.0 if balance < MINIMUM_ASSET_BALANCE else balance
            tickerBalances[ticker] = balance

        # return results with USD included
        if "ZUSD" in assetBalances:
            tickerBalances["USD"] = float(assetBalances.get("ZUSD"))
        return tickerBalances

    def getEquityHistory(self, startingDatetime=None, verify=True):
        """Get the historical account equity balance."""
        # get starting datetime from lookback days if none provided
        if not startingDatetime:
            now = datetime.datetime.utcnow()
            delta = datetime.timedelta(days=constants.LOOKBACK_DAYS)
            startingDatetime = now - delta
            self.logger.log("fetching equity balance since %s UTC" % startingDatetime.strftime("%Y-%m-%d %H:%M"))
        else:
            self.logger.log("fetching equity history")

        # fetch equity history
        queryFilter = {"utc_datetime": {"$gte": startingDatetime}}
        querySort = ("utc_datetime", constants.MONGODB_SORT_ASC)
        equityHistory = self.mongodb.find("equity", filter=queryFilter, sort=querySort)

        # verify history exists
        if not equityHistory and verify:
            raise RuntimeError("equity history is empty")

        # return equity history
        return equityHistory

    ############################
    ##  Order info
    ############################

    def getOpenPositions(self, startingDatetime=None):
        """Get open positions."""
        if not startingDatetime:
            self.logger.log("fetching open positions")
            return self.mongodb.find("position")

        # filter positions by date if one provided
        self.logger.log("fetching positions opened %s UTC or later" % startingDatetime.strftime("%Y-%m-%d %H:%M"))
        return self.mongodb.find("position", filter={"utc_datetime": {"$gte": startingDatetime}})

    def getOrders(self, transactionIds):
        """Get order information."""
        self.logger.log("fetching order information for transactions: %s" % str(transactionIds))
        return kraken.getOrders(transactionIds)

    ############################
    ##  Trading
    ############################

    def buy(self, ticker, volume, price=None, leverage=None):
        """Buy a cryptocurrency."""
        if ticker not in constants.SUPPORTED_TICKERS:
            raise RuntimeError("ticker not supported: %s" % ticker)
        logMessage = "buying %.3f %s" % (volume, ticker)
        if price:
            logMessage += " @ $%.3f" % price
        if leverage:
            logMessage += " with %i:1 leverage" % leverage
        self.logger.log(logMessage)

        # ensure margin trading is allowed before using leverage
        if leverage and not constants.ALLOW_MARGIN_TRADING:
            raise RuntimeError("unable to buy %s: margin trading is not allowed" % ticker)

        # buy cryptocurrency
        return self._executeTrade(kraken.buy, ticker, volume, price, leverage)

    def sell(self, ticker, volume, price=None, leverage=None):
        """Sell a cryptocurrency."""
        if ticker not in constants.SUPPORTED_TICKERS:
            raise RuntimeError("ticker not supported: %s" % ticker)
        logMessage = "selling %.3f %s" % (volume, ticker)
        if price:
            logMessage += " @ $%.3f" % price
        if leverage:
            logMessage += " with %i:1 leverage" % leverage
        self.logger.log(logMessage)

        # ensure margin trading is allowed before using leverage
        if leverage and not constants.ALLOW_MARGIN_TRADING:
            raise RuntimeError("unable to sell %s: margin trading is not allowed" % ticker)

        # sell cryptocurrency
        return self._executeTrade(kraken.sell, ticker, volume, price, leverage)

    ############################
    ##  Helper methods
    ############################

    def _executeTrade(self, tradeMethod, ticker, volume, price, leverage):
        """Execute trade and interpret order response."""
        confirmation = tradeMethod(ticker, volume, price=price, leverage=leverage)
        if confirmation:
            return True, {"transaction_id": confirmation.get("txid")[0], "description": confirmation.get("descr").get("order")}
        return False, {}
