"""Cryptocurrency module for storing information about a cryptocurrency."""
import constants
import logger
import manager
import random
import time

class Crypto(object):
    """Cryptocurrency object."""
    def __init__(self, ticker):
        self.logger = logger.Logger(ticker)
        self.ticker = ticker
        self.balance = None

        # use custom setter for prices to ensure timestamp is also updated
        self.__buyPrice = None
        self.__buyPriceTimestamp = None
        self.__sellPrice = None
        self.__sellPriceTimestamp = None

        # update properties upon initialization
        self.updateAll()

    @property
    def buyPrice(self):
        """Cryptocurrency buy price property."""
        return self.__buyPrice

    @buyPrice.setter
    def buyPrice(self, newBuyPrice):
        """Cryptocurrency buy price property setter."""
        self.__buyPrice = newBuyPrice
        self.__buyPriceTimestamp = time.time()

    @property
    def sellPrice(self):
        """Cryptocurrency sell price property."""
        return self.__sellPrice

    @sellPrice.setter
    def sellPrice(self, newSellPrice):
        """Cryptocurrency sell price property setter."""
        self.__sellPrice = newSellPrice
        self.__sellPriceTimestamp = time.time()

    def updateAll(self):
        """Update all properties."""
        self.updateBalance()
        self.updatePrice()

    def updateBalance(self):
        """Update current balance property."""
        newBalance = manager.getBalance(self.ticker)
        if newBalance != self.balance:
            self.logger.log("updated balance = %f" % newBalance)
        self.balance = newBalance

    def updatePrice(self):
        """Update current price properties."""
        self.buyPrice = manager.getPrice(self.ticker, priceType="ask")
        self.sellPrice = manager.getPrice(self.ticker, priceType="bid")
        self.logger.log("buy=$%f, sell=$%f" % (self.buyPrice, self.sellPrice))

    def __str__(self):
        return "%s: price=%f, balance=%f" % (self.ticker, self.buyPrice, self.balance)
