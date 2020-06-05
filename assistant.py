"""BitBot assistant information retrieval module."""
import constants
import datetime
import logger
from app import mongodb
from kraken import kraken

# initialize logger
logger = logger.Logger("Assistant")

############################
##  Prices
############################

def getAllPrices(ticker):
    """Get all current prices of a cryptocurrency."""
    logger.log("fetching all prices of %s" % ticker)
    if ticker not in constants.SUPPORTED_CRYPTOS:
        raise RuntimeError("ticker %s not supported" % ticker)
    return kraken.getAllPrices(ticker)

def getPrice(ticker, priceType):
    """Get the current price of a cryptocurrency."""
    logger.log("fetching %s price of %s" % (priceType, ticker))
    if ticker not in constants.SUPPORTED_CRYPTOS:
        raise RuntimeError("ticker not supported: %s" % ticker)
    if priceType not in constants.KRAKEN_PRICE_TYPES:
        raise RuntimeError("price type not supported: %s" % priceType)
    return kraken.getPrice(ticker, priceType)

def getPriceHistory(ticker, priceType="open"):
    """Get the historical price data of a cryptocurrency."""
    logger.log("fetching price history of %s" % (ticker))
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
    priceHistory = mongodb.find("price", filter=queryFilter, sort=querySort)

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

def getAccountBalances():
    """Get current account balances."""
    logger.log("fetching account balance")
    return kraken.getAccountBalances()

def getAccountValue():
    """Get current value of account in USD."""
    logger.log("fetching account value")
    return kraken.getAccountValue()

def getBalance(ticker):
    """Get the current balance of a cryptocurrency."""
    logger.log("fetching balance of %s" % ticker)
    if ticker not in constants.SUPPORTED_CRYPTOS:
        raise RuntimeError("ticker not supported: %s" % ticker)
    return kraken.getBalance(ticker)

def getMarginUsed():
    """Get the current margin used for all open positions."""
    logger.log("fetching margin used")
    return kraken.getMarginUsed()

def getTradeHistory(startDatetime=None, endDatetime=None):
    """Get trade history."""
    logger.log("fetching trade history (%s -> %s)" % (startDatetime, endDatetime))
    return kraken.getTradeHistory(startDatetime, endDatetime)

############################
##  Trading
############################

def buy(ticker, amount, priceLimit, priceTarget):
    """Buy a cryptocurrency."""
    logger.log("buying %f of %s @ price $%f (target $%f)" % (amount, ticker, priceLimit, priceTarget))
    if ticker not in constants.SUPPORTED_CRYPTOS:
        raise RuntimeError("ticker not supported: %s" % ticker)
    if priceTarget < priceLimit:
        raise RuntimeError("price target (%f) must be above price limit (%f)" % (priceTarget, priceLimit))
    return kraken.buy(ticker, amount, priceLimit, priceTarget)

def short(ticker, amount, priceLimit, priceTarget):
    """Short a cryptocurrency."""
    logger.log("shorting %f of %s @ price $%f (target $%f)" % (amount, ticker, priceLimit, priceTarget))
    if ticker not in constants.SUPPORTED_CRYPTOS:
        raise RuntimeError("ticker not supported: %s" % ticker)
    if priceTarget > priceLimit:
        raise RuntimeError("price target (%f) must be below price limit (%f)" % (priceTarget, priceLimit))
    return kraken.short(ticker, amount, priceLimit, priceTarget)
