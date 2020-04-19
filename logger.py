"""Logger module for printing information to the console."""

SEPERATOR = "------------------------------------------------"
MONEY_EXCHANGE_INDICATOR = "***"

class Logger:
    """Logger object."""
    def __init__(self, componentName):
        self.componentName = componentName
        self.prefix = "{%s} ::" % self.componentName

    def log(self, text, subcomponents=[], moneyExchanged=False, seperate=False):
        """Log a message to the console."""
        # open with seperator
        if seperate:
            self._seperate()

        # log message with subcomponents
        message = "%s %s" % (self.prefix, text)
        if moneyExchanged:
            message = "%s %s" % (MONEY_EXCHANGE_INDICATOR, message)
        print(message)
        for subcomponent in subcomponents:
            self._logSubcomponent(subcomponent)

        # close with seperator
        if seperate:
            self._seperate(close=True)

    def _logSubcomponent(self, subcomponent):
        """Log the subcomponent of a log message."""
        print("\t%s" % subcomponent)

    def _seperate(self, close=False):
        """Print log seperator."""
        template = "%s\n" if close else "\n%s"
        print(template % SEPERATOR)
