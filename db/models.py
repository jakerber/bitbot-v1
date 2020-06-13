"""BitBot database models module."""
import constants
import datetime
import db
import json

class BitBotModel:
    """Object representing base entry in all collections."""
    def __repr__(self):
        return str({prop: self.__dict__.get(prop) for prop in self.__dict__.keys()
                    if prop not in constants.MONGODB_EXCLUDE_PROPS})

class OpenPosition(BitBotModel):
    """Object representing an entry in the position collection."""
    collectionName = "position"

    def __init__(self, ticker, transactionId, description):
        self.ticker = ticker
        self.transaction_id = transactionId
        self.description = description
        self.utc_datetime = datetime.datetime.utcnow()

class Price(BitBotModel):
    """Object representing an entry in the price collection."""
    collectionName = "price"

    def __init__(self, ticker, ask, bid, vwap):
        self.ticker = ticker
        self.ask = ask
        self.bid = bid
        self.vwap = vwap
        self.utc_datetime = datetime.datetime.utcnow()
