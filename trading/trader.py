"""BitBot trader module."""
import constants
import logger

class Trader:
    """Object to make executive decisions on trades and oversee order execution."""
    def __init__(self, ticker, analysis, assistant):
        self.logger = logger.BitBotLogger("Trader")
        self.assistant = assistant
        self.ticker = ticker
        self.analysis = analysis

    ############################
    ##  Trade approval
    ############################

    @property
    def approves(self):
        """Perform any finals check to decide if the cryptocurrency should be traded."""
        # verify trade exceeds price deviation threshold
        _approval = self.analysis.current_percent_deviation >= constants.PERCENT_DEVIATION_TRADE_THRESHOLD

        # return approval
        if _approval:
            self.logger.log(self.analysis.__dict__)
            self.logger.log("%s trade approved!" % self.ticker)
        return _approval

    ############################
    ##  Trade execution
    ############################

    def execute(self):
        """Trade cryptocurrency."""
        # determine trading method
        if self.analysis.current_volume_weighted_average_price > self.analysis.current_price:
            tradingMethod = self.assistant.buy
            actionName = "buy"
            leverage = None
        else:
            tradingMethod = self.assistant.sell
            actionName = "short"
            leverage = constants.DEFAULT_LEVERAGE

        # safely execute trade
        tradeVolume = self.getVolume()
        self.logger.log("executing %s %s" % (self.ticker, actionName))
        try:
            success, order = tradingMethod(ticker=self.ticker,
                                           volume=tradeVolume,
                                           leverage=leverage)
        except Exception as err:
            self.logger.log("unable to execute %s trade: %s" % (self.ticker, str(err)))
            return None, None

        # return order confirmation if trade was successful
        return success, order

    ############################
    ##  Trade specifications
    ############################

    def getVolume(self):
        """Determine how much of the cryptocurrency should be traded."""
        minimumVolume = constants.KRAKEN_CRYPTO_CONFIGS.get(self.ticker).get("minimum_volume")

        # calculate volume based on current price deviation
        deviationAboveThreshold = self.analysis.current_percent_deviation - constants.PERCENT_DEVIATION_TRADE_THRESHOLD
        multiplier = min(deviationAboveThreshold, constants.MAXIMUM_TRADE_VOLUME_MULTIPLIER)
        costUSD = constants.BASE_BUY_USD + (constants.BASE_BUY_USD * multiplier)
        volume = costUSD / self.analysis.current_price

        # override to minimum volume if minimum not met
        return max(volume, minimumVolume)
