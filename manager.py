"""Manager module for fetching account and cryptocurrency info."""
from kraken import kraken
import constants
import logger

LOGGER = logger.Logger("Manager")

def getAccountBalance():
    """Get current account monetary balance."""
    LOGGER.log("fetching account balance")
    if constants.IS_SIMULATION:
        return constants.SIM_ACCOUNT_BALANCE
    else:
        return kraken.getAccountBalance()

def getBalance(ticker):
    """Get the current balance of a cryptocurrency."""
    LOGGER.log("fetching balance of %s" % ticker)
    if constants.IS_SIMULATION:
        return constants.SIM_BALANCES[ticker]
    else:
        return kraken.getBalance(ticker)

def getPrice(ticker, priceType):
    """Get the current price of a cryptocurrency."""
    if priceType not in constants.KRAKEN_PRICE_TYPES:
        raise RuntimeError("price request for %s price is unsupported" % priceType)
    return kraken.getPrice(ticker, priceType)

def buy(ticker, amount):
    """Buy a cryptocurrency."""
    LOGGER.log("buying %f of %s" % (amount, ticker))
    if constants.IS_SIMULATION:
        buyPrice = getPrice(ticker, priceType="ask")
        constants.SIM_BALANCES[ticker] += amount
        constants.SIM_ACCOUNT_BALANCE -= (buyPrice * amount)
        return buyPrice
    else:
        return kraken.buy(ticker, amount)  # returns buy price

def sell(ticker, amount):
    """Sell a cryptocurrency."""
    LOGGER.log("selling %f of %s" % (amount, ticker))
    if constants.IS_SIMULATION:
        sellPrice = getPrice(ticker, priceType="bid")
        constants.SIM_BALANCES[ticker] -= amount
        constants.SIM_ACCOUNT_BALANCE += (sellPrice * amount)
        return sellPrice
    else:
        kraken.sell(ticker, amount)  # returns sell price
