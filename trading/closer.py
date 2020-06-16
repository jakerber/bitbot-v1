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
        # verify position is profitable or exceeds trailing stop-loss close threshold
        profitWithFees = self.analysis.unrealized_profit_usd * (1 - constants.TRADING_FEE)
        profitMet = profitWithFees > self.analysis.initial_fee
        stopLossMet = self.analysis.trailing_percentage >= constants.PERCENT_TRAILING_CLOSE_THRESHOLD

        # return approval
        _approval = profitMet or stopLossMet
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
                                           leverage=self.analysis.leverage)
        except Exception as err:
            self.logger.log("unable to close %s position: %s" % (self.ticker, str(err)))
            return None, None, None

        # return order confirmation if trade was successful
        return success, order, self.analysis.unrealized_profit_usd
