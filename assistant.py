"""Assistant module for fetching account and cryptocurrency info."""
from kraken import kraken
import constants
import logger

LOGGER = logger.Logger("Assistant")

############################
##  Prices
############################

def getAllPrices(ticker):
    """Get all current prices of a cryptocurrency."""
    LOGGER.log("fetching all prices of %s" % ticker)
    if ticker not in constants.SUPPORTED_CRYPTOS:
        raise RuntimeError("ticker %s not supported" % ticker)
    return kraken.getAllPrices(ticker)

def getPrice(ticker, priceType):
    """Get the current price of a cryptocurrency."""
    LOGGER.log("fetching %s price of %s" % (priceType, ticker))
    if ticker not in constants.SUPPORTED_CRYPTOS:
        raise RuntimeError("ticker not supported: %s" % ticker)
    if priceType not in constants.KRAKEN_PRICE_TYPES:
        raise RuntimeError("price type not supported: %s" % priceType)
    return kraken.getPrice(ticker, priceType)

############################
##  Account info
############################

def getAccountBalances():
    """Get current account balances."""
    LOGGER.log("fetching account balance")
    return kraken.getAccountBalances()

def getAccountValue():
    """Get current value of account in USD."""
    LOGGER.log("fetching account value")
    return kraken.getAccountValue()

def getBalance(ticker):
    """Get the current balance of a cryptocurrency."""
    LOGGER.log("fetching balance of %s" % ticker)
    if ticker not in constants.SUPPORTED_CRYPTOS:
        raise RuntimeError("ticker not supported: %s" % ticker)
    return kraken.getBalance(ticker)

def getTradeHistory(startDatetime=None, endDatetime=None):
    """Get trade history."""
    LOGGER.log("fetching trade history (%s -> %s)" % (startDatetime, endDatetime))
    return kraken.getTradeHistory(startDatetime, endDatetime)

############################
##  Trading
############################

def buy(ticker, amount, priceLimit):
    """Buy a cryptocurrency."""
    LOGGER.log("buying %f of %s @ price %f" % (amount, ticker, priceLimit), moneyExchanged=True)
    if ticker not in constants.SUPPORTED_CRYPTOS:
        raise RuntimeError("ticker not supported: %s" % ticker)
    return kraken.buy(ticker, amount, priceLimit)

def sell(ticker, amount, priceLimit):
    """Sell a cryptocurrency."""
    LOGGER.log("selling %f of %s @ price %f" % (amount, ticker, priceLimit), moneyExchanged=True)
    if ticker not in constants.SUPPORTED_CRYPTOS:
        raise RuntimeError("ticker not supported: %s" % ticker)
    return kraken.sell(ticker, amount, priceLimit)
