"""BitBot assistant information retrieval module."""
import constants
import datetime
import logger
from kraken import kraken

class Assistant:
    """Object to retrieve information for BitBot."""
    def __init__(self, mongodb):
        self.mongodb = mongodb
        self.logger = logger.Logger("Assistant")

    ############################
    ##  Prices
    ############################

    def getAllPrices(self, ticker):
        """Get all current prices of a cryptocurrency."""
        self.logger.log("fetching all prices of %s" % ticker)
        if ticker not in constants.SUPPORTED_CRYPTOS:
            raise RuntimeError("ticker %s not supported" % ticker)
        return kraken.getAllPrices(ticker)

    def getPrice(self, ticker, priceType):
        """Get the current price of a cryptocurrency."""
        self.logger.log("fetching %s price of %s" % (priceType, ticker))
        if ticker not in constants.SUPPORTED_CRYPTOS:
            raise RuntimeError("ticker not supported: %s" % ticker)
        if priceType not in constants.KRAKEN_PRICE_TYPES:
            raise RuntimeError("price type not supported: %s" % priceType)
        return kraken.getPrice(ticker, priceType)

    def getPriceHistory(self, ticker, priceType="open"):
        """Get the historical price data of a cryptocurrency."""
        self.logger.log("fetching price history of %s" % (ticker))
        if ticker not in constants.SUPPORTED_CRYPTOS:
            raise RuntimeError("ticker not supported: %s" % ticker)
        if priceType not in constants.SUPPORTED_PRICE_TYPES:
            raise RuntimeError("price type not supported: %s" % priceType)

        # collect dates from lookback days
        dates = []
        now = datetime.datetime.now()
        for daysAgo in range(1, constants.LOOKBACK_DAYS):
            delta = datetime.timedelta(days=daysAgo)
            dateDaysAgo = now - delta
            dates.append(dateDaysAgo.strftime("%Y-%m-%d"))

        # fetch prices on dates
        queryFilter = {"date": {"$in": dates}, "ticker": ticker}
        querySort = ("date", constants.MONGODB_SORT_ASC)
        priceHistory = self.mongodb.find("price", filter=queryFilter, sort=querySort)

        # verify price history is complete
        if not priceHistory:
            raise RuntimeError("%s price history is empty" % ticker)
        elif len(priceHistory) != len(dates):
            datesFromDatabase = [price["date"] for price in priceHistory]
            missingDates = [date for date in dates if date not in datesFromDatabase]
            raise RuntimeError("%s price history is missing dates: %s" % (ticker, missingDates))

        # return price history
        return [price[priceType] for price in priceHistory]

    ############################
    ##  Account info
    ############################

    def getAccountBalances(self, ):
        """Get current account balances."""
        self.logger.log("fetching account balance")
        return kraken.getAccountBalances()

    def getAccountValue(self, ):
        """Get current value of account in USD."""
        self.logger.log("fetching account value")
        return kraken.getAccountValue()

    def getBalance(self, ticker):
        """Get the current balance of a cryptocurrency."""
        self.logger.log("fetching balance of %s" % ticker)
        if ticker not in constants.SUPPORTED_CRYPTOS:
            raise RuntimeError("ticker not supported: %s" % ticker)
        return kraken.getBalance(ticker)

    def getMarginUsed(self, ):
        """Get the current margin used for all open positions."""
        self.logger.log("fetching margin used")
        return kraken.getMarginUsed()

    def getTradeHistory(self, startDatetime=None, endDatetime=None):
        """Get trade history."""
        self.logger.log("fetching trade history (%s -> %s)" % (startDatetime, endDatetime))
        return kraken.getTradeHistory(startDatetime, endDatetime)

    ############################
    ##  Trading
    ############################

    def buy(self, ticker, amount, priceTarget):
        """Buy a cryptocurrency."""
        self.logger.log("buying %f of %s @ target $%f" % (amount, ticker, priceTarget))
        if ticker not in constants.SUPPORTED_CRYPTOS:
            raise RuntimeError("ticker not supported: %s" % ticker)
        return kraken.buy(ticker, amount, priceTarget)

    def short(self, ticker, amount, priceTarget):
        """Short a cryptocurrency."""
        self.logger.log("shorting %f of %s @ target $%f" % (amount, ticker, priceTarget))
        if ticker not in constants.SUPPORTED_CRYPTOS:
            raise RuntimeError("ticker not supported: %s" % ticker)
        return kraken.short(ticker, amount, priceTarget)
