"""Cryptocurrency bet module."""
import crypto
import logger
import trade
import uuid

class Bet:
    """Cryptocurrency bet object."""
    def __init__(self, id, ticker, amount, targetPrice):
        # static properties
        self.id = id
        self.ticker = ticker
        self.amount = amount
        self.targetPrice = targetPrice

        # dynamic properties
        self.active = True
        self.logger = logger.Logger("%s BET ON %s" % (self.id, self.ticker))

    def placeBet(self):
        """Place the bet buying the amount of the cryptocurrency."""
        self.logger.log("placing bet to buy %f %s at target price $%f" % (self.amount, self.ticker, self.targetPrice))
        trade.buy(self.ticker, self.amount)

    def sellIfTargetReached(self, currentPrice):
        """Sell the cryptocurrency in this bet if the target price is reached."""
        if currentPrice >= self.targetPrice:
            self.logger.log("target price reached")
            sellPrice = trade.sell(self.ticker, self.amount)
            self.logger.log("sold %f %s at $%f" % (self.amount, self.ticker, sellPrice))
            self.active = False
