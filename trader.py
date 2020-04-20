"""Trader module for buying and selling cryptocurrency."""
import random
import time

from algos import crunch
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

    @property
    def accountBalance(self):
        """Account balance property."""
        return manager.getAccountBalance()

    def considerBet(self):
        """Consider placing a bet on a cryptocurrency."""
        return crunch.crunchNumbers(self.crypto)

    def kill(self):
        """Set property to True to break continuous trading loop."""
        self.killSelf = True

    def sellAll(self):
        """Sell of all off the owned cryptocurrency."""
        if not constants.IS_SIMULATION:
            raise RuntimeError("selling total balance is for simulation purposes only")

        # update balance
        self.crypto.updateBalance()

        # sell total balance
        if self.crypto.balance:
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

            # update cryptocurrency price data
            # used to reduce calls to api
            self.crypto.updatePrice()

            # stop trading if BitBot has demanded such
            if self.killSelf:
                self.logger.log("killing self")
                self.sellAll()
                break  # breaking loop kills trading thread

            # determine if price target of any active bets were met
            for activeBet in self.activeBets:
                if self.crypto.sellPrice >= activeBet.priceTarget:
                    self.logger.log("price target of %f met" % activeBet.priceTarget)

                    # sell bet that met price target
                    sellPrice = manager.sell(self.crypto.ticker, activeBet.amount)
                    activeBet.isActive = False
                    self.tradesExecuted += 1
                    self.logger.log("sold %f @ %f" % (activeBet.amount, sellPrice), moneyExchanged=True)
                    self.logger.log("updated account balance = %f" % (self.accountBalance))

                    # update cryptocurrency balance after sell
                    self.crypto.updateBalance()

            self.activeBets = [bet for bet in self.activeBets if bet.isActive]

            # consult algos to see if buying is a smart move
            shouldBet, buyAmount, priceTarget = self.considerBet()
            if shouldBet:
                buyPrice = manager.buy(self.crypto.ticker, buyAmount)
                if not buyPrice:
                    self.logger.log("unable to buy")  # usually because of insufficient funds
                else:
                    self.tradesExecuted += 1
                    bet = Bet(self.crypto.ticker, buyAmount, priceTarget)
                    self.activeBets.append(bet)
                    self.logger.log("bought %f @ %f with price target %f" % (buyAmount, buyPrice, priceTarget), moneyExchanged=True)
                    self.logger.log("updated account balance = %f" % (self.accountBalance))

                    # update cryptocurrency balance after buy
                    self.crypto.updateBalance()

        # log final message
        self.logger.log("goodbye.")
