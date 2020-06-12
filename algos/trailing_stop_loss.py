"""Trailing stop-loss algo module."""

class TrailingStopLossAnalysis:
    """Object to store results from trailing stop-loss analysis."""
    def __init__(self, ticker, orderType, leverage, volume, currentPrice, initialPrice, percentDifference, actionablePrice, actionableDatetime, unrealizedProfit):
        self.ticker = ticker
        self.order_type = orderType
        self.leverage = leverage
        self.volume = volume
        self.current_price = currentPrice
        self.initial_price = initialPrice
        self.percent_difference = percentDifference
        self.actionable_price = actionablePrice
        self.actionable_datetime = actionableDatetime
        self.unrealized_profit = unrealizedProfit

class TrailingStopLoss:
    """Object to perform trailing stop-loss analysis on open positons."""
    def __init__(self, ticker, orderType, leverage, volume, currentPrice, initialPrice, priceHistory):
        self.ticker = ticker
        self.orderType = orderType  # initial trade that opened the position
        self.leverage = leverage
        self.volume = volume
        self.currentPrice = currentPrice
        self.initialPrice = initialPrice
        self.priceHistory = priceHistory

        # verify order type
        if self.orderType not in ["buy", "sell"]:
            raise RuntimeError("unknown order type: %s" % self.orderType)

    def analyze(self):
        """Determine price deviation from extreme (peak / valley)."""
        # determine actionable price
        actionablePrice = None
        actionableDatetime = None
        for price in self.priceHistory:

            # if initial buy: actionable price = peak since buy
            if self.orderType == "buy":
                _price = price.get("bid")
                _datetime = price.get("utc_datetime")
                if not actionablePrice or _price > actionablePrice:
                    actionablePrice = _price
                    actionableDatetime = _datetime

            # if initial sell: actionable price = valley since sell
            else:
                _price = price.get("ask")
                _datetime = price.get("utc_datetime")
                if not actionablePrice or _price < actionablePrice:
                    actionablePrice = _price
                    actionableDatetime = _datetime

        # calulate different between current and actionable prices
        # if initial buy: percent difference = how much price has fallen from max
        # if initial sell: percent difference = how much price has risen from min
        if self.orderType == "buy":
            percentDifference = (actionablePrice - self.currentPrice) / actionablePrice
            unrealizedProfit = (self.currentPrice - self.initialPrice) * self.volume
        else:
            percentDifference = (self.currentPrice - actionablePrice) / actionablePrice
            unrealizedProfit = (self.initialPrice - self.currentPrice) * self.volume

        # price trailing stop-loss analysis
        return TrailingStopLossAnalysis(self.ticker,
                                        self.orderType,
                                        self.leverage,
                                        self.volume,
                                        self.currentPrice,
                                        percentDifference,
                                        actionablePrice,
                                        actionableDatetime,
                                        unrealizedProfit)
