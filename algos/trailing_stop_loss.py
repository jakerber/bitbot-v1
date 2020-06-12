"""Trailing stop loss algo module."""

class TrailingStopLoss:
    """Object to perform trailing stop loss analysis on open positons."""
    def __init__(self, ticker, orderType, currentPrice, priceHistory):
        self.ticker = ticker
        self.orderType = orderType
        self.currentPrice = currentPrice
        self.priceHistory = priceHistory

        # verify order type
        if self.orderType not in ["buy", "sell"]:
            raise RuntimeError("unknown order type: %s" % self.orderType)

    def shouldClosePosition(self):
        """Determine if position should be closed."""
        actionablePrice = None
        priceOperation = max if self.orderType == "buy" else min

        # determine actionable price
        # if buy: actionable price = peak since buy
        # if sell: actionable price = valley since sell
        for price in self.priceHistory:
            if not actionablePrice:
                actionablePrice = price
            else:
                actionablePrice = priceOperation(price, actionablePrice)

        # calulate different between current and actionable prices
        # if buy: percent difference = how much price has fallen from max
        # if sell: percent difference = how much price has risen from min
        if self.orderType == "buy":
            percentDifference = (actionablePrice - self.currentPrice) / actionablePrice
        else:
            percentDifference = (self.currentPrice - actionablePrice) / actionablePrice

        # decide if position should be closed
        return percentDifference > constants.PERCENT_DEVIATION_TRAILING_STOP_LOSS_THRESHOLD:
