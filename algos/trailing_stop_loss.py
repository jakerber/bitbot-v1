"""Trailing stop loss algo module."""

class TrailingStopLoss:
    """Object to perform trailing stop loss analysis on open positons."""
    def __init__(self, ticker, orderType, currentPrice, priceHistory):
        self.ticker = ticker
        self.orderType = orderType
        self.currentPrice = currentPrice
        self.priceHistory = priceHistory
        self.actionablePrice = None
        self.percentDifference = None

        # verify order type
        if self.orderType not in ["buy", "sell"]:
            raise RuntimeError("unknown order type: %s" % self.orderType)

    def analyze(self):
        """Determine price deviation from extreme (peak / valley)."""
        priceOperation = max if self.orderType == "buy" else min

        # determine actionable price
        # if buy: actionable price = peak since buy
        # if sell: actionable price = valley since sell
        for price in self.priceHistory:
            if not self.actionablePrice:
                self.actionablePrice = price
            else:
                self.actionablePrice = priceOperation(price, self.actionablePrice)

        # calulate different between current and actionable prices
        # if buy: percent difference = how much price has fallen from max
        # if sell: percent difference = how much price has risen from min
        if self.orderType == "buy":
            self.percentDifference = (self.actionablePrice - self.currentPrice) / self.actionablePrice
        else:
            self.percentDifference = (self.currentPrice - self.actionablePrice) / self.actionablePrice

        # price deviation
        return self.percentDifference, self.actionablePrice
