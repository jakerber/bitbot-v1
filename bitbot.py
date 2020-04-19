"""Bitcoin trading bot module."""
import time

import trader
import constants
import logger
import manager
import thread

class BitBot:
    """Bitcoin trading bot object."""
    def __init__(self):
        # static properties
        self.cryptos = constants.SUPPORTED_CRYPTOS
        self.startingAccountBalance = self.accountBalance
        self.name = "BitBot (sim)" if constants.IS_SIMULATION else "BitBot"

        # dynamic properties
        self.logger = logger.Logger(self.name)
        self.traderThreads = []
        self.tradesExecuted = 0

    @property
    def accountBalance(self):
        """Account balance property."""
        return manager.getAccountBalance()

    def go(self):
        """Begin trading with BitBot."""
        # initialize a trader for each supported crypto
        for cryptoTicker in self.cryptos:
            newTrader = trader.Trader(cryptoTicker)

            # traders will trade in their own seperate threads
            traderThread = thread.Thread(newTrader, newTrader.trade, newTrader.kill)
            traderThread.start()  # calls "run" method of thread object
            self.traderThreads.append(traderThread)

            # stagger the creation of trader threads to stagger requests
            time.sleep(float(constants.SLEEP_INTERVAL) / float(len(self.cryptos)))

        # keep child threads alive when parent dies
        for traderThread in self.traderThreads:
            traderThread.join()

    def start(self):
        """Start BitBot."""
        self._logStartup()
        try:
            self.go()  # start trading
        except KeyboardInterrupt:

            # kill traders and shutdown
            for traderThread in self.traderThreads:
                traderThread.kill()

            # wait for traders to complete last interval
            time.sleep(constants.SLEEP_INTERVAL + 1)
            self._logShutdown()

        # log final message
        self.logger.log("goodbye.")

    def _logStartup(self):
        """Log startup message with info on parameters."""
        logSubcomponents = ["cryptos allowed = %s" % ",".join(self.cryptos),
                            "starting balance = $%f" % self.startingAccountBalance]
        self.logger.log("Starting up!", subcomponents=logSubcomponents, seperate=True)

    def _logShutdown(self):
        """Inform the user that BitBot is exiting."""
        endingAccountBalance = self.accountBalance
        logSubcomponents = ["starting balance = $%f" % self.startingAccountBalance,
                            "ending balance = $%f" % endingAccountBalance,
                            "total profit = $%f" % (endingAccountBalance - self.startingAccountBalance)]
        self.logger.log("Shutting down.", subcomponents=logSubcomponents, seperate=True)
