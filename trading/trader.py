"""BitBot trader module."""
import abc
import logger

class BitBotTraderInterface(abc.ABC):
    """Interface to define trading classes."""

    @property
    def approves(self):
        """Determine if a trade should be executed."""

    def execute(self):
        """Execute trade."""

class BitBotTrader(BitBotTraderInterface):
    """Base class for trading objects."""
    def __init__(self, ticker, analysis, assistant):
        self.logger = logger.Logger("Trade%s" % type(self).__name__)
        self.ticker = ticker
        self.analysis = analysis
        self.assistant = assistant
