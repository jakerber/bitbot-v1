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
        self.logger = logger.BitBotLogger("Assistant")

    ############################
    ##  Prices
    ############################

    def getPrice(self, ticker, priceType):
        """Get the current price of a cryptocurrency."""
        self.logger.log("fetching %s price of %s" % (priceType, ticker))
        if ticker not in constants.SUPPORTED_CRYPTOS:
            raise RuntimeError("ticker not supported: %s" % ticker)
        if priceType not in constants.SUPPORTED_PRICE_TYPES:
            raise RuntimeError("price type not supported: %s" % priceType)

        # fetch all prices
        prices = kraken.getPrices(ticker)

        # parse price type out of response
        priceConfig = constants.KRAKEN_PRICE_CONFIGS.get(priceType)
        priceTypeCode = priceConfig.get("code")
        priceTypeIndex = priceConfig.get("api_index")
        price = prices.get(priceTypeCode)[priceTypeIndex]

        # return converted price
        return float(price)

    def getAllPrices(self, ticker):
        """Get all supported prices of a cryptocurrency."""
        self.logger.log("fetching all prices of %s" % (ticker))
        if ticker not in constants.SUPPORTED_CRYPTOS:
            raise RuntimeError("ticker not supported: %s" % ticker)

        # fetch all prices
        prices = kraken.getPrices(ticker)

        # parse price type out of response
        allPrices = {}
        for priceType in constants.SUPPORTED_PRICE_TYPES:
            config = constants.KRAKEN_PRICE_CONFIGS.get(priceType)
            priceTypeCode = config.get("code")
            priceTypeIndex = config.get("api_index")
            allPrices[priceType] = float(prices.get(priceTypeCode)[priceTypeIndex])

        # return all prices
        return allPrices

    def getPriceHistory(self, ticker):
        """Get the historical price data of a cryptocurrency."""
        self.logger.log("fetching price history of %s" % (ticker))
        if ticker not in constants.SUPPORTED_CRYPTOS:
            raise RuntimeError("ticker not supported: %s" % ticker)

        # get starting unix timestamp based on lookback days
        now = datetime.datetime.utcnow()
        delta = datetime.timedelta(days=constants.LOOKBACK_DAYS)
        startingDatetime = now - delta

        # fetch prices within lookback
        queryFilter = {"ticker": ticker, "utc_datetime": {"$gte": startingDatetime}}
        querySort = ("utc_datetime", constants.MONGODB_SORT_ASC)
        priceHistory = self.mongodb.find("price", filter=queryFilter, sort=querySort)

        # verify price history exists
        if not priceHistory:
            raise RuntimeError("%s price history is empty" % ticker)

        # return price history
        return priceHistory

    ############################
    ##  Account info
    ############################

    def getAccountValue(self):
        """Get current value of account in USD."""
        self.logger.log("fetching account value")
        accountBalances = kraken.getAccountBalances()
        return accountBalances.get("eb") + accountBalances.get("n")  # balance + net of open positions

    def getAssetBalance(self, ticker):
        """Get the current balance of an asset in USD."""
        self.logger.log("fetching balance of %s" % ticker)
        assetBalances = getAssetBalances()
        if ticker in assetBalances:
            return assetBalances.get(ticker)
        return 0.0

    def getAssetBalances(self):
        """Get current balance of all assets."""
        self.logger.log("fetching balances of all assets")
        assetBalances = kraken.getAssetBalances()

        # convert assets to tickers and omit balances under minimum
        tickerBalances = {}
        for asset in assetBalances:
            for ticker in constants.KRAKEN_CRYPTO_CONFIGS:
                if constants.KRAKEN_CRYPTO_CONFIGS.get(ticker).get("asset") == asset:
                    balance = assetBalances.get(asset)
                    balance = 0.0 if balance < MINIMUM_ASSET_BALANCE else balance
                    tickerBalances[ticker] = balance
        return tickerBalances

    def getMarginLevel(self):
        """Get the current account margin level."""
        self.logger.log("fetching margin level")
        accountBalances = kraken.getAccountBalances()
        if "ml" in accountBalances:
            return accountBalances.get("ml")
        return None

    def getTradeHistory(self, startDatetime=None, endDatetime=None):
        """Get trade history."""
        self.logger.log("fetching trade history (%s -> %s)" % (startDatetime, endDatetime))
        return kraken.getTradeHistory(startDatetime, endDatetime)

    ############################
    ##  Trading
    ############################

    def buy(self, ticker, amount, price):
        """Buy a cryptocurrency."""
        if ticker not in constants.SUPPORTED_CRYPTOS:
            raise RuntimeError("ticker not supported: %s" % ticker)
        self.logger.log("buying ~$%.2f of %s" % (amount * price, ticker))
        return self._executeTrade(kraken.buy, ticker, amount, price)

    def short(self, ticker, amount, price):
        """Short a cryptocurrency."""
        if ticker not in constants.SUPPORTED_CRYPTOS:
            raise RuntimeError("ticker not supported: %s" % ticker)
        self.logger.log("shorting ~$%.2f of %s" % (amount * price, ticker))
        return self._executeTrade(kraken.short, ticker, amount, price)

    ############################
    ##  Helper methods
    ############################

    def _executeTrade(self, tradeMethod, ticker, amount, price):
        """Parse transaction ID and description out of order response."""
        confirmation = tradeMethod(ticker, amount, price)
        if confirmation:
            return True, {"transactionId": confirmation.get("txid")[0],
                          "description": confirmation.get("descr")}
        return False, {}
