"""Bitcoin trading bot simulator module."""
import bitbot

IS_STARTUP = True
STARTING_ACCOUNT_BALANCE = 1000.0

class BitBotSimulator(bitbot.BitBot):
    """Bitcoin trading bot simulator class."""
    def __init__(self, dropThreshold, timeWindow, maxBuy):
        # simulator-specific properties
        self.accountBalance = STARTING_ACCOUNT_BALANCE

        # initialize BitBot
        super(BitBotSimulator, self).__init__(dropThreshold, timeWindow, maxBuy)

    @property
    def currentAccountBalance(self):
        """Current account balance property."""
        return self.accountBalance
