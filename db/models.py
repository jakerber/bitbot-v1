"""BitBot MongoDB models."""
import datetime
import db
import json

EXCLUDE_PROPS = ["_id"]  # do not include these in model representations

class BitBotModel:
    """Parent model for all BitBot database collections."""
    def __repr__(self):
        return self.__dict__

class Price(BitBotModel):
    """Model for the price collection."""
    collectionName = "price"

    def __init__(self, ticker, openPrice, highPrice, lowPrice):
        self.ticker = ticker
        self.open = openPrice
        self.high = highPrice
        self.low = lowPrice
        self.date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.time = datetime.datetime.now().strftime("%H:%M:%S.%f")

    def __repr__(self):
        return str({prop: self.__dict__[prop] for prop in self.__dict__.keys()
    		        if prop not in ["_id"]})
