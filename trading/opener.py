"""BitBot position opener module."""
import constants
from trading import trader

class Opener(trader.BitBotTrader):
    """Object to open new trade positions."""

    ############################
    ##  Trade approval
    ############################

    @property
    def approves(self):
        """Determine if positon should be opened."""
        # verify trade exceeds price deviation threshold
        _approval = self.analysis.current_percent_deviation >= constants.PERCENT_DEVIATION_OPEN_THRESHOLD

        # return approval
        if _approval:
            self.logger.log(self.analysis.__dict__)
            self.logger.log("%s trade approved!" % self.ticker)
        return _approval

    ############################
    ##  Trade execution
    ############################

    def execute(self):
        """Open a position."""
        # determine trading method
        if self.analysis.current_volume_weighted_average_price > self.analysis.current_price:
            tradingMethod = self.assistant.buy
            actionName = "buy"
            leverage = None
        else:
            tradingMethod = self.assistant.sell
            actionName = "short"
            leverage = constants.DEFAULT_LEVERAGE


        # determine volume to trade
        minimumVolume = constants.KRAKEN_CRYPTO_CONFIGS.get(self.ticker).get("minimum_volume")
        volume = constants.OPEN_COST_USD / self.analysis.current_price
        volume = max(volume, minimumVolume)

        # safely execute trade
        self.logger.log("executing %s %s" % (self.ticker, actionName))
        try:
            success, order = tradingMethod(ticker=self.ticker,
                                           volume=volume,
                                           leverage=leverage)
        except Exception as err:
            self.logger.log("unable to execute %s trade: %s" % (self.ticker, str(err)))
            return None, None

        # return order confirmation if trade was successful
        return success, order
