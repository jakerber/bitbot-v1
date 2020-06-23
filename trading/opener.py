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
        # verify price deviation exceeds threshold
        _approval = self.analysis.current_percent_deviation >= constants.PERCENT_DEVIATION_OPEN_THRESHOLD

        # ensure price is fluctuating more than vwap
        if self.analysis.price_change_24_hours > 0:
            _approval = _approval and self.analysis.price_change_24_hours > self.analysis.vwap_change_24_hours
        elif self.analysis.price_change_24_hours < 0:
            _approval = _approval and self.analysis.price_change_24_hours < self.analysis.vwap_change_24_hours
        else:  # no 24-hour price change (unlikely)
            _approval = False

        # return approval
        if _approval:
            self.logger.log(self.analysis.__dict__)
            self.logger.log("%s position approved!" % self.ticker)
        return _approval

    ############################
    ##  Trade execution
    ############################

    def execute(self):
        """Open a position."""
        # determine trading method
        if self.analysis.current_volume_weighted_average_price > self.analysis.current_price:
            tradingMethod = self.assistant.buy
            leverage = None
        else:
            tradingMethod = self.assistant.sell
            leverage = constants.DEFAULT_LEVERAGE

            # ensure sufficient margin before opening leveraged short
            marginLevel = self.assistant.getAccountBalances().get("margin_level")
            if marginLevel and marginLevel < constants.MARGIN_LEVEL_MINIMUM:
                self.logger.log("unable to open %s position: insufficient margin" % self.ticker)
                return False, None

        # determine volume to trade
        minimumVolume = constants.KRAKEN_CRYPTO_CONFIGS.get(self.ticker).get("minimum_volume")
        volume = constants.BASE_COST_USD / self.analysis.current_price
        volume = max(volume, minimumVolume)

        # safely open position
        self.logger.log("executing %s %s" % (self.ticker, tradingMethod.__name__))
        try:
            success, order = tradingMethod(ticker=self.ticker,
                                           volume=volume,
                                           leverage=leverage)
        except Exception as err:
            self.logger.log("unable to open %s position: %s" % (self.ticker, str(err)))
            return None, None

        # return order confirmation if trade was successful
        return success, order
