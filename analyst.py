"""Analyst class to monitor the price of a cryptocurrency."""
import random
import time

import bet
import constants
import crypto
import logger

class Analyst:
    def __init__(self, ticker, dropThreshold, timeWindow, maxBuy):
        # static properties
        self.dropThreshold = dropThreshold
        self.timeWindow = timeWindow
        self.maxBuy = maxBuy
        self.name = "%s Analyst" % ticker

        # dynamic properties
        self.betNum = 0
        self.logger = logger.Logger(self.name)
        self.crypto = crypto.Crypto(ticker)
        self.startingPrice = self.crypto.price
        self.activeBets = []
        self.killSelf = False  # for threading

        # log starting price
        self.logger.log("starting price = $%f" % self.startingPrice)

    def analyze(self):
        """Analyze the price of a cryptocurrency."""
        while True:
            time.sleep(self.timeWindow)

            # store prices to reduce price api requests
            currentCryptoPrice = self.crypto.price
            lastCryptoPrice = self.crypto.lastPrice

            # sell active bets if target price reached
            for activeBet in self.activeBets:
                activeBet.sellIfTargetReached(currentCryptoPrice)
            self.activeBets = [bet for bet in self.activeBets if bet.active]

            # kill self if thread BitBot is shutting down
            if self.killSelf:
                self.logger.log("killing self")
                break

            # consider a bet if drop threshold is met
            percentDifference = self._getPercentDifference(currentCryptoPrice, lastCryptoPrice)
            if percentDifference < (self.dropThreshold * -1):
                self.logger.log("price dropped from %f to %f in %i seconds" % (lastCryptoPrice, currentCryptoPrice, self.timeWindow))
                self.logger.log("percent difference of %f%% < drop threshold of %f%%" % (percentDifference, self.dropThreshold))
                self.logger.log("considering a bet")

                # place bet if determined a smart move
                shouldBet, buyAmount, targetPrice = self.considerBet()
                if shouldBet:
                    self.betNum += 1
                    newBet = bet.Bet(self.betNum, self.crypto.ticker, buyAmount, targetPrice)
                    newBet.placeBet()
                    self.activeBets.append(newBet)

            # set last price
            self.crypto.lastPrice = currentCryptoPrice

        # log final message
        self.logger.log("goodbye.")

    def considerBet(self):
        """Consider placing a bet on a cryptocurrency."""
        return True, 1, self.crypto.lastPrice

    def kill(self):
        """Set prop to True to stop analysis."""
        self.killSelf = True

    def _getPercentDifference(self, currentPrice, previousPrice):
        """Get the percent difference between previous and current price."""
        return ((currentPrice - previousPrice) / previousPrice) * 100.0
