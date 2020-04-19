"""Bitcoin trading bot module."""
import time

import analyst
import constants
import logger
import thread

class BitBot:
    """Bitcoin trading bot object."""
    def __init__(self, dropThreshold, timeWindow, maxBuy):
        # static properties
        self.cryptos = constants.SUPPORTED_CRYPTOS
        self.dropThreshold = dropThreshold
        self.timeWindow = timeWindow
        self.maxBuy = maxBuy
        self.startingAccountBalance = self.currentAccountBalance

        # dynamic properties
        self.logger = logger.Logger("BitBot")
        self.analystThreads = []
        self.tradesExecuted = 0

    @property
    def currentAccountBalance(self):
        """Current account balance property."""
        raise NotImplementedError

    def getCryptoBalance(self, ticker):
        """Retrieve current cryptocurrency balance."""
        raise NotImplementedError

    def go(self):
        """Begin trading with BitBot."""
        threadCreationDelay = float(self.timeWindow) / float(len(self.cryptos))

        # initialize analysts for each supported crypto
        for cryptoTicker in self.cryptos:
            newAnalyst = analyst.Analyst(cryptoTicker, self.dropThreshold, self.timeWindow, self.maxBuy)

            # analysts will analyze in their own threads
            analystThread = thread.Thread(newAnalyst.name, newAnalyst.analyze, newAnalyst.kill)
            analystThread.start()  # calls "run" method of thread object
            self.analystThreads.append(analystThread)

            # stagger the creation of analyst threads to stagger requests
            time.sleep(threadCreationDelay)

        # keep child threads alive when parent dies
        for analystThread in self.analystThreads:
            analystThread.join()

    def start(self):
        """Start BitBot."""
        self._logStartup()
        try:
            self.go()  # start trading
        except KeyboardInterrupt:

            # kill analysts and shutdown
            for analystThread in self.analystThreads:
                analystThread.kill()
            self._logShutdown()

    def _logStartup(self):
        """Log startup message with info on parameters."""
        logSubcomponents = ["cryptos allowed = %s" % ",".join(self.cryptos),
                            "drop threshold (%%) = %f" % self.dropThreshold,
                            "time window (s) = %i" % self.timeWindow,
                            "max buy ($) = %f" % self.maxBuy,
                            "starting balance ($) = %f" % self.startingAccountBalance]
        self.logger.log("Starting up!", subcomponents=logSubcomponents, seperate=True, wait=True)

    def _logShutdown(self):
        """Inform the user that BitBot is exiting."""
        logSubcomponents = ["starting balance = %f" % self.startingAccountBalance,
                            "ending account balance = %f" % self.currentAccountBalance,
                            "trades executed = %i" % self.tradesExecuted,
                            "total profit = %f" % (self.currentAccountBalance - self.startingAccountBalance)]
        self.logger.log("Shutting down.", subcomponents=logSubcomponents, seperate=True)
