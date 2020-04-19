"""Trade cryptocurrency module."""

from kraken import kraken

def buy(ticker, amount):
    """Buy a cryptocurrency."""
    kraken.buy(ticker, amount)

def getAccountBalance():
    """Get current account monetary balance."""
    return kraken.getAccountBalance()

def getBalance(ticker):
    """Get the current balance of a cryptocurrency."""
    return kraken.getBalance(ticker)

def getPrice(ticker, priceType="ask"):
    """Get the current price of a cryptocurrency."""
    # execute kraken price request
    return kraken.getPrice(ticker, priceType)

def sell(ticker, amount):
    """Sell a cryptocurrency."""
    return kraken.sell(ticker, amount)
