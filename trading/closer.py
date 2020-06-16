"""BitBot position closer module."""
import constants
import datetime
from trading import trader

class Closer(trader.BitBotTrader):
    """Object to close open trade positions."""

    ############################
    ##  Close approval
    ############################

    @property
    def approves(self):
        """Determine if positon should be closed."""
        # verify mean reversion complete or trailing stop-loss close threshold exceeded
        if self.analysis.initial_order_type == "buy":
            meanReverted = self.analysis.current_price >= self.analysis.current_volume_weighted_average_price
        else:
            meanReverted = self.analysis.current_price <= self.analysis.current_volume_weighted_average_price
        stopLossMet = self.analysis.trailing_percentage >= constants.PERCENT_TRAILING_CLOSE_THRESHOLD

        # return approval
        _approval = meanReverted or stopLossMet
        if _approval:
            self.logger.log(self.analysis.__dict__)
            self.logger.log("%s close approved!" % self.ticker)
        return _approval

    ############################
    ##  Close execution
    ############################

    def execute(self):
        """Close a position."""
        # determine trading method
        if self.analysis.initial_order_type == "buy":
            tradingMethod = self.assistant.sell
        else:
            tradingMethod = self.assistant.buy

        # safely close position
        self.logger.log("executing %s %s" % (self.ticker, tradingMethod.__name__))
        try:
            success, order = tradingMethod(ticker=self.ticker,
                                           volume=self.analysis.volume,
                                           price=self.analysis.current_price,
                                           leverage=self.analysis.leverage)
        except Exception as err:
            self.logger.log("unable to close %s position: %s" % (self.ticker, str(err)))
            return None, None, None

        # return order confirmation if trade was successful
        return success, order, self.analysis.unrealized_profit_usd
