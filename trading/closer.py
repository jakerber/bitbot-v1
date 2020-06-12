"""BitBot position closer module."""
import constants
import datetime
import logger
from algos import trailing_stop_loss

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

        # store order constants
        self.startingPrice = float(self.order.get("price"))
        self.tradeAmount = float(self.order.get("vol"))
        self.leverage = int(self.order.get("descr").get("leverage")[0])

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
        try:
            priceHistory = self.assistant.getPriceHistory(self.ticker, startingDatetime=closeDatetime)
        except Exception as err:
            return False  # don't close position if no trade history

        # filter price history by relevant price type
        priceHistory = [price.get(self.closingPriceType) for price in priceHistory]

        # determine trade approval based on trailing stop loss analysis
        percentDifference, actionablePrice = trailing_stop_loss.TrailingStopLoss(self.ticker, self.orderType, self.currentPrice, priceHistory).analyze()
        _approval = percentDifference >= constants.PERCENT_DEVIATION_CLOSE_THRESHOLD

        # return approval
        if _approval:
            self.logger.log({"actionable_price": actionablePrice,
                             "percent_difference": percentDifference,
                             "current_price": self.currentPrice,
                             "initial_order_price": self.startingPrice})
            self.logger.log("%s close approved!" % self.ticker)
        return _approval

    ############################
    ##  Close execution
    ############################

    def execute(self):
        """Close a trade position."""
        # determine trading method
        if self.orderType == "buy":
            tradingMethod = self.assistant.sell
            profit = (self.currentPrice - self.startingPrice) * self.tradeAmount
        else:
            tradingMethod = self.assistant.buy
            profit = (self.startingPrice - self.currentPrice) * self.tradeAmount

        # safely close position
        self.logger.log("executing %s %s" % (self.ticker, tradingMethod.__name__))
        try:
            success, order = tradingMethod(ticker=self.ticker,
                                           amount=self.tradeAmount,
                                           leverage=self.leverage)
        except Exception as err:
            raise
            self.logger.log("unable to close %s position: %s" % (self.ticker, str(err)))
            return None, None, None

        # return order confirmation if close was successful
        return success, order, profit
