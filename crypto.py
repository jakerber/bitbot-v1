"""Cryptocurrency module."""
import random
import time
import trade

class Crypto(object):
    """Cryptocurrency object."""
    def __init__(self, ticker):
        self.ticker = ticker
        self.__lastPrice = None
        self.__lastPriceTimestamp = None

        # set last price to current price
        self.lastPrice = self.price

    @property
    def lastPrice(self):
        """Last Cryptocurrency price property."""
        return self.__lastPrice

    @lastPrice.setter
    def lastPrice(self, lastPrice):
        """Last Cryptocurrency price property and timestamp setter."""
        self.__lastPrice = lastPrice
        self.__lastPriceTimestamp = time.time()

    @property
    def lastPriceTimestamp(self):
        """Timestamp of last Cryptocurrency price property."""
        return self.__lastPriceTimestamp

    def setLastPrice(self, lastPrice):
        """Last Cryptocurrency last price and timestamp."""
        self.lastPrice = lastPrice
        self.lastPriceTimestamp = time.time()

    @property
    def balance(self):
        """Cryptocurrency balance property."""
        return trade.getBalance(self.ticker)

    @property
    def price(self):
        """Cryptocurrency price property."""
        return trade.getPrice(self.ticker)  # + random.uniform(-100, 100)  # TODO: remove this

    def __str__(self):
        return "%s: price=%f, balance=%f" % (self.ticker, self.price, self.balance)
