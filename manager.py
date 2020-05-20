"""Manager module for fetching account and cryptocurrency info."""
from kraken import kraken
import constants
import logger

LOGGER = logger.Logger("Manager")

def getAccountBalance():
    """Get current account balances."""
    LOGGER.log("fetching account balance")
    if constants.IS_SIMULATION:
        return constants.SIM_ACCOUNT_BALANCE
    else:
        return kraken.getAccountBalance()

def getBalance(ticker):
    """Get the current balance of a cryptocurrency."""
    LOGGER.log("fetching balance of %s" % ticker)
    if ticker not in constants.KRAKEN_CRYPTO_TICKERS.keys():
        raise RuntimeError("ticker not supported: %s" % ticker)
    if constants.IS_SIMULATION:
        return constants.SIM_BALANCES[ticker]
    else:
        return kraken.getBalance(ticker)

def getAllPrices(ticker):
    """Get all current prices of a cryptocurrency."""
    LOGGER.log("fetching all prices of %s" % ticker)
    if ticker not in constants.KRAKEN_CRYPTO_TICKERS.keys():
        raise RuntimeError("ticker %s not supported" % ticker)
    return kraken.getAllPrices(ticker)

def getPrice(ticker, priceType):
    """Get the current price of a cryptocurrency."""
    LOGGER.log("fetching %s price of %s" % (priceType, ticker))
    if ticker not in constants.KRAKEN_CRYPTO_TICKERS.keys():
        raise RuntimeError("ticker not supported: %s" % ticker)
    if priceType not in constants.KRAKEN_PRICE_TYPES:
        raise RuntimeError("price type not supported: %s" % priceType)
    return kraken.getPrice(ticker, priceType)

def buy(ticker, amount):
    """Buy a cryptocurrency."""
    LOGGER.log("buying %f of %s" % (amount, ticker))
    if constants.IS_SIMULATION:
        buyPrice = getPrice(ticker, priceType="ask")

        # determine if enough funds are available to buy
        buyDollarAmount = (buyPrice * amount)
        if buyDollarAmount > constants.SIM_ACCOUNT_BALANCE:
            LOGGER.log("unable to buy %s -- insufficient funds" % ticker)
            return None

        # update simulation balance constants
        constants.SIM_BALANCES[ticker] += amount
        constants.SIM_ACCOUNT_BALANCE -= buyDollarAmount
        return buyPrice
    else:
        return kraken.buy(ticker, amount)  # returns buy price

def sell(ticker, amount):
    """Sell a cryptocurrency."""
    LOGGER.log("selling %f of %s" % (amount, ticker))
    if constants.IS_SIMULATION:
        sellPrice = getPrice(ticker, priceType="bid")

        # update simulation balance constants
        constants.SIM_BALANCES[ticker] -= amount
        constants.SIM_ACCOUNT_BALANCE += (sellPrice * amount)
        return sellPrice
    else:
        kraken.sell(ticker, amount)  # returns sell price
