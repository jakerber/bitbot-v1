"""Logger module."""

SEPERATOR = "------------------------------------------------"
MONEY_EXCHANGE_INDICATOR = "***"

class Logger:
    """Logger object."""
    def __init__(self, componentName):
        self.componentName = componentName
        self.prefix = "{%s} ::" % self.componentName

    def log(self, text, subcomponents=[], moneyExchanged=False, seperate=False, wait=False):
        """Log a message to the console."""
        # open with seperator
        if seperate:
            self._seperate()

        # log message with subcomponents
        if moneyExchanged:
            text = "%s %s" % (MONEY_EXCHANGE_INDICATOR, text)
        print("%s %s" % (self.prefix, text))
        for subcomponent in subcomponents:
            self._logSubcomponent(subcomponent)

        # close with seperator
        if seperate:
            self._seperate(close=True)

        # await confirmation before continuing
        if wait:
            self._awaitConfirmation()

    def _awaitConfirmation(self):
        """Wait until user issues confirmation before continuing."""
        input("press ENTER to continue : ")

    def _logSubcomponent(self, subcomponent):
        """Log the subcomponent of a log message."""
        print("\t%s" % subcomponent)

    def _seperate(self, close=False):
        """Print log seperator."""
        template = "%s\n" if close else "\n%s"
        print(template % SEPERATOR)


    # def logShutdown(self, shutdownInfo):
    #     """Log a shutdown message with total profits."""
    #     # open with seperator
    #     self._seperate()
    #
    #     # log startup message with parameters
    #     print("%s Killing BitBot." % _get_prefix("SHUTDOWN"))
    #     for param_description in shutdownInfo:
    #         param_value = shutdownInfo[param_description]
    #         self._logSubcomponent("%s = %s" % (param_description, param_value))
    #
    #     # close with seperator
    #     self._seperate(close=True)
    #
    # def logStartup(self, startupInfo):
    #     """Log a startup message and continue with confirmation."""
    #     # open with seperator
    #     self._seperate()
    #
    #     # log startup message with parameters
    #     print("%s BitBot initialized!" % _get_prefix("STARTUP"))
    #     for param_description in startupInfo:
    #         param_value = startupInfo[param_description]
    #         self._logSubcomponent("%s = %s" % (param_description, param_value))
    #
    #     # close with seperator
    #     self._seperate(close=True)
    #
    #     # wait for user to issue confirmation
    #     self._awaitConfirmation()
