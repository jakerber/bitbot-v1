"""Trader module for buying and selling cryptocurrency."""
import random
import time

from algos import algos
import constants
import crypto
import logger
import manager

class Bet:
    """Bet object."""
    def __init__(self, ticker, amount, priceTarget):
        self.ticker = ticker
        self.amount = amount
        self.priceTarget = priceTarget
        self.isActive = True

class Trader:
    """Trader object."""
    def __init__(self, ticker):
        # static properties
        self.name = "%s Trader" % ticker

        # dynamic properties
        self.crypto = crypto.Crypto(ticker)
        self.logger = logger.Logger(self.name)
        self.activeBets = []
        self.tradesExecuted = 0
        self.killSelf = False  # for threading

    def considerBet(self):
        """Consider placing a bet on a cryptocurrency."""
        return algos.crunchNumbers(self.crypto)

    def kill(self):
        """Set property to True to break continuous trading loop."""
        self.killSelf = True

    def sellAll(self):
        """Sell of all off the owned cryptocurrency."""
        if not constants.IS_SIMULATION:
            raise RuntimeError("selling total balance is for simulation purposes only")

        # sell total balance
        self.logger.log("selling all")
        sellPrice = manager.sell(self.crypto.ticker, self.crypto.balance)
        self.tradesExecuted += 1
        self.logger.log("sold %f @ %f" % (self.crypto.balance, sellPrice), moneyExchanged=True)

    def trade(self):
        """Trade cryptocurrency based on price changes."""
        self.logger.log("beginning to trade...")
        while True:

            # pause time window
            time.sleep(constants.SLEEP_INTERVAL)

            # update crypto data
            # used to reduce calls to api
            self.crypto.update()

            # stop trading if BitBot has demanded such
            if self.killSelf:
                self.logger.log("killing self")
                self.sellAll()
                break  # breaking loop kills trading thread

            # sell active bets if target price is met
            for activeBet in self.activeBets:
                if self.crypto.sellPrice >= activeBet.priceTarget:
                    self.logger.log("price target of %f met" % activeBet.priceTarget)
                    sellPrice = manager.sell(self.crypto.ticker, activeBet.amount)
                    activeBet.isActive = False
                    self.tradesExecuted += 1
                    self.logger.log("sold %f @ %f" % (activeBet.amount, sellPrice), moneyExchanged=True)
            self.activeBets = [bet for bet in self.activeBets if bet.isActive]

            # place bet if algos say so
            shouldBet, buyAmount, priceTarget = self.considerBet()
            if shouldBet:
                buyPrice = manager.buy(self.crypto.ticker, buyAmount)
                self.tradesExecuted += 1
                self.activeBets.append(Bet(self.crypto.ticker, buyAmount, priceTarget))
                self.logger.log("bought %f @ %f with price target %f" % (buyAmount, buyPrice, priceTarget), moneyExchanged=True)

        # log final message
        self.logger.log("goodbye.")
