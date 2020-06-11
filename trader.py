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

    def approvesTrade(self):
        """Determine if a cryptocurrency should be traded."""
        if self.analysis.current_volume_weighted_average_price > self.analysis.current_price:
            tradeApproval = self.analysis.current_price < self.analysis.current_trend_price
        else:
            tradeApproval = self.analysis.current_price > self.analysis.current_trend_price

        # return trade approval
        if tradeApproval:
            self.logger.log(self.analysis.__dict__)
            self.logger.log("%s trade approved!" % self.ticker)
        return tradeApproval

    ############################
    ##  Trade execution
    ############################

    def executeTrade(self):
        """Trade cryptocurrency."""
        if self.analysis.current_volume_weighted_average_price > self.analysis.current_price:
            tradingMethod = self.assistant.buy
        else:
            tradingMethod = self.assistant.short

            # ensure margin trading is allowed before shorting
            if not constants.ALLOW_MARGIN_TRADING:
                raise RuntimeError("unable to short %s: margin trading is not allowed :(" % self.ticker)

        # gather trade specifications
        targetPrice = self.getTargetPrice()
        tradeAmount = self.getAmount()

        # execute trade
        self.logger.log("executing %s %s" % (self.ticker, tradingMethod.__name__))
        orderConfirmation = tradingMethod(ticker=self.ticker,
                                          amount=tradeAmount,
                                          price=self.analysis.current_price,
                                          targetPrice=targetPrice)
        self.logger.log("trade executed successfully")
        return orderConfirmation

    ############################
    ##  Trade specifications
    ############################

    def getTargetPrice(self):
        """Determine the target price of a cryptocurrency"""
        return self.analysis.current_trend_price

    def getAmount(self):
        """Determine how much of the cryptocurrency should be traded."""
        deviationAboveThreshold = self.analysis.current_percent_deviation - constants.PERCENT_DEVIATION_THRESHOLD
        multiplier = min(deviationAboveThreshold, constants.TRADE_AMOUNT_MULTIPLIER_MAX)
        tradeAmountUSD = constants.BASE_BUY_USD + (constants.BASE_BUY_USD * multiplier)
        return tradeAmountUSD / self.analysis.current_price
