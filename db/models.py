"""BitBot database models module."""
import constants
import datetime
import db
import json

class BitBotModel:
    """Object representing base entry in all collections."""
    def __repr__(self):
        return str({prop: self.__dict__[prop] for prop in self.__dict__.keys()
                    if prop not in constants.MONGODB_EXCLUDE_PROPS})

class Price(BitBotModel):
    """Object representing an entry in the price collection."""
    collectionName = "price"

    def __init__(self, ticker, openPrice, highPrice, lowPrice):
        self.ticker = ticker
        self.open = openPrice
        self.high = highPrice
        self.low = lowPrice
        self.date = datetime.datetime.now().strftime("%Y-%m-%d")
