"""BitBot database models module."""
import constants
import datetime
import db
import json

class BitBotModel:
    """Object representing base entry in the database."""
    def __repr__(self):
        return str({prop: self.__dict__.get(prop) for prop in self.__dict__.keys()
                    if prop not in constants.MONGODB_EXCLUDE_PROPS})

class Equity(BitBotModel):
    """Database entry representing account equity."""
    collectionName = "equity"

    def __init__(self, balance, unrealizedNetProfit, marginUsed):
        self.balance = balance
        self.margin_used = marginUsed
        self.unrealized_net_profit = unrealizedNetProfit
        self.value = balance + unrealizedNetProfit
        self.utc_datetime = datetime.datetime.utcnow()

class Position(BitBotModel):
    """Database entry representing a trade position."""
    collectionName = "position"

    def __init__(self, ticker, transactionId, description):
        self.ticker = ticker
        self.transaction_id = transactionId
        self.description = description
        self.mean_reverted = False
        self.utc_datetime = datetime.datetime.utcnow()

class Price(BitBotModel):
    """Database entry representing an asset price."""
    collectionName = "price"

    def __init__(self, ticker, ask, bid, vwap):
        self.ticker = ticker
        self.ask = ask
        self.bid = bid
        self.vwap = vwap
        self.utc_datetime = datetime.datetime.utcnow()
