"""BitBot position closer module."""
import constants
import datetime
import logger

class Closer:
    """Object to close open trade positions."""
    def __init__(self, ticker, analysis, assistant):
        self.logger = logger.BitBotLogger("Closer")
        self.ticker = ticker
        self.analysis = analysis
        self.assistant = assistant

    ############################
    ##  Close approval
    ############################

    @property
    def approves(self):
        """Determine if positon should be closed."""
        # verify position exceeds trailing stop-loss close threshold
        _approval = self.analysis.percent_difference >= constants.PERCENT_DEVIATION_CLOSE_THRESHOLD

        # return approval
        self.logger.log(self.analysis.__dict__)
        if _approval:
            self.logger.log("%s close approved!" % self.ticker)
        return _approval

    ############################
    ##  Close execution
    ############################

    def execute(self):
        """Close a trade position."""
        # determine trading method
        if self.analysis.initial_order_type == "buy":
            tradingMethod = self.assistant.sell
        else:
            tradingMethod = self.assistant.buy

        # safely close position
        self.logger.log("executing %s %s" % (self.ticker, tradingMethod.__name__))
        try:
            success, order = tradingMethod(ticker=self.ticker,
                                           volume=self.analysis.trade_volume,
                                           leverage=self.analysis.leverage)
        except Exception as err:
            self.logger.log("unable to close %s position: %s" % (self.ticker, str(err)))
            return None, None, None

        # return order confirmation if close was successful
        return success, order, self.analysis.unrealized_profit
