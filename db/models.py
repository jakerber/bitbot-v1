"""BitBot MongoDB models."""
import datetime
import db
import json

EXCLUDE_PROPS = ["id", "_id"]  # do not include these in model representations

class BitBotModel:
    """Parent model for all BitBot database collections."""
    def __repr__(self):
        return str({prop: self.__dict__[prop] for prop in self.__dict__.keys()
                    if prop not in EXCLUDE_PROPS})

class Alert(BitBotModel):
    """Model for the alert collection."""
    collectionName = "alert"

    def __init__(self, ticker, price, alertType):
        self.ticker = ticker
        self.price = price
        self.type = alertType
        self.date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.time = datetime.datetime.now().strftime("%H:%M:%S.%f")

class Price(BitBotModel):
    """Model for the price collection."""
    collectionName = "price"

    def __init__(self, ticker, openPrice, highPrice, lowPrice):
        self.ticker = ticker
        self.open = openPrice
        self.high = highPrice
        self.low = lowPrice
        self.date = datetime.datetime.now().strftime("%Y-%m-%d")
