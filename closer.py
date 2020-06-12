"""BitBot position closer module."""
import datetime
import logger

class Closer:
    """Object to close open trade positions."""
    def __init__(self, ticker, order, assistant):
        self.logger = logger.BitBotLogger("Closer")
        self.ticker = ticker
        self.order = order
        self.assistant = assistant

        # validate order type
        self.orderType = self.order.get("descr").get("type")
        if self.orderType not in ["buy", "sell"]:
            raise RuntimeError("unknown order type: %s", orderType)

        # fetch current price
        self.closingPriceType = "bid" if self.orderType == "buy" else "ask"
        self.currentPrice = self.assistant.getPrice(self.ticker, self.closingPriceType)

    ############################
    ##  Close approval
    ############################

    @property
    def approves(self):
        """Determine if positon should be closed."""
        # fetch price history from when initial order closed
        closeTimestamp = self.order.get("closetm")
        closeDatetime = datetime.datetime.fromtimestamp(closeTimestamp)
        priceHistory = self.assistant.getPriceHistory(self.ticker, startingDatetime=closeDatetime)

        # filter price history by relevant price type
        priceHistory = [price.get(self.closingPriceType) for price in self.priceHistory]

        # analyze trailing stop loss
        analysis = trailing_stop_loss.TrailingStopLoss(ticker, orderType, self.currentPrice, priceHistory).analyze()

        # determine trade approval
        percentDifference, actionablePrice = trailingStopLoss.shouldClosePosition()
        _approval = percentDifference >= constants.PERCENT_TRAILING_STOP_LOSS_THRESHOLD

        # return approval
        if _approval:
            self.logger.log({"actionable_price": actionablePrice, "percent_difference": percentDifference})
            self.logger.log("%s close approved!" % self.ticker)
        return _approval

    ############################
    ##  Close execution
    ############################

    def execute(self):
        """Close a trade position."""
        startingPrice = self.order.get("price")
        tradeAmount = self.order.get("vol")

        # determine trading method
        if self.orderType == "buy":
            tradingMethod = self.assistant.short
            useMargin = False
            profit = (self.currentPrice - startingPrice) * tradeAmount
        else:
            tradingMethod = self.assistant.buy
            useMargin = True
            profit = (startingPrice - self.currentPrice) * tradeAmount

        # safely close position

        self.logger.log("executing %s %s" % (self.ticker, tradingMethod.__name__))
        try:
            success, order = tradingMethod(ticker=self.ticker,
                                           amount=tradeAmount,
                                           useMargin=useMargin)  # TODO: specify margin from self.order.get("descr").get("leverage")
        except Exception as err:
            self.logger.log("unable to close %s position: %s" % (self.ticker, str(err)))
            return None, None, None

        # return order confirmation if trade was successful
        return success, order, profit
