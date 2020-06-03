"""Assistant module for fetching account and cryptocurrency info."""
from kraken import kraken
import constants
import logger

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

def getTradeHistory(startDatetime=None, endDatetime=None):
    """Get trade history."""
    logger.log("fetching trade history (%s -> %s)" % (startDatetime, endDatetime))
    return kraken.getTradeHistory(startDatetime, endDatetime)

############################
##  Trading
############################

def buy(ticker, amount, priceLimit, priceTarget):
    """Buy a cryptocurrency."""
    logger.log("buying %f of %s @ price %f (target %f)" % (amount, ticker, priceLimit, priceTarget))
    if ticker not in constants.SUPPORTED_CRYPTOS:
        raise RuntimeError("ticker not supported: %s" % ticker)
    if priceTarget < priceLimit:
        raise RuntimeError("price target (%f) must be above price limit (%f)" % (priceTarget, priceLimit))
    return kraken.buy(ticker, amount, priceLimit, priceTarget)

def short(ticker, amount, priceLimit, priceTarget):
    """Short a cryptocurrency."""
    logger.log("shorting %f of %s @ price %f (target %f)" % (amount, ticker, priceLimit, priceTarget))
    if ticker not in constants.SUPPORTED_CRYPTOS:
        raise RuntimeError("ticker not supported: %s" % ticker)
    if priceTarget > priceLimit:
        raise RuntimeError("price target (%f) must be below price limit (%f)" % (priceTarget, priceLimit))

    # determine if margin should be used
    useMargin = getBalance(ticker) < amount
    if useMargin and not constants.ALLOW_MARGIN_TRADING:
        raise RuntimeError("insufficient funds and margin trading is not allowed")

    return kraken.short(ticker, amount, priceLimit, priceTarget, useMargin)
