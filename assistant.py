"""Assistant module for fetching account and cryptocurrency info."""
from kraken import kraken
import constants
import logger

LOGGER = logger.Logger("Assistant")

def getAccountBalance():
    """Get current account balances."""
    LOGGER.log("fetching account balance")
    return kraken.getAccountBalance()

def getBalance(ticker):
    """Get the current balance of a cryptocurrency."""
    LOGGER.log("fetching balance of %s" % ticker)
    if ticker not in constants.SUPPORTED_CRYPTOS:
        raise RuntimeError("ticker not supported: %s" % ticker)
    return kraken.getBalance(ticker)

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

def buy(ticker, amount):
    """Buy a cryptocurrency."""
    LOGGER.log("buying %f of %s" % (amount, ticker))
    return kraken.buy(ticker, amount)  # returns buy price

def sell(ticker, amount):
    """Sell a cryptocurrency."""
    LOGGER.log("selling %f of %s" % (amount, ticker))
    kraken.sell(ticker, amount)  # returns sell price
